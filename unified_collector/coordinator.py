from __future__ import annotations

import os
import threading
import time
import uuid
from collections import deque
from dataclasses import replace
from typing import Any

from .artifacts import normalize_json_to_jsonl, run_dir, write_checkpoint
from .executors import run_task
from .platform_capabilities import canonical_platform
from .schema import CollectionTask, ExecutorResult


MAX_HISTORY = 40
DEFAULT_REAL_CONCURRENCY = 1
DEFAULT_DRY_RUN_CONCURRENCY = 8


class TaskCoordinator:
    """Process-local coordinator for safe UI-triggered collection tasks.

    The collector can launch browser automation, reuse login state, and touch the
    same merchant account. This coordinator makes those actions explicit:
    dry-runs may run concurrently; real tasks are globally bounded and
    platform/account scoped to avoid session collisions.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._real_limit = max(1, int(os.getenv("UNIFIED_COLLECTOR_REAL_CONCURRENCY", DEFAULT_REAL_CONCURRENCY)))
        self._dry_limit = max(1, int(os.getenv("UNIFIED_COLLECTOR_DRY_RUN_CONCURRENCY", DEFAULT_DRY_RUN_CONCURRENCY)))
        self._real_slots = threading.BoundedSemaphore(self._real_limit)
        self._dry_slots = threading.BoundedSemaphore(self._dry_limit)
        self._active_keys: dict[str, dict[str, Any]] = {}
        self._history: deque[dict[str, Any]] = deque(maxlen=MAX_HISTORY)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "active_count": len(self._active_keys),
                "active": list(self._active_keys.values()),
                "history": list(self._history),
                "real_concurrency": self._real_limit,
                "dry_run_concurrency": self._dry_limit,
            }

    def configure_limits(self, real_concurrency: int | None = None, dry_run_concurrency: int | None = None) -> dict[str, Any]:
        real_limit = max(1, int(real_concurrency or self._real_limit))
        dry_limit = max(1, int(dry_run_concurrency or self._dry_limit))
        with self._lock:
            if self._active_keys:
                return {
                    "ok": False,
                    "active_count": len(self._active_keys),
                    "message": "active tasks running; concurrency update deferred",
                    "real_concurrency": self._real_limit,
                    "dry_run_concurrency": self._dry_limit,
                }
            self._real_limit = real_limit
            self._dry_limit = dry_limit
            self._real_slots = threading.BoundedSemaphore(self._real_limit)
            self._dry_slots = threading.BoundedSemaphore(self._dry_limit)
            os.environ["UNIFIED_COLLECTOR_REAL_CONCURRENCY"] = str(self._real_limit)
            os.environ["UNIFIED_COLLECTOR_DRY_RUN_CONCURRENCY"] = str(self._dry_limit)
            return {
                "ok": True,
                "active_count": 0,
                "real_concurrency": self._real_limit,
                "dry_run_concurrency": self._dry_limit,
            }

    def dry_run(self, task: CollectionTask) -> ExecutorResult:
        return self.run(replace(task, options={**task.options, "dry_run": True}), action="dry_run")

    def validate(self, task: CollectionTask) -> ExecutorResult:
        task.validate()
        dry_task = replace(task, options={**task.options, "dry_run": True})
        result = self.run(dry_task, action="validate")
        return ExecutorResult(
            **{
                **result.to_dict(),
                "metrics": {
                    **result.metrics,
                    "validation": {
                        "schema": "ok",
                        "safe_mode": task.safety.safe_mode,
                        "deny_write_actions": task.safety.deny_write_actions,
                        "next_step": "Dry Run 验证通过后再执行真实采集；真实采集会受互斥锁和并发上限保护。",
                    },
                },
            }
        )

    def run(self, task: CollectionTask, action: str = "run") -> ExecutorResult:
        task.validate()
        is_dry_run = bool(task.options.get("dry_run"))
        semaphore = self._dry_slots if is_dry_run else self._real_slots
        key = self._task_key(task)
        run_id = uuid.uuid4().hex[:12]
        started_at = time.strftime("%Y-%m-%d %H:%M:%S")

        if not semaphore.acquire(blocking=False):
            return self._busy_result(
                task,
                run_id,
                key,
                f"{'Dry Run' if is_dry_run else '真实采集'}并发槽已满，请等待当前任务完成。",
            )

        registered = False
        try:
            with self._lock:
                if key in self._active_keys:
                    return self._busy_result(task, run_id, key, f"同一平台/账号正在执行：{key}")
                self._active_keys[key] = {
                    "run_id": run_id,
                    "key": key,
                    "platform": task.platform,
                    "account": task.account or task.country,
                    "action": action,
                    "dry_run": is_dry_run,
                    "started_at": started_at,
                }
                registered = True

            run_path = run_dir(run_id)
            write_checkpoint(
                run_id,
                "started",
                {
                    "task": task.to_dict(),
                    "action": action,
                    "dry_run": is_dry_run,
                    "task_key": key,
                    "run_dir": str(run_path),
                },
            )
            task = replace(task, options={**task.options, "run_id": run_id, "run_dir": str(run_path)})
            result = run_task(task)
            artifact_metrics: dict[str, Any] = {"run_dir": str(run_path), "checkpoint": str(run_path / "checkpoint.json")}
            if result.json_path and not is_dry_run:
                try:
                    artifact_metrics.update(normalize_json_to_jsonl(result.json_path, run_id))
                    write_checkpoint(run_id, "normalized", artifact_metrics)
                except Exception as exc:
                    artifact_metrics["normalization_error"] = str(exc)
                    write_checkpoint(run_id, "normalization_failed", artifact_metrics)
            write_checkpoint(
                run_id,
                "finished",
                {
                    "ok": result.ok,
                    "json_path": result.json_path,
                    "csv_path": result.csv_path,
                    "excel_path": result.excel_path,
                    "review_count": result.review_count,
                    "store_count": result.store_count,
                    "errors": result.errors,
                },
            )
            self._record_history(run_id, key, action, is_dry_run, started_at, result)
            return ExecutorResult(
                **{
                    **result.to_dict(),
                    "metrics": {
                        **result.metrics,
                        **artifact_metrics,
                        "run_id": run_id,
                        "action": action,
                        "task_key": key,
                        "started_at": started_at,
                        "coordinator": self._policy(is_dry_run),
                    },
                }
            )
        finally:
            if registered:
                with self._lock:
                    self._active_keys.pop(key, None)
            semaphore.release()

    def _task_key(self, task: CollectionTask) -> str:
        platform = canonical_platform(task.platform)
        account = task.account or task.country or "default"
        return f"{platform}:{account}"

    def _policy(self, is_dry_run: bool) -> dict[str, Any]:
        return {
            "dry_run": is_dry_run,
            "real_tasks": "全局默认串行，避免浏览器登录态和后台会话冲突。",
            "same_platform_account": "互斥执行，避免同账号跨任务抢占门店/筛选器。",
            "write_actions": "禁止回复、保存、删除、提交、支付、修改配置。",
        }

    def _busy_result(self, task: CollectionTask, run_id: str, key: str, message: str) -> ExecutorResult:
        return ExecutorResult(
            ok=False,
            platform=task.platform,
            account=task.account or task.country,
            errors=(message,),
            metrics={"run_id": run_id, "task_key": key, "coordinator": self._policy(bool(task.options.get("dry_run")))},
        )

    def _record_history(
        self,
        run_id: str,
        key: str,
        action: str,
        is_dry_run: bool,
        started_at: str,
        result: ExecutorResult,
    ) -> None:
        with self._lock:
            self._history.appendleft(
                {
                    "run_id": run_id,
                    "key": key,
                    "action": action,
                    "dry_run": is_dry_run,
                    "ok": result.ok,
                    "reviews": result.review_count,
                    "stores": result.store_count,
                    "started_at": started_at,
                    "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "errors": result.errors,
                }
            )


COORDINATOR = TaskCoordinator()
