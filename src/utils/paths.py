"""Centralized path resolution for runtime and config files."""

import os
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "trading.yaml"
DEFAULT_PROMPT_PATH = CONFIG_DIR / "ai_parser.prompt"


def resolve_user_path(value: Optional[str]) -> Path:
    """Resolve user-provided path values relative to project root."""
    if not value:
        return PROJECT_ROOT

    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate

    return (PROJECT_ROOT / candidate).resolve()


def resolve_config_path() -> Path:
    """Resolve the config path using CONFIG_PATH override when provided."""
    override = os.getenv("CONFIG_PATH")
    if override:
        return resolve_user_path(override)
    return DEFAULT_CONFIG_PATH


def resolve_prompt_path(prompt_file: Optional[str]) -> Path:
    """Resolve AI prompt path relative to project root when needed."""
    if prompt_file:
        return resolve_user_path(prompt_file)
    return DEFAULT_PROMPT_PATH


def resolve_data_dir() -> Path:
    """Resolve the data directory using DATA_DIR override when provided."""
    override = os.getenv("DATA_DIR")
    if override:
        return resolve_user_path(override)
    return PROJECT_ROOT / "data"


def resolve_picks_log_path() -> Path:
    """Resolve picks log path with PICKS_LOG_PATH taking precedence."""
    override = os.getenv("PICKS_LOG_PATH")
    if override:
        return resolve_user_path(override)
    return resolve_data_dir() / "picks_log.jsonl"


DATA_DIR = resolve_data_dir()
PICKS_LOG_PATH = resolve_picks_log_path()
