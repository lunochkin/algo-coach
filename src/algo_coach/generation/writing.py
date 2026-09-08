"""One writing, and what its call sites leave behind.

`machine.md` gives what a site outcome carries and why a run's stage lines do
not suffice.
"""

from dataclasses import dataclass, field

from algo_coach import mint
from algo_coach.generation.generator import Generated
from algo_coach.ids import new_id
from algo_coach.schema import Call, CallSite, Draft, Gate, MachineProvenance, SiteOutcome


@dataclass(frozen=True)
class Writing:
    """The four sites of one writing, grouped by a minted id.

    Silent by default, so `write_one` and `harden` are callable without a
    store and a test needs none.
    """

    target_template_id: str | None = None
    target_technique: str | None = None
    into: list[SiteOutcome] | None = None
    id: str = field(default_factory=new_id)

    def draft(self, generated: Generated, call: Call) -> Draft:
        """The draft of this writing, carrying the id its site outcomes
        group under and the form its target named."""
        return mint.draft(
            self.id,
            title=generated.title,
            statement=generated.statement,
            canonical=generated.canonical,
            declared=generated.cases,
            difficulty=generated.difficulty,
            # absent where nothing recorded the writing, as on the site
            # outcomes this id groups
            target_template_id=self.target_template_id,
            target_technique=self.target_technique,
            provenance=MachineProvenance.of(call),
        )

    def __call__(
        self,
        site: CallSite,
        call: Call | None,
        *,
        gate: Gate | None = None,
        detail: str = "",
        mutants: int = 0,
        survived: int = 0,
        won: int = 0,
        killed: int = 0,
        rounds: list[int] | None = None,
        proposed: int = 0,
        misdeclared: int = 0,
        separating: int | None = None,
        unseparated: str | None = None,
        largest: int | None = None,
    ) -> None:
        # a site that made no call left no configuration to compare, so it
        # writes nothing rather than a record with provenance missing
        if self.into is None or call is None:
            return
        self.into.append(
            mint.site_outcome(
                site,
                self.id,
                target_template_id=self.target_template_id,
                target_technique=self.target_technique,
                gate=gate,
                detail=detail,
                mutants=mutants,
                survived=survived,
                won=won,
                killed=killed,
                rounds=rounds,
                proposed=proposed,
                misdeclared=misdeclared,
                separating=separating,
                unseparated=unseparated,
                largest=largest,
                provenance=MachineProvenance.of(call),
            )
        )


# the default: a writing that was given no list records nothing
UNRECORDED = Writing()


__all__ = ["UNRECORDED", "Writing"]
