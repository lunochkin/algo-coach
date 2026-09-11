# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.

## Phase 8 — the engine serves (current)

The first attempts the engine produces itself, through the interface a sitting
happens in. The interface is a web app: a JSON API over the domain calls, and a
React frontend built to static files, served on the API's origin.

### The loop, as domain calls

- [x] Move `DRILL_CAP_MS` from `generation/speedup.py` into
      `algo_coach.sitting`, and import it back into generation. The cap is the
      sitting's, and the speedup search only measures a separating size by it
- [x] Add the `Sitting` record: an engine-minted id, the user, the problem and
      the start. The two calls of one sitting reach the engine as two requests,
      and the start has to outlive the first one
- [x] Add `Pause` and `ended_at` to `Sitting`, and count the elapsed time with
      every pause excluded. A total of the time paused says how long and never
      how often
- [x] Store sittings in a store revised in place, as the drafts are, and keep
      the record after the sitting ends. How often practice is interrupted is
      readable in that store alone
- [x] Add `algo_coach.sitting.pause`, `.resume` and `.end`. A sitting the loop
      leaves open reports an elapsed time that moves with the moment it is read
- [x] Add `sitting_id` to `Attempt`, optional as an additive field is. An
      attempt written without it can never be grouped with the sitting's other
      attempts, since the log is append-only
- [x] Add `algo_coach.sitting.serve`: a created problem in, its statement and a
      stored `Sitting` out. A restart between the two calls then loses no clock
- [x] Serve every created problem and skip the retired ones. No gate stands
      between landing and serving until Phase 14
- [x] Add `algo_coach.sitting.submit`: the code and the sitting's id in, an
      `Attempt` in the log out. The call runs the code against the problem's own
      cases at the drill cap and folds the case results to `solved`
- [x] Compute the attempt's duration from the stored sitting's start, and take
      no duration among `submit`'s arguments. A duration the browser reports is
      a number the engine did not witness
- [x] Take `user_id` as an argument to the sitting calls rather than defaulting
      to one user. Phase 9 keys the log by user, and a default here would spread
      that change into this module
- [x] Test one whole sitting over `algo_coach.sitting`: serve, a failing
      submit, a passing submit and end, on stores sharing one root. The unit
      tests pin each call alone, and this test pins that the calls compose
- [x] Store each attempt's verification as an `AttemptVerification` in the
      attempt log, keyed by `attempt_id`. The results of the user's own code are
      private, where a solution's verification is product data
- [x] Add the domain call retiring a problem as `defective`, moving the status
      on the stored record and nothing else. `ProblemStore.put` already refuses
      a record whose other fields moved
- [x] Add `algo-coach problem --retire <id>`, which prints the problem whole and
      then retires it as `defective`. A problem is served to every user, so
      retirement is a by-hand act rather than a control in the loop
- [x] Exclude a defective problem's attempts from the board, solved and failed
      alike. Dropping only the failures would raise a technique's solve rate
      because a problem was broken
- [x] Write the `AttemptClaim` the sitting's question produces, over the
      problem's own techniques and carrying a confidence level.
      `algo-coach claim` asks that question of attempts already in the log
- [x] Ask the claim per attempt of the sitting rather than once per sitting. A
      drill can mint several attempts, and a claim on the last alone would
      leave the earlier attempts to the problem's techniques

### The API

- [x] Add `algo_coach.api`: a FastAPI app over the sitting calls, JSON in and
      JSON out. The API is the second adapter beside the CLI, and neither
      adapter holds domain logic
- [x] Add the read routes the loop's first three steps need: the board, a
      technique's card and candidates, and a problem's statement
- [x] Add the write routes the rest of the loop needs: the submission and its
      per-case verdict, pausing and resuming the sitting, and the claim
- [x] Add a read route for one of the user's sittings by id, returning what
      `serve` returned. The sitting page has its own URL, and a reload there
      otherwise has no statement to show
- [x] Add read routes for every card and for one card by its slug. A slug
      stays the same across a re-seed, where the card's id is minted per store
- [x] Decide what a failing case shows the solver, its outcome alone or its
      arguments too, and write the choice into `flows.md`. Showing the
      arguments hands over a case the solver can special-case
