# TODO

## Phase 1 — push API + techniques + drill board — done

### Schema (before the first real ingest)
- [x] `user_id` on `Attempt`, stamped at ingest from the authenticated pusher
- [x] `Problem` provenance: owner set by ingest path, origin platform, pusher
- [x] Add `TechniqueClaim` — the record exists; nothing writes it yet
- [x] One claim per attempt naming every technique it used. A revision
      replaces the whole set
- [x] Claim source on `TechniqueClaim`, required, plus model and prompt
      version on a machine claim. Re-deriving has to know which are stale
- [x] `Attempt.origin`: push API or engine drill loop, stamped by the ingest
      path. Whether a test run backs the verdict is a separate fact
- [x] `Attempt.source_status`: the platform's own status, verbatim. A timeout
      and a wrong answer both land as unsolved
- [x] `started_at`, `time_to_solve_sec` and `code` optional. A backfill that
      rejects the backlog is worth less than one that counts it
- [x] Drop `Attempt.session`. A sitting is grouped on read, so the field would
      store a derived view on an append-only record

### Techniques
- [x] Scaffold project
- [x] Technique vocabulary as a data file under `src/algo_coach/`, so it ships
      in the built wheel
- [x] `is_known` for the write path only. In the model, a retired code would
      make historical records unreadable

### Push API
- [x] Ingest `Attempt`: validate, append, no-op on re-push. A batch ingests
      per record, so one bad line costs itself
- [x] Stamp `id` and `user_id` from the adapter, dropping client values
- [x] `algo-coach push <attempts|problems> <file|->`, `--user` standing in for
      authentication
- [x] Ingest `Problem`: validate and upsert. A re-push refreshes the
      descriptive fields and never moves the minted id
- [x] Drop client-supplied owner, id, user_id and techniques
- [x] Map `source_tags` to engine `techniques`, re-derived on every push. An
      unmapped tag produces no code
- [x] Resolve `problem_external_id` to the minted `problem_id`, rejecting what
      does not resolve. Problems are pushed first
- [x] `AttemptPush` and `ProblemPush` as the contract clients copy. Engine
      fields have nowhere to arrive, so the type enforces the stripping

### CLI
- [x] Retire `cards seed`. It wrote technique codes into the cards store, and
      the vocabulary ships in git now

### Drill board
- [x] Resolve an attempt's techniques: its claim if one exists, otherwise the
      problem's. Read-time only, so re-deriving the mapping reaches everything
- [x] Per-technique view: attempt count, recency, solved/unsolved, self-label
- [x] `algo-coach board` CLI command
- [x] Count the backlog's multi-tag share, which sets how badly Phase 3's
      classifier is needed. Over 485 problems: 61 map to no technique, 183 to
      one, 241 to two or more
- [x] Close the vocabulary gaps that count exposed: `tree`, `binary-tree` and
      `binary-search-tree` reached no code. Non-algorithmic tags stay unmapped

### Exit
- [x] A week of real attempts in the store, board rendering from them. 1785
      attempts over 117 practice days, 159 of them in the last 30
- [x] The board renders 25 technique rows, and 101 attempts reach none

## Phase 2 — drill loop on a pushed problem — superseded

Flow and its rules: `docs/architecture/README.md`, "Drill loop".

- [x] Pick a technique from the stale-ordered board, then a problem for it —
      least recently attempted first, lowest solve rate breaking a tie
- [x] Hand over the problem's origin URL and what the log says about it
- [x] `algo-coach drill` — the whole flow, prompting and rendering only.
      Invalid input re-asks, EOF ends the drill wherever it stands

The rest extends that command.

- [x] Wait for the user to push, then diff the log for what appeared against
      that problem. Exact, since the loop knows what was there before
- [x] Ask for a claim and a self-label on each attempt that appeared, the
      drilled technique pre-filled. `a` takes the defaults for the rest, `s`
      records nothing, EOF keeps whatever already landed
