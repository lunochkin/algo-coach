# Architecture

Target state, across this file and the ones beside it. The code lags these
files. On any difference, the doc wins.

## Shape

The engine is public and the content is private. Everything the practice loop
reads is local to the engine, which never contacts external platforms.

Consequence: no third-party dependency in the drill loop.

**Problems are the product's own, and the engine writes them.** A statement
scraped from a platform cannot ship, which forces the question of where
problems come from. The answer is a capability of the engine rather than a
licence fix.

**The engine is the platform.** It serves a generated problem, times the
sitting, runs the submission against the problem's own test cases, and records
the verdict. Python only: a canonical is Python, the test cases are
Python-shaped, and a second language is a runner rather than a record change.

**The engine is a learning platform, not a competitive one.** A verdict is
evidence about the user's own practice and ranks the user against nobody. A
solver who games a verdict misleads only their own board. So the drill loop
shows what helps a solver debug, and does not guard a verdict against the
solver.

## Terminology

Words this project gives its own meaning. The files beside this one use them
without redefining them. Grouped by the file that specifies the record.

### Content

- **Technique**: one entry in the vocabulary of skills the log references. A
  procedure, a structure, a paradigm or a problem class. Shipped as code.
- **Vocabulary**: every technique, each with the criterion for claiming it.
- **Card**: the study material for one technique: what to read, the
  templates to reproduce from memory, and a selector for problems to solve.
- **Template**: one form of a technique, authored on a card, that a user
  reproduces from memory. Core by default.
- **Trigger**: the field on a card or a template saying when to reach for the
  technique or the form. Withheld during a probe.
- **Speedup**: a flag on a template saying its form is asymptotically faster
  than the naive approach the technique replaces, by at least a factor of
  log n.
- **Selector**: a technique plus filters, on a card. The ladder is derived
  from it.
- **Ladder**: the problems a card has the user solve, derived from template
  matches and the selector. Never stored.
- **Rung**: one problem on a ladder. Required when it covers a core template.
- **Probe**: a problem assigned when a card is started, testing whether the
  form is recognised unprompted. Never drawn from the ladder.
- **Template match**: a record saying one solution displays one template.
  Written by the generator, the matcher or by hand.
- **Matcher**: the model call reading a canonical beside its statement and
  naming the templates it displays.
- **User record**: a claim or match written by the user rather than a model. Its
  `source` is `user`. It is written by hand: in the drill loop, or in a
  `--by-hand` pass over what the loop never asked. It stands over every
  machine record on the same question.

### Corpus

- **Problem**: a statement, its test cases and its solutions, written by the
  engine. Never edited. Only its status moves.
- **Statement**: the prose a solver is served. It carries the signature of
  `solve`, the fixed name of the function every solution defines.
- **Test case** (case): positional arguments and an expected return. The
  case set is every case a problem carries, appended to and never revised.
- **Target**: what a problem is written for: a template, naming the form, or a
  technique, naming only the skill. The prompt a site is given is built from
  it. Stored as `target_template_id` or `target_technique` on the problem, the
  draft and the site outcome, one of the two.
- **Canonical solution**: an exemplary solution, written to display the
  approach rather than to pass.
- **Reference solution**: a solution written from the statement alone.
  Correct, and deliberately not exemplary. It computes the expected returns.
- **Naive solution**: the approach the template's form replaces, written told
  which form to avoid. The speedup search times the canonical against it.
- **Role**: which of the three a solution is: canonical, reference or naive.
  Stored, since all three pass the same cases.
- **Verification**: executing a solution against a problem's cases. A
  `Verification` record stores one run, with a case outcome per case: passed,
  wrong, timed out or crashed.
- **Cap**: the wall-clock limit on a case's `solve` calls, measured in the
  child process. Generation's cap sits well above the sitting's.
- **Repeat count**: how many times a case calls `solve` on its arguments, the
  cap covering the calls together. One on every case but a separating one the
  ceiling put out of reach.
