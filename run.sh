#!/usr/bin/env bash
# Full pipeline: RPC backfill -> dbt build (models + tests) -> export (dashboard JSON, reports, chart)
set -euo pipefail
END_DAY=${1:-$(date -u -d yesterday +%F)}; N_DAYS=${2:-90}; RECON_DAY=${3:-$END_DAY}
.venv/bin/python -u scripts/backfill_rpc.py "$END_DAY" "$N_DAYS"
.venv/bin/dbt build --full-refresh --project-dir dbt --profiles-dir dbt
.venv/bin/python scripts/export.py "$RECON_DAY"
