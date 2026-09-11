# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.
The work not yet ready for a phase waits under Further developments.

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
- [x] Declare the drafts table, its declared and settled cases, and a call
      column for each of its five sites
- [x] Declare the users table, whose engine-minted id a private record's
      `user_id` references by foreign key
- [x] Declare the sittings table and its pauses
- [x] Declare the attempts table
- [x] Declare the attempt verifications table and its case results
- [x] Declare the attempt claims table
- [x] Declare the self-labels table
- [x] Declare the diagnoses table
- [x] Check that every stored record has a table. A record left without one is
      a store the copy to Postgres skips
- [x] Generate the first Alembic migration from those tables, creating every
      table
- [x] Add an `appended` identity column to every append-only table, in a
      second migration, and read a log in its order. A JSON line kept the
      order it landed in, and readers break a tie on `created_at` by it
- [x] Add a test database fixture: one database per xdist worker, built by the
      migrations and emptied between tests
- [x] Rewrite the calls store on Postgres, its tests on the fixture
- [x] Rewrite the cards store on Postgres, its tests on the fixture
- [x] Rewrite the problem store on Postgres, its tests on the fixture
- [x] Rewrite the case store on Postgres, its tests on the fixture
- [x] Rewrite the solution store on Postgres, its tests on the fixture
- [x] Rewrite the solution claims store on Postgres, its tests on the fixture
- [x] Rewrite the template matches store on Postgres, its tests on the fixture
- [x] Rewrite the verifications store on Postgres, its tests on the fixture
- [x] Rewrite the site outcomes store on Postgres, its tests on the fixture
- [x] Rewrite the draft store on Postgres: a put replaces the draft's row and
      all its cases in one transaction. Simple, and revisable, since the draft
      store is working state
- [x] Rewrite the sittings store on Postgres, its tests on the fixture
- [x] Rewrite the attempt log on Postgres, its tests on the fixture
- [x] Connect the CLI and the API to Postgres through `DATABASE_URL`
- [x] Delete `JsonlLog`, `FileStore` and the copy script, and stop writing
      `data/`, keeping `data/old/`. One backend is one set of write semantics
- [x] Refuse an update or a delete on an append-only table in the database
      itself, by grant or by trigger. A write path that skips the log's rule
      is otherwise one bug away
- [x] Copy every record under `data/` into Postgres with a one-off command, and
      check that each reads back equal. A record the copy loses from an
      append-only log is lost for good
- [x] Run Postgres for the suite in CI. The stores run on nothing else

### Users and access

- [x] Write into `docs/architecture/README.md` that Google and GitHub hold each
      identity and its login, and the engine holds the sessions and no
      password. No credential handling is our own
- [x] Add an `identities` table linking a provider's user id to a row of the
      users table, minted the first time the account signs in. `README.md`
      requires every reference in an append-only record to be engine-minted,
      and a provider switch would otherwise rewrite the log
- [x] Add the Google and GitHub sign-in and callback routes through Authlib,
      passing on only an email the provider verified. The library checks the
      state, the nonce and PKCE, where a hand-written flow goes wrong
- [x] Add a `sessions` table, and set a session's token in an `HttpOnly`,
      `SameSite=Lax` cookie at the callback. A stored session can be revoked,
      where a signed token stands until it expires
- [x] Add a dev login that signs in as the user `ALGO_COACH_DEV_LOGIN` names,
      with no provider. The app refuses to start with it beside a provider's
      client, and the route answers on loopback alone
- [x] Decide how the records written under the user `local` reach the author's
      account, and write the choice into `log.md`. Those records are the
      author's history, and the log is append-only
- [x] Read the user in `UserId` from a verified session, in place of the id
      the app was built with. Every route already takes the user through that
      one dependency
- [x] Refuse a write route whose request body is not JSON. A form on another
      site cannot send JSON without a preflight, so the check stops a forged
      write the cookie would otherwise carry
- [x] Add login and logout to the pages, and send a request without a session
      to the login. The session cookie stays on the pages' origin
- [x] Make one user's log readable and deletable without touching another's.
      The author's own log is the evidence of daily use and the set every eval
      reads, and must not mix with another user's
- [x] Gate sign-in on an `invitations` table of emails, checked at the
      callback. Untrusted execution behind open registration is an abuse
      surface with no upside at this size

### The deployment

- [x] Choose the host for the API, the pages, Postgres and the sandbox, and
      write the choice into `docs/architecture/README.md`. The sandbox needs a
      container runtime, which rules out a host that runs only functions
- [ ] Write the `Dockerfile` and `deploy/compose.yaml`, the compose file copied
      into the image. The server extracts the compose file from the image it
      pulled, so a deploy needs no checkout of this repo
