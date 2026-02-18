"""Artifact writing helpers for smoke tests."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def append_smoke_check(report_path: Path, name: str, status: str, details: Dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    else:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": [],
        }
    report["checks"].append({"name": name, "status": status, "details": details})
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
