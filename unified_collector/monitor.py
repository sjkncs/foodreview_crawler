from __future__ import annotations

import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .coordinator import COORDINATOR
from .schema import CollectionTask, TimeRange
from .settings import load_settings
from .task_loader import load_task


MAX_EVENT_HISTORY = 200
DEFAULT_RANGE_DAYS = 7
MAX_RANGE_DAYS = 30


class EventBus:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._next_id = 1
        self._events: deque[dict[str, Any]] = deque(maxlen=MAX_EVENT_HISTORY)

    def publish(self, level: str, title: str, message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            event = {
                "id": self._next_id,
                "level": level,
                "title": title,
                "message": message,
                "payload": payload or {},
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
            self._next_id += 1
            self._events.append(event)
            return event

    def list_since(self, since_id: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            return [event for event in self._events if int(event["id"]) > since_id]

    def latest_id(self) -> int:
        with self._lock:
            return self._next_id - 1


EVENT_BUS = EventBus()


def validate_week_range(start_date: str = "", end_date: str = "", days: int | None = None) -> TimeRange:
    if days is not None:
        if days < 1 or days > MAX_RANGE_DAYS:
            raise ValueError("days must be between 1 and 30")
        return TimeRange(type="last_days", days=days)
    if not start_date or not end_date:
        return TimeRange(type="last_days", days=DEFAULT_RANGE_DAYS)
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must not be earlier than start_date")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise ValueError("date range cannot exceed 30 days")
    return TimeRange(type="fixed", start_date=start.isoformat(), end_date=end.isoformat(), days=(end - start).days + 1)


class PlatformSyncMonitor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._state: dict[str, Any] = {
            "running": False,
            "dry_run": True,
            "interval_seconds": 3600,
            "parallel_workers": 1,
            "templates": [],
            "time_range": {},
            "last_started_at": "",
            "last_finished_at": "",
            "last_results": [],
        }

    def start(
        self,
        task_dir: Path,
        templates: list[str],
        interval_seconds: int = 3600,
        dry_run: bool = True,
        time_range: TimeRange | None = None,
        parallel_workers: int | None = None,
    ) -> dict[str, Any]:
        interval_seconds = max(60, int(interval_seconds))
        if parallel_workers is None:
            settings = load_settings(include_secrets=False)
            parallel_workers = int(((settings.get("processing") or {}).get("parallel_workers")) or 1)
        parallel_workers = max(1, int(parallel_workers))
        with self._lock:
            if self._thread and self._thread.is_alive():
                self._state.update(
                    {
                        "dry_run": dry_run,
                        "interval_seconds": interval_seconds,
                        "parallel_workers": parallel_workers,
                        "templates": templates,
                        "time_range": time_range.__dict__ if time_range else {},
                    }
                )
                EVENT_BUS.publish(
                    "info",
                    "Sync monitor reconfigured",
                    f"{len(templates)} task template(s), interval {interval_seconds}s, workers={parallel_workers}",
                )
                return self.status()
            self._stop.clear()
            self._state.update(
                {
                    "running": True,
                    "dry_run": dry_run,
                    "interval_seconds": interval_seconds,
                    "parallel_workers": parallel_workers,
                    "templates": templates,
                    "time_range": time_range.__dict__ if time_range else {},
                    "last_started_at": "",
                    "last_finished_at": "",
                    "last_results": [],
                }
            )
            self._thread = threading.Thread(
                target=self._loop,
                args=(task_dir, templates, dry_run, time_range),
                daemon=True,
            )
            self._thread.start()
        EVENT_BUS.publish(
            "info",
            "Sync monitor started",
            f"{len(templates)} task template(s), interval {interval_seconds}s, workers={parallel_workers}",
        )
        return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        with self._lock:
            self._state["running"] = False
        EVENT_BUS.publish("info", "Sync monitor stopped", "Background platform synchronization has been stopped.")
        return self.status()

    def status(self) -> dict[str, Any]:
        with self._lock:
            state = dict(self._state)
        state["thread_alive"] = bool(self._thread and self._thread.is_alive())
        return state

    def set_interval_seconds(self, interval_seconds: int) -> dict[str, Any]:
        value = max(60, int(interval_seconds))
        with self._lock:
            self._state["interval_seconds"] = value
        EVENT_BUS.publish("info", "Sync interval updated", f"Background sync interval set to {value}s")
        return self.status()

    def _loop(
        self,
        task_dir: Path,
        templates: list[str],
        dry_run: bool,
        time_range: TimeRange | None,
    ) -> None:
        while not self._stop.is_set():
            with self._lock:
                active_templates = list(self._state.get("templates") or templates)
                active_dry_run = bool(self._state.get("dry_run", dry_run))
                active_interval = max(60, int(self._state.get("interval_seconds") or 3600))
                active_workers = max(1, int(self._state.get("parallel_workers") or 1))
                state_time_range = self._state.get("time_range") or {}
            runtime_range: TimeRange | None = time_range
            if state_time_range and isinstance(state_time_range, dict):
                runtime_range = TimeRange(
                    type=str(state_time_range.get("type") or "last_days"),
                    days=int(state_time_range.get("days") or DEFAULT_RANGE_DAYS),
                    start_date=str(state_time_range.get("start_date") or ""),
                    end_date=str(state_time_range.get("end_date") or ""),
                )
            self.run_once(
                task_dir,
                active_templates,
                dry_run=active_dry_run,
                time_range=runtime_range,
                parallel_workers=active_workers,
            )
            self._stop.wait(active_interval)
        with self._lock:
            self._state["running"] = False

    def run_once(
        self,
        task_dir: Path,
        templates: list[str],
        dry_run: bool = True,
        time_range: TimeRange | None = None,
        parallel_workers: int = 1,
    ) -> list[dict[str, Any]]:
        started_at = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            self._state["last_started_at"] = started_at
        worker_count = max(1, int(parallel_workers or 1))
        template_list = list(templates or [])
        if worker_count == 1 or len(template_list) <= 1:
            results = [self._run_template_once(task_dir, name, dry_run=dry_run, time_range=time_range) for name in template_list]
        else:
            max_workers = min(worker_count, len(template_list))
            results_by_name: dict[str, dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sync-monitor") as pool:
                future_map = {
                    pool.submit(self._run_template_once, task_dir, name, dry_run, time_range): name
                    for name in template_list
                }
                for future in as_completed(future_map):
                    name = future_map[future]
                    try:
                        results_by_name[name] = future.result()
                    except Exception as exc:
                        result = {"template": name, "ok": False, "error": str(exc)}
                        results_by_name[name] = result
                        EVENT_BUS.publish("error", "Platform sync worker exception", f"{name}: {exc}", result)
            results = [results_by_name.get(name, {"template": name, "ok": False, "error": "worker_result_missing"}) for name in template_list]
        with self._lock:
            self._state["last_finished_at"] = datetime.now().isoformat(timespec="seconds")
            self._state["last_results"] = results[-20:]
        return results

    def _run_template_once(
        self,
        task_dir: Path,
        name: str,
        dry_run: bool = True,
        time_range: TimeRange | None = None,
    ) -> dict[str, Any]:
        path = task_dir / name
        if not path.exists():
            result = {"template": name, "ok": False, "error": "template not found"}
            EVENT_BUS.publish("error", "Task template missing", name, result)
            return result
        try:
            task = load_task(path)
            if time_range:
                task = replace(task, time_range=time_range)
            task = replace(task, options={**task.options, "dry_run": dry_run})
            output = COORDINATOR.dry_run(task) if dry_run else COORDINATOR.run(task, action="sync")
            result = {"template": name, "ok": output.ok, "result": output.to_dict()}
            if output.ok:
                title = "Platform sync dry-run completed" if dry_run else "Platform sync completed"
                message = f"{output.platform}: reviews={output.review_count}, stores={output.store_count}"
                EVENT_BUS.publish("success", title, message, result)
            else:
                EVENT_BUS.publish("error", "Platform sync failed", f"{output.platform}: {output.errors}", result)
            return result
        except Exception as exc:
            result = {"template": name, "ok": False, "error": str(exc)}
            EVENT_BUS.publish("error", "Platform sync exception", f"{name}: {exc}", result)
            return result


SYNC_MONITOR = PlatformSyncMonitor()
