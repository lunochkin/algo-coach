"""An answer decided, and the next item picked: `log.md`, Judging a solution."""

from collections.abc import Collection, Sequence
from enum import StrEnum

from algo_coach.schema import ItemStatus, Judgement, JudgementItem


class Verdict(StrEnum):
    RIGHT = "right"  # a clean item called clean
    FALSE_ALARM = "false_alarm"  # a clean item called flawed
    LOCATED = "located"  # a flaw called flawed, on its own line
    SPOTTED = "spotted"  # a flaw called flawed, on another line
    MISSED = "missed"  # a flaw called clean


def verdict(item: JudgementItem, answer: Judgement) -> Verdict:
    if item.clean:
        return Verdict.RIGHT if answer.called_clean else Verdict.FALSE_ALARM
    if answer.called_clean:
        return Verdict.MISSED
    return Verdict.LOCATED if answer.line == item.line else Verdict.SPOTTED


def next_item(
    items: Sequence[JudgementItem],
    answers: Sequence[Judgement],
    *,
    templates: Collection[str] | None = None,
) -> JudgementItem | None:
    """Unseen first, then the item answered longest ago; `templates` narrows
    the pick to one card's forms."""
    last: dict[str, int] = {}
    for order, one in enumerate(answers):
        last[one.item_id] = order
    open_ = [
        one
        for one in items
        if one.status is ItemStatus.SERVED and (templates is None or one.template_id in templates)
    ]
    if not open_:
        return None
    return min(open_, key=lambda one: (one.id in last, last.get(one.id, -1), one.id))
