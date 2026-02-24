import pytest

from src.models.webull_models import AccountBalanceResponse


@pytest.mark.contract
@pytest.mark.unit
def test_account_balance_response_parses_webull_shape():
    payload = {
        "account_id": "J6HA4EBQRQFJD2J6NQH0F7M649",
        "total_asset_currency": "USD",
        "total_market_value": "304516.77",
        "total_cash_balance": "49999999750177.87",
        "margin_utilization_rate": "0.00",
        "account_currency_assets": [
            {
                "currency": "USD",
                "net_liquidation_value": "50000000054694.64",
                "margin_power": "0.00",
                "cash_power": "49999999748643.59",
                "day_buying_power": "12000.10",
                "overnight_buying_power": "9000.05",
                "available_withdrawal": "49999999708917.48",
            }
        ],
    }

    balance = AccountBalanceResponse.model_validate(payload)

    assert balance.total_market_value == 304516.77
    assert balance.margin_utilization_rate == 0.0
    assert len(balance.account_currency_assets) == 1
    assert balance.account_currency_assets[0].margin_power == 0.0
    assert balance.account_currency_assets[0].cash_power == 49999999748643.59
    assert balance.account_currency_assets[0].day_buying_power == 12000.10
    assert balance.account_currency_assets[0].overnight_buying_power == 9000.05


@pytest.mark.contract
@pytest.mark.unit
def test_account_balance_response_ignores_unknown_fields():
    payload = {
        "account_id": "A1",
        "unknown_top_level": "ignored",
        "account_currency_assets": [
            {
                "currency": "USD",
                "cash_power": "100.00",
                "cash_balance": "-1344.10",
                "unexpected_nested": "ignored",
            }
        ],
    }

    balance = AccountBalanceResponse.model_validate(payload)

    assert balance.account_id == "A1"
    assert balance.account_currency_assets[0].cash_power == 100.0
    assert balance.account_currency_assets[0].cash_balance == -1344.1
