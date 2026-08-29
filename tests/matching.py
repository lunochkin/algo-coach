"""Fixtures the matcher tests share: a model answering from a script, and the
records a verdict needs to exist."""

import json
from dataclasses import dataclass, field

from helpers import PROVENANCE

from algo_coach.calls import Reply
from algo_coach.cards import CardStore, seed_cards
from algo_coach.problems import ProblemStore
from algo_coach.schema import Card, Problem, TemplateKind


@dataclass
class Verdict:
    """One reply the fake model gives: the templates it named, a failure it
    raises, or — naming nothing at all — an answer cut short."""

    templates: list[str] | None = None
    error: Exception | None = None


@dataclass
class FakeTransport:
    """Records the request rather than making one — the prompt is what these
    tests are about."""

    replies: list[Verdict]
    calls: list[dict] = field(default_factory=list)

    @classmethod
    def answering(cls, *verdicts: Verdict) -> FakeTransport:
        return cls(list(verdicts))

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        verdict = self.replies[len(self.calls) - 1]
        if verdict.error is not None:
            raise verdict.error
        if verdict.templates is None:
            return Reply(text=None, stop_reason="length", provider="fake")
        return Reply(
            text=json.dumps({"templates": verdict.templates}),
            stop_reason="stop",
            provider="fake",
        )


def template(slug: str, **overrides) -> dict:
    return {
        "slug": slug,
        "title": slug,
        "trigger": f"the cue for {slug}",
        "code": f"def {slug.replace('-', '_')}(): pass",
    } | overrides


def card(
    slug: str = "sliding-window",
    *,
    technique: str = "sliding-window",
    templates: list[dict] | None = None,
    **overrides,
) -> dict:
    return {
        "slug": slug,
        "technique": technique,
        "title": slug,
        "trigger": "a window over a contiguous run",
        "brief": "## Core idea\n\nGrow, then shrink.",
        "templates": templates or [template("longest-valid-window"), template("fixed-window")],
        "selector": {"technique": technique, "size": 5},
    } | overrides


def seeded(root, *records: dict) -> list[Card]:
    """Cards as the engine holds them: minted ids, since a match references
    them and a seed file carries none. In the order authored, not the order
    the store happens to list minted ids in."""
    store = CardStore(root)
    authored = records or (card(),)
    result = seed_cards(authored, store=store)
    assert result.rejected == []
    return [store.by_slug(one["slug"]) for one in authored]


def problem(
    id: str, *, techniques: list[str], statement: str = "Given an array, return ..."
) -> Problem:
    return Problem(
        id=id,
        title=id,
        statement=statement,
        techniques=techniques,
        **PROVENANCE,
    )


def stored(root, *problems: Problem) -> list[Problem]:
    store = ProblemStore(root)
    for one in problems:
        store.put(one)
    return store.all()


PROCEDURE = {"kind": TemplateKind.PROCEDURE.value}
