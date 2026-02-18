# Test Index

Use this map in two passes:
1. pick the feature or module
2. pick the test intent (`happy_path`, `edge_cases`, `contracts`, `smoke`)

## Unit (Flat)

- `tests/unit/test_parser_schema.py`
- `tests/unit/test_provider_dispatch.py`
- `tests/unit/test_stock_order_executor.py`
- `tests/unit/test_stock_order_planner.py`
- `tests/unit/test_market_hours.py`
- `tests/unit/test_webull_quote_service.py`
- `tests/unit/test_paths.py`

Quick command:

```bash
pytest tests/unit
```

## Features

### message_intake

- Happy path: `tests/features/message_intake/happy_path/`
- Edge cases: `tests/features/message_intake/edge_cases/`
- Contracts: `tests/features/message_intake/contracts/`
- Smoke: `tests/features/message_intake/smoke/`

### signal_generation

- Happy path: `tests/features/signal_generation/happy_path/`
- Edge cases: `tests/features/signal_generation/edge_cases/`
- Contracts: `tests/features/signal_generation/contracts/`
- Smoke: `tests/features/signal_generation/smoke/`

### risk_policy

- Happy path: `tests/features/risk_policy/happy_path/`
- Edge cases: `tests/features/risk_policy/edge_cases/`
- Contracts: `tests/features/risk_policy/contracts/`
- Smoke: `tests/features/risk_policy/smoke/`

### trade_execution

- Happy path: `tests/features/trade_execution/happy_path/`
- Edge cases: `tests/features/trade_execution/edge_cases/`
- Contracts: `tests/features/trade_execution/contracts/`
- Smoke: `tests/features/trade_execution/smoke/`

### broker_webull_adapter

- Happy path: `tests/features/broker_webull_adapter/happy_path/`
- Edge cases: `tests/features/broker_webull_adapter/edge_cases/`
- Contracts: `tests/features/broker_webull_adapter/contracts/`
- Smoke: `tests/features/broker_webull_adapter/smoke/`

### observability

- Happy path: `tests/features/observability/happy_path/`
- Edge cases: `tests/features/observability/edge_cases/`
- Contracts: `tests/features/observability/contracts/`
- Smoke: `tests/features/observability/smoke/`

Quick commands:

```bash
pytest tests/features -m feature
pytest tests/features -m contract
pytest -m feature_regression
```

## Shared Test Infrastructure

- Builders: `tests/testkit/builders/`
- Doubles: `tests/testkit/doubles/`
- Payloads: `tests/testkit/payloads/`
- Scenario catalogs: `tests/testkit/scenario_catalogs/`
- Helpers: `tests/testkit/helpers/`
- Datasets: `tests/testkit/datasets/`

## Tooling

- `tests/tooling/`
- `tests/tooling/scripts/`

Quick commands:

```bash
python -m scripts.check_test_file_purity
pytest tests/tooling
python -m scripts.quality.run_health_checks
```
