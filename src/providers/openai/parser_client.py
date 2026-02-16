"""OpenAI client wrapper for parser completions."""

import json
from typing import Any, List

from src.providers.openai.parser_contract import parser_response_format


def extract_structured_message_content(response: Any) -> str:
    message = response.choices[0].message
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_chunks: List[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    text_chunks.append(text)
            else:
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    text_chunks.append(text)
        joined = "".join(text_chunks).strip()
        if joined:
            return joined

    parsed = getattr(message, "parsed", None)
    if parsed is not None:
        if hasattr(parsed, "model_dump"):
            return json.dumps(parsed.model_dump())
        return json.dumps(parsed)

    raise ValueError("OpenAI response contained no parseable message content")


def request_parser_completion(
    client: Any,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=parser_response_format(),
    )
    return extract_structured_message_content(response)
