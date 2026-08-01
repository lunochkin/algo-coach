# Architecture

Target state. Code lags this doc; where they differ, this doc wins.

## Shape

Engine public, content private. Everything the practice loop reads is local to
the engine: problems, cards, and attempts live in datastore(s) the engine
controls, and the technique vocabulary ships with the package. The engine never
contacts external platforms; user clients push data in.

Consequence: no third-party dependency in the drill loop.

## Terminology

- **Attempt** — a user's solution to a problem, successful or failed.
- **Verification** — executing an attempt against a problem's test cases,
  yielding pass or fail.
- **Diagnosis** — classifying why an attempt failed; a `Diagnosis` record
  stores the result.

## Data classes

| Class | Owner | Visibility | Write semantics | Source of truth |
|---|---|---|---|---|
| Techniques | product | global | read-only at runtime | this repo, in git |
| Cards | product | global | read-only at runtime | private content repo |
| Problems | product or user | global if product-owned, user-scoped if pushed | read-only if product-owned, mutable cache if pushed | product set, or the pushing client |
| Attempts | user | private | append-only | the store |
| Technique claims | user | private | append-only | the store |
| Diagnoses | user | private | append-only | the store |

### Techniques

The vocabulary the append-only log references.

- **Versioned as code, not stored as data** — a file shipped with the package,
  not a datastore the engine writes.
- **A code is never deleted**, because records carrying it outlive it.
  Retirement means an entry in an alias map, applied when grouping.
- **Membership is checked on the write path only.** A model that validated
  codes on read would make the log unreadable by its own schema the moment a
  code was retired.

### Cards

Teaching content about a technique — not the vocabulary itself.

- **Product data, not code** — cards live in the engine datastore, seeded from
  a private repo that holds their version history.
- **Granularity follows teaching, not estimation.** One technique can carry
  several cards. Mastery is estimated per technique, so cards are never the
  unit of estimation and are never referenced by the log.

### Problems

- **Provenance is required.** Product problems need a rights record; pushed
  problems need an origin platform and a pushing user.
- **Two origins.** User-pushed problems arrive through the push API.
  Product-owned problems come from a content pipeline in a separate private
  repo.
- **Push identity is `(user_id, external_id)`**, so a re-push updates rather
  than duplicates. The engine mints the `id`, and it never moves on update,
  because attempts reference it.
- **Tag mapping is owned by the engine.** A pushed problem carries the origin
  platform's tags verbatim and the engine derives its own codes beside them.
  Raw tags are the truth, codes are a derived view, so re-running the mapping
  is legal and expected.
- **An unmapped tag blocks nothing.** It produces no code and the problem still
  ingests: a metadata mismatch must never cost a real attempt.

### Attempts

- **One source per problem** — the user if the problem is user-pushed,
  otherwise the engine.
- **Identity is the engine's.** A pushed attempt carries a client-minted id,
  unique per user, so re-pushing an ingested one is a no-op. The engine mints
  its own id and never accepts one from a client.
- **The problem reference is resolved at ingest**, from the platform's id to
  the minted one. An append-only record must not hold a reference nothing can
  follow, so an unresolvable one is rejected — hence problems are pushed first.
  Rejection is per-record, and re-pushing later is a no-op on what landed.
- **The verdict records what it rests on** — the client's word or the engine's
  own run. A pushed attempt can only carry the client's: the engine owns no
  test cases for a pushed problem, so it cannot have run them.
- **Problem techniques are never denormalized onto an attempt.** Tags are
  re-derivable, the log is not, and a copy taken at ingest would drift with no
  way to tell which is right.

### Technique claims

Which technique an attempt used — what per-technique progress is measured from.
A claim rather than a fact, and open to revision, so it is its own record
rather than a field on the attempt.

- **Two writers.** Initially the user's own assignment: they mark how they
  solved the problem. Later, an ML classifier assigns the solution to a
  technique.
- **A revision never rewrites what it replaces.** Successive claims accumulate
  and the latest wins on read — the same shape as `Diagnosis`, for the same
  reason.
- **Every claim records its source**, and a machine claim its model and prompt
  version. Both count the same toward progress, but a machine claim can be
  recomputed by a better classifier and a user's cannot — so re-deriving has to
  find the stale ones and leave the rest, as with platform tags and the codes
  derived from them.

### Diagnoses

Why an attempt failed. Keyed to an attempt, versioned by model and prompt
version, so every attempt can be re-diagnosed and compared.

## Boundaries

- **Push API** — the platform's only runtime ingest path, carrying user-pushed
  problems and attempts. A format contract, not a protocol: clients emit the
  `Problem` and `Attempt` schemas.
  - Attempts append, problems upsert.
  - Each attempt's problem reference is resolved to the engine's own id, so
    attempts are pushed after the problems they name.
  - A batch ingests per record: a bad one is rejected by index, the rest still
    land. One malformed line must not cost the attempts around it.
  - An already-ingested record is counted, not an error, so retrying is safe.
- **Verification** — runs locally, against test cases the engine owns. Product
  problems only: pushed problems carry no test cases, so their attempts happen
  outside the engine.
- **Storage** — concrete for now (JSON files under a gitignored directory), a
  database later. The schema is the contract; storage swaps underneath it.
- **Product content ingest** — cards, problems, and test cases are produced by
  an offline content pipeline in a separate private repo, and seeded into the
  engine datastore. File-based for now. The technique vocabulary is the
  exception: it ships with the package, in git.

## Invariants

Properties the system holds at all times.

- Attempts, technique claims, and diagnoses are append-only.
- Every reference in an append-only record is engine-minted. External ids are
  resolved at the boundary and never stored on an attempt, so the log stays
  readable without the platform that produced it.
- Aggregates are derived views, never stored truth.
- A problem's owner (product or user) is stored state, and determines its
  visibility, test-case availability, attempt origin, verifiability, and
  eligibility for cross-user aggregates. Those are derived, never stored
  independently, and the owner is set by the ingest path — never supplied by a
  client.
- Pushed attempts cannot be verified by the platform and never enter cross-user
  aggregates.
- The technique vocabulary is product-owned and global; no user-authored
  techniques or cards. Technique codes are stable identifiers with a migration
  path, since attempts, problems, and future user annotations reference them.
  Cards are teaching content and are never referenced by the log.
- Domain logic stays adapter-free and directly callable; the CLI is one
  adapter, a web API will be another.
- No third-party problem statements or test cases in git — in any repo.

## Repo constraints

Rules on how this repo is built, rather than properties of the running system.

- No concrete third-party problem-platform client ever enters this repo.
- Schema changes must be additive (new optional fields), never breaking.
- `data/` is gitignored; only the schema is public.
- Prefer tools and functions over agents; a pipeline earns multi-agent, not the
  other way around.

## Meta-rule

Ship thin on features; let the record schema run one phase ahead.
Component boundaries can be refactored. An append-only log cannot.
