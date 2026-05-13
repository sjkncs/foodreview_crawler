from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from dataclasses import replace
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unified_collector.executors import run_task
from unified_collector.task_loader import load_task


URLS = (
    "http://127.0.0.1:8080/",
    "http://127.0.0.1:8080/global-ops",
    "http://127.0.0.1:8080/prototype",
    "http://127.0.0.1:8080/stitch-static/index.html",
    "http://127.0.0.1:8080/stitch-static/review_workbench_global/code.html",
)

DRY_RUN_TASKS = (
    "unified_collector/tasks/google_maps_single_store_sample.json",
    "unified_collector/tasks/google_maps_us_last7.json",
    "unified_collector/tasks/openrice_hk_last7.json",
    "unified_collector/tasks/fantuan_ca_last7.json",
)


async def fetch(client: httpx.AsyncClient, index: int) -> dict:
    url = URLS[index % len(URLS)]
    start = time.perf_counter()
    try:
        response = await client.get(url)
        return {
            "ok": response.status_code == 200,
            "status": response.status_code,
            "ms": (time.perf_counter() - start) * 1000,
            "url": url,
            "bytes": len(response.content),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "ERR",
            "ms": (time.perf_counter() - start) * 1000,
            "url": url,
            "error": repr(exc),
        }


async def http_smoke(concurrency: int) -> list[dict]:
    async with httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
        limits=httpx.Limits(max_connections=max(10, concurrency)),
    ) as client:
        return await asyncio.gather(*(fetch(client, index) for index in range(concurrency)))


def dry_run_task(path: str):
    task = load_task(path)
    task = replace(task, options={**task.options, "dry_run": True})
    return run_task(task)


async def dry_run_smoke(concurrency: int) -> list[dict]:
    async def worker(index: int) -> dict:
        path = DRY_RUN_TASKS[index % len(DRY_RUN_TASKS)]
        start = time.perf_counter()
        try:
            result = await asyncio.to_thread(dry_run_task, path)
            return {
                "ok": result.ok,
                "platform": result.platform,
                "ms": (time.perf_counter() - start) * 1000,
                "errors": result.errors,
            }
        except Exception as exc:
            return {
                "ok": False,
                "platform": path,
                "ms": (time.perf_counter() - start) * 1000,
                "errors": (repr(exc),),
            }

    return await asyncio.gather(*(worker(index) for index in range(concurrency)))


def summarize(name: str, results: list[dict]) -> bool:
    ok = [item for item in results if item["ok"]]
    bad = [item for item in results if not item["ok"]]
    latencies = [item["ms"] for item in results]
    print(f"[{name}] total={len(results)} ok={len(ok)} bad={len(bad)}")
    if latencies:
        p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]
        print(
            f"[{name}] latency_ms min={min(latencies):.1f} "
            f"avg={statistics.mean(latencies):.1f} p95={p95:.1f} max={max(latencies):.1f}"
        )
    if bad:
        for item in bad[:5]:
            print(f"[{name}:bad] {item}")
    return not bad


async def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test NiceGUI global ops console")
    parser.add_argument("--http-concurrency", type=int, default=60)
    parser.add_argument("--dry-run-concurrency", type=int, default=24)
    args = parser.parse_args()

    http_results = await http_smoke(args.http_concurrency)
    dry_results = await dry_run_smoke(args.dry_run_concurrency)

    http_ok = summarize("http", http_results)
    dry_ok = summarize("dry_run", dry_results)
    if not (http_ok and dry_ok):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
