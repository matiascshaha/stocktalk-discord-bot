"""OpenAI parser contract schema and request format."""

from typing import Any, Dict

from src.models.parser_models import CONTRACT_VERSION


OPENAI_PARSER_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["contract_version", "source", "signals", "meta"],
    "properties": {
        "contract_version": {"type": "string", "enum": [CONTRACT_VERSION]},
        "source": {
            "type": "object",
            "additionalProperties": False,
            "required": ["author", "channel_id", "message_id", "message_text"],
            "properties": {
                "author": {"type": ["string", "null"]},
                "channel_id": {"type": ["string", "null"]},
                "message_id": {"type": ["string", "null"]},
                "message_text": {"type": ["string", "null"]},
            },
        },
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "ticker",
                    "action",
                    "confidence",
                    "reasoning",
                    "weight_percent",
                    "urgency",
                    "sentiment",
                    "is_actionable",
                    "vehicles",
                ],
                "properties": {
                    "ticker": {"type": "string", "minLength": 1},
                    "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD", "NONE"]},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "reasoning": {"type": "string"},
                    "weight_percent": {"type": ["number", "null"]},
                    "urgency": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                    "sentiment": {"type": "string", "enum": ["BULLISH", "BEARISH", "NEUTRAL"]},
                    "is_actionable": {"type": "boolean"},
                    "vehicles": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "type",
                                "enabled",
                                "intent",
                                "side",
                                "option_type",
                                "strike",
                                "expiry",
                                "quantity_hint",
                            ],
                            "properties": {
                                "type": {"type": "string", "enum": ["STOCK", "OPTION"]},
                                "enabled": {"type": "boolean"},
                                "intent": {"type": "string", "enum": ["EXECUTE", "WATCH", "INFO"]},
                                "side": {"type": "string", "enum": ["BUY", "SELL", "NONE"]},
                                "option_type": {"type": ["string", "null"], "enum": ["CALL", "PUT", None]},
                                "strike": {"type": ["number", "null"]},
                                "expiry": {"type": ["string", "null"]},
                                "quantity_hint": {"type": ["number", "null"]},
                            },
                        },
                    },
                },
            },
        },
        "meta": {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "provider", "error", "warnings"],
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["ok", "no_action", "invalid_json", "provider_error"],
                },
                "provider": {"type": ["string", "null"], "enum": ["openai", "anthropic", "google", None]},
                "error": {"type": ["string", "null"]},
                "warnings": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}


def parser_response_format() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "stocktalk_parser_contract",
            "strict": True,
            "schema": OPENAI_PARSER_JSON_SCHEMA,
        },
    }