- [ ] Add the deploy job: build the image, push it to the registry, then send
      one command the server's forced command accepts. It runs on a push to
      main, behind the checks
- [ ] Serve the pages and route `/api` to the API on one origin, answering a
      path naming no file with `index.html`. `README.md` gives why the two
      share an origin
- [ ] Publish Postgres on the server's loopback address alone in
      `deploy/compose.yaml`, and reach it from a laptop over an SSH tunnel. The
      generation commands run off the server, since their subprocesses move the
      wall clock a sitting's verdict is read from
- [ ] Keep the database URL and the provider's keys in the file the server
      alone holds, and out of both repos
- [ ] Back up the database on a schedule, and restore one backup into a scratch
      database. A backup never restored is not known to restore
- [ ] Rebuild the server once from nothing: create it, attach the volume,
      restore the latest dump, deploy, and sit a problem on it. The steps that
      fail are the volume, the secrets file and DNS, and only a rehearsal shows
      which
- [ ] Write down what the deployment holds, for how long, and who can read it.
      A user cannot check a retention claim that was never written down

### The sandbox

- [ ] Write the broker: a service holding the container runtime's socket and
      answering one request, the code, the arguments and the cap. The API holds
      no socket
- [ ] Fix the image, the flags and the limits in the broker's source, and add a
      test that a request naming an image, a mount or a capability is refused.
      Every later hardening step inherits a field a request can influence
- [ ] Pin the submission's image by digest, an interpreter and no engine code.
      A tag moves under the run that a stored verdict was measured by
- [ ] Install gVisor on the server, name its runtime in the broker, and check
      that the submission's image runs a canonical under it. A container under
      the host's own kernel is one kernel exploit away from the host
- [ ] Add a backend behind `runner.run` that calls the broker, keeping the
      signature and the child protocol, JSON in and JSON out. The `run`
      boundary was written for a second backend, so no second runner is needed
- [ ] Give the container no network, a read-only root filesystem, a non-root
      user, and limits on memory, processes and output. A submission that
      spawns a process or opens a connection fails
- [ ] Enforce the cap from outside the container as well as in the child. A
      child that ignores its own timer otherwise holds the machine
- [ ] Add a test that the sandbox backend's request carries no expected value.
      `corpus.md` keeps the comparison above the boundary, and a sandbox told
      the answer can be made to agree with it
- [ ] Run every problem's canonical under the sandbox at the drill cap, with
      gVisor already installed, and write down which cases it no longer
      finishes within a tenth of the cap. The separating sizes were found on
      the local subprocess, and a CPU limit and a slower system call both move
      them
- [ ] Cap submissions per user per minute. Each submission runs untrusted code
      on our machine
- [ ] Admit one submission at a time in the broker, and refuse a submission
      whose wait passes a bound. A submission running beside another moves the
      wall clock a verdict is read from, and an unbounded wait reads to the
      user as a sandbox that hung

### Other items

- [ ] Decide what ends a sitting the user leaves without pressing End, and
      write the choice into `log.md`. Two of the first seven sittings were left
      running, and serving that problem again reaches the old clock

### Exit
- [ ] Complete a sitting on the deployed engine, signed in as an invited user,
      from the board to the claim
## Phase 10 — the pages designed

The pages given one design, and the flows Phase 12 adds planned before they are
built. The web app holds a handful of pages, so rebuilding them on one design
costs least before Phase 12 adds its own.

### Design system

- [ ] Write the design tokens into `web/src/index.css` as the theme every
      component reads: color, type scale, spacing and radius. A value set in one
      component alone is a design no other component follows
- [ ] Add a page showing each token and each component the pages use, served in
      development alone. A component restyled there shows every use of it at
      once

### Overall design

- [ ] Write the pages' structure into `docs/architecture/`: the navigation, the
      main areas, and the page a signed-in user lands on. Phase 9's invited
      sittings are the input
- [ ] Rebuild each existing page on the design system and that structure: the
      board, the cards, a card, a technique's candidates, a problem, the
      sitting and the login
- [ ] Send a refused sign-in back to the login page with its reason. The
      callback is a navigation, and it answers a refusal with raw JSON today

### Flows planned

- [ ] Write the card run, ladder and recall trainer flows as sequences in
      `flows.md`, naming each detail only use can answer as deferred
- [ ] Draw a low-fidelity wireframe of each of those flows, kept beside
      `flows.md`. A sequence says what happens in what order, and a wireframe
      says what the user sees at each step

### Exit
- [ ] Build every existing page on the design system, and write and draw each
      flow Phase 12 adds

## Phase 11 — the matcher, measured

How much a generated corpus is worth, measured. Behind the beta: the drill loop
needs problems and not a score, and the attempts the loop produces rebuild the
eval set the classifier is scored against.

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

