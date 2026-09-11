# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.

## Phase 9 — the engine hosted (current)

The same loop, for people who are not the author. The stores move from JSON
files to Postgres, each person signs in to a log of their own, the app is
deployed, and submitted code runs in a sandbox. The local subprocess stays the
backend for our own generated code, which is not a threat model.

### Storage on Postgres

- [x] Choose how the engine reaches Postgres, a driver with plain SQL or a
      query layer over it, and write the choice into
      `docs/architecture/README.md`. Every store is rewritten against it
- [x] Decide the table shape, a table per record class holding the record as
      JSONB beside the columns a store queries, or a column per field, and write
      it into `docs/architecture/README.md`. The pydantic schema stays the
      contract either way
- [x] Add the shared `MetaData` to `algo_coach.storage`, the column conventions,
      and a test comparing a table's columns with its record's fields. The
      tables and the pydantic models are declared apart, so only a test keeps
      them equal
- [x] Declare the problems table beside the problem store
- [x] Declare the test cases table, the arguments and the expected value as
      JSONB
- [x] Declare the solutions table
- [x] Declare the solution claims table
- [x] Declare the template matches table
- [x] Declare the verifications table and its case results
- [x] Declare the site outcomes table
- [x] Declare the calls table
- [x] Declare the cards table and its templates
- [ ] Declare the drafts table, its declared and settled cases, and one table
      for the provenance of its five sites
- [ ] Declare the sittings table and its pauses
- [ ] Declare the attempt log's tables: attempts, attempt verifications and
      their case results, claims, self-labels and diagnoses
- [ ] Check that every stored record has a table. A record left without one is
      a store the copy to Postgres skips
- [ ] Generate the first Alembic migration from those tables, creating every
      table
- [ ] Back `JsonlLog` and `FileStore` with Postgres behind their current
      interfaces, so no domain call changes. The write semantics in the
      data-class table hold on either backend
- [ ] Refuse an update or a delete on an append-only table in the database
      itself, by grant or by trigger. A write path that skips the log's rule
      is otherwise one bug away
- [ ] Decide whether the file stores stay beside Postgres, for tests and for
      offline use, or go. Two backends are two write semantics to keep equal
- [ ] Copy every record under `data/` into Postgres with a one-off command, and
      check that each reads back equal. A record the copy loses from an
      append-only log is lost for good
- [ ] Run Postgres for `just app` and for the suite in CI. A store tested only
      against files is untested where it runs

### Users and access

- [ ] Choose the bought account provider, and write into
      `docs/architecture/README.md` what it holds: the identity and the login,
      and nothing of the practice log. No credential handling is our own
- [ ] Mint the engine's own user id for each account, and key the log on it.
      `README.md` requires every reference in an append-only record to be
      engine-minted, and a provider switch would otherwise rewrite the log
- [ ] Decide how the records written under the user `local` reach the author's
      account, and write the choice into `log.md`. Those records are the
      author's history, and the log is append-only
- [ ] Read the user in `UserId` from a verified session, in place of the id
      the app was built with. Every route already takes the user through that
      one dependency
- [ ] Add login and logout to the pages, and send a request without a session
      to the login. The session cookie stays on the pages' origin
- [ ] Key every private record by the engine's user id in its table:
      sittings, attempts, attempt verifications and claims. Problems, cases,
      solutions, matches and cards stay shared product data
- [ ] Make one user's log readable and deletable without touching another's.
      The author's own log is the evidence of daily use and the set every eval
      reads, and must not mix with another user's
- [ ] Gate access on an invitation. Untrusted execution behind open
      registration is an abuse surface with no upside at this size

### The deployment

- [ ] Choose the host for the API, the pages, Postgres and the sandbox, and
      write the choice into `docs/architecture/README.md`. The sandbox needs a
      container runtime, which rules out a host that runs only functions
- [ ] Serve the pages and route `/api` to the API on one origin, answering a
      path naming no file with `index.html`. `README.md` gives why the two
      share an origin
