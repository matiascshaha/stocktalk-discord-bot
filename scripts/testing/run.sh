#!/usr/bin/env bash
set -euo pipefail

ACK_VALUE="YES_IM_LIVE"
WEBULL_SMOKE_TEST="tests/brokers/webull/smoke/test_webull_live.py"
PYTHON_BIN="${PYTHON_BIN:-python}"

usage() {
  cat <<EOF
Simple unified test runner.

Usage:
  ./scripts/testing/run.sh list
  ./scripts/testing/run.sh quick
  ./scripts/testing/run.sh live
  ./scripts/testing/run.sh ai deterministic|live
  ./scripts/testing/run.sh discord deterministic|live
  ./scripts/testing/run.sh webull contract|read-paper|read-production|write-paper|night-probe [ACK]
  ./scripts/testing/run.sh night [ACK]
EOF
}

print_cmd() {
  printf '$ '
  printf '%q ' "$@"
  printf '\n'
}

run_step() {
  local name="$1"
  shift
  echo
  echo "== ${name} =="
  print_cmd "$@"
  "$@"
}

command_list() {
  cat <<EOF
quick
live
ai deterministic|live
discord deterministic|live
webull contract|read-paper|read-production|write-paper|night-probe [ACK]
night [ACK]
EOF
}

command_quick() {
  run_step "test_file_purity" "$PYTHON_BIN" -m scripts.check_test_file_purity
  run_step "deterministic_suite" "$PYTHON_BIN" -m pytest tests -m "not smoke and not live and not write"
}

command_live() {
  run_step "ai_live_smoke" env TEST_AI_LIVE=1 "$PYTHON_BIN" -m pytest tests/parser/smoke/test_ai_live.py -m "smoke and live"
  run_step "discord_live_smoke" env TEST_DISCORD_LIVE=1 "$PYTHON_BIN" -m pytest tests/channels/discord/smoke/test_discord_live.py -m "smoke and live and channel and source_discord"
  run_step "webull_read_production" env TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and not write"
}

command_ai() {
  local mode="${1:-deterministic}"
  case "$mode" in
    deterministic)
      run_step "ai_parser_contract" "$PYTHON_BIN" -m pytest tests/parser/contract/test_parser_contract.py tests/unit/test_parser_schema.py
      ;;
    live)
      run_step "ai_live_smoke" env TEST_AI_LIVE=1 "$PYTHON_BIN" -m pytest tests/parser/smoke/test_ai_live.py -m "smoke and live"
      ;;
    *)
      echo "Invalid ai mode: $mode"
      usage
      exit 2
      ;;
  esac
}

command_discord() {
  local mode="${1:-deterministic}"
  case "$mode" in
    deterministic)
      run_step "discord_deterministic_flow" "$PYTHON_BIN" -m pytest tests/channels/discord/integration/test_message_flow.py -k "not live_ai_pipeline_message_to_trader"
      ;;
    live)
      run_step "discord_live_smoke" env TEST_DISCORD_LIVE=1 "$PYTHON_BIN" -m pytest tests/channels/discord/smoke/test_discord_live.py -m "smoke and live and channel and source_discord"
      ;;
    *)
      echo "Invalid discord mode: $mode"
      usage
      exit 2
      ;;
  esac
}

command_webull() {
  local mode="${1:-contract}"
  local ack="${2:-}"
  case "$mode" in
    contract)
      run_step "webull_contract" "$PYTHON_BIN" -m pytest tests/brokers/webull/contract/test_webull_contract.py
      ;;
    read-paper)
      run_step "webull_read_paper" env TEST_WEBULL_READ=1 TEST_WEBULL_ENV=paper "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and not write"
      ;;
    read-production)
      run_step "webull_read_production" env TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and not write"
      ;;
    write-paper)
      run_step "webull_write_paper" env TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and write"
      ;;
    night-probe)
      if [[ "$ack" != "$ACK_VALUE" ]]; then
        echo "night-probe requires ACK: $ACK_VALUE"
        exit 2
      fi
      run_step "webull_night_probe_production" env TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=production TEST_WEBULL_NIGHT_PROBE=1 TEST_WEBULL_PROD_ACK="$ack" "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -k "night_probe_production_manual_cleanup" -m "smoke and live and write"
      ;;
    *)
      echo "Invalid webull mode: $mode"
      usage
      exit 2
      ;;
  esac
}

command_night() {
  local ack="${1:-}"
  command_webull "night-probe" "$ack"
}

main() {
  local command="${1:-}"
  case "$command" in
    list)
      command_list
      ;;
    quick)
      command_quick
      ;;
    live)
      command_live
      ;;
    ai)
      shift || true
      command_ai "${1:-deterministic}"
      ;;
    discord)
      shift || true
      command_discord "${1:-deterministic}"
      ;;
    webull)
      shift || true
      command_webull "${1:-contract}" "${2:-}"
      ;;
    night)
      shift || true
      command_night "${1:-}"
      ;;
    *)
      usage
      exit 2
      ;;
  esac
}

main "$@"

