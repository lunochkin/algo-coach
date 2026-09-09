"""Where a resume starts: the first step a draft took whose configuration or
prompt hash is no longer what the bench would send, the loop where a corrected
`speedup` released the draft the search held, or the search where the ceiling
that stopped its walk moved.

Where it starts and what it pays for are two questions: a site past the start
is asked again only where its own configuration or prompt hash moved.

The generator is not among them. The draft is that step's output, and a new
prompt writes a different problem rather than the same one again, so editing it
invalidates no stored draft.
"""

from algo_coach.generation.aim import Target
from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.blind import request_hash as blind_hash
from algo_coach.generation.inputs import request_hash as inputs_hash
from algo_coach.generation.naive import request_hash as naive_hash
from algo_coach.generation.speedup import CEILING, Missing
from algo_coach.schema import Draft, WritingState

# the steps a call answers, in the order they run. `checked`, `agreed` and
# `searched` are local runs, so nothing about a bench moves them
ANSWERED = (
    (WritingState.REFERENCED, "blind"),
    (WritingState.BUILT, "inputs"),
    (WritingState.PACED, "naive"),
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


def starts_at(draft: Draft, target: Target, bench: Bench = BENCH) -> WritingState:
    """Where a resume of this draft begins: the first step whose configuration
    or prompt hash moved, and otherwise the one it never took."""
    return moved_at(draft, target, bench) or next_step(draft)


def sending(draft: Draft, site: str, target: Target) -> str | None:
    """The prompt hash that site would send about this draft now, or `None` where
    only a local pass can say."""
    if site == "blind":
        return blind_hash(draft.statement)
    if site == "inputs":
        return inputs_hash(draft.statement)
    if site == "naive":
        # the one prompt carrying more than the statement, so an edited trigger
        # or an edited criterion re-asks the drafts that carry it and no others
        return naive_hash(draft.statement, target)
    # the discrimination prompt carries the survivors, and which mutants stand
    # is known only after the kill pass a resume runs
    return None


def re_asks(draft: Draft, site: str, target: Target, bench: Bench = BENCH) -> bool:
    """Whether a resume pays this site again: it never answered, or its own
    configuration or prompt hash moved.

    Per site rather than per position: three of the four prompts are a function
    of the statement, so none of them invalidates another.
    """
    taken = getattr(draft, f"{site}_provenance")
    if taken is None:
        return True
    # its own prompt hash where a local pass decides one, so the configuration is
    # what answers there
    prompt_hash = sending(draft, site, target) or taken.prompt_hash or ""
    return not taken.at_configuration(getattr(bench, site), prompt_hash)


def draws_again(draft: Draft, target: Target) -> bool:
    """Whether a resume asks the naive solution again though nothing about the bench
    moved.

    The naive solution finished at every size the input generator reached, and it is the one
    sampled site: a second call is a second draw rather than the answer already
    stored.

    Only that reason. A search that never ran is the inputs site's to repair,
    and a draw there pays for a call the search cannot use.
    """
    return (
        draft.state is WritingState.SEARCHED
        and target.template.speedup
        and draft.unseparated == Missing.NAIVE_FINISHED
    )


def re_walks(draft: Draft, target: Target, ceiling: int = CEILING) -> bool:
    """Whether a resume runs the search again though nothing about the bench
    moved: the walk stopped at a ceiling that is no longer the one in force.

    Absent counts as moved. The drafts written before the ceiling was recorded
    were walked under the first one.
    """
    return (
        draft.state is WritingState.SEARCHED
        and target.template.speedup
        and draft.separating_case is None
        and draft.unseparated in (Missing.INPUT_TOO_LARGE, Missing.CASE_TOO_LARGE)
        and draft.ceiling != ceiling
    )


def advances(draft: Draft, target: Target, bench: Bench = BENCH) -> bool:
    """Whether a resume would carry this draft past the state it stopped at.

    A draft whose template claims a speedup and whose search stored no case is
    held before the loop, so a resume starting after the search reaches neither
    the step that would separate it nor the one that would land it. `starts_at`
    still names a step, and it is one the run never takes.
    """
    if not (target.template.speedup and draft.separating_case is None):
        return True
    return reaches(starts_at(draft, target, bench), WritingState.SEARCHED)


def moved_at(draft: Draft, target: Target, bench: Bench = BENCH) -> WritingState | None:
    """The first step to re-run, or `None` where the bench and the template
    answer this draft as it stands.

    A step the draft never took is not moved: what to do about one is the
    draft's state rather than the bench's.
    """
    for state, site in ANSWERED:
        if getattr(draft, f"{site}_provenance") is not None and re_asks(draft, site, target, bench):
            return state
    # a flag edit moves neither a configuration nor a prompt hash, and it is what
    # releases a draft the search held: with no speedup claimed the loop is the
    # step that has not run
    if draft.state is WritingState.SEARCHED and not target.template.speedup:
        return WritingState.HARDENED
    # read after the flag: a corrected claim releases the draft without paying
    # for a draw the search no longer needs
    if draws_again(draft, target):
        return WritingState.PACED
    if re_walks(draft, target):
        return WritingState.SEARCHED
    return None


__all__ = [
    "ANSWERED",
    "ORDER",
    "advances",
    "draws_again",
    "later",
    "moved_at",
    "next_step",
    "re_asks",
    "re_walks",
    "reaches",
    "sending",
    "starts_at",
]
