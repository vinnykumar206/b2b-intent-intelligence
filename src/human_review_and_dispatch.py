"""
Human review and notification layer for the B2B Intent Intelligence Engine.

This module represents the final decision-support stage of the public
portfolio implementation.

The system can prepare a review notification, but it does not automatically
contact prospects, send messages, create CRM activities, or execute outreach.

The intended production pattern is:

Intent Detection
        ↓
Commercial Prioritization
        ↓
Human Review
        ↓
Decision
        ↓
Optional Sales Action
"""

from dataclasses import dataclass
from typing import Dict, List

from prospect_enrichment_and_crm import (
    CRMOpportunity,
    build_review_summary,
    opportunity_to_crm_payload,
)


@dataclass
class HumanReviewDecision:
    """Represents the decision made by a human reviewer."""

    signal_id: str
    organization: str
    decision: str
    reviewer_note: str = ""


VALID_DECISIONS = {
    "Pursue",
    "Research Further",
    "Defer",
    "Reject",
    "Route to Another Team",
}


def create_review_notification(
    opportunity: CRMOpportunity,
) -> Dict[str, object]:
    """
    Create a structured notification for human review.

    This function prepares the notification payload only.
    It does not send a message through Telegram, email, Slack,
    CRM, or any other external system.
    """
    return {
        "notification_type": "Intent Review Required",
        "priority": opportunity.priority,
        "organization": opportunity.organization,
        "intent": opportunity.intent,
        "intent_score": opportunity.intent_score,
        "stakeholder_persona": opportunity.stakeholder_persona,
        "recommended_action": opportunity.recommended_action,
        "human_review_required": True,
        "review_summary": build_review_summary(opportunity),
    }


def format_notification(
    notification: Dict[str, object],
) -> str:
    """
    Format a review notification into a human-readable message.
    """
    return (
        "=== B2B INTENT REVIEW ===\n"
        f"Priority: {notification['priority']}\n"
        f"Organization: {notification['organization']}\n"
        f"Intent: {notification['intent']}\n"
        f"Intent Score: {notification['intent_score']}\n"
        f"Stakeholder Persona: "
        f"{notification['stakeholder_persona']}\n"
        f"Recommended Action: "
        f"{notification['recommended_action']}\n"
        "\n"
        "Review Summary:\n"
        f"{notification['review_summary']}\n"
        "\n"
        "Decision required from human reviewer."
    )


def validate_decision(decision: str) -> bool:
    """Check whether a human review decision is supported."""
    return decision in VALID_DECISIONS


def record_human_decision(
    opportunity: CRMOpportunity,
    decision: str,
    reviewer_note: str = "",
) -> HumanReviewDecision:
    """
    Record the human decision associated with an opportunity.

    Invalid decisions are rejected rather than silently accepted.
    """
    if not validate_decision(decision):
        valid_options = ", ".join(sorted(VALID_DECISIONS))

        raise ValueError(
            f"Invalid decision '{decision}'. "
            f"Valid decisions: {valid_options}"
        )

    return HumanReviewDecision(
        signal_id=opportunity.signal_id,
        organization=opportunity.organization,
        decision=decision,
        reviewer_note=reviewer_note,
    )


def route_review_outcome(
    opportunity: CRMOpportunity,
    decision: HumanReviewDecision,
) -> Dict[str, object]:
    """
    Convert the human decision into a downstream routing instruction.

    No external action is performed.
    """
    routes = {
        "Pursue": "Sales Action Queue",
        "Research Further": "Research Queue",
        "Defer": "Deferred Opportunities",
        "Reject": "Rejected Opportunities",
        "Route to Another Team": "Internal Routing Queue",
    }

    return {
        "signal_id": opportunity.signal_id,
        "organization": opportunity.organization,
        "decision": decision.decision,
        "destination": routes[decision.decision],
        "reviewer_note": decision.reviewer_note,
        "external_action_executed": False,
    }


def build_dispatch_payload(
    opportunity: CRMOpportunity,
) -> Dict[str, object]:
    """
    Build a combined payload that could be consumed by a future
    notification or workflow integration.
    """
    notification = create_review_notification(opportunity)
    crm_payload = opportunity_to_crm_payload(opportunity)

    return {
        "notification": notification,
        "crm_opportunity": crm_payload,
        "requires_human_decision": True,
        "external_dispatch_enabled": False,
    }


def summarize_review_queue(
    opportunities: List[CRMOpportunity],
) -> Dict[str, int]:
    """Return a simple count of opportunities requiring review."""
    summary = {
        "total": len(opportunities),
        "high_priority": 0,
        "medium_priority": 0,
        "low_priority": 0,
    }

    for opportunity in opportunities:
        if opportunity.priority == "HIGH":
            summary["high_priority"] += 1
        elif opportunity.priority == "MEDIUM":
            summary["medium_priority"] += 1
        else:
            summary["low_priority"] += 1

    return summary


if __name__ == "__main__":
    from datetime import datetime, timezone

    from signal_ingestion_and_dedup import BusinessSignal

    demo_signal = BusinessSignal(
        signal_id="SIG-DEMO-REVIEW-001",
        source_type="Business Challenge",
        organization="Example Enterprise",
        content=(
            "Leadership discusses a capability gap and the challenge "
            "of improving operations during rapid expansion."
        ),
        timestamp=datetime.now(timezone.utc),
        location="India",
    )

    from prospect_enrichment_and_crm import create_crm_opportunity

    opportunity = create_crm_opportunity(demo_signal)

    notification = create_review_notification(opportunity)

    print(format_notification(notification))

    print()
    print("=== HUMAN DECISION EXAMPLE ===")

    decision = record_human_decision(
        opportunity=opportunity,
        decision="Research Further",
        reviewer_note=(
            "Validate whether the capability challenge represents "
            "an active business initiative."
        ),
    )

    route = route_review_outcome(
        opportunity=opportunity,
        decision=decision,
    )

    print(f"Decision: {route['decision']}")
    print(f"Destination: {route['destination']}")
    print(f"External action executed: {route['external_action_executed']}")