- **Solution claim**: a claim about a solution the engine wrote. Product data,
  and what a problem's techniques are folded from.
- **Defective**: a retirement reason: the statement asks for something its
  cases do not decide.
- **Enumeration**: a pass over a landed problem proposing other approaches,
  each generated as a further canonical.
- **Calibration corpus**: the platform problems and attempts under
  `data/old/`, kept for one deferred measurement, Phase 14 in `ROADMAP.md`.

### Generating a problem

- **Site** (call site): one of the five model calls writing a problem, each
  at its own configuration: generator, blind, inputs, naive and
  discrimination.
- **Generator**: the site writing the statement, the canonical and the first
  cases in one call.
- **Blind site**: the site writing the reference from the statement alone.
- **Inputs site**: the site writing the input generator.
- **Input generator**: model-written code building an input of a given size and
  seed.
- **Bound**: the largest input the statement admits, as the input generator's
  `size` counts it. Stored as `largest` on the draft and the site outcome.
- **Naive site**: the site writing the naive solution.
- **Discrimination site**: the site asked for cases that kill the surviving
  mutants.
- **Bench**: the configuration of each site a run is aimed with, from the
  `--site` flags or the built-in default.
- **Draft**: a problem being written, stored at every state so a failed step
  can resume. Cleared at landing.
- **Writing state**: how far a draft got: drafted, checked, referenced,
  agreed, built, paced, searched, hardened, landed, or rejected.
- **Paced**: the writing state after a naive solution passed the cases. Named
  for the pacer, the runner who sets the time others are measured against.
  `unpaced` is the reason a draft has none.
- **Hardened**: the writing state after the mutation loop appended the cases it
  won. Named for hardening, making a thing resist attack.
- **Gate**: a check a draft must pass to advance. A failed gate rejects the
  draft or holds it, and is named on the site outcome.
- **Rejected**: a draft's terminal state. The gate names why: `no_value`,
  `untested`, `disagreed` or `unexercised`.
- **Held**: a draft stopped at a state a resume can re-enter.
- **Landing**: the last step: the problem, its cases, its solutions and the
  generator's template match are stored together.
- **Resume**: `generate --resume`: re-entering every held draft at the first
  step whose configuration or prompt hash moved.
- **Mutant**: the canonical with one semantic change made on the parsed tree.
  A tree walk enumerates them, and no store holds them.
- **Kill**: a mutant failing at least one case, or answering a built input
  differently from the canonical.
- **Survivor**: a mutant no case and no built input killed.
- **Fuzz pass**: running the survivors against inputs the input generator
  builds. Costs no call.
- **Shrink**: reducing a kept fuzz input to the smallest list still killing
  the same mutants.
- **Kept input**: an input the fuzz pass built that killed a mutant, shrunk and
  stored as a case. `kept` on the draft.
- **Round**: one discrimination call, proposing cases for the survivors. At
  most two per draft.
- **Won case**: a round's proposal that killed a mutant, stored as a case.
  `won` on the draft and the site outcome.
- **Mutation loop**: the fuzz pass and the rounds together.
- **Speedup search** (the search): finding the smallest input on which the
  naive solution exceeds the sitting's cap and the canonical does not. The
  walk is the sequence of sizes it tries.
- **Separating case**: the case stored at the size the search found.
  Appended after the loop, naming no round.
- **Ceiling**: 1 MiB, the most a stored case may weigh.
- **Writing**: one run of the generation flow over one target, from the
  generator's call to landing or rejection. An attempt is a different
  thing: the log's record of a user's solution.
- **Site outcome**: the record of what one site left on one writing: the gate,
  the counters and the configuration.
- **Writing id**: the id a run mints per writing. The draft and its site
  outcomes share it.
- **Replay**: running the four answering sites over stored problems at a new
  bench. It writes nothing to the corpus.
- **Sweep**: one `generate` run over every target, or over every held draft.

### Machine records

