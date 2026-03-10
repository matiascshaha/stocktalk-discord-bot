"""Account-resolution helpers for Webull trading clients."""

from typing import Any, Callable, Dict, List, Optional


class WebullAccountResolver:
    """Resolve and validate account identity from Webull account-list responses."""

    def __init__(
        self,
        *,
        get_account_list: Callable[[], Any],
        check_response: Callable[[Any, str], None],
        mask_account_id: Callable[[str], str],
        logger: Any,
    ):
        self._get_account_list = get_account_list
        self._check_response = check_response
        self._mask_account_id = mask_account_id
        self._logger = logger

    def resolve_account_id(self, cached_account_id: Optional[str]) -> str:
        """Return a cached account id or resolve one from Webull account list."""
        if cached_account_id:
            self._logger.info("Using provided account ID: %s", self._mask_account_id(cached_account_id))
            return cached_account_id

        response = self._get_account_list()
        self._check_response(response, "get_account_list")
        payload = response.json()
        accounts = self.extract_accounts(payload)
        if not accounts:
            raise RuntimeError(f"No accounts found: {payload}")

        first_account = accounts[0]
        account_id = first_account.get("account_id") or first_account.get("accountId")
        if not account_id:
            raise RuntimeError(f"No account_id in: {first_account}")

        resolved = str(account_id)
        self._logger.info("Resolved account: %s", self._mask_account_id(resolved))
        return resolved

    @staticmethod
    def extract_accounts(data: Any) -> List[Dict]:
        """Extract account-list payload from known Webull response shapes."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("accounts") or data.get("data") or data.get("list", [])
        return []
