#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Windows Docker Desktop project: Python orchestrates and flushes its actual WSL kernel.
exec .venv/Scripts/python.exe scripts/run_suite.py
