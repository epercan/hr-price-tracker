#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
mkdir -p data
echo "=== $(date '+%Y-%m-%d %H:%M') ===" >> data/daily.log
.venv/bin/python -m tracker run >> data/daily.log 2>&1
