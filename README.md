# HEYTEA Global Review Collector

Production-oriented, read-only review collection console for overseas HEYTEA stores.

## What This Repository Contains

- Unified task DSL and executor registry under `unified_collector/`.
- Platform collectors for Hungry Panda, Fantuan, GrabFood, Google Maps, KeeTa, OpenRice, Mfood, Aomi, Dianping and Uber Eats under `platforms/` and `scripts/`.
- NiceGUI + Stitch static console under `main.py` and `ui/stitch_static/`.
- Real-time task monitor, checkpoint-aware run artifacts, normalized review export and quality-report APIs.
- Visual-agent fallback scaffolding under `visual_agent/`.

## Safety Boundary

The system is designed for read-only collection only. It allows login, navigation, store selection, date filtering, list reading, detail popup reading and export. It must not reply, save, submit, delete, confirm payments or modify merchant-store configuration.

Local credentials, browser profiles, cookies, raw exports, logs, Excel workbooks and screenshots are intentionally excluded by `.gitignore`.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

Open:

```text
http://127.0.0.1:8080/stitch-static/login_animation/code.html
```

## Local-Only Configuration

Create local credential files under `data/`; do not commit them.

Common files:

- `data/account_registry.local.json`
- `data/unified_settings.local.json`
- `data/store_registry.json`
- platform-specific `data/*credentials.local.json`

The UI settings page supports model providers, Base URL, API format, checkpoint path, export path, concurrency, sync interval, human-gate thresholds and quality scoring weights.

## Main APIs

- `GET /api/unified/status`
- `GET /api/unified/tasks`
- `GET /api/unified/runs`
- `GET /api/unified/reviews?days=7|30`
- `GET /api/unified/quality-report?days=7|30`
- `POST /api/unified/monitor/run-once`
- `POST /api/unified/monitor/start`
- `POST /api/unified/monitor/stop`
- `POST /api/unified/platform-diagnose`
- `POST /api/unified/translate`

## Public Repository Notes

This repository intentionally does not include production credentials or raw customer/order data. To run real merchant collection, configure local credentials and sessions on the target machine, then use the console Help Center and Production Check before starting a real sync.
