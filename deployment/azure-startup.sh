#!/bin/sh
set -eu
# One worker/instance: SQLite and duplicate-assessment locking are single-instance.
exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 45 --access-logfile - --error-logfile - cloud_app:app
