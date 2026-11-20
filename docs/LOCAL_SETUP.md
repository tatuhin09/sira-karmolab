# Local development setup

These instructions are for developers running their own copy. Visitors and judges can use the hosted demo without installing Python or supplying an API key.

## Run without a model key

Requirements: **Python 3.10+**, a modern browser, and an available local port. The application uses the Python standard library; no `pip install` is required. Python 3.14 was used for local verification. CI checks are configured separately.

```bash
git clone https://github.com/tatuhin09/sira-karmolab.git
cd sira-karmolab
python3 start_local.py
```

Open **http://127.0.0.1:8767/**. On Windows, use `py -3` instead of `python3` if needed.

```bash
python3 start_local.py --port 8770
```

Use the server rather than opening `dist/index.html` directly: history and assessment require the Python APIs. Press **Ctrl+C** to stop the server. Runtime databases are created automatically in `runtime/` and are not versioned.

## Enable Gemini in your own local copy

AI is disabled by default. Local observations are rule based; they are not a local LLM.

1. Obtain a Gemini Developer API key for a project with an available model and quota.
2. Store it in a private local file outside the repository, using this format:

```dotenv
GEMINI_API_KEY=YOUR_PRIVATE_KEY
```

3. Start with explicit opt-in:

```bash
python3 start_local.py --ai --key-file /absolute/path/to/private-key.env --model gemini-3.1-flash-lite --daily-limit 2
```

The launcher reads only the named key from that file. It does not run shell code or automatically load `.env`. An already configured `GEMINI_API_KEY` environment variable is also supported when `--key-file` is omitted. `.env.example` is a configuration reference, not an automatically loaded file.

The model ID above was used in limited real tests. Availability and limits depend on the provider and project. A Gemini consumer/student subscription does not by itself verify API entitlements; inspect the API project's quota and billing. Do not assume this code guarantees zero charges.

The app counts attempted calls, including failed calls, against a persisted **UTC-day** budget. The launcher accepts a limit from 1 to 20. Repeated submissions with the same ID return the saved result without another model request. No automatic retries are made. A socket timeout is configured for provider requests; it is not a hard end-to-end SLA. The browser allows 20 seconds for assessment requests.

When a limit is reached, practice continues with explicitly labelled local observations. Do not delete or reset the budget database to conceal usage. Use fictional practice text: automatic personal-data redaction is not implemented.

## Offline tests

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

If Node.js is installed, check browser-script syntax:

```bash
node --check dist/app.js
```

Unit and HTTP tests use mocked model responses and temporary databases; they do not need a key or spend API quota. Prior end-to-end browser checks covered the practice flow, persistence, language switching, session isolation, failure recovery, and mobile layout. The historical live-test observations and their limits are described in [evaluation](EVALUATION.md). The complete browser harness is not currently packaged as a portable test command in this repository.

## Hosted deployment

See [Azure deployment](../deployment/README.md) for the separate Flask/Gunicorn server, pinned dependencies, HTTPS settings and persistent storage. `start_local.py` is the local entry point; `cloud_app:app` is the hosted WSGI entry point.