- [x] Report a crashed case's exception from the child, and show it beside the
      failing case. A crash carries no message today, so the solver guesses
      which line raised
- [x] Serve the pages and the API from one origin, the frontend proxying
      `/api` to an API that holds no page. A second origin puts CORS on every
      request and the login cookie across domains once Phase 9 buys accounts

### The frontend

- [x] Add `web/`: a Vite and React app in TypeScript, built to static files.
      Phase 9 hosts these same pages, so a terminal interface here would be
      written twice
- [x] Add shadcn/ui over Radix to `web/`, with Tailwind. The components are
      copied into the repo as code to edit, and Radix keeps the keyboard and
      accessibility behaviour
- [x] Build the board as the entry point, showing per-technique progress and
      the technique the user picks from. A problem id as the entry point leaves
      the selection to the user
- [x] Route the pages by URL with React Router, so the address bar names the
      page and a reload stays on it
- [x] List the picked technique's candidates, least recently attempted first,
      and let the user pick the problem. A list shows no statement, since the
      clock starts when the statement is served
- [x] Add the cards list page: every card, grouped by technique, each linking
      to its own page
- [x] Add a card's page: its trigger, its brief and its templates, each
      template's code hidden until the user reveals it. `content.md` gives why
- [x] Link a technique's cards from its candidates page and from the picked
      problem's page. The card is offered, and no sitting requires it
- [x] Add a navigation menu linking the board and the cards list
- [x] Start the sitting from the picked problem's page: a button calls `serve`
      and opens the sitting's page. A card read before that press stays off
      the clock
- [x] Build the sitting page: the statement, the `solve` signature, and a
      CodeMirror editor with completion off. `flows.md` gives why the editor
      proposes nothing
- [ ] Show the per-case verdict beside the editor rather than on a page of its
      own. A sitting split over several pages is a workflow, and a workflow is
      not practised daily
- [ ] Pause and resume the sitting from the page, and show it paused. A user
      who steps away otherwise records a duration the clock kept counting
- [ ] Show the elapsed time during the sitting, counted from the start the API
      handed out. The engine records that duration, so the page shows the
      number the log will carry
- [ ] Build the prompt the sitting ends on: the claim over the problem's
      techniques
- [ ] Drive one whole sitting in a test through the API rather than a browser:
      serve, submit, verdict, claim. The frontend then carries no
      logic a test can only reach by rendering a page
- [x] Add `just app`: the API and the Vite dev server in one command, the dev
      server proxying the API. Two commands in two terminals is friction on
      every session
- [ ] Run the frontend's type check and lint from `just`, beside the Python
      checks. The pre-commit hook runs the Python checks, and a frontend check
      outside that hook never runs before a commit

### Exit
- [ ] Daily practice runs here, in the app, on problems the engine wrote and
      judged

## Phase 9 — the engine hosted

The same loop, for people who are not the author. The only change is the trust
the submitted code gets. The local backend is a subprocess per case, because
our own generated code on our own machine is not a threat model, and another
person's code is.

- [ ] Add a sandboxed backend behind `runner.run`. The backend keeps the
      signature and the child protocol, JSON in and JSON out. The `run` boundary
      was written for a second backend, so no second runner is needed
- [ ] Keep the comparison against `expected` above the boundary, where the
      comparison already sits. A sandbox is never told what a case expects
- [ ] Cap wall clock, memory and output per run, and give the sandbox no
      network. A submission that spawns a process or opens a connection
      fails
- [ ] Key `AttemptLog` by user. The log is the only store that changes.
      Problems, cases, solutions, matches and cards are shared product data
- [ ] Make one user's log readable and deletable without touching another's.
      The author's own log is the evidence of daily use and the set every eval
      reads, and must not mix with another user's
- [ ] Buy the account system, so no credential handling is our own
- [ ] Gate access on an invitation. Untrusted execution behind open
      registration is an abuse surface with no upside at this size
- [ ] Deploy the engine, and write down what the deployment holds and for how
      long. A user cannot check a retention claim that was never written down

### Exit
- [ ] Someone other than the author completes a sitting

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
- [ ] Add a container backend behind `runner.run`, with no network, a read-only
      root filesystem, memory and pid limits, a non-root user, and the cap
      enforced from outside as well as in the child. Triggered when the
      platform serves code someone else wrote
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
