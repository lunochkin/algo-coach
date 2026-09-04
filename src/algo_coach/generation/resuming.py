"""Where a resume starts: the first step a draft took whose configuration or
digest is no longer what the bench would send, or the loop where a corrected
`speedup` released the draft the search held.

The generator is not among them. The draft is that step's output, and a new
prompt writes a different problem rather than the same one again, so editing it
invalidates no stored draft.
"""

from algo_coach.generation.bench import BENCH, Bench
from algo_coach.generation.blind import request_hash as blind_hash
from algo_coach.generation.inputs import request_hash as inputs_hash
from algo_coach.outcomes import at_configuration
from algo_coach.schema import Draft, Template, WritingState

# the steps a call answers, in the order they run. `checked`, `agreed` and
# `searched` are local runs, so nothing about a bench moves them
ANSWERED = (
    (WritingState.REFERENCED, "blind"),
    (WritingState.BUILT, "inputs"),
    (WritingState.HARDENED, "discrimination"),
)


def sending(draft: Draft, site: str) -> str | None:
    """The digest that site would send about this draft now, or `None` where
    only a local pass can say."""
    if site == "blind":
        return blind_hash(draft.statement)
    if site == "inputs":
        return inputs_hash(draft.statement)
    # the discrimination prompt carries the survivors, and which mutants stand
    # is known only after the kill pass a resume runs
    return None


def moved_at(draft: Draft, template: Template, bench: Bench = BENCH) -> WritingState | None:
    """The first step to re-run, or `None` where the bench and the template
    answer this draft as it stands.

    A step the draft never took is not moved: what to do about one is the
    draft's state rather than the bench's.
    """
    for state, site in ANSWERED:
        taken = getattr(draft, site)
        if taken is None:
            continue
        # its own digest where a local pass decides one, so the configuration
        # is what answers there
        digest = sending(draft, site) or taken.prompt_hash or ""
        if not at_configuration(taken, getattr(bench, site), digest):
            return state
    # a flag edit moves neither a configuration nor a digest, and it is what
    # releases a draft the search held: with no speedup claimed the loop is the
    # step that has not run
    if draft.state is WritingState.SEARCHED and not template.speedup:
        return WritingState.HARDENED
    return None


__all__ = ["ANSWERED", "moved_at", "sending"]
