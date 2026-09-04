"""Where a resume starts: the first step a draft took whose configuration or
digest is no longer what the bench would send, or the loop where a corrected
`speedup` released the draft the search held.

Where it starts and what it pays for are two questions: a site past the start
is asked again only where its own configuration or digest moved.

The generator is not among them. The draft is that step's output, and a new
prompt writes a different problem rather than the same one again, so editing it
invalidates no stored draft.
"""

from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.blind import request_hash as blind_hash
from algo_coach.generation.clock import request_hash as clock_hash
from algo_coach.generation.inputs import request_hash as inputs_hash
from algo_coach.outcomes import at_configuration
from algo_coach.schema import Draft, Template, WritingState

# the steps a call answers, in the order they run. `checked`, `agreed` and
# `searched` are local runs, so nothing about a bench moves them
ANSWERED = (
    (WritingState.REFERENCED, "blind"),
    (WritingState.BUILT, "inputs"),
    (WritingState.PACED, "clock"),
    (WritingState.HARDENED, "discrimination"),
)

# every state in the order the steps reach it. `rejected` is terminal rather
# than a point in the sequence, so it is not among them
ORDER = (
    WritingState.DRAFTED,
    WritingState.CHECKED,
    WritingState.REFERENCED,
    WritingState.AGREED,
    WritingState.BUILT,
    WritingState.PACED,
    WritingState.SEARCHED,
    WritingState.HARDENED,
    WritingState.LANDED,
)


def reaches(start: WritingState, step: WritingState) -> bool:
    """Whether a run starting there takes this step, rather than reusing what
    the draft already holds."""
    return ORDER.index(step) >= ORDER.index(start)


def later(one: WritingState, other: WritingState) -> WritingState:
    """The further of two states along the sequence."""
    return max(one, other, key=ORDER.index)


def next_step(draft: Draft) -> WritingState:
    """The step a draft that stopped has not taken."""
    return ORDER[min(ORDER.index(draft.state) + 1, len(ORDER) - 1)]


def starts_at(draft: Draft, template: Template, bench: Bench = BENCH) -> WritingState:
    """Where a resume of this draft begins: the first step whose configuration
    or digest moved, and otherwise the one it never took."""
    return moved_at(draft, template, bench) or next_step(draft)


def sending(draft: Draft, site: str, template: Template) -> str | None:
    """The digest that site would send about this draft now, or `None` where
    only a local pass can say."""
    if site == "blind":
        return blind_hash(draft.statement)
    if site == "inputs":
        return inputs_hash(draft.statement)
    if site == "clock":
        # the one prompt carrying more than the statement, so an edited trigger
        # re-asks the drafts written for that form and no others
        return clock_hash(draft.statement, template.trigger)
    # the discrimination prompt carries the survivors, and which mutants stand
    # is known only after the kill pass a resume runs
    return None


def re_asks(draft: Draft, site: str, template: Template, bench: Bench = BENCH) -> bool:
    """Whether a resume pays this site again: it never answered, or its own
    configuration or digest moved.

    Per site rather than per position: three of the four prompts are a function
    of the statement, so none of them invalidates another.
    """
    taken = getattr(draft, site)
    if taken is None:
        return True
    # its own digest where a local pass decides one, so the configuration is
    # what answers there
    digest = sending(draft, site, template) or taken.prompt_hash or ""
    return not at_configuration(taken, getattr(bench, site), digest)


def moved_at(draft: Draft, template: Template, bench: Bench = BENCH) -> WritingState | None:
    """The first step to re-run, or `None` where the bench and the template
    answer this draft as it stands.

    A step the draft never took is not moved: what to do about one is the
    draft's state rather than the bench's.
    """
    for state, site in ANSWERED:
        if getattr(draft, site) is not None and re_asks(draft, site, template, bench):
            return state
    # a flag edit moves neither a configuration nor a digest, and it is what
    # releases a draft the search held: with no speedup claimed the loop is the
    # step that has not run
    if draft.state is WritingState.SEARCHED and not template.speedup:
        return WritingState.HARDENED
    return None


__all__ = [
    "ANSWERED",
    "ORDER",
    "later",
    "moved_at",
    "next_step",
    "re_asks",
    "reaches",
    "sending",
    "starts_at",
]
