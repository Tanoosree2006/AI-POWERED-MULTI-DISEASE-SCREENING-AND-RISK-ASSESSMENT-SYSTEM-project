#!/usr/bin/env bash
set -euo pipefail
(cd ml && python -m pytest -q)
(cd backend && python -m pytest -q)
(cd frontend && npm test && npm run build)
echo "All suites finished"