- [ ] Keep the database URL and the provider's keys in the host's secret store,
      and out of the repo
- [ ] Back up the database on a schedule, and restore one backup into a scratch
      database. A backup never restored is not known to restore
- [ ] Write down what the deployment holds, for how long, and who can read it.
      A user cannot check a retention claim that was never written down

### The sandbox

- [ ] Add a container backend behind `runner.run`, keeping the signature and
      the child protocol, JSON in and JSON out. The `run` boundary was written
      for a second backend, so no second runner is needed
- [ ] Give the container no network, a read-only root filesystem, a non-root
      user, and limits on memory, processes and output. A submission that
      spawns a process or opens a connection fails
- [ ] Enforce the cap from outside the container as well as in the child. A
      child that ignores its own timer otherwise holds the machine
- [ ] Add a test that the sandbox backend's request carries no expected value.
      `corpus.md` keeps the comparison above the boundary, and a sandbox told
      the answer can be made to agree with it
- [ ] Run every problem's canonical under the sandbox at the drill cap, and
      write down which cases it no longer finishes within a tenth of the cap.
      The separating sizes were found on the local subprocess, and a CPU limit
      moves them
- [ ] Cap submissions per user per minute. Each submission runs untrusted code
      on our machine

### Other items

- [ ] Decide what ends a sitting the user leaves without pressing End, and
      write the choice into `log.md`. Two of the first seven sittings were left
      running, and serving that problem again reaches the old clock

### Exit
- [ ] Complete a sitting on the deployed engine, signed in as an invited user,
      from the board to the claim
## Phase 10 — the matcher, measured

How much a generated corpus is worth, measured. Moved behind the beta on
2026-09-09: the drill loop needs problems and not a score, and the attempts
the loop produces rebuild the eval set the classifier is scored against.

### Matching the generated corpus by hand

The hand pass does two jobs at once. It writes the matcher's reference, and it
is the only reading of a generated problem that no model produced. A generator
that drifted from its target shows in the hand pass whatever the matcher says.

- [ ] Match by hand a sample of the problems the sweep landed, across the core
      templates the sweep reached. `--gaps` already names those templates, so
      no aiming is left
- [ ] Sample and match by hand through `algo-coach match --by-hand`, over pairs
      of a template and a solution. The command already samples across
      templates, and only the pair's subject changes, from a problem to a
      solution
- [ ] Match the eval set by hand from the templates alone, with no matcher
      reading in view. The first hand pass set the criterion, and a score over
      those same pairs measures the criterion against itself

### Scoring the matcher

Generation asserts a match and the matcher audits that match, so an unmeasured
matcher audits at an unknown error rate. An unmeasured matcher blocks trusting
the audit. Generation goes on without the score.

- [ ] Score the matcher per pair, grouped per template, over the pairs both the
      user and the matcher read. A match asserts one pair, so a score over a set
      would hide which template the matcher over-matches
- [ ] Report the positive verdicts in both directions: the templates the user
      named and the matcher missed, and the templates the matcher named and the
      user did not. Most pairs are negative, so accuracy would score a matcher
      that names nothing in the nineties
- [ ] Skip a pair the user settled on the run path, and read that pair in the
      eval. The skip's condition follows from the shape of the matcher's record,
      which `content.md` defers
- [ ] Lift the scorer out of `claims` for the matcher to share. The scorer
      already prints denominators and reports both directions, which is the
      shape a per-pair score needs
- [ ] Let the matcher read the pair the generator's match asserts, and report
      the disagreements. The disagreements mean something only once the matcher
      carries a score

### Exit
- [ ] The matcher carries a per-template score in both directions

## Phase 11 — ladder, recall and card runs

- [ ] Resolve the ladder from the matches, the selector filling out to `size`.
      A retired problem fills no rung
- [ ] Derive requiredness from the templates a rung covers. A rung covering a
      core template is required. A rung covering only the optional template is
      optional. A rung covering both is required, with the optional template
      offered as the alternative approach
