"""Brokerage domain exceptions."""


class BrokerageError(RuntimeError):
    """Base exception for brokerage execution failures."""


class BrokerageCapabilityError(BrokerageError):
    """Raised when a broker does not support a requested capability."""

    def __init__(self, broker: str, capability: str):
        self.broker = broker
        self.capability = capability
        super().__init__(f"Broker '{broker}' does not support capability '{capability}'")
