"""The stored drafts: a line per draft for `--drafts`, and one read whole for
`--draft`."""

from algo_coach.cli.display import case_line, configured, listing_code, shortened, sites
from algo_coach.generation import (
    Bench,
    Target,
    advances,
    starts_at,
)
from algo_coach.schema import (
    Draft,
    SiteOutcome,
    WritingState,
)


def listing(draft: Draft, target: Target | None, bench: Bench) -> str:
    """One stored draft: the form it was briefed on, how far it was written,
    and what it is waiting on."""
    form = target.template.slug if target is not None else str(draft.template_id)
    return f"{draft.id}  {form[:24]:<24}  {draft.state:<10}  {waiting_on(draft, target, bench)}"


def waiting_on(draft: Draft, target: Target | None, bench: Bench) -> str:
    """What a resume would do with this draft. A terminal state names what put
    it there, since no step follows it."""
    if draft.state is WritingState.REJECTED:
        return f"rejected by {draft.gate}"
    if draft.state is WritingState.LANDED:
        return f"landed as {draft.problem_id}, cleared by the next run"
    if target is None:
        # the form its brief named is not seeded, and a search reads `speedup`
        # from it
        return f"no template {draft.template_id}"
    if not advances(draft, target.template, bench):
        # the step `starts_at` names is past the search, and a draft with no
        # separating case is held before the loop: reporting that step would
        # name work the resume never does
        return f"held before the loop: {draft.unseparated}"
    return f"starts at {starts_at(draft, target.template, bench)}"


def drafts_summary(
    waiting: list[tuple[Draft, Target | None]], bench: Bench, *, listed: bool = True
) -> str:
    """How many drafts a sweep would carry, apart from the ones it would pass
    over.

    Counted over the store rather than over the lines above: a summary reading
    only what was printed would report fewer drafts than the store holds.

    The bench is not named. It is what a resume would pay at rather than what
    wrote any of these, and each draft carries its own — `--draft` prints one.
    """
    resuming = [
        draft
        for draft, target in waiting
        if target is not None
        and draft.state not in (WritingState.REJECTED, WritingState.LANDED)
        and advances(draft, target.template, bench)
    ]
    line = f"{len(waiting)} draft(s) stored, {len(resuming)} would resume"
    rejected = sum(draft.state is WritingState.REJECTED for draft, _ in waiting)
    if rejected and not listed:
        # named rather than dropped: nothing resumes one, and its gate is
        # readable nowhere else
        line += f"\n{rejected} rejected draft(s) not listed; --all prints them"
    return line


def report(draft: Draft, target: Target | None, outcomes: list[SiteOutcome], bench: Bench) -> str:
    """One draft as a page: where it stands, what each step was written at, the
    problem itself, and what the sites left."""
    return "\n".join(
        [
            f"# {draft.title} ({draft.id})",
            "",
            heading(draft, target),
            waiting_on(draft, target, bench),
            "",
            "## configurations",
            *(f"  {name:<15} {configured(getattr(draft, name))}" for name in Bench.model_fields),
            "",
            "## statement",
            "",
            draft.statement,
            "",
            *cases(draft),
            *listing_code("canonical", draft.canonical),
            *listing_code("reference", draft.reference),
            *listing_code(f"input generator (up to {draft.largest})", draft.builder),
            *listing_code("naive solution", draft.naive),
            *sites(outcomes, none="none recorded: they are written once the loop has run"),
        ]
    )


def heading(draft: Draft, target: Target | None) -> str:
    """The form it was briefed on and how far it was written. A technique brief
    names no form, and neither does a draft whose card is gone."""
    form = target.template.slug if target is not None else str(draft.template_id)
    return f"{form}, {draft.difficulty}, {draft.state}"


def cases(draft: Draft) -> list[str]:
    """The set as the steps left it: what the two solutions settled, what the
    rounds won, and the case the search stored. The declared set stands where
    no reference has settled it yet."""
    if not draft.cases:
        declared = [f"  {shortened(one.args, one.expected)}" for one in draft.declared]
        return ["## cases (declared, unsettled)", *declared, ""]
    separating = [draft.separating] if draft.separating is not None else []
    counted = f"{len(draft.cases)} settled, {len(draft.won)} won, {len(separating)} separating"
    return [
        f"## cases ({counted})",
        *(f"  {case_line(one)}" for one in [*draft.cases, *draft.won, *separating]),
        "",
    ]


__all__ = [
    "cases",
    "drafts_summary",
    "heading",
    "listing",
    "report",
    "waiting_on",
]