- [ ] Re-derive the ladder whenever the corpus moves under the ladder, a
      started card included. Progress is a fold over attempts, so a solved rung
      stays solved
- [ ] Add `CardRun`, minted where a card is started, since the ladder is
      measured from that start. The run holds when the run began and the
      probes assigned, and later probes append
- [ ] Add `RecallAttempt`, keyed to a card and a template. A recall attempt has
      no problem and no submission, so no field keys the record to an attempt.
      The hints taken before a pass are part of the record
- [ ] Generate probes from the corpus, as a skill, since choosing a probe is
      judgment
- [ ] Build the recall trainer. The template's name is hidden, the user types
      the form into a blank file from memory, and the file runs against the
      card's own tests. The template is never printed, since reading the form
      is not recalling the form
- [ ] Show a card's status: when each template was last recalled, which rungs
      are outstanding, and which probes are available. Those are the inputs a
      graduation rule reads, and no threshold is set yet

### Exit
- [ ] Recall and the ladder run daily

## Phase 12 — mastery, scheduling, failure mode

- [ ] Land `rust` against `gap` with the mastery model, or drop the
      distinction. The two labels differ only in whether the technique was ever
      fluent, and a single attempt does not carry that history
- [ ] Settle what `speed` means before anything writes the label. "Solved but
      too slowly" is about the user, a timeout is about the solution's
      complexity, and only the timeout is in the record
- [ ] Write the `SelfLabel` the loop asks for at the moment of solving, once
      `speed`, `rust` and `gap` are settled. A label cannot be given later, so
      one written under a meaning that later moved can never be corrected
- [ ] Offer only the failure modes an attempt's verification leaves open. A
      crash on every case and a timeout are in the record already, and a label
      contradicting the verdict would be a second answer to one question
- [ ] Narrow the diagnosis call, the model call that writes a `Diagnosis`, to
      what the record supports: a mechanical slip against a conceptual miss. A
      four-way verdict would ask the call for what the call cannot see
- [ ] Write the verdict as a `Diagnosis` carrying its provenance whole. A
      diagnosis never supersedes a self-label, because the eval scores the
      diagnosis against the self-label
- [ ] Score the diagnosis call per failure mode, with no overall share, against
      self-labels the loop produced. A call that only ever says `gap` would
      score well on a corpus of gaps

## Phase 13 — alternative solutions

Every other way to solve a stored problem, by the flow in `flows.md`,
"Enumerating a problem's other solutions". The schema and the match's subject
are in place already, and nothing before this phase writes a second canonical.

Enumeration buys a rung covering two forms at once, a scale case cross-checked
between two efficient solutions, and a problem's techniques widening past the
one form its target named.

- [ ] Write the enumeration call: a landed problem in, the approaches that
      solve the problem out, each a name and a one-line idea. The reply carries
      no code. A reply carrying code for every approach would fail whole on one
      bad entry, where a proposal costs one call
- [ ] Generate a canonical per approach, one call each, and store the canonicals
      the problem's cases pass. A failure rejects nothing. The cases judge the
      solution, and an enumerated canonical is no reading of the statement
- [ ] Add `algo-coach enumerate`, a problem in and canonicals out, through the
      transport the other commands share
- [ ] Decide what two canonicals of one form cost, once a corpus shows how
      often enumeration proposes two of one form. Execution cannot separate
      the two: top-down and bottom-up dynamic programming pass the same cases
- [ ] Re-run the mutation loop over a canonical enumeration added, or record
      that a later canonical carries less assurance. The case set was built to
      kill mutants of the first canonical, so a later canonical was never
      tested on its own failure modes

## Deferred

A backlog outside the phase order. Each item names a trigger: the event that
has to happen before the item is worth doing. An item is picked up when its
trigger fires, whatever phase is current.

