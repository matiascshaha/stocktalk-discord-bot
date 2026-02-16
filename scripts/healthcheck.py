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

from scripts.test_flags import resolve_test_flags


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
    if proc.returncode != 0:
        status = "failed"
    else:
        has_skips = " skipped" in combined
        has_passes = " passed" in combined
        status = "skipped" if has_skips and not has_passes else "passed"
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
    for stale_artifact in (
        ARTIFACTS_DIR / "webull_smoke_report.json",
        ARTIFACTS_DIR / "discord_live_smoke.json",
    ):
        if stale_artifact.exists():
            stale_artifact.unlink()

    py = sys.executable
    try:
        flags = resolve_test_flags(os.environ, default_mode="local")
    except ValueError as exc:
        print(f"Flag configuration error: {exc}")
        return 2
    required_external_checks = set()

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
            [py, "-m", "pytest", "tests/unit/test_paths.py"],
            name="pathing_contracts",
            external=False,
        )
    )

    checks.append(
        _run(
            [
                py,
                "-m",
                "pytest",
                "tests/contract/test_ai_parser_contract.py",
                "tests/unit/test_parser_schema.py",
            ],
            name="parser_deterministic",
            external=False,
        )
    )

    checks.append(
        _run(
            [py, "-m", "pytest", "tests/integration"],
            name="discord_mocked",
            external=False,
        )
    )

    checks.append(
        _run(
            [py, "-m", "pytest", "tests/contract/test_webull_contract.py"],
            name="webull_contract",
            external=False,
        )
    )

    if flags.ai_live:
        required_external_checks.add("ai_live_smoke")
        checks.append(
            _run(
                [py, "-m", "pytest", "tests/smoke/test_ai_live_smoke.py", "-m", "smoke and live"],
                name="ai_live_smoke",
                external=True,
            )
        )
        required_external_checks.add("ai_to_trader_live_pipeline")
        checks.append(
            _run(
                [
                    py,
                    "-m",
                    "pytest",
                    "tests/integration/test_discord_flow.py",
                    "-k",
                    "live_ai_pipeline_message_to_trader",
                    "-m",
                    "smoke and live",
                ],
                name="ai_to_trader_live_pipeline",
                external=True,
            )
        )
    else:
        checks.append(
            CheckResult(
                name="ai_live_smoke",
                status="skipped",
                command=f"{py} -m pytest tests/smoke/test_ai_live_smoke.py -m 'smoke and live'",
                exit_code=0,
                duration_seconds=0.0,
                external=True,
                output_excerpt="TEST_AI_LIVE != 1",
            )
        )
        checks.append(
            CheckResult(
                name="ai_to_trader_live_pipeline",
                status="skipped",
                command=(
                    f"{py} -m pytest tests/integration/test_discord_flow.py "
                    "-k live_ai_pipeline_message_to_trader -m 'smoke and live'"
                ),
                exit_code=0,
                duration_seconds=0.0,
                external=True,
                output_excerpt="TEST_AI_LIVE != 1",
            )
        )

    if flags.discord_live:
        required_external_checks.add("discord_live_smoke")
        checks.append(
            _run(
                [py, "-m", "pytest", "tests/smoke/test_discord_live_smoke.py", "-m", "discord_live"],
                name="discord_live_smoke",
                external=True,
            )
        )
    else:
        checks.append(
            CheckResult(
                name="discord_live_smoke",
                status="skipped",
                command=f"{py} -m pytest tests/smoke/test_discord_live_smoke.py -m discord_live",
                exit_code=0,
                duration_seconds=0.0,
                external=True,
                output_excerpt="TEST_DISCORD_LIVE != 1",
            )
        )

    if flags.webull_read:
        required_external_checks.add("webull_read_smoke")
        checks.append(
            _run(
                [
                    py,
                    "-m",
                    "pytest",
                    "tests/smoke/test_webull_smoke.py",
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
                command=f"{py} -m pytest tests/smoke/test_webull_smoke.py -m 'smoke and live and not webull_write'",
                exit_code=0,
                duration_seconds=0.0,
                external=True,
                output_excerpt="TEST_WEBULL_READ != 1",
            )
        )

    if flags.webull_write:
        required_external_checks.add("webull_write_smoke")
        checks.append(
            _run(
                [
                    py,
                    "-m",
                    "pytest",
                    "tests/smoke/test_webull_smoke.py",
                    "-m",
                    "smoke and live and webull_write",
                ],
                name="webull_write_smoke",
                external=True,
            )
        )
    else:
        checks.append(
            CheckResult(
                name="webull_write_smoke",
                status="skipped",
                command=f"{py} -m pytest tests/smoke/test_webull_smoke.py -m 'smoke and live and webull_write'",
                exit_code=0,
                duration_seconds=0.0,
                external=True,
                output_excerpt="TEST_WEBULL_WRITE != 1",
            )
        )

    deterministic_failures = [c for c in checks if not c.external and c.status == "failed"]
    external_failures = [c for c in checks if c.external and c.status == "failed"]
    skips = [c for c in checks if c.status == "skipped"]
    required_external_skips = [c for c in checks if c.name in required_external_checks and c.status == "skipped"]

    if deterministic_failures:
        overall_status = "red"
        exit_code = 1
    elif flags.strict_external and any(c.name in required_external_checks for c in external_failures):
        overall_status = "red"
        exit_code = 1
    elif flags.strict_external and required_external_skips:
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
            "TEST_MODE": flags.mode,
            "TEST_AI_LIVE": "1" if flags.ai_live else "0",
            "TEST_AI_SCOPE": flags.ai_scope,
            "TEST_DISCORD_LIVE": "1" if flags.discord_live else "0",
            "TEST_WEBULL_READ": "1" if flags.webull_read else "0",
            "TEST_WEBULL_WRITE": "1" if flags.webull_write else "0",
            "TEST_WEBULL_ENV": flags.webull_env,
            "TEST_AI_PROVIDERS": flags.ai_providers,
            "TEST_BROKERS": flags.brokers,
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
