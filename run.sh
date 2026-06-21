#!/usr/bin/env bash
# AI Morning Digest — daily run (wire this into cron). Portable: uses its own dir.
cd "$(dirname "$0")" || exit 1
if [ -f secrets.env ]; then set -a; . ./secrets.env; set +a; fi
./venv/bin/python digest.py >> digest.log 2>&1