- **Machine record**: any record a model wrote: a claim, a match, a solution, a
  case's arguments. It carries provenance whole.
- **Configuration**: model, effort, endpoint pin and temperature.
- **Provenance**: the configuration, the prompt hash of what was sent and the
  call that sent it.
- **Pin**: the endpoint a model id is fixed to, so one build answers.
- **Prompt hash**: the hash of the prompt a record was sent, `prompt_hash` on
  every machine record. Staleness keys on it.
- **Stale**: a record whose prompt hash differs from the one its site would send
  now. A re-run reads stale items and skips the rest.
- **Greedy** / **sampled**: temperature zero, or the provider's default. The
  answering sites are greedy. The generator and the naive site are sampled.
- **Call**: one request to a model and its response, domain-free. The call
  log holds every one.
- **Standing**: the record that answers a question when several were written
  about it. The user's stands over the machine's, and among the machine's the
  latest stands.

### The log

- **Attempt**: a user's solution to a problem, successful or failed.
- **Attempt verification**: executing an attempt's code against its problem's
  cases. An `AttemptVerification` record stores one run, and is private to the
  user where a solution's `Verification` is product data.
- **Sitting**: one timed session on one problem in the drill loop. It may
  mint several attempts, and each of them carries the sitting's id. The record
  is revised while the sitting runs and kept after the sitting ends.
- **Pause**: an interval a sitting's clock is stopped for. The elapsed time a
  sitting reports excludes every pause.
- **Drill loop**: the practice flow: pick a technique and a problem, read the
  card, solve, then answer the claim and the label.
- **Claim**: a record naming the techniques a piece of code used, by a named
  writer. Latest wins, and the user's stands over the classifier's.
- **Attempt claim**: a claim about the user's own attempt. Private, and what
  the board counts.
- **Classifier**: the model call reading an attempt's or a solution's code for
  the techniques it used. As a `source` value on any record, `classifier` means
  a model wrote it, whichever call.
- **Decline**: a claim stating that none of the candidates apply. Distinct
  from an empty claim, which answers nothing.
- **Fallback**: the problem's own techniques, answering an attempt no claim
  covers.
- **Self-label**: the user's own verdict on why an attempt went the way it
  did.
- **Diagnosis**: the machine's verdict on why an attempt failed. A
  `Diagnosis` record stores it.
- **Card run**: the record that a card was started, and the probes it was
  given.
- **Recall attempt**: one template reproduced from memory, with the hints
  taken.
- **Board**: the per-technique view of progress, derived from attempts and
  claims. Never stored.
- **Mastery**: what a user can solve, per technique. Derived from the board's
  inputs, never stored.
- **Eval set**: the hand-claimed attempts a classifier configuration is
  scored against.
- **Adjudication**: resolving each divergence between the user's blind claims
  and a frontier model's claims, by editing the criterion or the claim.

## Where the rest lives

This file is the map: what the system is, where it ends, and what holds at all
times. Each record class is specified in one of the files beside it.

| File | Holds |
|---|---|
| [`content.md`](content.md) | Techniques, cards, template matches |
| [`corpus.md`](corpus.md) | Problems, test cases, solutions, solution claims |
| [`log.md`](log.md) | Sittings, attempts, attempt verifications, claims, self-labels, diagnoses, card runs, recall attempts |
| [`machine.md`](machine.md) | What a model-written record carries, what a generation run's call sites leave, and the call log |
| [`flows.md`](flows.md) | Generating a problem, the states it is written through, replaying a site, the drill loop, adjudicating the eval set |

## Data classes

