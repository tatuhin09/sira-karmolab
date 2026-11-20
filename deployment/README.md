# Azure demo deployment

Live training demo: https://sira-karmolab-tatuhin09.azurewebsites.net

The deployment uses a dedicated resource group and Linux Azure App Service Free (F1) plan. The pre-existing SIRA Firelab Container App is independent and is not modified.

## Entry point

Install `requirements.txt`, then use:

```bash
sh deployment/azure-startup.sh
```

The startup script runs one Gunicorn worker with four threads on port 8000. Keep one instance: duplicate-request locking and SQLite are designed for this deployment shape, not distributed replicas.

## Settings

| Setting | Purpose |
| --- | --- |
| `KARMOLAB_PUBLIC_HOST` | Exact public hostname, without scheme/path |
| `KARMOLAB_DATA_PATH` | Persistent database path; Azure uses `/home/karmolab/practice.sqlite3` |
| `KARMOLAB_AI_ENABLED` | `1` enables bounded optional Gemini calls |
| `KARMOLAB_GEMINI_MODEL` | `gemini-3.1-flash-lite`, subject to provider availability |
| `KARMOLAB_AI_DAILY_LIMIT` | Persisted UTC-day attempted-call cap; initial demo configuration is 10 |
| `GEMINI_API_KEY` | Private Azure app setting; never a repository file or browser value |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` for dependency installation during ZIP deployment |
| `ENABLE_ORYX_BUILD` | `true` |
| `WEBSITES_ENABLE_APP_SERVICE_STORAGE` | `true` |
| `WEBSITE_WARMUP_PATH` | `/healthz` |

App Service must have HTTPS-only enabled. Do not include a key or runtime database in a source ZIP. Use a reviewed file allowlist and private settings outside the deployment archive. The CLI output should show setting names only, never key values.

## Persistence and demo boundaries

SQLite is stored under persistent `/home`, outside the deployed code directory, so replacing application code does not overwrite practice records or reset the daily budget. Browser session cookies still control access to a session's history. There are no separate authenticated learner/trainer accounts. Use fictional data; review controls do not certify a trainer's identity.

`GET /healthz` checks application readiness without calling Gemini. Check the home page, scripts, logo, policy API, cookies and API boundaries before sharing the link.

## Free-plan limits

F1 has shared resource quotas and can sleep or reach platform limits. Cold starts can delay the first visit; this is not always-on production hosting and there is no promised availability SLA. Confirm the plan still reports `tier: Free` before any upgrade. Any paid upgrade or additional paid storage should be a separate decision. Free hosting does not guarantee free model calls: Gemini billing/quota are separate, and the application enforces its own bounded daily attempts.

The current deployment is a single-instance demo. Production use requires authentication, trainer-role authorization, a retention/deletion policy, abuse controls, backups and measured capacity.
