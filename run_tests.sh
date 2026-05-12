#!/bin/bash
set -euo pipefail

if [[ "${COVERAGE:-}" == "1" ]]; then
    pytest -n auto tests --cov=src --cov-report html
else
    pytest -n auto tests --testmon
fi