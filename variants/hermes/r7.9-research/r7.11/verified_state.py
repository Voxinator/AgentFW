"""verified_state — read/write helpers for r7.11 verified-state.json.

Item 1 of the r7.11 implementation order. Standalone; no Hermes integration.
Per DESIGN-r7.11-architecture.md §4: this file is the wrapper's machine-
authoritative source of truth across session boundaries. The schema is
locked at version "1.0" for r7.11.

Stdlib only. Module exposes:

    Enums:        PhaseStatus, DecisionAction
    Dataclasses:  PhaseSpec, Spec, PhaseStateEntry, HistoryEntry,
                  VerifiedState, Decision
    Errors:       SchemaError (ValueError), IntegrityError (ValueError)
    Functions:    bootstrap, load, save, record_verdict, decide,
                  to_dict, from_dict

Atomic-write contract: save() writes to a NamedTemporaryFile in the SAME
directory as the target, fsyncs, then os.replace()s onto the target. If
the replace fails, the temp file is unlinked. Readers can therefore
assume the target file is either the prior committed state or the new
committed state — never a partial write.

Validation policy on load(): unknown extra fields are TOLERATED for
forward-compatibility. The wrapper and parent are independently
versioned and may run skewed; rejecting unknown fields would couple
their release cycles unnecessarily. Required fields and enum values
ARE strictly validated; that's where lifecycle correctness lives.
"""

from __future__ import annotations

import dataclasses
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class SchemaError(ValueError):
    """Raised when verified-state.json fails schema validation on load."""


class IntegrityError(ValueError):
    """Raised on a semantic violation (e.g., verdict for unknown phase)."""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PhaseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED_PASSED = "verified_passed"
    VERIFIED_FAILED = "verified_failed"


class DecisionAction(str, Enum):
    ADVANCE = "advance"
    REVISE = "revise"
    ESCALATE = "escalate"
    COMPLETE = "complete"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PhaseSpec:
    id: int
    title: str


@dataclass
class Spec:
    scaffold_root: str
    plan_md_path: str
    phases: List[PhaseSpec]


@dataclass
class PhaseStateEntry:
    id: int
    status: PhaseStatus
    tier_run: Optional[int] = None
    verified_at: Optional[str] = None
    session_id: Optional[str] = None
    missing_paths: List[str] = field(default_factory=list)
    integrity_issues: List[str] = field(default_factory=list)
    runtime_smoke_findings: List[str] = field(default_factory=list)
    # Tier 3.7 acceptance-runner findings (added for r7.11 F-7 fix). Mirrors
    # the runtime_smoke_findings shape: a flat list of prefix-tagged
    # strings ([ACCEPTANCE_PASSED], [ACCEPTANCE_FAILED:N], [ENVIRONMENT:..],
    # [INCONCLUSIVE:..], [SKIPPED]). Empty list when tier 3.7 didn't run.
    acceptance_runner_findings: List[str] = field(default_factory=list)
    semantic_concerns: List[str] = field(default_factory=list)
    corrective_dispatch: Optional[str] = None
    revision_count: int = 0
    max_revisions: int = 3


@dataclass
class HistoryEntry:
    session_id: str
    phase_id: int
    verdict: str  # "passed" | "failed"
    ts: str


@dataclass
class VerifiedState:
    schema_version: str
    spec: Spec
    phase_state: List[PhaseStateEntry]
    history: List[HistoryEntry]


