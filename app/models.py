"""Typed domain models. FROZEN after M2 — the parallel streams (M3/M4/M5) build on these
and must not change them mid-stream (see missions.md parallel-safety rules).

The load-bearing type here is ``Proposal``: an AI-generated artifact that, by construction,
*persists nothing*. It exists only in memory until a human disposes of it via
``decision_log.record(...)``. That separation is the propose→dispose boundary (Invariant 1).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# --- Persona / record (synthetic source data) ---

@dataclass(frozen=True)
class Record:
    id: str
    date: str
    source: str
    author: str
    type: str
    text: str
    risk_indicator: bool = False
    risk_category: str | None = None
    risk_rationale: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Record":
        return cls(
            id=d["id"],
            date=d.get("date", ""),
            source=d.get("source", ""),
            author=d.get("author", ""),
            type=d.get("type", ""),
            text=d.get("text", ""),
            risk_indicator=bool(d.get("risk_indicator", False)),
            risk_category=d.get("risk_category"),
            risk_rationale=d.get("risk_rationale"),
        )


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    age: int
    synthetic: bool
    summary_line: str
    records: tuple[Record, ...]
    demo_note: str | None = None

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def has_risk_indicator(self) -> bool:
        return any(r.risk_indicator for r in self.records)

    def get_record(self, record_id: str) -> Record | None:
        return next((r for r in self.records if r.id == record_id), None)

    @classmethod
    def from_dict(cls, d: dict) -> "Persona":
        return cls(
            id=d["id"],
            name=d["name"],
            age=d.get("age", 0),
            synthetic=bool(d.get("synthetic", False)),
            summary_line=d.get("summary_line", ""),
            records=tuple(Record.from_dict(r) for r in d.get("records", [])),
            demo_note=d.get("demo_note"),
        )


# --- The propose → log → dispose primitive ---

class Surface(str, Enum):
    CONTEXT = "context"
    DRAFTING = "drafting"
    ESCALATION = "escalation"


class ProposalType(str, Enum):
    BRIEF = "brief"
    CASE_NOTE = "case_note"
    FOLLOW_UP = "follow_up"
    RISK_FLAG = "risk_flag"


class Disposition(str, Enum):
    """The human action taken on a proposal. There is no 'auto' member — by design,
    a disposition is always something a person chose."""
    COMMIT = "commit"
    DISCARD = "discard"
    SEND = "send"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Proposal:
    """An AI-generated proposal that has NOT been disposed of. Constructing one writes
    nothing anywhere — it is purely in-memory until a human acts on it."""
    persona_id: str
    surface: Surface
    proposal_type: ProposalType
    proposal_text: str
    model: str | None = None


@dataclass(frozen=True)
class DecisionLogEntry:
    """One immutable row of the decision log: an AI proposal + the human disposition of it."""
    id: int
    created_at: str
    persona_id: str | None
    surface: str
    proposal_type: str | None
    proposal_text: str | None
    disposition: str
    final_text: str | None
    author: str
    model: str | None

    @classmethod
    def from_row(cls, row) -> "DecisionLogEntry":
        return cls(
            id=row["id"],
            created_at=row["created_at"],
            persona_id=row["persona_id"],
            surface=row["surface"],
            proposal_type=row["proposal_type"],
            proposal_text=row["proposal_text"],
            disposition=row["disposition"],
            final_text=row["final_text"],
            author=row["author"],
            model=row["model"],
        )
