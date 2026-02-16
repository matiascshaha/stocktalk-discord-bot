#!/usr/bin/env python3
"""One-command confidence runner."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from scripts.test_flags import TestFlags, resolve_test_flags


AI_PROVIDER_KEYS: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
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


def _preflight(env: Dict[str, str], flags: TestFlags) -> PreflightResult:
    warnings: List[str] = []
    info: List[str] = []

    if flags.ai_live:
        providers, keys = _enabled_ai_keys(env)
        if not any(env.get(k) for k in keys):
            warnings.append(
                "AI live smoke is enabled but no provider key was found for "
                f"providers={','.join(providers)}."
            )
        else:
            info.append(f"AI smoke providers: {','.join(providers)}")

    if flags.discord_live:
        if not env.get("DISCORD_TOKEN"):
            warnings.append("Discord live smoke is enabled but DISCORD_TOKEN is missing.")
        if not env.get("CHANNEL_ID"):
            warnings.append("Discord live smoke is enabled but CHANNEL_ID is missing.")

    if flags.webull_read or flags.webull_write:
        if not env.get("WEBULL_APP_KEY"):
            warnings.append("Webull smoke is enabled but WEBULL_APP_KEY is missing.")
        if not env.get("WEBULL_APP_SECRET"):
            warnings.append("Webull smoke is enabled but WEBULL_APP_SECRET is missing.")

    if flags.webull_write:
        if flags.webull_env == "paper":
            warnings.append(
                "Webull write smoke in paper mode may fail with 404 depending on account/environment provisioning."
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
    env.setdefault("TEST_AI_PROVIDERS", "openai,anthropic,google")
    env.setdefault("TEST_BROKERS", "webull")

    env["TEST_MODE"] = args.mode
    if args.ai_live is not None:
        env["TEST_AI_LIVE"] = args.ai_live
    if args.discord_live is not None:
        env["TEST_DISCORD_LIVE"] = args.discord_live
    if args.webull_read is not None:
        env["TEST_WEBULL_READ"] = args.webull_read
    if args.webull_write is not None:
        env["TEST_WEBULL_WRITE"] = args.webull_write
    if args.webull_env is not None:
        env["TEST_WEBULL_ENV"] = args.webull_env
    if args.ai_scope is not None:
        env["TEST_AI_SCOPE"] = args.ai_scope

    if args.ai_provider:
        env["AI_PROVIDER"] = args.ai_provider.strip().lower()
        if env["AI_PROVIDER"] in AI_PROVIDER_KEYS:
            env["TEST_AI_PROVIDERS"] = env["AI_PROVIDER"]

    if args.brokers:
        env["TEST_BROKERS"] = args.brokers

    flags = resolve_test_flags(env, default_mode=args.mode)
    return flags.to_env(env)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local/smoke/strict confidence checks.")
    parser.add_argument(
        "--mode",
        choices=["local", "smoke", "strict"],
        default="strict",
        help="Base test mode (strict by default for full confidence checks).",
    )
    parser.add_argument(
        "--ai-live",
        choices=["0", "1"],
        default=None,
        help="Override TEST_AI_LIVE.",
    )
    parser.add_argument(
        "--discord-live",
        choices=["0", "1"],
        default=None,
        help="Override TEST_DISCORD_LIVE.",
    )
    parser.add_argument(
        "--webull-read",
        choices=["0", "1"],
        default=None,
        help="Override TEST_WEBULL_READ.",
    )
    parser.add_argument(
        "--webull-write",
        choices=["0", "1"],
        default=None,
        help="Override TEST_WEBULL_WRITE.",
    )
    parser.add_argument(
        "--webull-env",
        choices=["paper", "production"],
        default=None,
        help="Override TEST_WEBULL_ENV.",
    )
    parser.add_argument(
        "--ai-scope",
        choices=["sample", "full"],
        default=None,
        help="Override TEST_AI_SCOPE for the live AI pipeline subset.",
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
    return parser


def main() -> int:
    load_dotenv(override=False)
    args = _parser().parse_args()
    try:
        env = _build_env(args)
        flags = resolve_test_flags(env, default_mode=args.mode)
    except ValueError as exc:
        print(f"Flag configuration error: {exc}", flush=True)
        return 2

    preflight = _preflight(env, flags)

    print("== Full Confidence Runner ==", flush=True)
    print(f"Mode: {flags.mode}", flush=True)
    print(f"Strict gate: {'1' if flags.strict_external else '0'}", flush=True)
    print(
        "Live flags: "
        f"AI={env.get('TEST_AI_LIVE')} "
        f"AIScope={env.get('TEST_AI_SCOPE')} "
        f"Discord={env.get('TEST_DISCORD_LIVE')} "
        f"WebullRead={env.get('TEST_WEBULL_READ')} "
        f"WebullWrite={env.get('TEST_WEBULL_WRITE')}",
        flush=True,
    )
    print(f"Webull target: {env.get('TEST_WEBULL_ENV')}", flush=True)
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