@dataclass
class Decision:
    action: DecisionAction
    phase_id: Optional[int]
    reason: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """ISO-8601 UTC timestamp with timezone, second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require(d: dict, key: str, ctx: str) -> Any:
    if key not in d:
        raise SchemaError(f"missing required field {key!r} in {ctx}")
    return d[key]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def to_dict(state: VerifiedState) -> dict:
    """Serialize VerifiedState to a JSON-ready dict (Enums as strings)."""
    return {
        "schema_version": state.schema_version,
        "spec": {
            "scaffold_root": state.spec.scaffold_root,
            "plan_md_path": state.spec.plan_md_path,
            "phases": [
                {"id": p.id, "title": p.title} for p in state.spec.phases
            ],
        },
        "phase_state": [
            {
                "id": e.id,
                "status": e.status.value,
                "tier_run": e.tier_run,
                "verified_at": e.verified_at,
                "session_id": e.session_id,
                "missing_paths": list(e.missing_paths),
                "integrity_issues": list(e.integrity_issues),
                "runtime_smoke_findings": list(e.runtime_smoke_findings),
                "acceptance_runner_findings": list(e.acceptance_runner_findings),
                "semantic_concerns": list(e.semantic_concerns),
                "corrective_dispatch": e.corrective_dispatch,
                "revision_count": e.revision_count,
                "max_revisions": e.max_revisions,
            }
            for e in state.phase_state
        ],
        "history": [
            {
                "session_id": h.session_id,
                "phase_id": h.phase_id,
                "verdict": h.verdict,
                "ts": h.ts,
            }
            for h in state.history
        ],
    }


def from_dict(d: dict) -> VerifiedState:
    """Parse a dict (e.g., from JSON) into a VerifiedState. Validates."""
    if not isinstance(d, dict):
        raise SchemaError(f"top-level value must be an object, got {type(d).__name__}")

    schema_version = _require(d, "schema_version", "top-level")
    if schema_version != SCHEMA_VERSION:
        raise SchemaError(
            f"unsupported schema_version {schema_version!r}; expected {SCHEMA_VERSION!r}"
        )

    spec_d = _require(d, "spec", "top-level")
    if not isinstance(spec_d, dict):
        raise SchemaError("'spec' must be an object")

    scaffold_root = _require(spec_d, "scaffold_root", "spec")
    plan_md_path = _require(spec_d, "plan_md_path", "spec")
    phases_raw = _require(spec_d, "phases", "spec")
    if not isinstance(phases_raw, list):
        raise SchemaError("'spec.phases' must be a list")
    phases: List[PhaseSpec] = []
    for i, p in enumerate(phases_raw):
        if not isinstance(p, dict):
            raise SchemaError(f"spec.phases[{i}] must be an object")
        pid = _require(p, "id", f"spec.phases[{i}]")
        title = _require(p, "title", f"spec.phases[{i}]")
        if not isinstance(pid, int):
            raise SchemaError(f"spec.phases[{i}].id must be int")
        if not isinstance(title, str):
            raise SchemaError(f"spec.phases[{i}].title must be string")
        phases.append(PhaseSpec(id=pid, title=title))

    spec = Spec(
        scaffold_root=scaffold_root,
        plan_md_path=plan_md_path,
        phases=phases,
    )

    phase_state_raw = _require(d, "phase_state", "top-level")
    if not isinstance(phase_state_raw, list):
        raise SchemaError("'phase_state' must be a list")

    valid_status = {s.value for s in PhaseStatus}
    spec_ids = {p.id for p in phases}
    phase_state: List[PhaseStateEntry] = []
    for i, e in enumerate(phase_state_raw):
        if not isinstance(e, dict):
            raise SchemaError(f"phase_state[{i}] must be an object")
        eid = _require(e, "id", f"phase_state[{i}]")
        status_raw = _require(e, "status", f"phase_state[{i}]")
        if not isinstance(eid, int):
            raise SchemaError(f"phase_state[{i}].id must be int")
        if status_raw not in valid_status:
            raise SchemaError(
                f"phase_state[{i}].status invalid: {status_raw!r}; "
                f"allowed: {sorted(valid_status)}"
            )
        if eid not in spec_ids:
            raise SchemaError(
                f"phase_state[{i}].id={eid} not present in spec.phases ids {sorted(spec_ids)}"
            )
        phase_state.append(
            PhaseStateEntry(
                id=eid,
                status=PhaseStatus(status_raw),
                tier_run=e.get("tier_run"),
                verified_at=e.get("verified_at"),
                session_id=e.get("session_id"),
                missing_paths=list(e.get("missing_paths") or []),
                integrity_issues=list(e.get("integrity_issues") or []),
                runtime_smoke_findings=list(e.get("runtime_smoke_findings") or []),
                acceptance_runner_findings=list(
                    e.get("acceptance_runner_findings") or []
                ),
                semantic_concerns=list(e.get("semantic_concerns") or []),
                corrective_dispatch=e.get("corrective_dispatch"),
                revision_count=int(e.get("revision_count", 0)),
                max_revisions=int(e.get("max_revisions", 3)),
            )
        )

    history_raw = _require(d, "history", "top-level")
    if not isinstance(history_raw, list):
        raise SchemaError("'history' must be a list")
    history: List[HistoryEntry] = []
    for i, h in enumerate(history_raw):
        if not isinstance(h, dict):
            raise SchemaError(f"history[{i}] must be an object")
        sid = _require(h, "session_id", f"history[{i}]")
        pid = _require(h, "phase_id", f"history[{i}]")
        verdict = _require(h, "verdict", f"history[{i}]")
        ts = _require(h, "ts", f"history[{i}]")
        if verdict not in ("passed", "failed"):
            raise SchemaError(f"history[{i}].verdict must be 'passed' or 'failed'")
        history.append(HistoryEntry(session_id=sid, phase_id=int(pid), verdict=verdict, ts=ts))

    return VerifiedState(
        schema_version=schema_version,
        spec=spec,
        phase_state=phase_state,
        history=history,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def bootstrap(
    scaffold_root: str,
    plan_md_path: str,
    phases: List[PhaseSpec],
    max_revisions: int = 3,
) -> VerifiedState:
    """Create initial VerifiedState. All phases PENDING; history empty."""
    return VerifiedState(
        schema_version=SCHEMA_VERSION,
        spec=Spec(
            scaffold_root=scaffold_root,
            plan_md_path=plan_md_path,
            phases=list(phases),
        ),
        phase_state=[
            PhaseStateEntry(
                id=p.id,
                status=PhaseStatus.PENDING,
                revision_count=0,
                max_revisions=max_revisions,
            )
            for p in phases
        ],
        history=[],
    )


def load(path: Union[str, Path]) -> VerifiedState:
    """Read JSON from path, validate, return VerifiedState."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        try:
            d = json.load(f)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"invalid JSON in {p}: {exc}") from exc
    return from_dict(d)


