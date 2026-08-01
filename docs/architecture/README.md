# Architecture

Target state. Code lags this doc; where they differ, this doc wins.

## Shape

Engine public, content private.
Everything the practice loop reads is local to the engine:
problems, cards, and attempts all live in datastore(s) the engine controls.
The engine never contacts external platforms; user clients push data in.

Consequence: no third-party dependency in the drill loop.

## Terminology

An attempt is a user's solution to a problem, successful or failed.

The corpus is the set of all attempts, successful and failed.

Verification is the process of executing an attempt against a problem's
test cases, yielding pass or fail.

Diagnosis is the process of classifying why an attempt failed;
a `Diagnosis` record stores the result.

## Data classes

### Techniques

- Owner: product
- Visibility: global, identical for all users
- Write semantics: read-only at runtime
- Source of truth: this repo, in git

The technique vocabulary is the anchor the append-only log references, so it
is versioned as code rather than stored as data: a file shipped with the
package, not a datastore the engine writes.

A code is never deleted, because records carrying it outlive it. Retirement
means an entry in an alias map, applied when grouping.

Membership is checked on the write path only. A model that validated codes on
read would make the log unreadable by its own schema the moment a code was
retired.

### Cards

- Owner: product
- Visibility: global, identical for all users
- Write semantics: read-only at runtime
- Source of truth: private content repo

Cards are teaching content about a technique — not the vocabulary itself.
They are product data, not code: they live in the engine datastore, seeded
from a private repo that holds their version history.

Card granularity follows teaching granularity, which is finer than the
technique: one technique can carry several cards. Mastery is estimated per
technique, so cards are never the unit of estimation and are never referenced
by the log.

### Problems

- Owner: product or user
- Visibility: global for product-owned, scoped for user-pushed
- Write semantics: read-only for product-owned, mutable cache for user-pushed
- Source of truth: the product set or the pushing client

Problems have provenance.
Product problems need a rights record; pushed problems need an origin
platform and a pushing user.

User-pushed problems arrive through the push API.

Product-owned problems are created using a content pipeline, which lives
in a separate private repo.

Tag mapping is owned by the engine. A pushed problem carries the origin
platform's tags verbatim; the engine derives its own technique codes beside
them. The raw tags are the truth, the codes are a derived view, so re-running
the mapping is legal and expected. An unmapped tag produces no code and blocks
nothing: a metadata mismatch must never cost a real attempt.

### Attempts

- Owner: user
- Visibility: private
- Write semantics: append-only
- Source of truth: the store — records are either user-pushed or produced by the engine

Attributing an attempt to a technique is a claim, not a fact, so it lives in
its own append-only record rather than on the attempt:
- Initially the user's own assignment: they mark how they solved the problem
- Later, an ML classifier assigns the solution to a technique

Neither overwrites the other. Successive claims accumulate and the latest wins
on read, so the disagreement between user and classifier stays measurable —
the same shape as `Diagnosis`, for the same reason.

An attempt never denormalizes the problem's techniques. Problem tags are
re-derivable; the log is not, and a copy taken at ingest would drift from its
source with no way to tell which is right.

Attempts for a given problem come from one source only: the user if the
problem is user-pushed, otherwise the engine.

User-pushed attempts carry an id minted by the pushing client, unique per
user, so re-pushing an already-ingested attempt is a no-op. The engine mints
its own id and never accepts one from a client.

### Diagnoses

- Owner: user
- Visibility: private
- Write semantics: append-only
- Source of truth: the store

## Boundaries

- **Push API** — the platform's only runtime ingest path. Carries user-pushed
  problems and attempts. A format contract, not a protocol: clients emit the
  `Problem` and `Attempt` schemas; ingest is validate and append.
- **Verification** — runs locally, against test cases the engine owns. Product
  problems only: pushed problems carry no test cases, so their attempts
  happen outside the engine.
- **Storage** — concrete for now (JSON files under a gitignored directory), a
  database later. The schema is the contract; storage swaps underneath it.
- **Product content ingest** — cards, problems, and test cases are produced by
  an offline content pipeline in a separate private repo, and seeded into the
  engine datastore. File-based for now. The technique vocabulary is the
  exception: it ships with the package, in git.

## Invariants

- Attempts and diagnoses are append-only.
- `Diagnosis` is a separate record, keyed to an attempt and versioned by model
  and prompt version, so the whole corpus can be re-diagnosed and compared.
- No third-party problem statements or test cases in git — in any repo.
- Pushed attempts cannot be verified by the platform and never enter
  cross-user aggregates.
- The technique vocabulary is product-owned and global; no user-authored
  techniques or cards. Technique codes are stable identifiers with a migration
  path, since attempts, problems, and future user annotations reference them.
  Cards are teaching content and are never referenced by the log.
- Aggregates are derived views, never stored truth.
- Domain logic stays adapter-free and directly callable; the CLI is one
  adapter, a web API will be another.
- A problem's owner (product or user) is stored state and determines its visibility, test-case
  availability, attempt origin, verifiability, and eligibility for cross-user
  aggregates. These are derived, never stored independently, and the owner is
  set by the ingest path — never supplied by a client.

## Additional constraints

- No concrete third-party problem-platform client ever enters this repo.
- Schema changes must be additive (new optional fields), never breaking.
- `data/` is gitignored; only the schema is public.
- Prefer tools and functions over agents; a pipeline earns multi-agent, not the
  other way around.

## Follow-ups

The eval approach will be decided later.

## Meta-rule

Ship thin on features; let the record schema run one phase ahead.
Component boundaries can be refactored. An append-only log cannot.
