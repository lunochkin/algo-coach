"""The naive solution: the slowest correct approach to a statement, which is
what the speedup search measures the canonical against.

It settles no case and discards no problem, so it is the one answering site
that may be told which form to avoid, and the one that is sampled. `corpus.md`
gives what it may never do.
"""

from algo_coach.calls import Configuration

# Sampled rather than greedy, as the generator is: it produces an artifact
# rather than a verdict, and a second call is a second draw where the first
# wrote the form.
CLOCK_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio"
)


__all__ = ["CLOCK_DEFAULT"]