- [ ] Re-claim thirty attempts with the earlier machine claims hidden, to
      measure the user's own consistency, which caps every classifier score.
      Triggered when mastery estimation reads claims, and a wrong claim starts
      spending practice time
- [ ] Read the architecture doc against the code, landing every divergence as
      an item in this file. The goal is not that no divergence exists, since
      the doc is target state. The goal is that no divergence is unknown
- [ ] Classify an attempt over the whole vocabulary and intersect with the
      problem's techniques in code, once the user claims can score that
      configuration against the one constrained to the problem's techniques. A
      verdict naming a technique outside the problem's own is the only signal
      that the problem's techniques are incomplete
- [ ] Point the matcher at an attempt as well as a canonical, and keep the
      records apart as attempt claims and solution claims are kept apart.
      Triggered when a rung or a recall probe needs to know which form the
      user's own solution used
- [ ] Write the generation call for a technique target: a technique and its
      criteria in, a problem out, carrying `target_technique`. A paradigm and a
      problem class have no template, so nothing else reaches those two kinds.
      Triggered when a technique with no card needs problems
- [ ] Choose what a matcher reading of a solution stores, a verdict per
      candidate template or one record naming the templates the matcher found,
      and write the choice into `content.md`. Scoping through the problem's
      techniques bounds the pairs today. Triggered when a canonical displays a
      form outside the problem's techniques, which enumeration produces
- [ ] Decide whether a canonical that yields no value on a proposed case is a
      defect rather than an input the statement excludes, and write the choice
      into `flows.md`. Triggered when a run drops such cases often enough to
      show in the run's report
- [ ] Run each case in its own subinterpreter inside a pooled worker, where
      the children are started ahead of their cases today. A subinterpreter
      cannot be preempted, so a case over the cap kills its worker instead of
      receiving a signal. Triggered when interpreter start is again the largest
      cost of a run
- [ ] Decide how long a rejected draft is kept, and write the choice into
      `flows.md`. Triggered when the draft store outgrows the corpus the drafts
      produced
- [ ] Choose how a case with several correct returns is decided, by a
      normaliser over the returned value or by a checker per problem, and write
      the choice into `corpus.md`. Triggered when a core template can only be
      exercised by a problem whose answer is not unique
- [ ] Name on the verification the rule that decided a case, once that rule is
      no longer JSON equality. A verdict stored without the rule cannot be
      re-read after the rule moves. Triggered by a second deciding rule landing
- [ ] Settle the full shape of a verification's environment, which the `runner`
      string stands in for. The machine decides a timeout as much as the cap
      does. Triggered when two runs under one backend disagree
- [ ] Fall back to another endpoint of the same transport shape on an outage,
      never to Anthropic direct, whose compatibility layer ignores
      `response_format`, `strict` and `reasoning_effort`. Triggered when an
      outage blocks a run
- [ ] Vary one argument across a separating case's calls, so a submission
      that caches its own answer fails it. The calls are identical today, and
      the count separates the two solutions the engine wrote because neither
      caches. Triggered when the drill loop judges a submission against a case
      carrying a count
- [ ] Read the naive solution with the classifier, and hold the draft where the
      verdict names the card's technique. One call per naive solution, and it
      catches what the prompt misses rather than hoping. Triggered when a sweep
      still holds drafts whose naive solution reached the form
- [ ] Carry a tolerance on a case, and name on the verification that the
      tolerance decided it. A statement asks for exactly comparable values
      today, so a real-valued answer cannot be asked for at all. Triggered when
      a core template's answer is neither an integer nor a reduced fraction
- [ ] Write the inputs and naive site outcomes where a resume re-ran the search
      and re-asked neither site. A site that made no call writes no record, so
      the separating size and the count of a resumed landing are readable
      nowhere once the draft is cleared. Triggered when a report reads the
      separating size of a problem a resume landed
- [ ] Let a user request a problem's retirement, as a private record an admin
      reads before retiring the problem by hand. Problems are served to every
      user, so no user retires one directly. Triggered when someone other than
      the author sits
