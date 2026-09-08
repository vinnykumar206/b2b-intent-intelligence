"""
Signal ingestion and deduplication layer for the B2B Intent Intelligence Engine.

This public implementation is intentionally deterministic and sanitized.
It demonstrates how incoming business signals can be normalized,
fingerprinted, deduplicated, and filtered by recency before intent analysis.

No live API, browser session, CRM, or production data is included.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Iterable, List


@dataclass
class BusinessSignal:
    signal_id: str
    source_type: str
    organization: str
    content: str
    timestamp: datetime
    location: str = ""


def normalize_text(text: str) -> str:
    """Normalize signal text for comparison and fingerprinting."""
    return " ".join(text.lower().strip().split())


def generate_fingerprint(signal: BusinessSignal) -> str:
    """
    Generate a deterministic fingerprint from the core signal content.

    This allows repeated or near-identical signals to be identified
    without storing the original source data.
    """
    normalized = "|".join(
        [
            normalize_text(signal.source_type),
            normalize_text(signal.organization),
            normalize_text(signal.content),
        ]
    )

    return sha256(normalized.encode("utf-8")).hexdigest()


def deduplicate_signals(
    signals: Iterable[BusinessSignal],
) -> List[BusinessSignal]:
    """Return only the first occurrence of each unique signal."""
    seen = set()
    unique_signals = []

    for signal in signals:
        fingerprint = generate_fingerprint(signal)

        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        unique_signals.append(signal)

    return unique_signals


def filter_recent_signals(
    signals: Iterable[BusinessSignal],
    hours: int = 48,
    now: datetime | None = None,
) -> List[BusinessSignal]:
    """
    Keep signals that fall within the configured recency window.

    The default monitoring window is 48 hours.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=hours)

    return [
        signal
        for signal in signals
        if signal.timestamp >= cutoff
    ]


def prepare_signals(
    signals: Iterable[BusinessSignal],
    recency_hours: int = 48,
    now: datetime | None = None,
) -> List[BusinessSignal]:
    """
    Prepare incoming signals for downstream intent analysis.

    Processing sequence:
    1. Deduplicate
    2. Apply recency filtering
    """
    unique_signals = deduplicate_signals(signals)

    return filter_recent_signals(
        unique_signals,
        hours=recency_hours,
        now=now,
    )


if __name__ == "__main__":
    demo_now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)

    demo_signals = [
        BusinessSignal(
            signal_id="SIG-001",
            source_type="Hiring",
            organization="Example Enterprise",
            content="Example Enterprise is expanding its leadership team.",
            timestamp=datetime(
                2026, 9, 7, 9, 0, tzinfo=timezone.utc
            ),
            location="India",
        ),
        BusinessSignal(
            signal_id="SIG-002",
            source_type="Hiring",
            organization="Example Enterprise",
            content="Example Enterprise is expanding its leadership team.",
            timestamp=datetime(
                2026, 9, 7, 9, 5, tzinfo=timezone.utc
            ),
            location="India",
        ),
        BusinessSignal(
            signal_id="SIG-003",
            source_type="Business Challenge",
            organization="Example Enterprise",
            content="Leadership discusses challenges created by rapid expansion.",
            timestamp=datetime(
                2026, 9, 6, 11, 0, tzinfo=timezone.utc
            ),
            location="India",
        ),
    ]

    prepared = prepare_signals(
        demo_signals,
        recency_hours=48,
        now=demo_now,
    )

    print(f"Input signals: {len(demo_signals)}")
    print(f"Prepared signals: {len(prepared)}")

    for signal in prepared:
        print(
            f"- {signal.signal_id}: "
            f"{signal.source_type} | "
            f"{signal.organization}"
        )