| Class | Owner | Visibility | Write semantics | Source of truth |
|---|---|---|---|---|
| Techniques | product | global | read-only at runtime | this repo, in git |
| Cards | product | global | read-only at runtime | the store, seeded from `content/` |
| Drafts | product | global | revised in place | the store |
| Problems | product | global | created once; only its status moves | the store |
| Test cases | product | global | written with the problem | the store |
| Solutions | product | global | append-only | the store |
| Solution claims | product | global | append-only | the store |
| Verification runs | product | global | append-only | the store |
| Template matches | product | global | append-only | the store |
| Site outcomes | product | global | append-only | the store |
| Sittings | user | private | revised in place | the store |
| Card runs | user | private | append-only | the store |
| Recall attempts | user | private | append-only | the store |
| Attempts | user | private | append-only | the store |
| Attempt verifications | user | private | append-only | the store |
| Attempt claims | user | private | append-only | the store |
| Calls | user | private | append-only | the store |
| Self-labels | user | private | append-only | the store |
| Diagnoses | user | private | append-only | the store |

## Boundaries

- **Verification runs locally**, so every submission is judged by whatever
  ran it.
- **The web app is two deployables on one origin.** The API answers JSON under
  `/api` and serves no page. The frontend is static files, and whatever serves
  them routes `/api` to the API: Vite's proxy locally, the host in Phase 9.
  - A second origin is rejected. Every request would need CORS, and the login
    cookie Phase 9 brings would have to cross domains.
  - A path naming no file is answered with `index.html`. The frontend routes
    its pages by URL, so a reload of any page reaches the app rather than a
    404.
- **Google and GitHub hold each identity and its login.** A person signs in
  through one of the two, and the engine stores no password. Password resets,
  second factors and leaked credentials are the provider's to handle, so no
  credential handling is the engine's own.
  - The engine runs the sign-in flow itself, through Authlib, which checks the
    state, the nonce and PKCE. A managed account provider is rejected: its
    login and its tokens live on its own domain, and the session cookie stays
    on the pages' origin.
  - The engine keeps each session in Postgres, and sets the session's id in an
    `HttpOnly`, `SameSite=Lax` cookie. A stored session can be revoked, where a
    signed token stands until it expires.
  - An `identities` row links a provider's user id to a user id the engine
    mints at the first sign-in. The log keys on the engine's id, so adding or
    replacing a provider rewrites no record.
  - Sign-in by email is deferred until a user needs it. An emailed link, a
    managed provider or a company's own sign-in would each be one more provider
    an `identities` row names.
  - A dev login signs in as a named user with no provider, for local work. A
    flag enables the dev login, and the app refuses to start with the flag
    unless it is bound to `127.0.0.1`.
- **Storage is one Postgres database**, named by `DATABASE_URL`, and every
  store writes there. The schema is the contract, and the tables are declared
  against it.
  - The engine reaches Postgres through SQLAlchemy Core, and Alembic applies
    the migrations. The tables are declared once in Python, so a field added
    to a record is one column and one generated migration, where hand-written
    SQL names the field again in every statement that lists columns.
  - The ORM is not used. Core builds each statement explicitly, so a write the
    code does not name never happens, and the append-only logs stay visible
    as inserts alone.
  - A table holds a column per field, `NOT NULL` where the record requires
    the field. The database then refuses a record the schema refuses, rather
    than storing whatever a writer sent.
  - A string enum is a Postgres enum type holding the member values, the
    strings a stored JSON record already carries. A timestamp keeps its time
    zone.
  - A list of records is a child table keyed to its parent, with its position
    where the order matters: a sitting's pauses, a run's case results, a
    card's templates. A list of strings is a `text[]` column.
  - JSONB holds a value only where the value is JSON of any shape by design,
    as a test case's arguments and its expected value are.
  - A machine record's table holds its `call_id`, a foreign key to `calls`,
    and none of the configuration. `machine.md` gives why the configuration
    is stored once.
  - The migrations live in `migrations/`, generated by Alembic from the
    declared tables and read before they are committed. An enum type is
    created once, before every table using it, and dropped after them, since
    a column declaring its own type would create it twice.
  - A field added to a record is a nullable column added by a migration, which
    is the additive rule in `## Repo constraints`. A test compares each table's
    columns with its record's fields, since the two are declared apart.
  - An append-only table refuses an `UPDATE` and a `DELETE` by a trigger, and
    so do the case results stored with a run. A store with a bug in its write
    path is then refused by the database instead of rewriting the log. A
    migration creating an append-only table adds the trigger by hand, since
    Alembic generates none, and a test lists the tables that carry it.
