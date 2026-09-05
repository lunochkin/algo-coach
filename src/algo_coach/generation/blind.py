"""The reference solution: the statement in, a solution out, and nothing else.

Its own brief, naming no technique, template or cue: those are what the
statement withholds.
"""

from algo_coach.calls import CallLog, Transport, prompt_hash
from algo_coach.generation.contract import ALONE, ENTRY, POSITIONAL, RUNTIME
from algo_coach.generation.contract import read_solution as read
from algo_coach.generation.contract import solution_schema as schema
from algo_coach.generation.site import answer
from algo_coach.schema import Call, Configuration

# unmeasured, as every site's is. Greedy: this site writes against a statement
# that already exists, so its variance buys no diversity
BLIND_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio", temperature=0.0
)

SYSTEM = f"""You write a correct solution to a problem statement.

The statement is all you are given. Write the plainest solution that is
certainly correct: what the prose says, done directly. Do not optimise, and do
not reach for a technique the statement did not ask for.

Follow the statement literally. Where it leaves something undecided, implement
what it says rather than what you take it to have meant. Another solution is
being written from the same prose, and where the two disagree the problem is
discarded rather than either solution corrected.

{RUNTIME}, {ENTRY},
{POSITIONAL}.
{ALONE}"""


def prompt(statement: str) -> str:
    # delimited: the statement is data the model solves, not instructions
    return f"<problem>\n{statement}\n</problem>"


def request_hash(statement: str) -> str:
    return prompt_hash(SYSTEM, prompt(statement))


def reference(
    transport: Transport,
    log: CallLog,
    statement: str,
    *,
    configuration: Configuration = BLIND_DEFAULT,
) -> tuple[str, Call]:
    # the site's own configuration by default: independence is what the model
    # was shown, so this call may run the model that wrote the statement
    text, call = answer(
        transport,
        log,
        system=SYSTEM,
        content=prompt(statement),
        schema=schema(),
        configuration=configuration,
        missing="no solution",
    )
    return read(text), call


__all__ = ["SYSTEM", "prompt", "read", "reference", "request_hash", "schema"]
