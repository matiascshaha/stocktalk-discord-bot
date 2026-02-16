"""Google client wrapper for parser completions."""

from typing import Any


def request_parser_completion(client: Any, prompt: str) -> str:
    response = client.generate_content(prompt)
    return response.text.strip()
