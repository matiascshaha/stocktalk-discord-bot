# Developer Runbook

Canonical commands for setup, running the monitor, and validating test confidence.

## Prerequisites

- Run commands from repository root.
- Use Python 3.11.x.
- Activate virtual environment before running app/tests.

## Setup

Preferred automated setup:

```bash
python3 scripts/bootstrap/project_setup.py
source .venv/bin/activate
```

Manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade "pip<25" "setuptools<70" wheel
PIP_NO_BUILD_ISOLATION=1 pip install -r requirements.txt
pip install -e .
```

## Configuration and Credential Checks

```bash
cp .env.example .env
python -m scripts.diagnostics.verify_credentials
```

Main config files:

- `config/trading.yaml`
- `config/ai_parser.prompt`
- `.env`

## Run the Tool

Default monitor run:

```bash
python -m src.main
```

Editable-install console entrypoint:

```bash
stock-monitor
```

Useful runtime modes:

- Monitor-only mode: set `trading.auto_trade: false` in `config/trading.yaml`.
- No-AI mode: set `ai.provider: none` in `config/trading.yaml`.
- Auto-trade mode: set `trading.auto_trade: true` and configure broker credentials in `.env`.
- Paper-trade safety: set `trading.paper_trade: true` for manual validation.

## Deploy Commands (DigitalOcean + GHCR)

Publish image from GitHub Actions:

```bash
gh workflow run publish-image.yml
```

Local publish fallback:

```bash
IMAGE_REPOSITORY=ghcr.io/<owner>/stocktalk-discord-bot
IMAGE_TAG="$(git rev-parse HEAD)"
echo "<github-token>" | docker login ghcr.io -u <github-username> --password-stdin
docker build -t "${IMAGE_REPOSITORY}:${IMAGE_TAG}" -t "${IMAGE_REPOSITORY}:latest" .
docker push "${IMAGE_REPOSITORY}:${IMAGE_TAG}"
docker push "${IMAGE_REPOSITORY}:latest"
```

One-time GHCR auth on VM:

```bash
echo "<github-token>" | sudo docker login ghcr.io -u <github-username> --password-stdin
```

Deploy immutable SHA image:

```bash
./scripts/ops/do_deploy_image.sh \
  --host <droplet-ip> \
  --image-repository ghcr.io/<owner>/stocktalk-discord-bot \
  --image-tag <full-commit-sha> \
  --identity ~/.ssh/id_ed25519_stocktalk
```

VM runtime config file used by container:

```bash
/opt/stocktalk/config/trading.yaml
```

Container is started with `CONFIG_PATH=/app/config/trading.yaml` and host bind mount of that file.

Roll forward/rollback by SHA:

```bash
./scripts/ops/do_deploy_image.sh --host <droplet-ip> --image-tag <full-commit-sha> --identity ~/.ssh/id_ed25519_stocktalk
./scripts/ops/do_deploy_image.sh --host <droplet-ip> --image-tag <previous-good-sha> --identity ~/.ssh/id_ed25519_stocktalk
```

## PR Workflow (Auto-Merge Required)

Create a PR from the current branch:

```bash
gh pr create --base webull-integration --head webull-wt-1 --fill
```

Enable auto-merge right after PR creation:

```bash
gh pr merge --auto --squash <pr-number>
```

Useful checks:

```bash
gh pr checks <pr-number> --watch
gh pr view <pr-number> --web
gh pr view <pr-number> --json mergeable,baseRefName,headRefName
```

Conflict handling rule:

- Before enabling auto-merge, check `mergeable` status.
- If the PR is conflicted, stop and ask the requester how to resolve each conflict.
- Ask explicitly whether to prefer current branch changes, base branch changes, or a manual merge per file.

## Testing Commands

Use one script:

```bash
./scripts/testing/run.sh list
```

### Core

```bash
./scripts/testing/run.sh quick
./scripts/testing/run.sh live
```

### AI Parser

```bash
./scripts/testing/run.sh ai deterministic
./scripts/testing/run.sh ai live
```

### Discord

```bash
./scripts/testing/run.sh discord deterministic
./scripts/testing/run.sh discord live
```

### Webull

```bash
./scripts/testing/run.sh webull contract
./scripts/testing/run.sh webull read-paper
./scripts/testing/run.sh webull read-production
./scripts/testing/run.sh webull write-paper
./scripts/testing/run.sh webull night-probe YES_IM_LIVE
./scripts/testing/run.sh night YES_IM_LIVE
```

### Safety

- `pytest` default excludes `live` and `write`.
- Production write verification is manual only.
- Night probe requires `YES_IM_LIVE` and auto-cancels after submit.

## Deterministic Test Commands

Fast local deterministic default:

```bash
pytest
```

Deterministic CI-style run:

```bash
python -m scripts.check_test_file_purity
python -m pytest tests -m "not smoke and not live and not write"
```

Targeted deterministic suites:

```bash
pytest tests/unit
pytest tests/parser/contract/test_parser_contract.py tests/unit/test_parser_schema.py
pytest tests/channels/discord/integration/test_message_flow.py -k "not live_ai_pipeline_message_to_trader"
pytest tests/brokers/webull/contract/test_webull_contract.py
pytest tests/system/integration
```

## Smoke and Live Test Commands

Parser AI live smoke:

```bash
TEST_AI_LIVE=1 pytest tests/parser/smoke/test_ai_live.py -m "smoke and live"
```

AI to trader live pipeline:

```bash
TEST_AI_LIVE=1 TEST_AI_SCOPE=sample pytest tests/channels/discord/integration/test_message_flow.py -k "live_ai_pipeline_message_to_trader" -m "smoke and live"
```

Webull live read smoke:

```bash
TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production pytest tests/brokers/webull/smoke/test_webull_live.py -m "smoke and live and not write"
```

Webull live write smoke (opt-in):

```bash
TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper pytest tests/brokers/webull/smoke/test_webull_live.py -m "smoke and live and write"
```

Discord live smoke:

```bash
TEST_DISCORD_LIVE=1 pytest tests/channels/discord/smoke/test_discord_live.py -m "smoke and live and channel and source_discord"
```

## Quality Runners

Health check runner:

```bash
python -m scripts.quality.run_health_checks
TEST_MODE=strict python -m scripts.quality.run_health_checks
```

Confidence suite runner:

```bash
python -m scripts.quality.run_confidence_suite
python -m scripts.quality.run_confidence_suite --mode local
python -m scripts.quality.run_confidence_suite --webull-env paper
python -m scripts.quality.run_confidence_suite --webull-write 1
```

Full scenario matrix:

```bash
python -m scripts.quality.run_full_matrix --list
python -m scripts.quality.run_full_matrix
python -m scripts.quality.run_full_matrix --skip-discord-live --skip-webull-prod-write --ai-scope sample
python -m scripts.quality.run_full_matrix --only webull_read_paper,webull_write_paper
```

## Artifacts and Reports

- Health report JSON: `artifacts/health_report.json`
- Reliability workflow deterministic JUnit: `artifacts/junit-deterministic.xml`
- Reliability workflow external smoke JUnit: `artifacts/junit-external-smoke.xml`

## Related Docs

- Detailed test strategy and matrix: `tests/README.md`
- Test structure policy: `docs/testing.md`
- Test standards playbook: `docs/test-standards.md`
- Manual happy-path check: `docs/manual-testing.md`
- Script details: `docs/SCRIPTS.md`
- DigitalOcean VM deployment: `docs/deploy-digitalocean.md`
