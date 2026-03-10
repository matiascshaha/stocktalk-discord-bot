"""Signal logging helpers for Discord message processing."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


class DiscordSignalLogger:
    """Append parsed-message signal payloads to JSONL."""

    def __init__(self, *, logger: Any):
        self._logger = logger

    def append(self, *, message: Any, parsed_message: Mapping[str, Any], output_path: Path) -> None:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "author": str(message.author),
            "message": message.content,
            "message_url": message.jump_url,
            "ai_parsed_signals": parsed_message,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(log_entry) + "\n")

        self._logger.debug("Pick logged to %s", output_path)