- [x] Nothing pushed, nothing recorded: wait again or end, never hold the
      answers against a record that may not arrive

### Closed
Superseded by Phase 8. The platform serves, times and judges, so this loop can
never verify a submission or time a sitting it did not witness. Phase 8 asks
the same two questions of an attempt the engine witnessed.

## Phase 3 — technique attribution — done

Which techniques a solution used. The evidence is the code and the code does
not decay, so the classifier can be scored against a hand answer given
retroactively. Whether two careful readers agree is what the scoring asks, not
what licenses it. Why an attempt failed is a different kind of question, and
moved to Phase 9.

### Hand claims

An eval set and the correction path, never training data, since nothing is
trained. The board's numbers decide what gets drilled, so a classifier nothing
checks sends practice somewhere unverified for weeks.

- [x] `algo-coach claim` — the loop's technique question over sampled
      attempts, no drill and no push. Offers only what a claim would decide:
      unclaimed, carrying code, on a problem whose tags leave a choice
- [x] Sample one attempt per problem. A retry asks the identical question, so
      counting both would weight that problem twice
- [x] Of a problem's attempts, the latest carrying code: the solution that
      stands. The collapse runs before the claimed filter, so a claimed problem
      does not return through an older sibling
- [x] Drawn from problems carrying two or more tags, and spread across
      techniques so any prefix is spread and `--count` needs no quota. The seed
      chooses within a technique, not across
- [x] Label before running the classifier. Reviewing its answers is the same
      labour but anchors on them, and a plausible wrong call gets accepted
- [x] Claim the next batch blind, since the first thirty were revised against
      readings and no longer measure agreement independently. 100 attempts
      claimed, every one of them blind on its first claim

### Technique attribution

- [x] Classifier picks among the problem's own tags rather than classifying
      freely. The response schema enforces them; thinking is not constrained,
      so a reading meets the candidates only at emission
- [x] Write the verdict as a `TechniqueClaim`, source `classifier`. Reject a
      code `is_known` rejects, whole rather than per code, since half a set is
      a set nobody made
- [x] `algo-coach classify` over the stored log, newest first, resuming rather
      than paying twice. All 1785 attempts carry code
- [x] `algo-coach score` against the hand claims per technique, by set
      equality. Writes nothing: a machine claim on a hand-claimed attempt would
      be the later record
- [x] Report over-claiming and under-claiming apart, and print every
      disagreement. They want opposite fixes, and a mislabelled hand claim
      surfaces nowhere else
- [x] `algo-coach movement`: the board with the classifier's claims against
      the board without them, needing no hand claim and no call. A sanity
      check, never a criterion
- [x] `classify --redo` re-derives stale machine claims, leaving user claims
      untouched. Unclaimed first: a first claim buys a number the board does
      not have
- [x] An unchanged verdict is still written, or the agreement is paid for
      again on every later run

### Storing what the classifier read

- [x] Resolve a claim user-first rather than latest-wins, so a machine claim
      lands without superseding. Changed while the two sets were still
      disjoint, so no board number moved
- [x] `effort` and `prompt_hash` required beside model and prompt version. The
      25 machine claims already written were deleted rather than re-derived: a
      partly-known configuration compares with nothing
- [x] `is_stale` compares model, effort and prompt version, not the hash. The
      hash would re-derive the backlog for a reflowed sentence
- [x] `score` stores what it reads, and reads only what it has no reading for
      at this configuration. A stored reading is free to score again
- [x] `--limit` caps the reads, not the attempts scored
- [x] Collapse the eval set to one attempt per problem, which the doc said and
      the code did not
- [x] Count an undecided verdict rather than scoring it
- [x] `score --model`, over the attempts both configurations read. Each one's
      own sample would score against a different denominator
- [x] A `Configuration` value object. A lookup key threaded as four keywords
      is one a caller can get half right
