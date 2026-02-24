# Testing Commands

Use one script:

```bash
./scripts/testing/run.sh list
```

## Core

```bash
./scripts/testing/run.sh quick
./scripts/testing/run.sh live
```

## AI Parser

```bash
./scripts/testing/run.sh ai deterministic
./scripts/testing/run.sh ai live
```

## Discord

```bash
./scripts/testing/run.sh discord deterministic
./scripts/testing/run.sh discord live
```

## Webull

```bash
./scripts/testing/run.sh webull contract
./scripts/testing/run.sh webull read-paper
./scripts/testing/run.sh webull read-production
./scripts/testing/run.sh webull write-paper
./scripts/testing/run.sh webull night-probe YES_IM_LIVE
./scripts/testing/run.sh night YES_IM_LIVE
```

## Safety

- `pytest` default excludes `live` and `write`.
- Production write verification is manual only.
- Night probe requires `YES_IM_LIVE` and auto-cancels after submit.
