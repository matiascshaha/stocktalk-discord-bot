# DigitalOcean VM Deployment (doctl + GHCR)

This guide uses a staged, low-cost deployment model:

- Build/publish Docker images in GitHub Actions.
- Deploy immutable SHA-tagged images to the Droplet.
- Do not build Docker images on the VM.

This avoids build-time OOM on small droplets.

From local machine, you can connect without hardcoding IP:

```bash
./scripts/ops/do_ssh_vm.sh stocktalk-vm root
```

## Cost and "Turn Off" Modes

- App off (`systemctl stop stocktalk`): VM still billed.
- VM off (`do_shutdown_vm.sh`): VM still billed.
- Billing off (`do_stop_billing.sh`): snapshot + destroy Droplet; compute billing stops.

If your requirement is "not billed anymore," use snapshot + destroy.

## 1) Prerequisites

- `doctl` installed and authenticated.
- SSH key added to DigitalOcean.
- GitHub repository has Actions enabled.
- GitHub Container Registry (GHCR) package publishing allowed for the repo.

Auth check:

```bash
doctl auth list
doctl account get
```

## 2) Pick Cheapest Size in Region

```bash
./scripts/ops/do_select_cheapest_size.sh nyc1
```

The script selects the cheapest available size slug for the region.

## 3) Create Droplet

```bash
./scripts/ops/do_create_droplet.sh \
  --name stocktalk-vm \
  --region nyc1 \
  --ssh-key <ssh-fingerprint-or-id> \
  --tag stocktalk
```

Optional: add project assignment with `--project <project-id>`.

## 4) Bootstrap VM (One Command)

From your local machine:

```bash
./scripts/ops/do_bootstrap_vm.sh --host <droplet-ip> --identity ~/.ssh/id_ed25519_stocktalk
```

If your key has a passphrase and you want non-interactive runs:

```bash
ssh-add ~/.ssh/id_ed25519_stocktalk
BATCH_MODE=1 ./scripts/ops/do_bootstrap_vm.sh --host <droplet-ip> --identity ~/.ssh/id_ed25519_stocktalk
```

`bootstrap_vm.sh` creates:

- `/opt/stocktalk/.env` from `.env.example` (if missing)
- `/opt/stocktalk/.env.runtime` from `deploy/systemd/stocktalk.env.runtime.example` (if missing)
- `/opt/stocktalk/config/trading.yaml` from `config/trading.yaml` (via repo sync)

The runtime file must be set to your GHCR image before first app start.

Optional market-hours schedule (start 09:20 ET, stop 16:10 ET weekdays):

```bash
./scripts/ops/do_bootstrap_vm.sh --host <droplet-ip> --install-market-hours-timers --identity ~/.ssh/id_ed25519_stocktalk
ssh -i ~/.ssh/id_ed25519_stocktalk root@<droplet-ip> 'sudo systemctl start stocktalk-start.timer stocktalk-stop.timer'
```

## 5) Configure Runtime Secrets and Modes

On VM:

```bash
sudo nano /opt/stocktalk/.env
```

Set runtime mode in:

```bash
sudo nano /opt/stocktalk/config/trading.yaml
```

Recommended safe defaults:

- `ai.provider: none` (no AI API calls/cost)
- `trading.auto_trade: false` (monitor-only, no order execution)
- `trading.paper_trade: true` (extra safety if auto-trade is re-enabled later)

## 6) Publish Image to GHCR

Workflow: `.github/workflows/publish-image.yml`

- Trigger automatically on push to `main`.
- Or run manually:

```bash
gh workflow run publish-image.yml
```

Image tags produced:

- `ghcr.io/<owner>/stocktalk-discord-bot:<full-commit-sha>`
- `ghcr.io/<owner>/stocktalk-discord-bot:latest` (default branch convenience tag)

Optional local publish fallback:

