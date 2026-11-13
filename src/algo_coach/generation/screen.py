"""The screen: whether a draft copied a published problem. `flows.md` gives
where it runs and what it rejects."""

import json
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, model_validator

from algo_coach.calls import CallLog, Transport, prompt_hash
from algo_coach.generation.site import answer
from algo_coach.schema import Call, Configuration, DraftCase

# unmeasured, as every site's is. Greedy: a verdict about a statement that
# already exists. Which model recalls the most published problems is open
SCREEN_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio", temperature=0.0
)

SYSTEM = """You check a newly written practice problem against the published
problems you know from programming practice sites and contests.

Report the problem as copied when one of these holds:
- its worked example, or any test case, reuses the input values of a specific
  published problem's example: the same list, the same numbers, the same
  string;
- its statement reuses a published statement's wording, sentence for
  sentence, rather than retelling the question in its own words.

A published question told again in a new setting, with new values and new
wording, is not copied. Many problems share one question, and that is allowed.
Small values that any problem might use, such as [1, 2, 3] or a single digit,
are not a reuse either.

When you report a copy, name the published problem and say what was reused.
Report a copy only where you can name the problem it came from."""


class Verdict(BaseModel):
    copied: bool
    published: str | None = None
    reused: str | None = None

    @model_validator(mode="after")
    def _a_copy_names_its_source(self) -> Verdict:
        if self.copied and not self.published:
            raise ValueError("a copy names the published problem it came from")
        return self

    @property
    def detail(self) -> str:
        return f"{self.published}: {self.reused or 'reused'}" if self.copied else ""


def prompt(statement: str, cases: Sequence[DraftCase]) -> str:
    # delimited: the draft is data the model judges, not instructions
    listed = "\n".join(
        f"args={json.dumps(one.args)} expected={json.dumps(one.expected)}" for one in cases
    )
    return f"<problem>\n{statement}\n</problem>\n<cases>\n{listed}\n</cases>"


def request_hash(statement: str, cases: Sequence[DraftCase]) -> str:
    return prompt_hash(SYSTEM, prompt(statement, cases))


def schema() -> dict[str, Any]:
    nullable = {"type": ["string", "null"]}
    return {
        "type": "object",
        "properties": {
            "copied": {"type": "boolean"},
            "published": nullable | {"description": "the published problem it came from"},
            "reused": nullable | {"description": "what was reused"},
        },
        "required": ["copied", "published", "reused"],
        "additionalProperties": False,
    }


def screen(
    transport: Transport,
    log: CallLog,
    statement: str,
    cases: Sequence[DraftCase],
    *,
    configuration: Configuration = SCREEN_DEFAULT,
) -> tuple[Verdict, Call]:
    text, call = answer(
        transport,
        log,
        system=SYSTEM,
        content=prompt(statement, cases),
        schema=schema(),
        configuration=configuration,
        missing="no verdict",
    )
    return Verdict.model_validate_json(text), call


__all__ = ["SCREEN_DEFAULT", "SYSTEM", "Verdict", "prompt", "request_hash", "schema", "screen"]
