"""
End-to-end orchestration layer for the B2B Intent Intelligence Engine.

This module connects the public deterministic components into a simple
signal-to-opportunity pipeline.

The architecture is intentionally lightweight. It demonstrates how
signal preparation, intent analysis, prioritization, and human review
can be connected without exposing production integrations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List

from intent_classification_engine import evaluate_signal
from signal_ingestion_and_dedup import (
    BusinessSignal,
    prepare_signals,
)


@dataclass
class OpportunityRecord:
    """Structured output for a potentially relevant business opportunity."""

    signal_id: str
    organization: str
    intent: str
    intent_score: int
    priority: str
    persona: str
    explanation: str
    human_review_required: bool


def build_opportunity(signal: BusinessSignal) -> OpportunityRecord:
    """
    Convert a classified business signal into a structured opportunity record.
    """
    analysis = evaluate_signal(signal)

    return OpportunityRecord(
        signal_id=analysis["signal_id"],
        organization=analysis["organization"],
        intent=analysis["intent"],
        intent_score=analysis["intent_score"],
        priority=analysis["priority"],
        persona=analysis["persona"],
        explanation=analysis["explanation"],
        human_review_required=analysis["human_review_required"],
    )


def run_intent_pipeline(
    signals: Iterable[BusinessSignal],
    recency_hours: int = 48,
    now: datetime | None = None,
) -> List[OpportunityRecord]:
    """
    Run the public intent-intelligence workflow.

    Processing sequence:

    1. Signal ingestion
    2. Deduplication
    3. Recency filtering
    4. Intent classification
    5. Prioritization
    6. Structured opportunity creation
    7. Human review requirement
    """
    prepared_signals = prepare_signals(
        signals,
        recency_hours=recency_hours,
        now=now,
    )

    opportunities = []

    for signal in prepared_signals:
        opportunity = build_opportunity(signal)

        opportunities.append(opportunity)

    return opportunities


def summarize_pipeline(
    opportunities: Iterable[OpportunityRecord],
) -> Dict[str, object]:
    """
    Produce a simple management-level summary of pipeline output.
    """
    opportunity_list = list(opportunities)

    priority_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    intent_counts: Dict[str, int] = {}

    for opportunity in opportunity_list:
        priority_counts[opportunity.priority] = (
            priority_counts.get(opportunity.priority, 0) + 1
        )

        intent_counts[opportunity.intent] = (
            intent_counts.get(opportunity.intent, 0) + 1
        )

    return {
        "signals_processed": len(opportunity_list),
        "priority_distribution": priority_counts,
        "intent_distribution": intent_counts,
        "human_review_required": len(opportunity_list),
    }


def format_for_human_review(
    opportunity: OpportunityRecord,
) -> str:
    """
    Create a compact review brief for a sales professional.

    The purpose is to support a human decision, not to automate outreach.
    """
    return (
        f"Organization: {opportunity.organization}\n"
        f"Intent: {opportunity.intent}\n"
        f"Priority: {opportunity.priority}\n"
        f"Intent Score: {opportunity.intent_score}\n"
        f"Indicative Persona: {opportunity.persona}\n"
        f"Why It Matters: {opportunity.explanation}\n"
        f"Human Review Required: "
        f"{opportunity.human_review_required}"
    )


if __name__ == "__main__":
    from datetime import timezone

    demo_now = datetime(
        2026,
        9,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    demo_signals = [
        BusinessSignal(
            signal_id="SIG-DEMO-001",
            source_type="Hiring",
            organization="Example Enterprise",
            content=(
                "Example Enterprise is expanding the team "
                "and hiring a business leader."
            ),
            timestamp=datetime(
                2026,
                9,
                7,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            location="India",
        ),
        BusinessSignal(
            signal_id="SIG-DEMO-002",
            source_type="Business Challenge",
            organization="Example Enterprise",
            content=(
                "Leadership discusses a capability gap and "
                "the challenge of improving operations."
            ),
            timestamp=datetime(
                2026,
                9,
                6,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            location="India",
        ),
    ]

    opportunities = run_intent_pipeline(
        demo_signals,
        recency_hours=48,
        now=demo_now,
    )

    summary = summarize_pipeline(opportunities)

    print("=== INTENT INTELLIGENCE PIPELINE ===")
    print()

    for opportunity in opportunities:
        print(format_for_human_review(opportunity))
        print()
        print("-" * 50)
        print()

    print("=== PIPELINE SUMMARY ===")
    print(f"Signals processed: {summary['signals_processed']}")
    print(
        f"Priority distribution: "
        f"{summary['priority_distribution']}"
    )
    print(
        f"Intent distribution: "
        f"{summary['intent_distribution']}"
    )
    print(
        f"Human reviews required: "
        f"{summary['human_review_required']}"
    )
