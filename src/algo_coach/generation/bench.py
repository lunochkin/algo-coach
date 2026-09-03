"""Which model writes what, per call site.

Writing a problem takes four calls, and they ask for different things: a
statement and a solution, an independent reading of that statement, the inputs
that catch a wrong solution, and code that builds an input of a given size. One
configuration over all four makes the cheapest of them pay the price of the
hardest.
"""

from pydantic import BaseModel

from algo_coach.generation.generator import DEFAULT, Configuration


class Bench(BaseModel, frozen=True):
    """One configuration per generation call site.

    Every site defaults to the one they shared before there was a bench, so a
    run that names none is the run that ran yesterday.
    """

    generator: Configuration = DEFAULT
    blind: Configuration = DEFAULT
    discrimination: Configuration = DEFAULT
    inputs: Configuration = DEFAULT

    @property
    def shared(self) -> Configuration | None:
        """The one configuration all four sites carry, where they agree. A
        reporter names four otherwise."""
        one = {self.generator, self.blind, self.discrimination, self.inputs}
        return self.generator if len(one) == 1 else None


BENCH = Bench()


__all__ = ["BENCH", "Bench"]
