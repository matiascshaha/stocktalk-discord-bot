#!/usr/bin/env python3
"""Reliability-first health checks for deterministic + optional smoke suites."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List


ARTIFACTS_DIR = Path("artifacts")
REPORT_PATH = ARTIFACTS_DIR / "health_report.json"


@dataclass
class CheckResult:
    name: str
    status: str
    command: str
    exit_code: int
    duration_seconds: float
    external: bool
    output_excerpt: str


def _run(command: List[str], name: str, external: bool = False) -> CheckResult:
    started = time.time()
    proc = subprocess.run(command, capture_output=True, text=True)
    elapsed = time.time() - started
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    excerpt = combined[-2500:] if combined else ""
    status = "passed" if proc.returncode == 0 else "failed"
    return CheckResult(
        name=name,
        status=status,
        command=" ".join(command),
        exit_code=proc.returncode,
        duration_seconds=round(elapsed, 3),
        external=external,
        output_excerpt=excerpt,
    )


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
            .strip()
        )
    except Exception:
        return "unknown"


def main() -> int:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    checks: List[CheckResult] = []

    checks.append(
        _run(
            [
                py,
                "-c",
                "from src.utils.paths import resolve_config_path, resolve_prompt_path; "
                "from config.settings import validate_config; "
                "print(resolve_config_path()); print(resolve_prompt_path('config/ai_parser.prompt')); "
                "print(validate_config() is not None)",
            ],
            name="config_path_validation",
            external=False,
        )
    )

    checks.append(
        _run(
            [py, "-m", "pytest", "tests/test_gpt_integration.py", "-m", "not live"],
            name="parser_deterministic",
            external=False,
        )
    )

    checks.append(
        _run(
            [py, "-m", "pytest", "tests/test_discord_integration.py"],
            name="discord_mocked",
            external=False,
        )
    )

    run_webull_read = os.getenv("RUN_WEBULL_READ_SMOKE") == "1"
    if run_webull_read:
        checks.append(
            _run(
                [
                    py,
                    "-m",
                    "pytest",
                    "tests/test_webull_smoke.py",
                    "-m",
                    "smoke and live and not webull_write",
                ],
                name="webull_read_smoke",
                external=True,
            )
        )
    else:
        checks.append(
            CheckResult(
                name="webull_read_smoke",
                status="skipped",
                command=f"{py} -m pytest tests/test_webull_smoke.py -m 'smoke and live and not webull_write'",
                exit_code=0,
                duration_seconds=0.0,
                external=True,
                output_excerpt="RUN_WEBULL_READ_SMOKE != 1",
            )
        )

    deterministic_failures = [c for c in checks if not c.external and c.status == "failed"]
    external_failures = [c for c in checks if c.external and c.status == "failed"]
    skips = [c for c in checks if c.status == "skipped"]

    if deterministic_failures:
        overall_status = "red"
        exit_code = 1
    elif external_failures:
        overall_status = "yellow"
        exit_code = 2
    else:
        overall_status = "green"
        exit_code = 0

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "overall_status": overall_status,
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "command": c.command,
                "exit_code": c.exit_code,
                "duration_seconds": c.duration_seconds,
                "external": c.external,
                "output_excerpt": c.output_excerpt,
            }
            for c in checks
        ],
        "failures": [c.name for c in checks if c.status == "failed"],
        "skips": [c.name for c in skips],
        "external_dependencies": {
            "RUN_LIVE_AI_TESTS": os.getenv("RUN_LIVE_AI_TESTS", "0"),
            "RUN_DISCORD_LIVE_SMOKE": os.getenv("RUN_DISCORD_LIVE_SMOKE", "0"),
            "RUN_WEBULL_READ_SMOKE": os.getenv("RUN_WEBULL_READ_SMOKE", "0"),
            "RUN_WEBULL_WRITE_TESTS": os.getenv("RUN_WEBULL_WRITE_TESTS", "0"),
            "WEBULL_PAPER_REQUIRED": os.getenv("WEBULL_PAPER_REQUIRED", "1"),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Health status: {overall_status.upper()}")
    for c in checks:
        print(f"- {c.name}: {c.status} (exit={c.exit_code})")
    print(f"JSON report: {REPORT_PATH}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
