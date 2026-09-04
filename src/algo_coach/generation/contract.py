"""What every solution this engine runs must be, stated once.

Four briefs ask for code, and each stated the same three facts in its own
words. `corpus.md` gives the entry point as an invariant, so a per-brief copy
of it is a copy that can drift.

Each brief still writes its own signature: the two that answer a statement take
what the prose describes, and the input generator takes a size and a seed.
"""

# named because the runner executes under it: a model writing for an older
# interpreter reaches stdlib behaviour this one rejects
RUNTIME = "Python 3.14"

ENTRY = "one module-level function named `solve`"

ALONE = "The code stands alone: no input is read and nothing is printed."


__all__ = ["ALONE", "ENTRY", "RUNTIME"]
