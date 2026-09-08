"""
Prospect enrichment and CRM-oriented output layer.

This public implementation demonstrates how an intent-qualified signal
can be transformed into a structured commercial record suitable for
human review or downstream CRM workflows.

No live CRM integration, contact database, or personal prospect data
is included.
"""

from dataclasses import asdict, dataclass
from typing import Dict, Optional

from intent_classification_engine import evaluate_signal
from signal_ingestion_and_dedup import BusinessSignal


@dataclass
class ProspectProfile:
    """
    Sanitized prospect context.

    These fields represent enrichment dimensions that a production
    system could populate from approved business data sources.
    """

    organization: str
    location: str
    stakeholder_persona: str
    contactability: str
    business_fit: str
    enrichment_status: str


@dataclass
class CRMOpportunity:
    """
    CRM-oriented opportunity record.

    This is a structured decision-support object, not an automated
    sales action.
    """

    organization: str
    signal_id: str
    intent: str
    intent_score: int
    priority: str
    stakeholder_persona: str
    contactability: str
    business_fit: str
    location: str
    opportunity_status: str
    recommended_action: str
    human_review_required: bool


def infer_stakeholder_persona(signal: BusinessSignal) -> str:
    """
    Infer a broad stakeholder persona from the available signal text.

    The result is intentionally broad and should be validated by a human
    before being used for outreach.
    """
    text = (
        f"{signal.source_type} "
        f"{signal.content}"
    ).lower()

    if any(
        keyword in text
        for keyword in [
            "ciso",
            "security",
            "information technology",
            "technology",
            "engineering",
            "architect",
        ]
    ):
        return "Technical Leader"

    if any(
        keyword in text
        for keyword in [
            "ceo",
            "cfo",
            "coo",
            "cto",
            "cio",
            "founder",
            "chief",
            "managing director",
        ]
    ):
        return "Executive"

    if any(
        keyword in text
        for keyword in [
            "head of",
            "vice president",
            "vp",
            "director",
            "leadership",
            "business leader",
        ]
    ):
        return "Business Leader"

    return "Unknown"


def assess_business_fit(signal: BusinessSignal) -> str:
    """
    Provide a simple illustrative business-fit assessment.

    Production systems should replace this rule with configurable
    account-fit criteria such as industry, company size, geography,
    solution relevance, and strategic account status.
    """
    if signal.organization.strip():
        return "Requires Validation"

    return "Unknown"


def assess_contactability(signal: BusinessSignal) -> str:
    """
    Indicate whether a potential stakeholder may be identifiable.

    This implementation does not discover or store contact details.
    """
    persona = infer_stakeholder_persona(signal)

    if persona != "Unknown":
        return "Potentially Available"

    return "Unknown"


def enrich_prospect(signal: BusinessSignal) -> ProspectProfile:
    """
    Create a sanitized prospect profile from the business signal.
    """
    return ProspectProfile(
        organization=signal.organization,
        location=signal.location or "Unknown",
        stakeholder_persona=infer_stakeholder_persona(signal),
        contactability=assess_contactability(signal),
        business_fit=assess_business_fit(signal),
        enrichment_status="Preliminary",
    )


def determine_recommended_action(
    intent: str,
    priority: str,
) -> str:
    """
    Convert intent and priority into a human-review recommendation.

    The system deliberately stops before automated outreach.
    """
    if intent == "Buying Request":
        return "Validate buying context and consider priority outreach."

    if intent == "Recommendation":
        return "Validate solution relevance and identify the appropriate stakeholder."

    if intent == "Hiring":
        return "Investigate whether the hiring signal indicates a relevant business need."

    if intent == "Business Challenge":
        return "Research the underlying challenge before considering outreach."

    if priority == "HIGH":
        return "Perform human review and validate commercial relevance."

    return "Monitor and research further before taking action."


def create_crm_opportunity(
    signal: BusinessSignal,
) -> CRMOpportunity:
    """
    Transform a business signal into a CRM-oriented opportunity record.
    """
    analysis = evaluate_signal(signal)
    prospect = enrich_prospect(signal)

    return CRMOpportunity(
        organization=signal.organization,
        signal_id=signal.signal_id,
        intent=analysis["intent"],
        intent_score=analysis["intent_score"],
        priority=analysis["priority"],
        stakeholder_persona=prospect.stakeholder_persona,
        contactability=prospect.contactability,
        business_fit=prospect.business_fit,
        location=prospect.location,
        opportunity_status="Requires Human Validation",
        recommended_action=determine_recommended_action(
            analysis["intent"],
            analysis["priority"],
        ),
        human_review_required=True,
    )


def opportunity_to_crm_payload(
    opportunity: CRMOpportunity,
) -> Dict[str, object]:
    """
    Convert the opportunity into a CRM-friendly dictionary.

    This does not send anything to a CRM.
    """
    payload = asdict(opportunity)

    payload["source"] = "B2B Intent Intelligence Engine"
    payload["automation_status"] = "Human Review Required"

    return payload


def build_review_summary(
    opportunity: CRMOpportunity,
) -> str:
    """
    Create a concise commercial review summary.
    """
    return (
        f"Organization: {opportunity.organization}\n"
        f"Intent: {opportunity.intent}\n"
        f"Priority: {opportunity.priority}\n"
        f"Intent Score: {opportunity.intent_score}\n"
        f"Stakeholder Persona: {opportunity.stakeholder_persona}\n"
        f"Business Fit: {opportunity.business_fit}\n"
        f"Contactability: {opportunity.contactability}\n"
        f"Status: {opportunity.opportunity_status}\n"
        f"Recommended Action: {opportunity.recommended_action}\n"
        f"Human Review Required: {opportunity.human_review_required}"
    )


if __name__ == "__main__":
    from datetime import datetime, timezone

    demo_signal = BusinessSignal(
        signal_id="SIG-DEMO-CRM-001",
        source_type="Business Challenge",
        organization="Example Enterprise",
        content=(
            "Leadership discusses a capability gap and the challenge "
            "of improving operations during rapid expansion."
        ),
        timestamp=datetime.now(timezone.utc),
        location="India",
    )

    opportunity = create_crm_opportunity(demo_signal)

    print("=== CRM-ORIENTED OPPORTUNITY ===")
    print()
    print(build_review_summary(opportunity))

    print()
    print("=== CRM PAYLOAD ===")
    print()

    payload = opportunity_to_crm_payload(opportunity)

    for key, value in payload.items():
        print(f"{key}: {value}")
