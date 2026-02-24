import pytest

from src.utils.paths import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROMPT_PATH,
    PROJECT_ROOT,
    resolve_config_path,
    resolve_data_dir,
    resolve_picks_log_path,
    resolve_prompt_path,
    resolve_user_path,
)

pytestmark = pytest.mark.unit


def test_project_root_shape():
    assert (PROJECT_ROOT / "src").exists()
    assert (PROJECT_ROOT / "config").exists()


def test_resolve_user_path_relative():
    resolved = resolve_user_path("config/trading.yaml")
    assert resolved == (PROJECT_ROOT / "config" / "trading.yaml").resolve()


def test_resolve_user_path_absolute(tmp_path):
    absolute = (tmp_path / "example.yaml").resolve()
    assert resolve_user_path(str(absolute)) == absolute


def test_resolve_config_path_default(monkeypatch):
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    assert resolve_config_path() == DEFAULT_CONFIG_PATH


def test_resolve_config_path_override_relative(monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", "config/trading.yaml")
    assert resolve_config_path() == (PROJECT_ROOT / "config" / "trading.yaml").resolve()


def test_resolve_prompt_path_default():
    assert resolve_prompt_path(None) == DEFAULT_PROMPT_PATH


def test_resolve_prompt_path_override_relative():
    assert resolve_prompt_path("config/ai_parser.prompt") == (
        PROJECT_ROOT / "config" / "ai_parser.prompt"
    ).resolve()


def test_resolve_data_dir_override(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "custom-data")
    assert resolve_data_dir() == (PROJECT_ROOT / "custom-data").resolve()


def test_resolve_picks_log_path_uses_data_dir_when_override_present(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "custom-data")
    monkeypatch.delenv("PICKS_LOG_PATH", raising=False)
    assert resolve_picks_log_path() == (
        PROJECT_ROOT / "custom-data" / "picks_log.jsonl"
    ).resolve()


def test_resolve_picks_log_path_explicit_override(monkeypatch):
    monkeypatch.setenv("PICKS_LOG_PATH", "logs/custom-picks.jsonl")
    assert resolve_picks_log_path() == (PROJECT_ROOT / "logs" / "custom-picks.jsonl").resolve()
