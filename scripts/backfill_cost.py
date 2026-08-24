"""Fill `cost` on the calls and claims taken before the router's charge was
recorded, priced at today's catalogue.

    uv run python scripts/backfill_cost.py          # report, write nothing
    uv run python scripts/backfill_cost.py --apply  # rewrite both logs

What this writes is an estimate, and the field it writes into is defined as a
charge. That is the trade the run accepted: one column instead of two, at the
cost of a reader no longer being able to tell a price that was paid from one
computed afterwards. Everything written from here on is the real charge, so
the estimates are exactly the records dated before this ran.

Priced per call, never per claim: a claim carries no token counts, so its cost
comes from the call it cites. A call missing either count, or naming a model
the catalogue no longer lists, is left unpriced rather than guessed at — which
covers the readings taken through the native Anthropic transport, whose model
ids were never OpenRouter's.
"""

import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CALLS = DATA / "calls.jsonl"
CLAIMS = DATA / "technique_claims.jsonl"
# Kept beside the log it came from, as the earlier migrations were.
BACKUP = ".pre-cost"

CATALOGUE = "https://openrouter.ai/api/v1/models/{model}/endpoints"


def prices(models: set[str]) -> dict[tuple[str, str | None], tuple[float, float]]:
    """Per-token prompt and completion rates, keyed by model and endpoint.

    A model with no endpoint named is keyed under `None` at its first
    endpoint's rate. The pin was not recorded then, so which build answered is
    unknown and any of them is a guess — this one is at least stated.
    """
    rates: dict[tuple[str, str | None], tuple[float, float]] = {}
    for model in sorted(models):
        try:
            with urllib.request.urlopen(CATALOGUE.format(model=model)) as response:
                endpoints = json.load(response)["data"]["endpoints"]
        except Exception:
            print(f"  no catalogue entry: {model}", file=sys.stderr)
            continue
        for endpoint in endpoints:
            pricing = endpoint.get("pricing") or {}
            pair = (float(pricing.get("prompt") or 0), float(pricing.get("completion") or 0))
            rates[model, endpoint.get("tag")] = pair
            rates.setdefault((model, None), pair)
    return rates


def priced(call: dict, rates: dict) -> float | None:
    inputs, outputs = call.get("input_tokens"), call.get("output_tokens")
    if inputs is None or outputs is None:
        return None
    rate = rates.get((call.get("model"), call.get("pin")))
    if rate is None:
        return None
    return inputs * rate[0] + outputs * rate[1]


def rewrite(path: Path, lines: list[str], apply: bool) -> None:
    if not apply:
        return
    path.with_suffix(path.suffix + BACKUP).write_text(path.read_text())
    path.write_text("".join(lines))


def main() -> None:
    apply = "--apply" in sys.argv
    calls = [json.loads(line) for line in CALLS.read_text().splitlines() if line.strip()]
    claims = [json.loads(line) for line in CLAIMS.read_text().splitlines() if line.strip()]

    rates = prices({call["model"] for call in calls})

    costs: dict[str, float] = {}
    for call in calls:
        if call.get("cost") is not None:
            costs[call["id"]] = call["cost"]
            continue
        cost = priced(call, rates)
        if cost is not None:
            call["cost"] = cost
            costs[call["id"]] = cost

    filled = 0
    for claim in claims:
        # Only ever a machine claim: the schema rejects a hand one carrying a
        # price, since nothing re-derives a hand claim and no model was paid.
        if claim.get("source") == "user" or claim.get("cost") is not None:
            continue
        cost = costs.get(claim.get("call_id"))
        if cost is not None:
            claim["cost"] = cost
            filled += 1

    print(f"calls  {len(costs)}/{len(calls)} priced")
    print(f"claims {filled}/{sum(1 for c in claims if c.get('source') != 'user')} filled")
    # Two reasons a call goes unpriced, and only one of them is worth acting
    # on. A failure has no tokens and cost nothing recordable. A model the
    # catalogue does not list cannot be priced at all, which is every reading
    # taken before the router — those ids were never OpenRouter's.
    untokened: Counter[tuple[str, str | None]] = Counter()
    unrated: Counter[tuple[str, str | None]] = Counter()
    for call in calls:
        if call.get("cost") is not None:
            continue
        key = (call.get("model"), call.get("pin"))
        which = untokened if call.get("input_tokens") is None else unrated
        which[key] += 1
    for name, tally in (("no rate", unrated), ("no tokens", untokened)):
        if tally:
            print(f"\nleft unpriced, {name}:")
            for (model, pin), count in tally.most_common():
                print(f"  {count:5}  {model} @ {pin}")

    rewrite(CALLS, [json.dumps(call) + "\n" for call in calls], apply)
    rewrite(CLAIMS, [json.dumps(claim) + "\n" for claim in claims], apply)
    print("\nwritten" if apply else "\nnothing written — pass --apply")


if __name__ == "__main__":
    main()