- [x] `--effort` alternating with `--model`, so which followed which survives.
      No `--prompt-version`, which would relabel the same prompt text
- [x] `--stored` makes no call and asks for no credentials, so a comparison is
      reproducible once the reads are paid for
- [x] Fan the calls out, keep one writer: `--concurrency` on `classify` and
      `score`. The write left the worker so the log cannot tear
- [x] Abort counts consecutive failures by the order answered, costing up to
      `concurrency` of them on a broken key
- [x] The progress index counts answers rather than positions, which jump
      about with calls in flight
- [x] Key reuse on what an attempt was sent, not on a rulebook version. An
      author can forget to bump a version while the text moves; a digest
      cannot. Editing one entry re-derived 7 of 31
- [x] `prompt_version` is gone. It cost a rulebook that can no longer be cited
      by name
- [x] `--fresh` asks anyway, which measuring a model against itself needs
- [x] A call log below the claims: model, effort, prompt, digest, response,
      reasoning, tokens, error. Domain-free, and holding the declines, failures
      and costs a claim cannot

### What a code means

Twelve configurations spanning a 10x price range scored within two attempts of
each other and failed in the same cells, so the model was never what to change.
The vocabulary is 27 bare codes, and the prompt asks one question of all of
them. That question is well posed for a procedure, and means something else for
a structure, a paradigm and a problem class.

- [x] Give each code its kind, what earns it, and the near miss it is confused
      with. The near miss decides cases: nothing failed for want of knowing
      what a traversal is
- [x] Render them beside the candidates rather than into the system text,
      which every call pays for whether or not the code is a candidate
- [x] Report per-decision agreement beside the share. Set equality compounds a
      per-candidate error: 95% of calls reads as 87% over three candidates
- [x] The candidates are the denominator, since declining a code correctly is
      a decision the share never credits
- [x] Render a kind as its test rather than its name. No measured gain at
      version 4, and kept on its own argument
- [x] Hash the instructions and the criteria together — landed as a digest of
      the whole payload, per attempt, which subsumes the version with it
- [x] Measure a configuration against itself: three `--fresh` passes. 1 of 31
      attempts flips for opus, 3 for haiku and sonnet — 0.5-2.2% of decisions
- [x] Read the calibration set after each criteria edit. It cannot measure
      quality, having helped write the criteria
- [x] Show the reader the same criteria the classifier gets. Otherwise a
      disagreement is ambiguous between an unclear rule and two different ones

### What a claim was made against

Nothing recorded whether a hand claim was made before or after a reading of the
same attempt, and the user's latest wins. A revision asked with the readings in
view therefore became, silently, what that reading was scored against.

- [x] `informed_by`: the calls shown when the claim was made, empty for a
      blind one. Named one by one, since a claim informed by one configuration
      still measures another
- [x] `confidence`, a level rather than a float, asked on the hand pass alone.
      Empty leaves it unsaid rather than defaulting to the middle
- [x] `--disputed` unset rather than 1, so the pool is every claim. Offering
      only what a classifier contests corrected the hand claims in one
      direction
- [x] The log answers it anyway: `claimable` offers unclaimed attempts and
      `revisable` claimed ones. 138 claims over 100 attempts, so 38 revisions

### Adjudicating the eval set

Flow and its rules: `docs/architecture/README.md`, "Adjudicating the eval set".

- [x] Read the 62 hand-claimed attempts with a frontier configuration, stored
      as readings. Nothing is added to the blind pass while a reading is in view
- [x] Resolve every divergence by hand, one at a time: the criterion is edited
      or the claim is. `claim --revise --disputed 1` is the queue
- [x] Re-read the attempts a criteria edit reaches, until the frontier
      disagrees with nothing. That is the stopping signal, not a score

### Closed
- [x] Attribution runs and its claims stand, with the board consuming them.
      Whether it beats the tag fallback is measured in Phase 9

## Phase 4 — cards and template matching — done