- **The calibration corpus is the platform data the pivot to generated
  problems left behind**, under `data/old/`: a platform's problems, the
  attempts against them, the claims and the calls. It is a corpus rather than
  a store: no store points there, and nothing on the run path reads it.
  - The corpus is kept for one measurement, deferred to Phase 14 in
    `ROADMAP.md`: how often a matcher names a form from a statement alone. A
    corpus no generator wrote is the baseline for that rate. How the corpus is
    read is deferred to taking the measurement.
- **Content generation is a command of the engine**, beside the classifier and
  the matcher, and it writes the problems, their test cases and their
  solutions. The command reuses one transport, one call log and one provenance
  base, rather than standing a second copy of each somewhere else.
  - Extraction to a pipeline of its own stays possible and is not planned. Such
    a pipeline would have to preserve the minted ids, since the attempt log
    references them.
- **Cards are ingested from files.** They are authored in `content/` and seeded
  into the datastore. `content/` is gitignored like `data/`. The technique
  vocabulary is the exception: it ships with the package, in git.
  - An authored card has its own shape. `CardSeed`
    (`src/algo_coach/schema/seed.py`) is the payload the stored card is built
    from, not the card, and it has no field for the identity the engine mints.
  - A card and each template are matched by their authored slug, which makes
    re-seeding refresh rather than duplicate. A new slug is a new card: the
    runs and the recall history stay with the old card, so renaming is a title
    change.

## Invariants

Properties the system holds at all times.

- Attempts, attempt claims, self-labels and diagnoses are append-only: no
  record is ever revised or removed in place. Deleting a private log
  wholesale while it holds nothing irreplaceable is a different act. That
  allowance ends the first time a record in the log is worth keeping.
- Every record keyed to an attempt carries an engine-minted `id`, its
  `attempt_id` and `created_at`.
- The user's own record stands over the machine's answer to the same question,
  whichever was written later: a attempt claim resolves user-first, and a
  diagnosis never supersedes a self-label. The machine's record is kept and
  scored, never deleted and never promoted.
- Every reference in an append-only record is engine-minted, so the log stays
  readable without anything outside the engine.
- Aggregates are derived views, never stored truth.
- Every problem is the product's own, written by the engine.
- A problem never lands without the test cases that decide it, a canonical
  solution that passed them, and a reference solution that agreed with the
  canonical on every case.
- The technique vocabulary and the cards are product-owned and global, and no
  user authors a technique or a card.
- Domain logic stays adapter-free and directly callable. The CLI is one
  adapter, and the web app is the second. A sitting happens in
  the web app, and the by-hand passes stay in the terminal.
- No third-party problem statements or test cases in git, in any repo.

## Repo constraints

Rules on how this repo is built, rather than properties of the running system.

- No concrete third-party problem-platform client ever enters this repo.
- Schema changes must be additive (new optional fields), never breaking. A
  change may tighten instead, by making a field required, removing a field or
  widening a validator. Tightening is allowed only while no stored record
  carries the loose shape, which in practice means deleting the records that
  do. Weigh what is deleted, not how many: the log has to stay readable by its
  own schema, and a field kept for a handful of disposable records is one every
  reader branches on forever.
- `data/` and `content/` are gitignored, and only the schema is public. The
  generated corpus could be published, since the product owns it, and is not:
  the database holding the corpus also holds the private log.
- Prefer tools and functions over agents. Multi-agent is adopted once a
  pipeline needs it, never as the starting structure.

## Meta-rule

Ship thin on features, and design the record schema one phase ahead of them.
Component boundaries can be refactored. An append-only log cannot.
