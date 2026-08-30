# Architecture

Target state, across this file and the ones beside it. Code lags them; where
they differ, the doc wins.

## Shape

Engine public, content private. Everything the practice loop reads is local to
the engine. Problems, cards and attempts live in datastores the engine
controls, and the technique vocabulary ships with the package. The engine never
contacts external platforms.

Consequence: no third-party dependency in the drill loop.

**Problems are the product's own, and the engine writes them.** A statement
scraped from a platform cannot ship, which is what forces the question, but the
answer is a capability rather than a licence fix. A generated problem carries
the test cases that decide it. Test cases are what make verification reachable,
and verification is what turns a canonical solution from an assertion into a
fact.

**The engine is the platform.** It serves a generated problem, times the
sitting, runs the submission against the problem's own test cases, and records
the verdict. Serving, timing and judging are all its own. Python only: a
canonical is Python, the test cases are Python-shaped, and a second language is
a runner rather than a record change.

## Terminology

- **Attempt** — a user's solution to a problem, successful or failed.
- **Canonical solution** — an exemplary solution to a problem, written to
  display the approach rather than to pass. Never an attempt.
- **Reference solution** — a solution written from the statement alone. It
  computes the expected outputs and calibrates a timing bar. Correct, and
  deliberately not exemplary.
- **Verification** — executing a solution against a problem's test cases,
  yielding pass or fail. An attempt or a generated solution in either role.
- **Diagnosis** — classifying why an attempt failed. A `Diagnosis` record
  stores the result.

## Where the rest lives

This file is the map: what the system is, where it ends, and what holds at all
times. Each record class is specified in one of the files beside it.

| File | Holds |
|---|---|
| [`content.md`](content.md) | Techniques, cards, template matches |
| [`corpus.md`](corpus.md) | Problems, test cases, solutions |
| [`log.md`](log.md) | Attempts, claims, self-labels, diagnoses, card runs, recall attempts |
| [`machine.md`](machine.md) | What a model-written record carries, and the call log |
| [`flows.md`](flows.md) | Generating a problem, the drill loop, adjudicating the eval set |

## Data classes

| Class | Owner | Visibility | Write semantics | Source of truth |
|---|---|---|---|---|
| Techniques | product | global | read-only at runtime | this repo, in git |
| Cards | product | global | read-only at runtime | the store, seeded from `content/` |
| Problems | product | global | append-only | the store |
| Test cases | product | global | written with the problem | the store |
| Solutions | product | global | append-only | the store |
| Verification runs | product | global | append-only | the store |
| Template matches | product | global | append-only | the store |
| Card runs | user | private | append-only | the store |
| Recall attempts | user | private | append-only | the store |
| Attempts | user | private | append-only | the store |
| Technique claims | user | private | append-only | the store |
| Calls | user | private | append-only | the store |
| Self-labels | user | private | append-only | the store |
| Diagnoses | user | private | append-only | the store |

## Boundaries

- **Verification** — runs locally, against test cases the engine owns. Every
  problem carries them, so every submission is judged by whatever ran it.
- **Storage** — concrete for now (JSON files under a gitignored directory), a
  database later. The schema is the contract, and storage swaps underneath it.
- **Calibration corpus** — what the pivot to generated problems left behind,
  under `data/old/`: a platform's problems, the attempts against them, the
  claims and the calls. It is a corpus, not a store. No store points there, and
  nothing on the run path reads it.
  - It is kept for one measurement. The announcement floor is how often a form
    is named from the statement alone, and a corpus no generator wrote is what
    sets that floor. How it is read is deferred to taking that measurement.
- **Content generation** — problems, their test cases and their solutions are
  written by the engine, as a command beside the classifier and the matcher. It
  reuses one transport, one call log and one provenance base, rather than
  standing a second copy of each somewhere else.
  - Extraction to a pipeline of its own stays possible and is not planned. What
    it would have to preserve is the minted ids, since the attempt log
    references them.
- **Card ingest** — cards are authored in `content/` and seeded into the
  datastore. File-based for now, and gitignored like `data/`. The technique
  vocabulary is the exception: it ships with the package, in git.
  - What an author writes has its own shape. `CardSeed`
    (`src/algo_coach/schema/seed.py`) is the payload the stored card is built
    from, not the card, and it has no field for the identity the engine mints.
  - A card and each template are matched by their authored slug, which makes
    re-seeding refresh rather than duplicate. A new slug is a new card: the
    runs and the recall history stay with the old one, so renaming is a title
    change.

## Invariants

Properties the system holds at all times.

- Attempts, technique claims, self-labels and diagnoses are append-only: no
  record is ever revised or removed in place. Discarding a private log
  wholesale while it holds nothing irreplaceable is a different act, and that
  window closes the first time a record is worth keeping.
- Every record keyed to an attempt carries an engine-minted `id`, its
  `attempt_id` and `created_at`, so one reader orders any of them.
- The user's own record stands over the machine's answer to the same question,
  whichever was written later: a technique claim resolves user-first, and a
  diagnosis never supersedes a self-label. What the machine wrote is kept and
  scored, never discarded and never promoted.
- Every reference in an append-only record is engine-minted, so the log stays
  readable without anything outside the engine.
- Aggregates are derived views, never stored truth.
- Every problem is the product's own, written by the engine.
- A problem never lands without the test cases that decide it, a canonical
  solution that passed them, and a reference solution that agreed with it on
  every one. One whose canonical fails, or whose two solutions disagree, is not
  stored for repair; it is not stored.
- The technique vocabulary and the cards are product-owned and global, with no
  user-authored ones of either. Codes are stable identifiers with a migration
  path, since the log references them. The attempt log never references a card;
  a template match does, but it is a fact about the corpus rather than about a
  sitting, and mastery reads no card.
- Domain logic stays adapter-free and directly callable. The CLI is one
  adapter, and a web API will be another.
- No third-party problem statements or test cases in git — in any repo.

## Repo constraints

Rules on how this repo is built, rather than properties of the running system.

- No concrete third-party problem-platform client ever enters this repo.
- Schema changes must be additive (new optional fields), never breaking. A
  change may tighten instead — a field made required, one removed, a validator
  widened — only while no stored record carries the loose shape, which in
  practice means deleting the ones that do. Weigh what is deleted, not how
  many: the log has to stay readable by its own schema, and a field kept for a
  handful of disposable records is one every reader branches on forever.
- `data/` and `content/` are gitignored; only the schema is public. The
  generated corpus could be committed, since the product owns it, and is not:
  those directories also hold the private log, and storage moves to a database
  before the corpus ships anywhere.
- Prefer tools and functions over agents. A pipeline earns multi-agent, not the
  other way around.

## Meta-rule

Ship thin on features, and let the record schema run one phase ahead.
Component boundaries can be refactored. An append-only log cannot.
