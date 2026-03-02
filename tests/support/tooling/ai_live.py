import os

import src.ai_parser as ai_parser_module


def apply_fast_path_toggle(monkeypatch) -> None:
    if os.getenv("TEST_AI_FAST_PATH", "0") != "1":
        return
    monkeypatch.setitem(ai_parser_module.AI_CONFIG["openai"], "fast_confidence_threshold", 0.85)
    monkeypatch.setitem(ai_parser_module.AI_CONFIG["openai"], "fast_max_tokens", 250)