def save(state: VerifiedState, path: Union[str, Path]) -> None:
    """Atomically write `state` to `path`.

    Writes to a NamedTemporaryFile in the same directory, fsyncs, then
    os.replace()s. If replace fails, the temp file is removed.
    """
    target = Path(path)
    target_dir = target.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(to_dict(state), indent=2, sort_keys=False)

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(target_dir),
        prefix=target.name + ".",
        suffix=".tmp",
        delete=False,
    )
    tmp_path = Path(tmp.name)
    try:
        try:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(str(tmp_path), str(target))
    except BaseException:
        # Cleanup on any failure (replace error, signal, etc.)
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


def record_verdict(
    state: VerifiedState,
    phase_id: int,
    passed: bool,
    session_id: str,
    tier_run: int,
    missing_paths: Optional[List[str]] = None,
    integrity_issues: Optional[List[str]] = None,
    runtime_smoke_findings: Optional[List[str]] = None,
    semantic_concerns: Optional[List[str]] = None,
    corrective_dispatch: Optional[str] = None,
    acceptance_runner_findings: Optional[List[str]] = None,
) -> VerifiedState:
    """Return a NEW VerifiedState with the verdict recorded.

    Original state is not mutated. On passed=False, increments
    revision_count for the affected phase. Always appends a HistoryEntry.

    Raises IntegrityError if `phase_id` is not in `state.spec.phases`.
    """
    spec_ids = {p.id for p in state.spec.phases}
    if phase_id not in spec_ids:
        raise IntegrityError(
            f"cannot record verdict: phase_id={phase_id} not in spec.phases {sorted(spec_ids)}"
        )

    ts = _now_iso()
    new_phase_state: List[PhaseStateEntry] = []
    for entry in state.phase_state:
        if entry.id != phase_id:
            new_phase_state.append(_clone_entry(entry))
            continue
        new_status = PhaseStatus.VERIFIED_PASSED if passed else PhaseStatus.VERIFIED_FAILED
        new_revision_count = entry.revision_count + (0 if passed else 1)
        new_phase_state.append(
            PhaseStateEntry(
                id=entry.id,
                status=new_status,
                tier_run=tier_run,
                verified_at=ts,
                session_id=session_id,
                missing_paths=list(missing_paths or []),
                integrity_issues=list(integrity_issues or []),
                runtime_smoke_findings=list(runtime_smoke_findings or []),
                acceptance_runner_findings=list(
                    acceptance_runner_findings or []
                ),
                semantic_concerns=list(semantic_concerns or []),
                corrective_dispatch=corrective_dispatch,
                revision_count=new_revision_count,
                max_revisions=entry.max_revisions,
            )
        )

    new_history = [_clone_history(h) for h in state.history]
    new_history.append(
        HistoryEntry(
            session_id=session_id,
            phase_id=phase_id,
            verdict="passed" if passed else "failed",
            ts=ts,
        )
    )

    return VerifiedState(
        schema_version=state.schema_version,
        spec=Spec(
            scaffold_root=state.spec.scaffold_root,
            plan_md_path=state.spec.plan_md_path,
            phases=[PhaseSpec(id=p.id, title=p.title) for p in state.spec.phases],
        ),
        phase_state=new_phase_state,
        history=new_history,
    )


