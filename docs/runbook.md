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
- `config/ai_parser_fast.prompt`
- `config/ai_parser.prompt`
- `.env`

Provider-routing keys in `config/trading.yaml`:

- `trading.execution_provider` (for example `webull`)
- `trading.quote_provider` (`auto`, `webull`, or `yahoo`)

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

Canonical runner:

```bash
./scripts/testing/run.sh list
```

### Core Profiles

```bash
./scripts/testing/run.sh critical
./scripts/testing/run.sh deterministic
./scripts/testing/run.sh all
```

### Live Read Smoke (No Writes)

```bash
./scripts/testing/run.sh live-read
```

### AI Live (Manual Opt-In)

```bash
./scripts/testing/run.sh ai-live --ai-scope sample
./scripts/testing/run.sh ai-live --ai-scope full
```

### Production Night Probe (Manual + Explicit Ack)

```bash
./scripts/testing/run.sh night-probe --ack YES_IM_LIVE
```

### Safety Defaults

- `pytest` default excludes `live` and `write`.
- `critical` is the PR gate profile for core Discord -> parser -> execution confidence.
- `all` includes deterministic + live-read checks.
- `ai-live` is manual only due API cost.
- `night-probe` is production write verification and requires explicit `YES_IM_LIVE` acknowledgement.

## Artifacts and Reports

- Runner JSON report: `artifacts/ci_report.json`
- JUnit XML reports: `artifacts/junit-*.xml`
- Per-suite logs: `artifacts/logs/*.log`

## Related Docs

- Detailed test strategy and matrix: `tests/README.md`
- Test structure policy: `docs/testing.md`
- Test standards playbook: `docs/test-standards.md`
- Manual happy-path check: `docs/manual-testing.md`
- Script details: `docs/SCRIPTS.md`
- DigitalOcean VM deployment: `docs/deploy-digitalocean.md`