```bash
IMAGE_REPOSITORY=ghcr.io/<owner>/stocktalk-discord-bot
IMAGE_TAG="$(git rev-parse HEAD)"
echo "<github-token>" | docker login ghcr.io -u <github-username> --password-stdin
docker build -t "${IMAGE_REPOSITORY}:${IMAGE_TAG}" -t "${IMAGE_REPOSITORY}:latest" .
docker push "${IMAGE_REPOSITORY}:${IMAGE_TAG}"
docker push "${IMAGE_REPOSITORY}:latest"
```

## 7) Configure GHCR Pull Auth on VM (One Time)

Create a GitHub token with package read access, then on VM:

```bash
echo "<github-token>" | sudo docker login ghcr.io -u <github-username> --password-stdin
```

## 8) Deploy Pinned Image Tag

First deploy (set repository + tag):

```bash
./scripts/ops/do_deploy_image.sh \
  --host <droplet-ip> \
  --image-repository ghcr.io/<owner>/stocktalk-discord-bot \
  --image-tag <full-commit-sha> \
  --identity ~/.ssh/id_ed25519_stocktalk
```

Next deploys (tag only):

```bash
./scripts/ops/do_deploy_image.sh \
  --host <droplet-ip> \
  --image-tag <full-commit-sha> \
  --identity ~/.ssh/id_ed25519_stocktalk
```

For non-interactive deploys with a passphrase-protected key, use the `ssh-add` flow from section 4 and run with `BATCH_MODE=1`.

## 9) Rollback

Redeploy the previous known-good SHA:

```bash
./scripts/ops/do_deploy_image.sh \
  --host <droplet-ip> \
  --image-tag <previous-good-sha> \
  --identity ~/.ssh/id_ed25519_stocktalk
```

## 10) App Control and Logs

```bash
./scripts/ops/do_app_control.sh --host <droplet-ip> --action status --identity ~/.ssh/id_ed25519_stocktalk
./scripts/ops/do_app_control.sh --host <droplet-ip> --action logs --identity ~/.ssh/id_ed25519_stocktalk
./scripts/ops/do_app_control.sh --host <droplet-ip> --action stop --identity ~/.ssh/id_ed25519_stocktalk
./scripts/ops/do_app_control.sh --host <droplet-ip> --action start --identity ~/.ssh/id_ed25519_stocktalk
```

For non-interactive control commands with a passphrase-protected key, use the same `ssh-add` setup from section 4 and run with `BATCH_MODE=1`. `The agent has no identities` means no key is loaded in your local `ssh-agent`.

## 11) VM Power Control (Still Billed)

```bash
./scripts/ops/do_shutdown_vm.sh --droplet stocktalk-vm
./scripts/ops/do_power_on_vm.sh --droplet stocktalk-vm
```

## 12) Stop Billing (Snapshot + Destroy)

```bash
./scripts/ops/do_stop_billing.sh --droplet stocktalk-vm
```

This script:

1. Creates a snapshot.
2. Verifies snapshot exists.
3. Deletes the Droplet.

It prints snapshot ID/name for restore.

## 13) Restore from Snapshot

```bash
./scripts/ops/do_restore_from_snapshot.sh \
  --snapshot <snapshot-id-or-name> \
  --name stocktalk-vm \
  --region nyc1 \
  --ssh-key <ssh-fingerprint-or-id> \
  --tag stocktalk
```

Then redeploy a known-good image tag:

```bash
./scripts/ops/do_deploy_image.sh \
  --host <droplet-ip> \
  --image-tag <known-good-sha> \
  --identity ~/.ssh/id_ed25519_stocktalk
```

If SSH returns `Permission denied (publickey)` after snapshot restore:

- Snapshot image may not accept newly attached keys.
- Recover access through DigitalOcean web console/recovery flow and re-add your key to `~/.ssh/authorized_keys`.
- For future restores, prefer a source snapshot where cloud-init key injection is verified, or recreate from fresh Ubuntu + `bootstrap_vm.sh`.