How studying a technique is organised. Not an ability estimate. Mastery is what
a user can solve, per technique, and it is Phase 9.

- [x] `Card`: the topic, its templates, and the selector a ladder resolves
      from. Names no problem, so it ships anywhere. Several per technique
- [x] Port the authoring skill onto the structured card. Nine cards ported,
      each authored blind and then compared against the hand-written one. The
      diffs are what the skill's rules are
- [x] Every code template runs against a brute force before it lands
- [x] `statement` on `ProblemPush` and `Problem`, optional. Landed before
      anything read it, since every earlier export is a corpus that has to be
      re-pushed
- [x] Tightened to required and non-blank at 485 of 485. A missing statement
      is a problem nothing can ever match, and nothing reported it
- [x] `provider` on `Call`, optional: who actually served the request, which
      the model id stops answering the moment anything routes
- [x] Replace the Anthropic transport rather than adding beside it. The request
      shape and the response walk move behind a neutral `Reply`. One shape at a
      time, by rule
- [x] Read models through OpenRouter as the only transport: `response_format`
      for the schema, `reasoning` for the effort, key and base URL from config
- [x] Pin the route rather than taking what it offers: `require_parameters` on,
      fallbacks off, and the serving provider recorded on the call
- [x] `temperature` on the configuration, the call and the claim, greedy by
      default. `None` is the provider's own default, a named arm that keeps
      earlier readings scorable rather than discarded
- [x] The pinned endpoint on all three, and required. A model id resolves to as
      many builds as there are endpoints serving it, and quantization changes
      the weights
- [x] Seed from files through a path that stays a boundary
- [x] `TemplateMatch`: one record per template and problem, not a set per
      template. Problems arrive a push at a time
- [x] The negative is stored, or every re-run re-tests every non-match forever
- [x] Provenance shared with the claim as `MachineProvenance`. The question
      differs; what a re-run must know to supersede a reading does not
- [x] Lift the driver the run loops share, the fan-out and the abort limit out
      of `claims`. How many calls are in flight is not a fact about what is
      being read
- [x] Match the corpus against a card's templates after import. One call per
      problem and card, candidates in and the subset out, records per pair
- [x] Pre-filter by technique, or it is every template against every problem
      for an answer that is almost always no
- [x] Exclude procedure templates: a framing procedure is exercised by
      everything its technique reaches
- [x] Its own configuration, not the claim classifier's, since the two ask
      different questions
- [x] Time a call at both levels: what the caller waited and how many requests,
      beside the last request's own time. Without the count, a run held behind
      a per-minute cap read as a slow model
- [x] A hand match: `MatchSource.USER`, carrying no provenance. Nothing
      re-derives it, which is what makes it the reference
- [x] Sample what to annotate: unannotated questions first, spread across
      templates rather than cards. Counted per card, the three
      dynamic-programming cards would carry the set
- [x] A seed, so an order is reproducible. It chooses within a template, as
      the claim sample chooses within a technique
- [x] `--card` narrows the sample, which is what a card just added asks for.
      The counts still read the whole reference, or a card's forms would look
      untouched beside nothing
- [x] `algo-coach annotate` — the statement and the card's templates numbered,
      answered at once, one record per template. Reading a statement once to
      judge five forms is the cheap order
- [x] Blind by default, with the matcher's verdict shown only on request, as
      `claim --revise` shows a reading
- [x] `0` for none, opened per caller. A problem exercising no form is a
      verdict on every pair, and an empty claim must stay distinct from a
      stated one
- [x] The whole corpus synced, ~4k problems against 485, every statement
      non-blank. The field tightened last phase held across an eight-fold push

### Closed
- [x] Cards are authored into `content/` and seeded, the matcher reads the
      corpus against their templates, and the annotation pass writes the
      reference its readings are scored against
- [x] The ladder, runs, recall and probes wait on a corpus that can fill them,
      and are Phase 7. What measures the matcher is Phase 6

