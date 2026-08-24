"""Which of a problem's techniques a solution used.

A prompted model reading the code, not a trained one: public corpora tag
problems, not solutions, so a model trained on them would predict the fallback
rather than improve on it.
"""

import json
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel

from algo_coach.calls import CallLog, Transport, ask
from algo_coach.calls import prompt_hash as digest
from algo_coach.schema import Call
from algo_coach.techniques import criterion

# Twenty configurations read the same 80 hand-claimed attempts, and the readers
# do not share a ceiling: the spread is 70% to 95%, and of the sixteen attempts
# any of the leaders got wrong, none defeated all of them and ten were wrong for
# exactly one. So the choice is not only cost — an earlier note here claimed
# every model that reached the ceiling erred on the same attempts, and the eval
# set has since disproved it.
#
# This one agrees with the best reader to within a single attempt, which is
# inside the noise its own effort arms measured, at a twentieth of the price.
# What that buys is re-derivation: a criteria edit re-reads the attempts it
# reaches, and at this rate the whole backlog is under a dollar rather than a
# decision. The cost is time — it is the slowest of the leaders by an order of
# magnitude, and a full sweep is hours rather than minutes.
MODEL = "google/gemma-4-31b-it"
EFFORT = "medium"
# Which endpoint may serve it, named to the quantization. A router picks one
# per request from whoever carries the model, so without a pin two runs of one
# configuration are answered by different builds of the same weights — and fp4
# and bf16 are different weights, not one model behind two doors.
PIN = "coreweave/fp4"
# Greedy. Classification over a fixed candidate set has one right answer per
# decision, and sampling turns a verdict the model holds at 0.9 into one it
# gives four times in five. That noise is tolerable in an eval, which is
# repeated and averaged; the backlog sweep writes into an append-only log the
# board reads forever, so the same 1% would be permanent and would move
# readings a criteria edit never touched.
TEMPERATURE: float | None = 0.0
SYSTEM = """You name which techniques a solution used.

The candidates are one problem's tags — what the problem could exercise. Say
which of them the code in front of you actually did. Name every one it used
and nothing more: a solution can combine several, and one naming every
candidate agrees with the tags and decides nothing.

Each candidate carries what earns it and the near miss it is confused with.
Decide each against its own rule, and where the code fits the near miss
instead, do not name it.

Name a candidate even when a narrower one also applies. What a solution does
can be true at more than one level, and every level it did is claimed — never
withhold a code because another candidate covers it. An entry that is an
exception to this says so.

What disqualifies a candidate is incidental use: the technique appears in the
code without being part of how the solution works. Read for the invariant, not
the syntax, and let each candidate's near miss say where that line falls.

If the code used none of the candidates, name none of them."""


class Configuration(BaseModel, frozen=True):
    """Which classifier a reading came from, and the key it is found under.

    The prompt is not among them. It varies per attempt, since a candidate's
    criterion travels with it. So what rulebook a reading came from is a digest
    of what that attempt was actually sent, and never a property of the
    classifier. Frozen because it is an identity: compared whole, never
    ordered, so a rollback is naming the earlier one.
    """

    model: str = MODEL
    effort: str = EFFORT
    # Which build read it. Quantization changes the weights, so an fp4
    # endpoint and a bf16 one answer as two readers and a reading from one
    # does not answer for the other. Required rather than optional: unpinned,
    # the router chooses per request, and the readings under that key would be
    # a mixture no later run could take apart.
    pin: str = PIN
    # Identity beside the pin, and for the same kind of reason: the pin fixes
    # which weights answered, this fixes how they were sampled. `None`
    # is the provider's own default — a named arm rather than a gap, as an
    # unsent effort is, so every reading taken before this field existed stays
    # comparable instead of being discarded.
    temperature: float | None = TEMPERATURE

    @property
    def deployment(self) -> tuple[str, str]:
        """Which deployment answers, and so whose cap a call is metered against.

        OpenRouter imposes no request limit on a paid model; every 429 comes
        from the provider, and a provider meters per model per endpoint. Two
        configurations differing only in effort or temperature reach one
        deployment and share one budget.

        What it does not cover: the account-wide caps on free models, and one
        key driven by two runs at once. Neither is a property of a reading.
        """
        return self.model, self.pin


