from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "fantuan_weekly_reviews.py"


def main() -> int:
    command = [sys.executable, str(SCRIPT), "--country", "ca", *sys.argv[1:]]
    return subprocess.run(command).returncode


if __name__ == "__main__":
    raise SystemExit(main())
