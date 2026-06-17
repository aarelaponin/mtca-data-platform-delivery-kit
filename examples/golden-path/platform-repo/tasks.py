#!/usr/bin/env python3
"""OS-agnostic task runner (works identically on Windows and macOS/Linux).
Usage: python tasks.py <setup|dbt-build|dbt-test|lint>"""
import subprocess, sys

def sh(cmd): print("+", cmd); raise SystemExit(subprocess.call(cmd, shell=True))

TASKS = {
    "setup":     "python -m pip install -U uv && uv venv && uv pip install dbt-clickhouse pre-commit sqlfluff ruff && pre-commit install",
    "dbt-build": "cd dbt && dbt build",
    "dbt-test":  "cd dbt && dbt test",
    "lint":      "pre-commit run --all-files",
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in TASKS:
        print("tasks:", ", ".join(TASKS)); raise SystemExit(2)
    sh(TASKS[sys.argv[1]])
