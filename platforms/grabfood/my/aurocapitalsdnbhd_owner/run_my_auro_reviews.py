from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "grabfood_weekly_reviews.py"


def main() -> int:
    command = [sys.executable, str(SCRIPT), "--account", "my_auro", *sys.argv[1:]]
    return subprocess.run(command).returncode


if __name__ == "__main__":
    raise SystemExit(main())
