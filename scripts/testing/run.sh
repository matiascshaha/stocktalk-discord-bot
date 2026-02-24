#!/usr/bin/env bash
set -euo pipefail

ACK_VALUE="YES_IM_LIVE"
WEBULL_SMOKE_TEST="tests/brokers/webull/smoke/test_webull_live.py"
PYTHON_BIN="${PYTHON_BIN:-python}"

usage() {
  echo "Usage:"
  echo "  ./scripts/testing/run.sh list"
  echo "  ./scripts/testing/run.sh quick"
  echo "  ./scripts/testing/run.sh live"
  echo "  ./scripts/testing/run.sh ai [deterministic|live]"
  echo "  ./scripts/testing/run.sh discord [deterministic|live]"
  echo "  ./scripts/testing/run.sh webull [contract|read-paper|read-production|write-paper|night-probe] [ACK]"
  echo "  ./scripts/testing/run.sh night [ACK]"
}

run() {
  printf '$ '
  printf '%q ' "$@"
  printf '\n'
  "$@"
}

cmd="${1:-}"
arg1="${2:-}"
arg2="${3:-}"

case "$cmd" in
  list)
    echo "quick"
    echo "live"
    echo "ai [deterministic|live]"
    echo "discord [deterministic|live]"
    echo "webull [contract|read-paper|read-production|write-paper|night-probe] [ACK]"
    echo "night [ACK]"
    ;;
  quick)
    run "$PYTHON_BIN" -m scripts.check_test_file_purity
    run "$PYTHON_BIN" -m pytest tests -m "not smoke and not live and not write"
    ;;
  live)
    run env TEST_AI_LIVE=1 "$PYTHON_BIN" -m pytest tests/parser/smoke/test_ai_live.py -m "smoke and live"
    run env TEST_DISCORD_LIVE=1 "$PYTHON_BIN" -m pytest tests/channels/discord/smoke/test_discord_live.py -m "smoke and live and channel and source_discord"
    run env TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and not write"
    ;;
  ai)
    if [[ "${arg1:-deterministic}" == "live" ]]; then
      run env TEST_AI_LIVE=1 "$PYTHON_BIN" -m pytest tests/parser/smoke/test_ai_live.py -m "smoke and live"
    else
      run "$PYTHON_BIN" -m pytest tests/parser/contract/test_parser_contract.py tests/unit/test_parser_schema.py
    fi
    ;;
  discord)
    if [[ "${arg1:-deterministic}" == "live" ]]; then
      run env TEST_DISCORD_LIVE=1 "$PYTHON_BIN" -m pytest tests/channels/discord/smoke/test_discord_live.py -m "smoke and live and channel and source_discord"
    else
      run "$PYTHON_BIN" -m pytest tests/channels/discord/integration/test_message_flow.py -k "not live_ai_pipeline_message_to_trader"
    fi
    ;;
  webull)
    mode="${arg1:-contract}"
    if [[ "$mode" == "contract" ]]; then
      run "$PYTHON_BIN" -m pytest tests/brokers/webull/contract/test_webull_contract.py
    elif [[ "$mode" == "read-paper" ]]; then
      run env TEST_WEBULL_READ=1 TEST_WEBULL_ENV=paper "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and not write"
    elif [[ "$mode" == "read-production" ]]; then
      run env TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and not write"
    elif [[ "$mode" == "write-paper" ]]; then
      run env TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -m "smoke and live and write"
    elif [[ "$mode" == "night-probe" ]]; then
      if [[ "${arg2:-}" != "$ACK_VALUE" ]]; then
        echo "night-probe requires ACK: $ACK_VALUE"
        exit 2
      fi
      run env TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=production TEST_WEBULL_NIGHT_PROBE=1 TEST_WEBULL_PROD_ACK="$arg2" "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -k "night_probe_production_manual_cleanup" -m "smoke and live and write"
    else
      usage
      exit 2
    fi
    ;;
  night)
    if [[ "${arg1:-}" != "$ACK_VALUE" ]]; then
      echo "night requires ACK: $ACK_VALUE"
      exit 2
    fi
    run env TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=production TEST_WEBULL_NIGHT_PROBE=1 TEST_WEBULL_PROD_ACK="$arg1" "$PYTHON_BIN" -m pytest "$WEBULL_SMOKE_TEST" -k "night_probe_production_manual_cleanup" -m "smoke and live and write"
    ;;
  *)
    usage
    exit 2
    ;;
esac
