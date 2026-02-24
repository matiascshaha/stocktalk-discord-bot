"""Anthropic client wrapper for parser completions."""

from typing import Any


def request_parser_completion(
    client: Any,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