## Phase 5 — pivot to generated problems (current)

The engine writes its own problems, so a second ingest path is dead weight.
The work splits by precondition: the doc settles the shape, the ingest path
goes, and the records tighten only once the store holds nothing carrying the
loose shape.

### Docs first
- [x] The architecture doc pivots to an owned corpus: the engine writes the
      problem, the cases that decide it and the canonical that passes them.
      The owner distinction went, and origin decides what a problem carries
- [x] Re-sequence the phases around that corpus, and amend the exit rule. A
      phase exits when its deliverable is in use by whatever consumes it, and
      `superseded` joins `done` as a way to close
- [x] Keep a TODO item to a line or two, splitting before compressing. The
      argument behind an item belongs in the architecture doc
- [x] The architecture doc drops the push boundary and the pushed-problem
      rules. It still says the push API is a second ingest path, which stops
      being true here
- [x] Problems, Attempts, Boundaries and Invariants each carry a rule that
      exists because two origins did. Each states what one origin makes of it,
      or goes
- [x] `README.md` drops the push API from what the engine exposes

### Archive
- [x] Move the pushed corpus and log to `data/old/`: 1785 attempts, 3962
      problems, the claims and the call log

### The ingest path
- [x] Remove `algo-coach push` and the `ingest` package
- [x] Remove `AttemptPush` and `ProblemPush`. The payload contract has no
      reader once nothing is pushed
- [x] Remove the external-id resolution. Every reference is engine-minted once
      nothing arrives from outside
- [ ] Remove the tag mapping. A generated problem derives its techniques from
      its canonical solutions, and there is no platform vocabulary left to map
- [ ] Remove the superseded drill loop: the push wait and the log diff. Neither
      act has a subject once nothing is pushed
- [ ] Drop the tests that covered the removed paths, rather than adapting them
      to a shape nothing produces

### The reset
- [ ] Empty the live store. The 138 hand claims over 100 attempts go with it,
      and a later classifier is scored against a set rebuilt by hand on
      generated problems
- [ ] Tighten the records only after the store is empty: `origin: push`,
      `source_status`, `external_id` and the platform fields. Legal only while
      nothing stored carries the loose shape

### Exit
- [ ] One origin end to end: nothing ingests a third-party record, no doc
      describes a path that does, and the store holds only what the engine
      wrote

## Phase 6 — problem generation

The engine writes problems: a statement, the test cases that decide it, and at
least one canonical solution. Flow and its rules:
`docs/architecture/README.md`, "Generating a problem".

The matcher lands first. Generation asserts a match and the matcher audits it,
so an unmeasured matcher would audit at an unknown error rate.

- [ ] Score the matcher per pair, grouped per template, over the pairs both
      read. Not as a set: a match asserts a pair
- [ ] Report the positive verdicts in both directions. Accuracy would score a
      matcher that names nothing in the nineties
- [ ] Skip a pair the hand settled on the run path, and read it in the eval.
      The skip needs every template of the card settled, since the call asks
      about the card whole
- [ ] The first hand pass calibrates and a blind one measures, the claims rule
      unchanged. A score over the pairs that drew the line is agreement with
      itself
- [ ] `generated_for` on `Problem`, naming the template it was written for. An
      assertion rather than a reading, which is what makes the first
      `TemplateMatch` provenance
- [ ] `TestCase` and `CanonicalSolution`, written with the problem in one
      call. Cases derived afterwards describe whatever the solution happens to
      do
- [ ] The canonical carries how many cases passed, out of how many. A count
      rather than a flag, as a share prints its denominator
- [ ] The runner: execute a solution against a problem's cases locally, pass or
      fail per case. One subject today, a canonical, and an attempt on the same
      path in Phase 8
- [ ] `algo-coach generate`, a template in and a problem out, through the
      transport the classifier and the matcher already share
