"""Making a call and recording it, with nothing said about what it was for.

The transport half of a classification: a caller hands over the text and the
schema it wants back, and gets the answer and the id of the record that now
holds it. What the answer means is the caller's.
"""

from hashlib import sha256
from typing import Any

from algo_coach.calls.store import CallLog
from algo_coach.mint import call as mint_call
from algo_coach.schema import Call

# Twelve hex characters of sha256. Only ever compared for equality, so the
# collision margin is irrelevant beside carrying sixty-four of them on every
# line of an append-only log.
HASH_LENGTH = 12

# Returned rather than hidden: a summary is what says why a verdict came out
# the way it did, and it costs no tokens — thinking happens and is billed the
# same whether or not the summary comes back.
THINKING = {"type": "adaptive", "display": "summarized"}

# The effort of a model that is asked for none — some reject the parameter
# outright. A named level rather than an absent field, since a reading whose
# configuration is partly unknown compares with nothing.
UNSENT = "default"


def payload(system: str, content: str) -> str:
    """The prompt as one string: what was sent, in the order it was sent.

    Hashed and stored in this form, so the stored text digests to the hash
    beside it and a renderer that changes cannot make an old record unreadable.
    """
    return f"{system}\n\n---\n\n{content}"


def prompt_hash(system: str, content: str) -> str:
    return sha256(payload(system, content).encode()).hexdigest()[:HASH_LENGTH]


def ask(
    client: Any,
    log: CallLog,
    *,
    system: str,
    content: str,
    model: str,
    effort: str,
    schema: dict[str, Any] | None = None,
    max_tokens: int = 16000,
) -> tuple[Call, str | None]:
    """Send one prompt, record what happened, and return the call and its text.

    A failure is recorded too, then raised: the caller decides whether one
    attempt's problem ends the run, and the record is what makes a run that
    broke at two in the morning readable afterwards. Only the message and the
    exception's type are kept — a repr can carry request context, and this file
    outlives the terminal it would have been printed to.

    The output schema is not part of the hash. It is built from the candidates,
    which already appear verbatim in the content, so it varies with nothing the
    hash does not already cover.
    """
    text = payload(system, content)
    digest = prompt_hash(system, content)

    output_config: dict[str, Any] = {}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": schema}

    # Both are sent only where they were asked for: a model that does not take
    # them rejects every call carrying them, whatever the level. They are sent
    # together because they arrived together — a model old enough to reject the
    # effort parameter rejects adaptive thinking too — so `UNSENT` is how a
    # caller says this model takes neither, in one word rather than two.
    request: dict[str, Any] = {}
    if effort != UNSENT:
        output_config["effort"] = effort
        request["thinking"] = THINKING

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            output_config=output_config,
            messages=[{"role": "user", "content": content}],
            **request,
        )
    except Exception as exc:
        log.append(
            mint_call(
                model=model,
                effort=effort,
                prompt=text,
                prompt_hash=digest,
                error=f"{type(exc).__name__}: {exc}",
            )
        )
        raise

    answer = next((block.text for block in response.content if block.type == "text"), None)
    call = mint_call(
        model=model,
        effort=effort,
        prompt=text,
        prompt_hash=digest,
        # A response with no text block answered nothing — a refusal, or an
        # answer cut short. Recorded as the failure it is, so the log does not
        # claim an empty verdict was a reading.
        response=answer,
        error=None if answer is not None else f"no verdict: {response.stop_reason}",
        thinking=summarised(response),
        stop_reason=getattr(response, "stop_reason", None),
        input_tokens=getattr(getattr(response, "usage", None), "input_tokens", None),
        output_tokens=getattr(getattr(response, "usage", None), "output_tokens", None),
    )
    log.append(call)
    return call, answer


def summarised(response: Any) -> str | None:
    """The reasoning the model was willing to show. Empty on a model that
    returns none, which is a fact about the model rather than a gap."""
    blocks = [
        getattr(block, "thinking", "")
        for block in response.content
        if getattr(block, "type", None) == "thinking"
    ]
    joined = "\n".join(block for block in blocks if block)
    return joined or None
