#!/usr/bin/env python3
"""One-command confidence runner.

This script configures environment flags and runs ``scripts.healthcheck``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

from dotenv import load_dotenv


AI_PROVIDER_KEYS: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


PROFILE_FLAGS: Dict[str, Dict[str, str]] = {
    "full": {
        "FULL_CONFIDENCE_REQUIRED": "1",
        "RUN_LIVE_AI_TESTS": "1",
        "RUN_LIVE_AI_PIPELINE_FULL": "0",
        "RUN_DISCORD_LIVE_SMOKE": "1",
        "RUN_WEBULL_READ_SMOKE": "1",
    },
    "deterministic": {
        "FULL_CONFIDENCE_REQUIRED": "0",
        "RUN_LIVE_AI_TESTS": "0",
        "RUN_DISCORD_LIVE_SMOKE": "0",
        "RUN_WEBULL_READ_SMOKE": "0",
        "RUN_WEBULL_WRITE_TESTS": "0",
    },
}


@dataclass
class PreflightResult:
    warnings: List[str]
    info: List[str]


def _parse_csv(raw: str) -> List[str]:
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _enabled_ai_keys(env: Dict[str, str]) -> Tuple[List[str], List[str]]:
    providers = _parse_csv(env.get("TEST_AI_PROVIDERS", "openai,anthropic,google"))
    selected_provider = env.get("AI_PROVIDER", "auto").strip().lower()
    if selected_provider in AI_PROVIDER_KEYS:
        providers = [selected_provider]

    keys = [AI_PROVIDER_KEYS[p] for p in providers if p in AI_PROVIDER_KEYS]
    return providers, keys


def _preflight(env: Dict[str, str]) -> PreflightResult:
    warnings: List[str] = []
    info: List[str] = []

    if env.get("RUN_LIVE_AI_TESTS") == "1":
        providers, keys = _enabled_ai_keys(env)
        if not any(env.get(k) for k in keys):
            warnings.append(
                "Live AI smoke enabled but no provider key found for "
                f"providers={','.join(providers)}."
            )
        else:
            info.append(f"AI smoke providers: {','.join(providers)}")

    if env.get("RUN_DISCORD_LIVE_SMOKE") == "1":
        if not env.get("DISCORD_TOKEN"):
            warnings.append("Discord live smoke enabled but DISCORD_TOKEN is missing.")
        if not env.get("CHANNEL_ID"):
            warnings.append("Discord live smoke enabled but CHANNEL_ID is missing.")

    if env.get("RUN_WEBULL_READ_SMOKE") == "1" or env.get("RUN_WEBULL_WRITE_TESTS") == "1":
        if not env.get("WEBULL_APP_KEY"):
            warnings.append("Webull smoke enabled but WEBULL_APP_KEY is missing.")
        if not env.get("WEBULL_APP_SECRET"):
            warnings.append("Webull smoke enabled but WEBULL_APP_SECRET is missing.")

    if env.get("RUN_WEBULL_WRITE_TESTS") == "1":
        paper_required = env.get("WEBULL_PAPER_REQUIRED", "1") == "1"
        paper_trade = env.get("WEBULL_SMOKE_PAPER_TRADE", env.get("PAPER_TRADE", "true")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if paper_required and not paper_trade:
            warnings.append(
                "Webull write smoke is enabled with WEBULL_PAPER_REQUIRED=1 but WEBULL_SMOKE_PAPER_TRADE is not true."
            )
        if paper_trade:
            warnings.append(
                "Webull write smoke in paper/UAT mode may fail with 404 depending on account/environment provisioning."
            )
        else:
            warnings.append(
                "Webull write smoke in production can fail outside trading hours (CAN_NOT_TRADING_FOR_NON_TRADING_HOURS)."
            )

    return PreflightResult(warnings=warnings, info=info)


def _run(command: List[str], env: Dict[str, str]) -> int:
    print(f"\n$ {' '.join(command)}", flush=True)
    proc = subprocess.run(command, env=env)
    return int(proc.returncode)


def _build_env(args: argparse.Namespace) -> Dict[str, str]:
    env = dict(os.environ)

    # Baseline defaults used by both profiles.
    env.setdefault("TEST_AI_PROVIDERS", "openai,anthropic,google")
    env.setdefault("TEST_BROKERS", "webull")
    env.setdefault("RUN_LIVE_AI_PIPELINE_FULL", "0")

    # Profile defaults can still be overridden by explicitly set env vars.
    for key, value in PROFILE_FLAGS[args.mode].items():
        env.setdefault(key, value)

    if args.mode == "full":
        if args.include_webull_write:
            env["RUN_WEBULL_WRITE_TESTS"] = "1"
        else:
            env.setdefault("RUN_WEBULL_WRITE_TESTS", "0")
        default_paper_value = env.get("PAPER_TRADE", "true") if args.include_webull_write else "0"
        env.setdefault("WEBULL_SMOKE_PAPER_TRADE", default_paper_value)
    else:
        env.setdefault("WEBULL_SMOKE_PAPER_TRADE", env.get("PAPER_TRADE", "true"))

    if args.ai_provider:
        env["AI_PROVIDER"] = args.ai_provider.strip().lower()
        env["TEST_AI_PROVIDERS"] = env["AI_PROVIDER"]

    if args.brokers:
        env["TEST_BROKERS"] = args.brokers

    if args.webull_paper_required:
        env["WEBULL_PAPER_REQUIRED"] = "1"
    elif args.mode == "full":
        env.setdefault("WEBULL_PAPER_REQUIRED", "1")

    if args.webull_smoke_paper_trade:
        env["WEBULL_SMOKE_PAPER_TRADE"] = "1"

    return env


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic or full end-to-end confidence checks.")
    parser.add_argument(
        "--mode",
        choices=["deterministic", "full"],
        default="full",
        help="Run profile. 'full' enables strict confidence and live smokes by default.",
    )
    parser.add_argument(
        "--include-webull-write",
        action="store_true",
        help="Include Webull write-path smoke tests (opt-in).",
    )
    parser.add_argument(
        "--ai-provider",
        choices=["openai", "anthropic", "google", "auto", "none"],
        help="Force AI provider for this run.",
    )
    parser.add_argument(
        "--brokers",
        default=None,
        help="Comma-separated broker matrix override (default from TEST_BROKERS/webull).",
    )
    parser.add_argument(
        "--webull-paper-required",
        action="store_true",
        help="Force WEBULL_PAPER_REQUIRED=1 for this run.",
    )
    parser.add_argument(
        "--webull-smoke-paper-trade",
        action="store_true",
        help="Force Webull smoke tests to use paper/UAT endpoint.",
    )
    return parser


def main() -> int:
    load_dotenv(override=False)
    args = _parser().parse_args()
    env = _build_env(args)
    preflight = _preflight(env)

    print("== Full Confidence Runner ==", flush=True)
    print(f"Mode: {args.mode}", flush=True)
    print(f"Strict gate (FULL_CONFIDENCE_REQUIRED): {env.get('FULL_CONFIDENCE_REQUIRED')}", flush=True)
    print(
        "Live flags: "
        f"AI={env.get('RUN_LIVE_AI_TESTS')} "
        f"AIPipelineFull={env.get('RUN_LIVE_AI_PIPELINE_FULL', '0')} "
        f"Discord={env.get('RUN_DISCORD_LIVE_SMOKE')} "
        f"WebullRead={env.get('RUN_WEBULL_READ_SMOKE')} "
        f"WebullWrite={env.get('RUN_WEBULL_WRITE_TESTS')}",
        flush=True,
    )
    print(f"Webull smoke paper mode: {env.get('WEBULL_SMOKE_PAPER_TRADE')}", flush=True)
    print(f"Provider matrix: {env.get('TEST_AI_PROVIDERS')}", flush=True)
    print(f"Broker matrix: {env.get('TEST_BROKERS')}", flush=True)

    for item in preflight.info:
        print(f"[info] {item}", flush=True)
    for warning in preflight.warnings:
        print(f"[warn] {warning}", flush=True)

    health_exit = _run([sys.executable, "-m", "scripts.healthcheck"], env=env)
    print("\nReport: artifacts/health_report.json", flush=True)
    return health_exit


if __name__ == "__main__":
    raise SystemExit(main())
