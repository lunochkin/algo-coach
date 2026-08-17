# algo-coach

AI coaching layer for deliberate practice of algorithmic problem-solving:
spaced repetition over a technique-mastery model, with LLM-based attribution of
what a solution actually did.

Most practice tools schedule *problems*. algo-coach models mastery of
*techniques* — what a solution used is read from the code rather than inferred
from a problem's tags, and scheduling will target the weakest technique rather
than the oldest problem. Procedural-skill SRS, not fact SRS — built for
experienced engineers restoring fluency, not beginners learning concepts.

**Status: early.** Push API, technique vocabulary,
attribution classifier and drill loop are built; cards are in progress;
failure-mode diagnosis and scheduling are not started. Sequencing lives in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## Core loop, as built

```
board (per technique, by staleness) → pick a technique → pick a problem
      → solve it wherever you already solve → push → the loop diffs its log
      → claim which techniques the solution used + label why it went that way
```

Diagnosis and scheduling close this loop later; today the user picks what to
drill and the board says what is stale.

## Design

[`docs/architecture/README.md`](docs/architecture/README.md) is the primary
design document — the concepts, boundaries and invariants, and the reasons
behind them. The load-bearing ones:

- **[The log is append-only.](docs/architecture/README.md#invariants)** No
  record is revised or removed in place, so component boundaries can be
  refactored and the record schema cannot. The schema runs a phase ahead of the
  features on purpose.
- **[Identity is the engine's.](docs/architecture/README.md#problems)** A client
  pushes external ids; the engine mints its own and resolves references at the
  boundary, so the log stays readable without the platform that produced it.
- **[The user's record stands over the machine's](docs/architecture/README.md#technique-claims)**
  answer to the same question, whichever was written later. What the machine
  wrote is kept and scored, never discarded and never promoted.
- **[Aggregates are derived views](docs/architecture/README.md#invariants)**,
  never stored truth — the board, a card's ladder, mastery.
- **[No third-party problem statements or test cases in git](docs/architecture/README.md#repo-constraints)**,
  in any repo. The engine contacts no external platform, and no platform client
  lives here.

Two features worth reading the doc for:

- **[Technique attribution](docs/architecture/README.md#technique-claims)** —
  which techniques a solution used, read from the code by a prompted
  classifier, because no training data exists for that label: public corpora
  tag *problems*, not solutions. Constrained to the problem's own tags, scored
  against hand claims by set equality per technique, and every reading records
  the model, the effort, the digest of what was sent and the call that sent it.
- **[Cards](docs/architecture/README.md#cards)** — teaching content per
  technique: a recognition cue, what to read, and the templates to reproduce
  from memory. A card names no problem; it carries a selector, and its ladder
  resolves against the corpus.

## Commands

```
uv run algo-coach <command>
```

| Command | What it does |
|---|---|
| `push attempts\|problems` | ingest records your own client exports |
| `board` | per-technique standing: attempts, solved, recency, labels |
| `drill` | pick a technique, then a problem, then record what came back |
| `claim` | hand-label which techniques a stored attempt used |
| `classify` | claim stored attempts with the classifier |
| `score` | the classifier against the hand claims, per technique |
| `movement` | how far the classifier's claims move the board off the tags |

## Where things are

```
src/algo_coach/schema/       the record contracts — the public part
src/algo_coach/techniques/   the vocabulary: 27 codes, each with its criterion
src/algo_coach/{board,claims,ingest,log,calls}/
docs/architecture/README.md  concepts, boundaries, invariants
docs/{ROADMAP,TODO}.md       sequencing, and what is open
.claude/skills/card-author/  the skill that authors cards
data/                        your attempts and solutions — never committed
```

## Your data stays yours

Attempt logs, solutions and card content live under `data/` and `content/`,
both gitignored. The schema is public; the data is not.

## Development

```
uv sync
uv run pytest
```

Conventions in [`CLAUDE.md`](CLAUDE.md). Git hooks in `.githooks/`, enabled once
with `git config core.hooksPath .githooks`.

## License

Apache-2.0.
