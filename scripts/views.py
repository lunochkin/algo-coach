"""Build `views.duckdb` — SQL views over the JSONL logs, no copy of the data.

The file holds view definitions and nothing else, so it stays a few hundred
kilobytes however large the logs grow, and every query reads them live. Any
DuckDB front end opens it: `duckdb -ui views.duckdb`, Harlequin, DBeaver.

    uv run --with duckdb python scripts/views.py

A log that does not exist yet is skipped rather than failing the build: the
store fills in as phases land, and re-running picks up what appeared.
"""

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB = ROOT / "views.duckdb"

# Absolute paths on purpose: a front end launched from anywhere resolves them,
# where a relative one would follow whatever directory the GUI started in.
LOGS = {
    "attempts": "attempts.jsonl",
    "claims": "technique_claims.jsonl",
    "calls": "calls.jsonl",
    "matches": "template_matches.jsonl",
    "self_labels": "self_labels.jsonl",
    "diagnoses": "diagnoses.jsonl",
}

# A call holds its whole prompt, so the reader's default object cap is too low.
BIG = {"calls"}

# Views over the views. Flattening is mechanical and safe to state twice;
# a rule is not, so only one appears here and it says whose copy it is.
DERIVED = {
    "claim_techniques": """
        -- One row per claim and technique. `unnest` cannot be grouped on
        -- inline, so every per-technique query starts from this.
        select c.id claim_id, c.attempt_id, c.source, c.model, c.effort,
               c.temperature, c.pin, c.created_at, unnest(c.techniques) technique
        from claims c
    """,
    "problem_techniques": """
        select p.id problem_id, p.title, unnest(p.techniques) technique
        from problems p
    """,
    "standing_claims": """
        -- MIRRORS `algo_coach.techniques.standing_claims`. The user's claim
        -- wins however late the machine's is; otherwise the latest classifier
        -- one. Latest alone would let a re-derivation bury ground truth.
        --
        -- Two copies of one rule, and this is the lesser evil: without it every
        -- ad-hoc query silently reads latest-wins and gets a different board
        -- than the engine does. Check it against the Python when that changes.
        --
        -- The Python breaks a `created_at` tie on append order, which a JSON
        -- scan cannot promise; this breaks it on `id`. No tie exists in the
        -- log today, and both are arbitrary among records written together.
        select * exclude (rank) from (
            select c.*, row_number() over (
                partition by c.attempt_id
                order by (c.source = 'user') desc, c.created_at desc, c.id desc
            ) rank
            from claims c
        ) where rank = 1
    """,
    "attributed": """
        -- What an attempt counts toward: its standing claim where that names
        -- anything, the problem's tags otherwise. A claim naming nothing is a
        -- reading that declined, so the fallback stands.
        select a.id attempt_id, a.problem_id, a.solved, a.finished_at,
               coalesce(nullif(s.techniques, []), p.techniques) techniques,
               s.source is not null and len(s.techniques) > 0 claimed
        from attempts a
        join problems p on p.id = a.problem_id
        left join standing_claims s on s.attempt_id = a.id
    """,
}


def main() -> int:
    if not DATA.is_dir():
        print(f"no store at {DATA}", file=sys.stderr)
        return 1

    DB.unlink(missing_ok=True)
    con = duckdb.connect(str(DB))

    made, skipped = [], []
    for name, filename in LOGS.items():
        path = DATA / filename
        if not path.exists():
            skipped.append(name)
            continue
        cap = ", maximum_object_size=50000000" if name in BIG else ""
        con.sql(f"create view {name} as select * from read_json_auto('{path}'{cap})")
        made.append(name)

    problems = DATA / "problems"
    if any(problems.glob("*.json")):
        con.sql(f"create view problems as select * from read_json_auto('{problems}/*.json')")
        made.append("problems")
    else:
        skipped.append("problems")

    for name, sql in DERIVED.items():
        # A derived view over a log that is not there yet cannot be created,
        # and saying which is missing beats a binder error.
        try:
            con.sql(f"create view {name} as {sql}")
        except duckdb.Error as failure:
            skipped.append(f"{name} ({failure.__class__.__name__})")
            continue
        made.append(name)

    con.close()
    print(f"{DB.relative_to(ROOT)}: {', '.join(made)}")
    if skipped:
        print(f"skipped, nothing to read yet: {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
