"""Runtime monkey-patches for discord.py-self compatibility."""

from typing import Any


class DiscordRuntimePatcher:
    """Apply resilient Discord gateway patches used by this runtime."""

    def __init__(self, *, logger: Any):
        self._logger = logger

    def patch_pending_payments(self) -> None:
        """
        Work around discord.py-self handling pending_payments=None from gateway payloads.
        Prevents: TypeError: 'NoneType' object is not iterable.
        """
        try:
            from discord import state as discord_state
        except Exception:
            return

        original = getattr(discord_state.ConnectionState, "parse_ready_supplemental", None)
        if not original or getattr(original, "_patched_pending_payments", False):
            return

        def patched(connection_state, data):
            payload = data if isinstance(data, dict) else {}
            payload = dict(payload)

            pending = payload.get("pending_payments")
            if not isinstance(pending, list):
                payload["pending_payments"] = []

            try:
                return original(connection_state, payload)
            except TypeError as exc:
                if "NoneType" in str(exc) and "iterable" in str(exc):
                    payload["pending_payments"] = []
                    try:
                        return original(connection_state, payload)
                    except Exception:
                        connection_state.pending_payments = {}
                        return None
                raise

        patched._patched_pending_payments = True
        discord_state.ConnectionState.parse_ready_supplemental = patched
        self._logger.debug("Applied pending_payments runtime patch")
