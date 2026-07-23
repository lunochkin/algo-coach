from collections import Counter

from pydantic import BaseModel

from algo_coach.schema import Attempt, Diagnosis, FailureMode


class AgreementReport(BaseModel):
    n: int  # attempts with both a self-label and a diagnosis
    agree: int
    rate: float
    confusion: dict[str, dict[str, int]]  # self_label -> diagnosed -> count


def agreement(attempts: list[Attempt], diagnoses: list[Diagnosis]) -> AgreementReport:
    """Classifier agreement vs self-labels — the Phase 1 product-truth
    number. Uses the latest diagnosis per attempt."""
    latest: dict[str, FailureMode] = {}
    for d in sorted(diagnoses, key=lambda d: d.created_at):
        latest[d.attempt_id] = d.mode

    pairs = [
        (a.self_label, latest[a.id])
        for a in attempts
        if a.self_label is not None and a.id in latest
    ]

    confusion: dict[str, Counter] = {}
    agree = 0
    for self_label, diagnosed in pairs:
        confusion.setdefault(self_label.value, Counter())[diagnosed.value] += 1
        if self_label == diagnosed:
            agree += 1

    n = len(pairs)
    return AgreementReport(
        n=n,
        agree=agree,
        rate=agree / n if n else 0.0,
        confusion={k: dict(v) for k, v in confusion.items()},
    )
