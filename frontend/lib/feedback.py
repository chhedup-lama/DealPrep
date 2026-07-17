"""Phase 1D trust loop: a local, append-only feedback log so an AE can mark
an insight useful/not-useful (and why), and so precision-by-flag-type is
measurable instead of assumed (PRD-phase1-dashboard.md §Phase 1D).

Persisted to a plain JSONL file rather than session state so feedback
survives a page rerun and accumulates across AEs during a demo session —
still not a real database (see roadmap: no production analytics store yet).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "feedback.jsonl"

VALID_KINDS = ("useful", "not_useful", "dismissed")


def record(ae: str, account_id: str, flag_type: str, kind: str, reason: str | None = None) -> None:
    if kind not in VALID_KINDS:
        raise ValueError(f"Unknown feedback kind: {kind}")
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ae": ae,
        "account_id": account_id,
        "flag_type": flag_type,
        "kind": kind,
        "reason": reason,
    }
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _read_all() -> list[dict]:
    if not FEEDBACK_PATH.exists():
        return []
    entries = []
    with FEEDBACK_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def precision_by_flag_type() -> dict[str, dict[str, int]]:
    """{"usage_decline": {"useful": 3, "not_useful": 1}, ...} — only counts
    useful/not_useful, not dismissals (dismissing isn't a quality signal on
    its own — an AE might dismiss something true but already handled)."""
    stats: dict[str, dict[str, int]] = {}
    for entry in _read_all():
        if entry["kind"] not in ("useful", "not_useful"):
            continue
        bucket = stats.setdefault(entry["flag_type"], {"useful": 0, "not_useful": 0})
        bucket[entry["kind"]] += 1
    return stats