- [ ] Sampled rather than greedy, so one model's habits do not become the
      whole corpus. The cost is a canonical that is re-runnable and never
      reproducible
- [ ] Nothing lands half-verified. A problem whose canonical fails is discarded
      whole, and the call is recorded either way
- [ ] Derive a generated problem's techniques from its canonical solutions,
      beside the tag mapping rather than replacing it. A view, so adding a
      canonical can widen the codes
- [ ] Settle the discrimination bar on a real corpus. Cases that separate
      nothing license `verified` on a canonical that is wrong
- [ ] Measure the announcement floor against the archived corpus in
      `data/old/`, then read the generated one against it. A form the matcher
      names from the statement alone was telegraphed

### Exit
- [ ] A card's reported gaps are filled by generated problems, and Phase 7
      resolves a ladder over them

## Phase 7 — ladder, recall and card runs

- [ ] Resolve the ladder from the matches, the selector filling out to `size`
- [ ] Derive requiredness from what a rung covers: studied means required, the
      optional template alone means optional, both means required with the
      optional template offered as the alternative
- [ ] Resolve the ladder at import, and never rewrite one a card has already
      been started on
- [ ] Report a studied template no problem matches. The card claims to teach
      that form, so a corpus that cannot exercise it is a fact about the store
- [ ] `CardRun`: starting is explicit, since the ladder is measured from it.
      Holds when it began and the probes assigned; later probes append
- [ ] A recall attempt is its own record, keyed to a card and a template. There
      is no problem and no submission. What was hinted before a pass is part of
      it
- [ ] Generate probes from the corpus. A skill now, since it is judgment, and
      possibly an agent later
- [ ] The trainer: names hidden, blank-filed cold, run against the card's own
      tests, never printing the template
- [ ] Card status — recalled when, ladder outstanding, probes available. The
      inputs a graduation rule reads, and no threshold

### Exit
- [ ] Recall and the ladder run daily

## Phase 8 — in-engine drill loop

The first attempts the engine produces itself.

- [ ] Serve a generated problem, time the sitting, run the submission against
      the problem's own cases, and mint the attempt
- [ ] The verification result on `Attempt`. Additive, and meaningless before
      Phase 6
- [ ] Ask for a claim and a self-label as Phase 2 asked them. What changes is
      who witnessed the sitting, not who writes

### Exit
- [ ] Daily practice runs here, on problems the engine wrote and judged

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] The annotator against themselves as the ceiling: a re-pass over thirty
      attempts, readings hidden. Triggered when mastery estimation reads
      claims, and a wrong one starts spending practice time
- [ ] Read the architecture doc against the code, landing every divergence
      here. The goal is not that none exists, since the doc is target state.
      The goal is that none is unknown
- [ ] Classify freely over the whole vocabulary and intersect in code, once the
      hand claims can score it against the constrained one. A verdict outside
      the problem's own techniques is the only signal that they are the gap
- [ ] An outage falls back to another endpoint of the same shape, never to
      Anthropic direct, whose compatibility layer ignores `response_format`,
      `strict` and `reasoning_effort`. Triggered when an outage blocks a run

## Later phases

### Phase 9 — mastery, scheduling, failure mode
- [ ] Rust against gap is a question about per-technique state, asked of a
      single attempt. Only whether the technique was ever fluent separates
      them, so it lands with the mastery model or not at all
- [ ] Settle `SPEED` before anything writes it. "Solved but too slowly" is
      about the user, a timeout is about the solution's complexity, and only
      the second is in the record
- [ ] Narrow the failure classifier to what the record supports: a mechanical
      slip against a conceptual miss. A four-way router would ask it for what
      it cannot see
- [ ] Write the verdict as a `Diagnosis` with model and prompt version. It
      never supersedes a self-label, because the eval scores one against the
      other
- [ ] Eval per mode rather than overall, against self-labels the loop
      produced. A router that only ever says `gap` would score well on a corpus
      of gaps

