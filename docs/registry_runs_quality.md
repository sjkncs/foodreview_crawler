# Unified Registry, Runs, and Quality Artifacts

## Store Registry

`data/store_registry.json` is generated from the overseas store Excel workbook:

```powershell
python -X utf8 scripts\build_store_registry.py --excel "C:\Users\Administrator\Desktop\海外店鋪.xlsx" --output data\store_registry.json
```

The registry stores only non-secret operational metadata:

- store identity: `jde`, `store_name`, `country`, `country_code`, `city`
- platform locator: `platforms.<platform>.url`, `meta`, `note`
- local credential pointer: `platforms.<platform>.account_ref`

It must not store plaintext passwords. Passwords stay in local-only credential files under `data\`.

## Account Registry

`data/account_registry.local.json` is local-only and generated from existing platform credential files:

```powershell
python -X utf8 -m unified_collector.account_registry --write
```

Use masked inspection when debugging:

```powershell
python -X utf8 -m unified_collector.account_registry --masked
```

The public-safe registry references accounts by labels such as `hungry_panda:default`, `hungry_panda:kr`, `fantuan:ca`, `grabfood:sg`, and `keeta:default`.

## Run Artifacts

Every coordinated task receives a `run_id` and writes:

- `exports\runs\<run_id>\checkpoint.json`
- `exports\runs\<run_id>\normalized_reviews.jsonl` for real runs with JSON output
- `exports\runs\<run_id>\quality_report.json` for real runs with JSON output

The checkpoint records task start, normalization, finish, and errors. It is the restart and audit anchor for long-running batches.

## Normalized Review JSONL

`normalized_reviews.jsonl` uses one record per review and standard fields:

`platform`, `country`, `account`, `store`, `store_id`, `rating`, `sub_ratings`, `review`, `review_language`, `translated_review`, `customer`, `review_time`, `order_id`, `ordered_items`, `order_detail`, `image_urls`, `source`, `raw_json`, `quality_flags`.

## Quality Report

`quality_report.json` currently includes:

- field completeness
- order detail coverage
- image URL count
- duplicate count
- out-of-range placeholder
- manual gate count placeholder
- error count
- retry candidates for missing order details

The next layer can feed this report plus `normalized_reviews.jsonl` to a model API for narrative inspection, failure classification, and retry planning.
