"""Which model writes what, per call site.

Writing a problem takes four calls, and they ask for different things: a
statement and a solution, an independent reading of that statement, the inputs
that catch a wrong solution, and code that builds an input of a given size. One
configuration over all four makes the cheapest of them pay the price of the
hardest.
"""

from pydantic import BaseModel

from algo_coach.calls import Configuration
from algo_coach.generation.blind import BLIND_DEFAULT
from algo_coach.generation.discrimination import DISCRIMINATION_DEFAULT
from algo_coach.generation.generator import GENERATOR_DEFAULT
from algo_coach.generation.inputs import INPUTS_DEFAULT


class Bench(BaseModel, frozen=True):
    """One configuration per generation call site.

    Each site defaults to its own, which the site's module names. Four
    identical defaults are one bench rather than a shared setting, so changing
    a site changes one file.
    """

    generator: Configuration = GENERATOR_DEFAULT
    blind: Configuration = BLIND_DEFAULT
    discrimination: Configuration = DISCRIMINATION_DEFAULT
    inputs: Configuration = INPUTS_DEFAULT

    @property
    def shared(self) -> Configuration | None:
        """The one configuration all four sites carry, where they agree. A
        reporter names four otherwise."""
        one = {self.generator, self.blind, self.discrimination, self.inputs}
        return self.generator if len(one) == 1 else None


BENCH = Bench()


__all__ = ["BENCH", "Bench"]
