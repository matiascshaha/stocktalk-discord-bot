#!/usr/bin/env python3
"""Run the full reliability matrix in one command."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from dotenv import load_dotenv


@dataclass(frozen=True)
class Scenario:
    name: str
    command: List[str]
    env_overrides: Dict[str, str]


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    return_code: int
    duration_seconds: float

    @property
    def status(self) -> str:
        return "PASS" if self.return_code == 0 else "FAIL"


def _scenario(name: str, command: Sequence[str], **env_overrides: str) -> Scenario:
    return Scenario(name=name, command=list(command), env_overrides=dict(env_overrides))


def build_scenarios(ai_scope: str, skip_discord_live: bool, skip_webull_prod_write: bool) -> List[Scenario]:
    py = sys.executable
    scenarios: List[Scenario] = [
        _scenario("deterministic", [py, "-m", "pytest"]),
        _scenario(
            "ai_live_smoke",
            [py, "-m", "pytest", "tests/smoke/test_ai_live_smoke.py", "-m", "smoke and live", "-q"],
            TEST_AI_LIVE="1",
        ),
        _scenario(
            "ai_pipeline_live",
            [
                py,
                "-m",
                "pytest",
                "tests/integration/test_discord_flow.py",
                "-k",
                "live_ai_pipeline_message_to_trader",
                "-m",
                "smoke and live",
                "-q",
            ],
            TEST_AI_LIVE="1",
            TEST_AI_SCOPE=ai_scope,
        ),
        _scenario(
            "webull_read_paper",
            [
                py,
                "-m",
                "pytest",
                "tests/smoke/test_webull_smoke.py",
                "-m",
                "smoke and live and not webull_write",
                "-q",
            ],
            TEST_WEBULL_READ="1",
            TEST_WEBULL_ENV="paper",
        ),
        _scenario(
            "webull_write_paper",
            [
                py,
                "-m",
                "pytest",
                "tests/smoke/test_webull_smoke.py",
                "-m",
                "smoke and live and webull_write",
                "-q",
            ],
            TEST_WEBULL_WRITE="1",
            TEST_WEBULL_ENV="paper",
        ),
        _scenario(
            "webull_read_production",
            [
                py,
                "-m",
                "pytest",
                "tests/smoke/test_webull_smoke.py",
                "-m",
                "smoke and live and not webull_write",
                "-q",
            ],
            TEST_WEBULL_READ="1",
            TEST_WEBULL_ENV="production",
        ),
    ]

    if not skip_webull_prod_write:
        scenarios.append(
            _scenario(
                "webull_write_production",
                [
                    py,
                    "-m",
                    "pytest",
                    "tests/smoke/test_webull_smoke.py",
                    "-m",
                    "smoke and live and webull_write",
                    "-q",
                ],
                TEST_WEBULL_WRITE="1",
                TEST_WEBULL_ENV="production",
            )
        )

    if not skip_discord_live:
        scenarios.append(
            _scenario(
                "discord_live_smoke",
                [py, "-m", "pytest", "tests/smoke/test_discord_live_smoke.py", "-m", "discord_live", "-q"],
                TEST_DISCORD_LIVE="1",
            )
        )

    return scenarios


def _format_command(scenario: Scenario) -> str:
    env_prefix = " ".join(f"{key}={value}" for key, value in scenario.env_overrides.items())
    command = " ".join(scenario.command)
    return f"{env_prefix} {command}".strip()


def _run_scenario(scenario: Scenario, base_env: Dict[str, str]) -> ScenarioResult:
    env = dict(base_env)
    env.update(scenario.env_overrides)

    print(f"\n== Scenario: {scenario.name} ==", flush=True)
    print(f"$ {_format_command(scenario)}", flush=True)
    start = time.monotonic()
    proc = subprocess.run(scenario.command, env=env)
    duration = time.monotonic() - start
    print(f"[{scenario.name}] {'PASS' if proc.returncode == 0 else 'FAIL'} ({duration:.1f}s)", flush=True)
    return ScenarioResult(name=scenario.name, return_code=proc.returncode, duration_seconds=duration)


def _names(scenarios: Iterable[Scenario]) -> List[str]:
    return [scenario.name for scenario in scenarios]


def _select_scenarios(scenarios: List[Scenario], only: str | None) -> List[Scenario]:
    if not only:
        return scenarios

    requested = [item.strip() for item in only.split(",") if item.strip()]
    by_name = {scenario.name: scenario for scenario in scenarios}
    missing = [name for name in requested if name not in by_name]
    if missing:
        raise ValueError(f"Unknown scenario(s): {', '.join(missing)}")
    return [by_name[name] for name in requested]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run full reliability scenario matrix.")
    parser.add_argument(
        "--ai-scope",
        choices=["sample", "full"],
        default="full",
        help="AI live pipeline message subset size (default: full).",
    )
    parser.add_argument(
        "--skip-discord-live",
        action="store_true",
        help="Skip Discord live smoke scenario.",
    )
    parser.add_argument(
        "--skip-webull-prod-write",
        action="store_true",
        help="Skip Webull production write scenario.",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated scenario names to run.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List scenario names and exit.",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop immediately after first failing scenario.",
    )
    return parser


def main() -> int:
    load_dotenv(override=False)
    args = _parser().parse_args()

    scenarios = build_scenarios(
        ai_scope=args.ai_scope,
        skip_discord_live=args.skip_discord_live,
        skip_webull_prod_write=args.skip_webull_prod_write,
    )
    if args.list:
        print("\n".join(_names(scenarios)), flush=True)
        return 0

    try:
        selected = _select_scenarios(scenarios, args.only)
    except ValueError as exc:
        print(f"Scenario selection error: {exc}", flush=True)
        return 2

    print("== Full Matrix Runner ==", flush=True)
    print(f"AI scope: {args.ai_scope}", flush=True)
    print(f"Scenarios: {', '.join(_names(selected))}", flush=True)

    base_env = dict(os.environ)
    results: List[ScenarioResult] = []
    for scenario in selected:
        result = _run_scenario(scenario, base_env=base_env)
        results.append(result)
        if args.stop_on_fail and result.return_code != 0:
            break

    failed = [result for result in results if result.return_code != 0]
    passed = [result for result in results if result.return_code == 0]

    print("\n== Summary ==", flush=True)
    for result in results:
        print(f"{result.status:>4}  {result.name}  ({result.duration_seconds:.1f}s)", flush=True)
    print(f"Passed: {len(passed)}", flush=True)
    print(f"Failed: {len(failed)}", flush=True)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