def decide(state: VerifiedState) -> Decision:
    """Walk phase_state in order; return the next action.

    Sequential discipline: a failed-or-pending earlier phase always wins
    over later phases. A failed earlier phase escalates if revisions are
    exhausted; advance is only emitted for pending/in-progress phases
    that come after all-passed predecessors.
    """
    for entry in state.phase_state:
        if entry.status == PhaseStatus.VERIFIED_FAILED:
            if entry.revision_count < entry.max_revisions:
                return Decision(
                    action=DecisionAction.REVISE,
                    phase_id=entry.id,
                    reason=(
                        f"phase {entry.id} verified_failed; "
                        f"revision_count={entry.revision_count} < max_revisions={entry.max_revisions}"
                    ),
                )
            return Decision(
                action=DecisionAction.ESCALATE,
                phase_id=entry.id,
                reason=f"max revisions exceeded for phase {entry.id}",
            )
        if entry.status in (PhaseStatus.PENDING, PhaseStatus.IN_PROGRESS):
            return Decision(
                action=DecisionAction.ADVANCE,
                phase_id=entry.id,
                reason=f"phase {entry.id} {entry.status.value}; advance to dispatch",
            )
        # VERIFIED_PASSED → continue to next
    return Decision(
        action=DecisionAction.COMPLETE,
        phase_id=None,
        reason="all phases verified",
    )


# ---------------------------------------------------------------------------
# Internal: deep-copy helpers (immutability for record_verdict)
# ---------------------------------------------------------------------------

def _clone_entry(e: PhaseStateEntry) -> PhaseStateEntry:
    return PhaseStateEntry(
        id=e.id,
        status=e.status,
        tier_run=e.tier_run,
        verified_at=e.verified_at,
        session_id=e.session_id,
        missing_paths=list(e.missing_paths),
        integrity_issues=list(e.integrity_issues),
        runtime_smoke_findings=list(e.runtime_smoke_findings),
        acceptance_runner_findings=list(e.acceptance_runner_findings),
        semantic_concerns=list(e.semantic_concerns),
        corrective_dispatch=e.corrective_dispatch,
        revision_count=e.revision_count,
        max_revisions=e.max_revisions,
    )


def _clone_history(h: HistoryEntry) -> HistoryEntry:
    return HistoryEntry(
        session_id=h.session_id,
        phase_id=h.phase_id,
        verdict=h.verdict,
        ts=h.ts,
    )


__all__ = [
    "SCHEMA_VERSION",
    "SchemaError",
    "IntegrityError",
    "PhaseStatus",
    "DecisionAction",
    "PhaseSpec",
    "Spec",
    "PhaseStateEntry",
    "HistoryEntry",
    "VerifiedState",
    "Decision",
    "bootstrap",
    "load",
    "save",
    "record_verdict",
    "decide",
    "to_dict",
    "from_dict",
]