## Phase 12 — ladder, recall and card runs

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
- [ ] Go through a card run by hand: start a card, solve a rung of its ladder,
      recall a template cold against the card's tests, and see a probe
      offered

## Phase 13 — mastery and scheduling

- [ ] Write into `docs/architecture/` what a technique's mastery is derived
      from: the attempts, their claims and their verdicts. Mastery is never
      stored, so the derivation is the whole model
- [ ] Write into `flows.md` how the scheduler picks the next sitting from
      mastery, and what the board offers beside the pick. The user picks every
      technique and problem today
- [ ] Serve the scheduler's pick on the board, with every technique still on
      offer beside it
- [ ] Re-claim thirty attempts with the earlier machine claims hidden, to
      measure the user's own consistency, which caps every classifier score.
      Mastery reads claims, and a wrong claim spends practice time

### Exit
- [ ] Start a sitting from the scheduler's pick on the board, and complete it
      to the claim

## Further developments

Blocks of work not ready for a phase, grouped and unordered. A planned phase is
a block that became ready. A block, or a single item of one, is planned into a
phase once it is clear enough to plan. An item's trigger, where it names one, is
the event that makes the item ready.

### Failure mode

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

### Alternative solutions

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
- [ ] Choose what a matcher reading of a solution stores, a verdict per
      candidate template or one record naming the templates the matcher found,
      and write the choice into `content.md`. Scoping through the problem's
      techniques bounds the pairs until enumeration adds a canonical displaying
      a form outside them

### Classifier and matcher

- [ ] Classify an attempt over the whole vocabulary and intersect with the
      problem's techniques in code, once the user claims can score that
      configuration against the one constrained to the problem's techniques. A
      verdict naming a technique outside the problem's own is the only signal
      that the problem's techniques are incomplete
- [ ] Point the matcher at an attempt as well as a canonical, and keep the
      records apart as attempt claims and solution claims are kept apart.
      Triggered when a rung or a recall probe needs to know which form the
      user's own solution used

### Problem generation

- [ ] Write the generation call for a technique target: a technique and its
      criteria in, a problem out, carrying `target_technique`. A paradigm and a
      problem class have no template, so nothing else reaches those two kinds.
      Triggered when a technique with no card needs problems
- [ ] Decide whether a canonical that yields no value on a proposed case is a
      defect rather than an input the statement excludes, and write the choice
      into `flows.md`. Triggered when a run drops such cases often enough to
      show in the run's report
- [ ] Decide how long a rejected draft is kept, and write the choice into
      `flows.md`. Triggered when the draft store outgrows the corpus the drafts
      produced
- [ ] Read the naive solution with the classifier, and hold the draft where the
      verdict names the card's technique. One call per naive solution, and it
      catches what the prompt misses rather than hoping. Triggered when a sweep
      still holds drafts whose naive solution reached the form
- [ ] Write the inputs and naive site outcomes where a resume re-ran the search
      and re-asked neither site. A site that made no call writes no record, so
      the separating size and the count of a resumed landing are readable
      nowhere once the draft is cleared. Triggered when a report reads the
      separating size of a problem a resume landed

### Cases and verdicts

- [ ] Choose how a case with several correct returns is decided, by a
      normaliser over the returned value or by a checker per problem, and write
      the choice into `corpus.md`. Triggered when a core template can only be
      exercised by a problem whose answer is not unique
- [ ] Name on the verification the rule that decided a case, once that rule is
      no longer JSON equality. A verdict stored without the rule cannot be
      re-read after the rule moves. Triggered by a second deciding rule landing
- [ ] Carry a tolerance on a case, and name on the verification that the
      tolerance decided it. A statement asks for exactly comparable values
      today, so a real-valued answer cannot be asked for at all. Triggered when
      a core template's answer is neither an integer nor a reduced fraction
- [ ] Settle the full shape of a verification's environment, which the `runner`
      string stands in for. The machine decides a timeout as much as the cap
      does. Triggered when two runs under one backend disagree

### Transport

- [ ] Fall back to another endpoint of the same transport shape on an outage,
      never to Anthropic direct, whose compatibility layer ignores
      `response_format`, `strict` and `reasoning_effort`. Triggered when an
      outage blocks a run

### Product

- [ ] Let a user request a problem's retirement, as a private record an admin
      reads before retiring the problem by hand. Problems are served to every
      user, so no user retires one directly. Triggered when someone other than
      the author sits

### Docs

- [ ] Read the architecture doc against the code, landing every divergence as
      an item in this file. The goal is not that no divergence exists, since
      the doc is target state. The goal is that no divergence is unknown.
      Triggered when a phase closes
