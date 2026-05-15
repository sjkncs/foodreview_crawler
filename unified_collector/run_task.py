from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from dataclasses import replace

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from unified_collector.coordinator import COORDINATOR
    from unified_collector.task_loader import load_task
else:
    from .coordinator import COORDINATOR
    from .task_loader import load_task


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a unified review collection task")
    parser.add_argument("task", help="Path to task JSON")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the command without launching the collector")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print result JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task = load_task(args.task)
    if args.dry_run:
        task = replace(task, options={**task.options, "dry_run": True})
    result = COORDINATOR.dry_run(task) if args.dry_run else COORDINATOR.run(task, action="cli_run")
    if args.pretty:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result.to_dict(), ensure_ascii=False))
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
