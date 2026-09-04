"""One attempt at writing a problem, and what its call sites leave behind.

`machine.md` gives what a site outcome carries and why a run's stage lines do
not suffice.
"""

from dataclasses import dataclass, field

from algo_coach import mint
from algo_coach.generation.landing import written_by
from algo_coach.schema import Call, CallSite, Discard, SiteOutcome


@dataclass(frozen=True)
class Writing:
    """The four sites of one attempt, grouped by a minted id.

    Silent by default, so `write_one` and `harden` are callable without a
    store and a test needs none.
    """

    template_id: str = ""
    into: list[SiteOutcome] | None = None
    id: str = field(default_factory=mint.new_id)

    def __call__(
        self,
        site: CallSite,
        call: Call | None,
        *,
        gate: Discard | None = None,
        detail: str = "",
        mutants: int = 0,
        survived: int = 0,
        won: int = 0,
        killed: int = 0,
        rounds: list[int] | None = None,
        offered: int = 0,
        separating: int | None = None,
        unseparated: str | None = None,
    ) -> None:
        # a site that made no call left no configuration to compare, so it
        # writes nothing rather than a record with provenance missing
        if self.into is None or call is None:
            return
        self.into.append(
            mint.site_outcome(
                site,
                self.id,
                self.template_id,
                gate=gate,
                detail=detail,
                mutants=mutants,
                survived=survived,
                won=won,
                killed=killed,
                rounds=rounds,
                offered=offered,
                separating=separating,
                unseparated=unseparated,
                **written_by(call),
            )
        )


# the default: an attempt that was given no list records nothing
UNRECORDED = Writing()


__all__ = ["UNRECORDED", "Writing"]
