# GrabFood Review Collector

GrabFood is isolated under `platforms/grabfood/` and exports to `exports/grabfood/`.

## Accounts

- `my_auro`: Malaysia owner account A
- `my_puresips`: Malaysia owner account B
- `sg`: Singapore owner account

Credentials are loaded from command-line arguments, environment variables, or
`data/grabfood_credentials.local.json`. The `data/` directory is ignored by Git.

## Read-only Scope

The collector only logs in, opens Feedback, selects filters/stores, reads the
Customer reviews table, and opens the Reply drawer to read order detail text.
It does not type replies and does not click `Submit`.

## Fields

- Rating
- Review
- Customer
- Customer ID
- Store
- Type
- Date / time
- Ordered items from the Reply drawer when available
- Raw network JSON when the API response is captured

## Run

Malaysia Auro:

```bash
python platforms/grabfood/grabfood_weekly_reviews.py --account my_auro --max-reviews 100
```

Malaysia Puresips:

```bash
python platforms/grabfood/grabfood_weekly_reviews.py --account my_puresips --max-reviews 100
```

Singapore:

```bash
python platforms/grabfood/grabfood_weekly_reviews.py --account sg --max-reviews 100
```

Wrappers:

```bash
python platforms/grabfood/my/aurocapitalsdnbhd_owner/run_my_auro_reviews.py --max-reviews 100
python platforms/grabfood/my/puresipsdnbhd_owner/run_my_puresips_reviews.py --max-reviews 100
python platforms/grabfood/sg/run_sg_reviews.py --max-reviews 100
```

Smoke test one store:

```bash
python platforms/grabfood/grabfood_weekly_reviews.py --account my_auro --limit-stores 1 --max-reviews 3 --output-prefix smoke
```

If Grab shows OTP/captcha, run without `--headless` and add `--manual-login`.
