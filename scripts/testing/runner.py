#!/usr/bin/env python3
"""Canonical test runner for local development and CI."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping


ACK_VALUE = "YES_IM_LIVE"
DEFAULT_REPORT_PATH = Path("artifacts/ci_report.json")
LOGS_DIR = Path("artifacts/logs")
SUPPORTED_PROFILES = ("critical", "deterministic", "live-read", "all", "ai-live", "night-probe")
PROFILE_ALIASES = {
    "quick": "deterministic",
    "live": "live-read",
    "night": "night-probe",
}


@dataclass(frozen=True)
class SuiteSpec:
    name: str
    description: str
    command: List[str]
    env_overrides: Mapping[str, str]
    junit_path: str | None = None
    require_all_env: tuple[str, ...] = ()
    require_any_env: tuple[str, ...] = ()


@dataclass(frozen=True)
class SuiteResult:
    name: str
    status: str
    description: str
    command: str
    retry_command: str
    duration_seconds: float
    exit_code: int
    summary: str
    log_path: str
    junit_path: str | None
    missing_requirements: List[str]


def _pytest_suite(
    *,
    python_bin: str,
    name: str,
    description: str,
    pytest_args: Iterable[str],
    env_overrides: Mapping[str, str] | None = None,
    require_all_env: tuple[str, ...] = (),
    require_any_env: tuple[str, ...] = (),
) -> SuiteSpec:
    junit_path = f"artifacts/junit-{name}.xml"
    command = [python_bin, "-m", "pytest", *pytest_args, f"--junitxml={junit_path}"]
    return SuiteSpec(
        name=name,
        description=description,
        command=command,
        env_overrides=dict(env_overrides or {}),
        junit_path=junit_path,
        require_all_env=require_all_env,
        require_any_env=require_any_env,
    )


def resolve_profile_name(raw_profile: str) -> str:
    candidate = (raw_profile or "").strip().lower()
    resolved = PROFILE_ALIASES.get(candidate, candidate)
    if resolved not in SUPPORTED_PROFILES and resolved != "list":
        supported = ", ".join(("list", *SUPPORTED_PROFILES, *PROFILE_ALIASES.keys()))
        raise ValueError(f"Unsupported profile '{raw_profile}'. Supported values: {supported}")
    return resolved


def build_profile_suites(profile: str, *, ai_scope: str, ack: str | None, python_bin: str) -> List[SuiteSpec]:
    if profile == "critical":
        return [
            SuiteSpec(
                name="test_file_purity",
                description="Ensure test modules stay test-only and shared helpers stay in support folders.",
                command=[python_bin, "-m", "scripts.check_test_file_purity"],
                env_overrides={},
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="pathing_contracts",
                description="Validate config/prompt path resolution contract.",
                pytest_args=["tests/unit/test_paths.py"],
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="parser_contracts",
                description="Protect parser output contract and normalization behavior.",
                pytest_args=["tests/parser/contract/test_parser_contract.py", "tests/unit/test_parser_schema.py"],
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="discord_mocked_flow",
                description="Validate Discord message handling and order routing with deterministic fakes.",
                pytest_args=[
                    "tests/channels/discord/integration/test_message_flow.py",
                    "-k",
                    "not live_ai_pipeline_message_to_trader",
                ],
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="webull_paper_trade_flow",
                description="Validate Discord->Webull paper trade flow and picks logging behavior.",
                pytest_args=["tests/brokers/webull/integration/test_paper_trade_discord_flow.py"],
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="webull_account_context",
                description="Validate margin, buying power, and submit rejection handling.",
                pytest_args=["tests/brokers/webull/integration/test_paper_trade_account_context.py"],
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="webull_contract",
                description="Validate Webull adapter/sdk contract compatibility.",
                pytest_args=["tests/brokers/webull/contract/test_webull_contract.py"],
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="system_quality",
                description="Validate test tooling and quality-flag contract behavior.",
                pytest_args=["tests/system/integration"],
            ),
        ]

    if profile == "deterministic":
        return [
            SuiteSpec(
                name="test_file_purity",
                description="Ensure test modules stay test-only and shared helpers stay in support folders.",
                command=[python_bin, "-m", "scripts.check_test_file_purity"],
                env_overrides={},
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="deterministic_all",
                description="Run full deterministic suite (no smoke/live/write tests).",
                pytest_args=["tests", "-m", "not smoke and not live and not write"],
            ),
        ]

    if profile == "live-read":
        return [
            _pytest_suite(
                python_bin=python_bin,
                name="discord_live_smoke",
                description="Validate live Discord connectivity and channel access.",
                pytest_args=["tests/channels/discord/smoke/test_discord_live.py", "-m", "smoke and live and channel and source_discord"],
                env_overrides={"TEST_DISCORD_LIVE": "1"},
                require_all_env=("DISCORD_TOKEN", "CHANNEL_ID"),
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="webull_read_smoke_paper",
                description="Validate live Webull read path in paper mode (no write).",
                pytest_args=["tests/brokers/webull/smoke/test_webull_live.py", "-m", "smoke and live and not write and broker and broker_webull"],
                env_overrides={"TEST_WEBULL_READ": "1", "TEST_WEBULL_ENV": "paper", "TEST_BROKERS": "webull"},
                require_all_env=("WEBULL_TEST_APP_KEY", "WEBULL_TEST_APP_SECRET"),
            ),
        ]

    if profile == "all":
        return build_profile_suites("deterministic", ai_scope=ai_scope, ack=ack, python_bin=python_bin) + build_profile_suites(
            "live-read",
            ai_scope=ai_scope,
            ack=ack,
            python_bin=python_bin,
        )

    if profile == "ai-live":
        return [
            _pytest_suite(
                python_bin=python_bin,
                name="ai_live_smoke",
                description="Validate provider output against live AI smoke fixtures.",
                pytest_args=["tests/parser/smoke/test_ai_live.py", "-m", "smoke and live"],
                env_overrides={"TEST_AI_LIVE": "1", "TEST_AI_SCOPE": ai_scope},
                require_any_env=("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"),
            ),
            _pytest_suite(
                python_bin=python_bin,
                name="ai_to_trader_live_pipeline",
                description="Validate live AI parsing through deterministic trade-routing probe.",
                pytest_args=[
                    "tests/channels/discord/integration/test_message_flow.py",
                    "-k",
                    "live_ai_pipeline_message_to_trader",
                    "-m",
                    "smoke and live",
                ],
                env_overrides={"TEST_AI_LIVE": "1", "TEST_AI_SCOPE": ai_scope},
                require_any_env=("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"),
            ),
        ]

    if profile == "night-probe":
        if ack != ACK_VALUE:
            raise ValueError(f"night-probe requires --ack {ACK_VALUE}")
        return [
            _pytest_suite(
                python_bin=python_bin,
                name="webull_night_probe_production",
                description="Manually-acknowledged production write probe with cancellation cleanup.",
                pytest_args=[
                    "tests/brokers/webull/smoke/test_webull_live.py",
                    "-k",
                    "night_probe_production_manual_cleanup",
                    "-m",
                    "smoke and live and write and broker and broker_webull",
                ],
                env_overrides={
                    "TEST_WEBULL_WRITE": "1",
                    "TEST_WEBULL_ENV": "production",
                    "TEST_WEBULL_NIGHT_PROBE": "1",
                    "TEST_WEBULL_PROD_ACK": ack,
                    "TEST_BROKERS": "webull",
                },
                require_all_env=("WEBULL_APP_KEY", "WEBULL_APP_SECRET"),
            )
        ]

    raise ValueError(f"Unsupported profile: {profile}")


def _format_command(command: Iterable[str], env_overrides: Mapping[str, str]) -> str:
    env_prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in env_overrides.items())
    command_text = " ".join(shlex.quote(item) for item in command)
    return f"{env_prefix} {command_text}".strip()


def _missing_requirements(base_env: Mapping[str, str], suite: SuiteSpec) -> List[str]:
    missing = [name for name in suite.require_all_env if not str(base_env.get(name, "")).strip()]
    if suite.require_any_env and not any(str(base_env.get(name, "")).strip() for name in suite.require_any_env):
        missing.append(f"one-of:{','.join(suite.require_any_env)}")
    return missing


def _extract_summary(stdout: str, stderr: str) -> str:
    combined_lines = [line.strip() for line in (stdout + "\n" + stderr).splitlines() if line.strip()]
    for line in reversed(combined_lines):
        if re.search(r"\b(passed|failed|skipped|xfailed|xpassed|error)\b", line):
            return line
    return "No explicit pytest summary line found."


def _build_log_text(suite: SuiteSpec, command_text: str, stdout: str, stderr: str) -> str:
    parts = [
        f"Suite: {suite.name}",
        f"Description: {suite.description}",
        f"Command: {command_text}",
        "",
        "=== STDOUT ===",
        stdout.rstrip(),
        "",
        "=== STDERR ===",
        stderr.rstrip(),
        "",
    ]
    return "\n".join(parts)


def run_suite(suite: SuiteSpec, *, base_env: Mapping[str, str], show_log_tail: int) -> SuiteResult:
    command_text = _format_command(suite.command, suite.env_overrides)
    retry_command = command_text
    missing = _missing_requirements(base_env, suite)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"{suite.name}.log"

    if missing:
        reason = f"Skipped: missing env requirement(s): {', '.join(missing)}"
        log_path.write_text(reason + "\n", encoding="utf-8")
        return SuiteResult(
            name=suite.name,
            status="skipped",
            description=suite.description,
            command=command_text,
            retry_command=retry_command,
            duration_seconds=0.0,
            exit_code=0,
            summary=reason,
            log_path=str(log_path),
            junit_path=suite.junit_path,
            missing_requirements=missing,
        )

    env = dict(base_env)
    env.update(suite.env_overrides)

    print(f"\n[{suite.name}] {suite.description}", flush=True)
    print(f"$ {command_text}", flush=True)
    started = time.monotonic()
    proc = subprocess.run(suite.command, capture_output=True, text=True, env=env)
    duration = round(time.monotonic() - started, 3)

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    log_path.write_text(_build_log_text(suite, command_text, stdout, stderr), encoding="utf-8")
    summary = _extract_summary(stdout, stderr)

    if proc.returncode != 0:
        status = "failed"
        print(f"[{suite.name}] FAIL ({duration:.2f}s)", flush=True)
        print(f"[{suite.name}] {summary}", flush=True)
        tail_text = "\n".join((stdout + "\n" + stderr).splitlines()[-show_log_tail:])
        if tail_text.strip():
            print(f"[{suite.name}] Last {show_log_tail} lines:", flush=True)
            print(tail_text, flush=True)
    else:
        status = "passed"
        if " skipped" in stdout and " passed" not in stdout:
            status = "skipped"
        print(f"[{suite.name}] {status.upper()} ({duration:.2f}s)", flush=True)
        print(f"[{suite.name}] {summary}", flush=True)

    return SuiteResult(
        name=suite.name,
        status=status,
        description=suite.description,
        command=command_text,
        retry_command=retry_command,
        duration_seconds=duration,
        exit_code=int(proc.returncode),
        summary=summary,
        log_path=str(log_path),
        junit_path=suite.junit_path,
        missing_requirements=missing,
    )


def _print_summary(profile: str, results: List[SuiteResult], report_path: Path) -> int:
    passed = [result for result in results if result.status == "passed"]
    failed = [result for result in results if result.status == "failed"]
    skipped = [result for result in results if result.status == "skipped"]
    overall = "FAILED" if failed else "PASSED"

    print("\n== Runner Summary ==", flush=True)
    print(f"Profile: {profile}", flush=True)
    for result in results:
        print(
            f"{result.status.upper():>7}  {result.name:<30}  {result.duration_seconds:>6.2f}s  {result.summary}",
            flush=True,
        )
        print(f"         rerun: {result.retry_command}", flush=True)
        print(f"         logs: {result.log_path}", flush=True)
        if result.junit_path:
            print(f"         junit: {result.junit_path}", flush=True)

    print("\nTotals:", flush=True)
    print(f"- passed: {len(passed)}", flush=True)
    print(f"- failed: {len(failed)}", flush=True)
    print(f"- skipped: {len(skipped)}", flush=True)
    print(f"Overall: {overall}", flush=True)
    print(f"JSON report: {report_path}", flush=True)
    return 1 if failed else 0


def _write_report(profile: str, results: List[SuiteResult], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "overall_status": "failed" if any(result.status == "failed" for result in results) else "passed",
        "counts": {
            "passed": sum(result.status == "passed" for result in results),
            "failed": sum(result.status == "failed" for result in results),
            "skipped": sum(result.status == "skipped" for result in results),
            "total": len(results),
        },
        "suites": [
            {
                "name": result.name,
                "status": result.status,
                "description": result.description,
                "duration_seconds": result.duration_seconds,
                "command": result.command,
                "retry_command": result.retry_command,
                "exit_code": result.exit_code,
                "summary": result.summary,
                "log_path": result.log_path,
                "junit_path": result.junit_path,
                "missing_requirements": result.missing_requirements,
            }
            for result in results
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical test runner for local + CI use.")
    parser.add_argument(
        "profile",
        nargs="?",
        default="list",
        help="Profile to run: list, critical, deterministic, live-read, all, ai-live, night-probe.",
    )
    parser.add_argument(
        "--ai-scope",
        choices=("sample", "full"),
        default="sample",
        help="Scope for AI live profile (default: sample).",
    )
    parser.add_argument(
        "--ack",
        default=None,
        help=f"Ack value for night-probe profile (must be {ACK_VALUE}).",
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python executable used for subprocess commands.",
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT_PATH),
        help=f"JSON report output path (default: {DEFAULT_REPORT_PATH}).",
    )
    parser.add_argument(
        "--show-log-tail",
        type=int,
        default=80,
        help="When a suite fails, print this many combined stdout/stderr lines from the tail.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        profile = resolve_profile_name(args.profile)
    except ValueError as exc:
        print(str(exc), flush=True)
        return 2

    if profile == "list":
        print("Available profiles:", flush=True)
        for item in SUPPORTED_PROFILES:
            print(f"- {item}", flush=True)
        print("Aliases:", flush=True)
        for alias, target in PROFILE_ALIASES.items():
            print(f"- {alias} -> {target}", flush=True)
        return 0

    try:
        suites = build_profile_suites(profile, ai_scope=args.ai_scope, ack=args.ack, python_bin=args.python_bin)
    except ValueError as exc:
        print(str(exc), flush=True)
        return 2

    print("== StockTalk Test Runner ==", flush=True)
    print(f"Profile: {profile}", flush=True)
    print(f"Suites: {', '.join(suite.name for suite in suites)}", flush=True)

    base_env = dict(os.environ)
    results = [run_suite(suite, base_env=base_env, show_log_tail=max(args.show_log_tail, 10)) for suite in suites]

    report_path = Path(args.report_path)
    _write_report(profile, results, report_path)
    return _print_summary(profile, results, report_path)


if __name__ == "__main__":
    raise SystemExit(main())

