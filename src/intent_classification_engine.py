"""
Deterministic intent classification layer for the B2B Intent Intelligence Engine.

This public implementation demonstrates a transparent, explainable approach
to classifying business signals before any future semantic AI layer is added.

The scoring is for prioritization only. It is not a prediction of purchase
probability, revenue, or deal outcome.
"""

import re
from dataclasses import dataclass
from typing import Dict, List

from signal_ingestion_and_dedup import BusinessSignal


INTENT_SCORES: Dict[str, int] = {
    "Buying Request": 85,
    "Recommendation": 80,
    "Hiring": 75,
    "Business Challenge": 70,
    "General Discussion": 30,
}


INTENT_PATTERNS: Dict[str, List[str]] = {
    "Buying Request": [
        r"\blooking for\b",
        r"\bneed a solution\b",
        r"\bseeking\b",
        r"\brecommend a vendor\b",
        r"\bvendor recommendation\b",
        r"\bsolution provider\b",
    ],
    "Recommendation": [
        r"\brecommend\b",
        r"\bwho can help\b",
        r"\bany recommendations\b",
        r"\blooking for a provider\b",
        r"\blooking for a partner\b",
    ],
    "Hiring": [
        r"\bhiring\b",
        r"\bopen position\b",
        r"\bjob opening\b",
        r"\bjoining our team\b",
        r"\bwe are expanding\b",
        r"\bexpanding the team\b",
    ],
    "Business Challenge": [
        r"\bchallenge\b",
        r"\bproblem\b",
        r"\bstruggling\b",
        r"\bdifficulty\b",
        r"\bissue\b",
        r"\bneed to improve\b",
        r"\bcapability gap\b",
    ],
}


PERSONA_PATTERNS: Dict[str, List[str]] = {
    "Executive": [
        r"\bceo\b",
        r"\bcfo\b",
        r"\bcoo\b",
        r"\bcto\b",
        r"\bcio\b",
        r"\bchief\b",
        r"\bfounder\b",
        r"\bmanaging director\b",
    ],
    "Business Leader": [
        r"\bhead of\b",
        r"\bvice president\b",
        r"\bvp\b",
        r"\bdirector\b",
        r"\bbusiness leader\b",
        r"\bleadership\b",
    ],
    "Technical Leader": [
        r"\bciso\b",
        r"\bsecurity\b",
        r"\binformation technology\b",
        r"\btechnology leader\b",
        r"\bengineering\b",
        r"\barchitect\b",
    ],
}


@dataclass
class IntentAnalysis:
    category: str
    base_score: int
    keyword_bonus: int
    persona: str
    persona_bonus: int
    final_score: int
    priority: str
    explanation: str


def _find_matches(text: str, patterns: List[str]) -> List[str]:
    """Return the patterns that match the supplied text."""
    matches = []

    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(pattern)

    return matches


def detect_intent(text: str) -> str:
    """
    Detect the highest-priority intent category using transparent rules.

    Source type can also be used by callers as contextual evidence, but
    this function deliberately evaluates only the supplied text.
    """
    normalized = text.lower()

    category_order = [
        "Buying Request",
        "Recommendation",
        "Hiring",
        "Business Challenge",
    ]

    for category in category_order:
        if _find_matches(normalized, INTENT_PATTERNS[category]):
            return category

    return "General Discussion"


def detect_persona(text: str) -> str:
    """Detect an indicative stakeholder persona from text."""
    normalized = text.lower()

    for persona, patterns in PERSONA_PATTERNS.items():
        if _find_matches(normalized, patterns):
            return persona

    return "Unknown"


def classify_signal(signal: BusinessSignal) -> IntentAnalysis:
    """
    Classify and prioritize a business signal.

    Scoring:
    - Base intent score determined by category.
    - Keyword evidence can add up to 10 points.
    - Indicative stakeholder persona adds 5 points.
    """
    text = normalize_for_analysis(signal)

    category = detect_intent(text)
    base_score = INTENT_SCORES[category]

    matches = _find_matches(
        text,
        INTENT_PATTERNS.get(category, []),
    )

    keyword_bonus = min(len(matches) * 5, 10)

    persona = detect_persona(text)
    persona_bonus = 5 if persona != "Unknown" else 0

    final_score = min(
        base_score + keyword_bonus + persona_bonus,
        100,
    )

    priority = determine_priority(final_score)

    explanation = build_explanation(
        category=category,
        persona=persona,
        matches=matches,
        final_score=final_score,
    )

    return IntentAnalysis(
        category=category,
        base_score=base_score,
        keyword_bonus=keyword_bonus,
        persona=persona,
        persona_bonus=persona_bonus,
        final_score=final_score,
        priority=priority,
        explanation=explanation,
    )


def normalize_for_analysis(signal: BusinessSignal) -> str:
    """Combine useful signal fields into one analysis string."""
    return " ".join(
        [
            signal.source_type,
            signal.organization,
            signal.content,
            signal.location,
        ]
    ).lower()


def determine_priority(score: int) -> str:
    """Convert the prioritization score into an action-oriented category."""
    if score >= 85:
        return "HIGH"

    if score >= 70:
        return "MEDIUM"

    return "LOW"


def build_explanation(
    category: str,
    persona: str,
    matches: List[str],
    final_score: int,
) -> str:
    """Create a human-readable explanation for the classification."""
    evidence_count = len(matches)

    return (
        f"Classified as '{category}' with {evidence_count} "
        f"matching intent signal(s). "
        f"Indicative persona: {persona}. "
        f"Final prioritization score: {final_score}. "
        f"Human review is required before commercial action."
    )


def evaluate_signal(signal: BusinessSignal) -> Dict[str, object]:
    """Return a structured dictionary suitable for downstream workflows."""
    analysis = classify_signal(signal)

    return {
        "signal_id": signal.signal_id,
        "organization": signal.organization,
        "intent": analysis.category,
        "intent_score": analysis.final_score,
        "priority": analysis.priority,
        "persona": analysis.persona,
        "explanation": analysis.explanation,
        "human_review_required": True,
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    demo_signal = BusinessSignal(
        signal_id="SIG-DEMO-INTENT-001",
        source_type="Business Challenge",
        organization="Example Enterprise",
        content=(
            "Leadership discusses a capability gap and the challenge "
            "of improving operations during rapid expansion."
        ),
        timestamp=datetime.now(timezone.utc),
        location="India",
    )

    result = evaluate_signal(demo_signal)

    for key, value in result.items():
        print(f"{key}: {value}")
