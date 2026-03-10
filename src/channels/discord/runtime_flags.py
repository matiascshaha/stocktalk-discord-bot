"""Environment-driven Discord runtime flags."""

import os


class DiscordRuntimeFlags:
    """Read lightweight boolean flags from environment variables."""

    @staticmethod
    def env_enabled(name: str) -> bool:
        return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}
