import os
from typing import List

import pytest

from tests.testkit.helpers.matrix import enabled_ai_providers, enabled_brokers


@pytest.fixture(scope="session")
def configured_ai_provider() -> str:
    return os.getenv("AI_PROVIDER", "auto").strip().lower()


@pytest.fixture(scope="session")
def ai_smoke_providers() -> List[str]:
    providers = enabled_ai_providers()
    return providers or ["openai"]


@pytest.fixture(scope="session")
def broker_matrix() -> List[str]:
    brokers = enabled_brokers()
    return brokers or ["webull"]