DEFAULT = Configuration()


class ClassifierError(Exception):
    """The model returned no verdict — a refusal, or an answer cut short."""


def request_hash(candidates: Sequence[str], code: str) -> str:
    """The digest of what this attempt would be sent, right now.

    What decides whether a reading is worth paying for again. A criterion
    travels with its candidate, so editing one entry changes this for the
    attempts carrying that code and for no others. That is the whole reason it
    is computed per attempt rather than carried on the configuration.
    """
    return digest(SYSTEM, prompt(candidates, code))


def classify(
    transport: Transport,
    log: CallLog,
    candidates: Sequence[str],
    code: str,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """The techniques a solution used, chosen from the problem's own tags, and
    the call that read them — `None` where the answer cost nothing.

    The candidates appear twice, doing different jobs. The response schema
    enforces them, so the classifier cannot name a technique the tags do not.
    The prompt informs them: thinking is not schema-constrained, so a model
    that met the candidates only at emission time would reason about the code
    without knowing which answers exist, then be forced into the nearest one.

    The code is the only evidence beyond them: a title or a statement
    describes what the problem admits, which is the question the fallback
    already answers.

    Naming nothing is legal — the tags may not cover what the code did, and no
    claim leaves the fallback standing rather than asserting a wrong one. A
    reply cut short by the token cap names nothing for a different reason, and
    the call's `stop_reason` is what separates the two.
    """
    if len(candidates) < 2:
        # Nothing to decide: the fallback already says this, and a schema
        # offering one choice would ask the model to agree with itself.
        return list(candidates), None

    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(candidates, code),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(candidates),
    )
    if call.stop_reason == "length":
        # The decoder ran out of tokens, so whatever came back is truncated and
        # carries no verdict. Named as nothing rather than raised, because this
        # one repeats: a reading is greedy, so the same prompt runs the same
        # way and every later run pays the whole cap again to fail identically.
        # What is stored is a fact about this configuration on this prompt, and
        # the call beside it says which — `stop_reason` tells an exhausted
        # reading from a considered decline.
        return [], call
    if text is None:
        raise ClassifierError(call.error or "no verdict")

    # Checked again because the schema's guarantee ends with the request and
    # the record does not: an append-only log has no pass that fixes a bad
    # code later.
    named = set(json.loads(text)["techniques"])
    return [technique for technique in candidates if technique in named], call


def prompt(candidates: Sequence[str], code: str) -> str:
    """The candidates and their criteria before the code, so the reading is
    made knowing what can be named and what earns each one. Delimited, since
    the code is data the model reads rather than instructions it follows.

    Beside the candidates rather than in the system text. A criterion is a
    per-code rule, and one carried by every call is paid for on the calls where
    its code is not a candidate. Over a vocabulary of this size, that is nearly
    all of them.
    """
    return "\n".join(
        [
            f"Candidates: {', '.join(candidates)}",
            "",
            *(line for candidate in candidates for line in block(candidate)),
            "<solution>",
            code,
            "</solution>",
        ]
    )


def block(candidate: str) -> list[str]:
    """The prompt's copy of one rule: the shared lines, and the blank that
    separates one candidate from the next. A retired code costs its own lines,
    not the separator around a rule that is not there."""
    lines = criterion(candidate)
    return [*lines, ""] if lines else []


def schema(candidates: Sequence[str]) -> dict[str, Any]:
    """The same candidates as an enum. The prompt informs the reading; this
    enforces it — an instruction can be violated, a response format cannot."""
    return {
        "type": "object",
        "properties": {
            "techniques": {"type": "array", "items": {"type": "string", "enum": list(candidates)}},
        },
        "required": ["techniques"],
        "additionalProperties": False,
    }
