# DigitalOcean VM Deployment (doctl)

This guide deploys the app to a long-running Droplet with manual control.

## Cost and "Turn Off" Modes

- App off (`systemctl stop stocktalk`): VM still billed.
- VM off (`do_shutdown_vm.sh`): VM still billed.
- Billing off (`do_stop_billing.sh`): snapshot + destroy Droplet; compute billing stops.

If your requirement is "not billed anymore," use snapshot + destroy.

## Prerequisites

- `doctl` installed and authenticated.
- SSH key added to DigitalOcean.
- Docker available on the VM (bootstrap script handles this).

Auth check:

```bash
doctl auth list
doctl account get
```

## 1) Pick Cheapest Size in Region

```bash
./scripts/ops/do_select_cheapest_size.sh nyc1
```

The script selects the cheapest *available* size slug for the region.

## 2) Create Droplet (Cheapest)

```bash
./scripts/ops/do_create_droplet.sh \
  --name stocktalk-vm \
  --region nyc1 \
  --ssh-key <ssh-fingerprint-or-id> \
  --tag stocktalk
```

Optional: add project assignment with `--project <project-id>`.

## 3) Bootstrap VM

SSH to the Droplet, clone the repo, then:

```bash
sudo ./scripts/ops/bootstrap_vm.sh --start-now
```

Optional market-hours app schedule (start 09:20 ET, stop 16:10 ET weekdays):

```bash
sudo ./scripts/ops/bootstrap_vm.sh --install-market-hours-timers
sudo systemctl start stocktalk-start.timer stocktalk-stop.timer
```

## 4) Configure Secrets

On VM:

```bash
sudo cp /opt/stocktalk/.env.example /opt/stocktalk/.env
sudo nano /opt/stocktalk/.env
```

Then restart:

```bash
sudo systemctl restart stocktalk
```

## 5) App Control (Manual)

From local machine:

```bash
./scripts/ops/do_app_control.sh --host <droplet-ip> --action status
./scripts/ops/do_app_control.sh --host <droplet-ip> --action start
./scripts/ops/do_app_control.sh --host <droplet-ip> --action stop
./scripts/ops/do_app_control.sh --host <droplet-ip> --action logs
```

## 6) VM Power Control (Still Billed)

```bash
./scripts/ops/do_shutdown_vm.sh --droplet stocktalk-vm
./scripts/ops/do_power_on_vm.sh --droplet stocktalk-vm
```

## 7) Stop Billing (Snapshot + Destroy)

```bash
./scripts/ops/do_stop_billing.sh --droplet stocktalk-vm
```

This script:

1. Creates a snapshot.
2. Verifies snapshot exists.
3. Deletes the Droplet.

It prints snapshot ID/name for restore.

## 8) Restore from Snapshot

```bash
./scripts/ops/do_restore_from_snapshot.sh \
  --snapshot <snapshot-id-or-name> \
  --name stocktalk-vm \
  --region nyc1 \
  --ssh-key <ssh-fingerprint-or-id> \
  --tag stocktalk
```

Then start app:

```bash
./scripts/ops/do_app_control.sh --host <droplet-ip> --action start
```

## 9) Recommended Safety Defaults

- First run with `trading.auto_trade=false`.
- Validate parser and notifications before enabling auto-trade.
- Keep write-path tests opt-in only.

Use validation commands from `docs/runbook.md`.
