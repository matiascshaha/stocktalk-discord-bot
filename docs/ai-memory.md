# AI Memory

Use this file as durable memory for high-value repo knowledge.

## Entry format

| Date | Area | Type | Fact/Decision | Evidence | Owner | Review date |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | ui-tests | fact | Replace me | path:line | handle | YYYY-MM-DD |
| 2026-02-25 | ops | command | `scripts/ops/do_app_control.sh` supports `--action enable|disable`; `disable` applies no-autostart behavior by running `systemctl disable` plus stop. | scripts/ops/do_app_control.sh:9; docs/deploy-digitalocean.md:181 | codex | 2026-05-25 |
| 2026-02-25 | ai | decision | `ai.provider=none` is an explicit hard disable and no longer falls back to available providers, even if `ai.fallback_to_available_provider=true`. | src/ai_parser.py:370; tests/unit/test_parser_schema.py:208 | codex | 2026-05-25 |
| 2026-02-25 | ops | decision | VM runtime mode control is host-mounted config: systemd passes `CONFIG_PATH=/app/config/trading.yaml` and bind-mounts `/opt/stocktalk/config/trading.yaml`, allowing `ai.provider` and `trading.auto_trade` changes without rebuilding images. | deploy/systemd/stocktalk.service:15; docs/deploy-digitalocean.md:74 | codex | 2026-05-25 |
| 2026-02-25 | ops | decision | Production VM deploy path is prebuilt GHCR image pull with pinned SHA tags; `stocktalk.service` no longer builds images on VM start. | deploy/systemd/stocktalk.service:1; docs/deploy-digitalocean.md:1 | codex | 2026-05-25 |
| 2026-02-25 | ops | command | Canonical image deploy command is `./scripts/ops/do_deploy_image.sh --host <droplet-ip> --image-tag <full-commit-sha> --identity ~/.ssh/id_ed25519_stocktalk` (pass `--image-repository` on first deploy). | scripts/ops/do_deploy_image.sh:1; docs/deploy-digitalocean.md:132 | codex | 2026-05-25 |
| 2026-02-25 | ops | gotcha | `bootstrap_vm.sh --start-now` skips service start if `/opt/stocktalk/.env.runtime` still has placeholder owner; set real GHCR repository/tag first. | scripts/ops/bootstrap_vm.sh:95 | codex | 2026-05-25 |
| 2026-02-25 | testing | decision | Provider unit tests for Anthropic/Gemini are opt-in behind `RUN_OPTIONAL_PROVIDER_TESTS=1`; default provider unit runs focus on OpenAI path. | tests/unit/test_provider_client_factory.py:9; tests/unit/test_provider_dispatch.py:9 | codex | 2026-05-25 |
| 2026-02-25 | ai | decision | Provider SDK imports are lazy in `client_factory`; OpenAI-only deployments can omit `anthropic` and `google-generativeai` from default `requirements.txt` without breaking startup. | src/providers/client_factory.py:1; requirements.txt:1 | codex | 2026-05-25 |
| 2026-02-25 | ops | command | Preferred VM bootstrap flow is local one-command remote bootstrap: `./scripts/ops/do_bootstrap_vm.sh --host <droplet-ip> --identity ~/.ssh/id_ed25519_stocktalk` (can run with `BATCH_MODE=1` after `ssh-add`). | scripts/ops/do_bootstrap_vm.sh:1; docs/deploy-digitalocean.md:53 | codex | 2026-05-25 |
| 2026-02-25 | ops | gotcha | `bootstrap_vm.sh` must resolve Docker Compose package by distro (`docker-compose-plugin` or `docker-compose-v2`) to work on Ubuntu 24.04 droplets. | scripts/ops/bootstrap_vm.sh:53 | codex | 2026-05-25 |
| 2026-02-25 | ops | gotcha | Non-interactive SSH ops (`BATCH_MODE=1`) require the passphrase-protected key to be preloaded in local `ssh-agent` (`ssh-add ~/.ssh/id_ed25519_stocktalk`), otherwise auth fails with `Permission denied (publickey)` or `The agent has no identities`. | docs/deploy-digitalocean.md:61; scripts/ops/do_app_control.sh:86 | codex | 2026-05-25 |
| 2026-02-25 | ops | gotcha | `scripts/ops/do_app_control.sh` must allow explicit SSH identity selection in multi-key environments; use `--identity <private-key-path>` to avoid `Permission denied (publickey)` when default SSH key is not the Droplet key. | scripts/ops/do_app_control.sh:1; docs/deploy-digitalocean.md:169 | codex | 2026-05-25 |
| 2026-02-24 | architecture | decision | Webull stock payload/sizing logic now lives in `src/brokerages/webull/stock_payload_builder.py`; `WebullTrader` delegates stock payload construction to keep order sizing logic modular and avoid mutating `StockOrderRequest` input quantity. | src/brokerages/webull/stock_payload_builder.py:1; src/webull_trader.py:309 | codex | 2026-05-24 |
| 2026-02-24 | testing | decision | Unified test entrypoint is `./scripts/testing/run.sh`; production Webull write verification is manual-only via `night`/`night-probe` with explicit `YES_IM_LIVE` ack and cleanup cancel. | scripts/testing/run.sh:1; tests/brokers/webull/smoke/test_webull_live.py:125; docs/testing.md:1 | codex | 2026-05-24 |
| 2026-02-22 | testing | decision | Test tree is domain-first (`tests/parser`, `tests/channels`, `tests/brokers`, `tests/system`, `tests/unit`); strategy split lives lower (`contract`/`integration`/`smoke`) and marker taxonomy is orthogonal (`unit|contract|integration|e2e`, `smoke`, `live`, `write`, domain markers). | tests/README.md:1; docs/testing.md:9; pytest.ini:1 | codex | 2026-05-22 |
| 2026-02-16 | architecture | decision | Provider integrations should live under `src/providers/<provider>/` with separate contract and client modules; parser orchestrators should call provider entry points instead of embedding provider protocol details. | AGENTS.md:50; docs/conventions.md:28 | codex | 2026-05-16 |
| 2026-02-11 | docs | decision | Deep application/platform knowledge lives in `docs/system-context/` and is linked from `docs/architecture.md`; consult it early for behavior-heavy tasks. | AGENTS.md:22; docs/architecture.md:35; docs/system-context/index.md:1 | codex | 2026-05-11 |
| 2026-02-11 | docs | decision | System context is organized as task-routed files (topology, dependencies, APIs, UI journeys, Jira process, domain model, onboarding, source registry) to mirror real onboarding and speed retrieval. | docs/system-context/index.md:11; docs/system-context/reference/source-registry.md:1; docs/architecture.md:37 | codex | 2026-05-11 |

## Types

- `fact`: stable technical truth
- `decision`: selected approach with rationale
- `gotcha`: recurring failure pattern
- `command`: canonical command for setup/verify/release

## Rules

- Keep entries short and verifiable.
- Link to source files, PRs, or run logs.
- Remove or supersede stale entries.
