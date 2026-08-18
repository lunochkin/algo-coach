# TODO

## Phase 1 — push API + techniques + drill board

### Schema (before the first real ingest)
- [x] `user_id` on `Attempt`, stamped at ingest from the authenticated pusher
- [x] `Problem` provenance: owner set by ingest path, origin platform, pusher
- [x] Add `TechniqueClaim` — the record exists; nothing writes it yet
- [x] One claim per attempt naming every technique it used, since a solution
      can use several and a revision has to replace the whole set
- [x] Claim source on `TechniqueClaim`, required, plus model and prompt
      version on a machine claim. Not deferred: "attribution is always
      automatic" is an assumption the log would be stuck with, and re-deriving
      needs to know which machine claims are stale
- [x] `Attempt.origin`: push API or engine drill loop, stamped by the ingest
      path. Whether a real test run backs the verdict is a separate fact,
      recorded when the engine can first verify anything
- [x] `Attempt.source_status`: the origin platform's own status, verbatim. A
      timeout and a wrong answer both land as unsolved, and Phase 3 cannot
      recover the difference from a boolean
- [x] `started_at`, `time_to_solve_sec` and `code` optional — a platform gives
      the submission time and often nothing else, and a backfill that rejects
      the backlog is worth less than one that counts it
- [x] Drop `Attempt.session`: a sitting is grouped from the log on read, so a
      client-set field would be a derived view stored on an append-only record

### Techniques
- [x] Scaffold project
- [x] Technique vocabulary as a data file under `src/algo_coach/`, so it ships
      with the package. Checked in the built wheel
- [x] `is_known` for the write path only — in the pydantic model, a retired
      code would make historical records unreadable

### Push API
- [x] Ingest `Attempt`: validate, append, no-op on re-push. A duplicate is not
      an error, and a batch ingests per record, so one bad line costs itself
- [x] Stamp `id` and `user_id` from the adapter, dropping client values
- [x] `algo-coach push <attempts|problems> <file|->`, `--user` standing in for
      authentication
- [x] Ingest `Problem`: validate, upsert as user-owned. A re-push refreshes
      the descriptive fields and never moves the minted id
- [x] Drop client-supplied owner, id, user_id and techniques
- [x] Map `source_tags` to engine `techniques`; an unmapped tag produces no
      code. Re-derived on every push, so a mapping change reaches stored
      problems
- [x] Resolve `problem_external_id` to the minted `problem_id`, rejecting what
      does not resolve. Problems are pushed first; re-pushing after they land
      is a no-op on what ingested
- [x] `AttemptPush` and `ProblemPush` as the contract clients copy. Engine
      fields have no field to arrive in, so stripping is enforced by the type
      rather than a hand-kept name list

### CLI
- [x] Retire `cards seed` — it wrote technique codes into the cards store, and
      the vocabulary ships in git now

### Drill board
- [x] Resolve an attempt's techniques: its claim if one exists, otherwise the
      problem's. Read-time only — never stored, so re-deriving the tag mapping
      reaches every unclaimed attempt
- [x] Per-technique view: attempt count, recency, solved/unsolved, self-label
- [x] `algo-coach board` CLI command
- [x] Count how much of the backlog carries more than one tag — it sets how
      badly Phase 2's classifier is needed. Measured over 485 problems: 61 map
      to no technique, 183 to one, 241 to two or more. Fallback attribution
      over-credits half the corpus
- [x] Close the vocabulary gaps the count exposed: `tree`, `binary-tree` and
      `binary-search-tree` reach no code, so their attempts group nowhere.
      Non-algorithmic tags (database, dataframe work) are correctly unmapped
      and stay that way

### Exit
- [x] A week of real attempts in the store, board rendering from them. 1785
      attempts over 117 practice days, 159 of them in the last 30; the board
      renders 25 technique rows, and 101 attempts reach no row

## Phase 2 — drill loop

Flow and its rules: `docs/architecture/README.md`, "Drill loop".

- [x] Pick a technique from the stale-ordered board, then a problem for it —
      least recently attempted first, lowest solve rate breaking a tie
- [x] Hand over the problem's origin URL and what the log says about it. The
      card shown before it is Phase 4; the loop runs without a brief until then
- [x] `algo-coach drill` — the whole flow, prompting and rendering only.
      Invalid input re-asks, EOF ends the drill wherever it stands

The rest extends that command.

- [x] Wait for the user to push, then diff the log for what appeared against
      that problem — exact, since the loop knows what was there before
- [x] Ask for a claim and a self-label on each attempt that appeared, the
      drilled technique pre-filled and the previous answer carried forward.
      `a` takes the defaults for the rest, `s` records nothing for that
      question, and EOF keeps whatever already landed
- [x] Nothing pushed, nothing recorded: wait again or end, never hold the
      answers against a record that may not arrive

### Exit
- [ ] The loop runs on real daily attempts

## Phase 3 — technique attribution

Which techniques a solution used. The evidence is the code and the code does
not decay, so the classifier can be scored against a hand answer given
retroactively. Whether two careful readers agree is what the scoring asks, not
what licenses it. Why an attempt failed is a different kind of question and
moved to Phase 5.

### Hand claims

An eval set and the correction path — never training data, since nothing is
trained. Retroactive on purpose: the evidence is the code, and the code is
still there. The board's numbers decide what gets drilled, so a classifier
nothing checks sends practice somewhere unverified for weeks.

- [x] `algo-coach claim` — the loop's technique question over sampled
      attempts, no drill and no push. Writes a `TechniqueClaim`, source `user`.
      Offers only what a claim would decide: unclaimed, carrying its code, on
      a problem whose tags leave a choice
- [x] Sample one attempt per problem, not per attempt: a backfill retries the
      same problem, and a repeat asks the identical question — same code, same
      candidate tags — so counting both weights that problem twice. Per problem
      rather than per sitting, since a retry months later repeats it too, and
      sittings land with the mastery model
- [x] Of a problem's attempts, the latest carrying code — the solution that
      stands. An earlier one may show an approach that was abandoned, and the
      claim worth scoring is the one the board credits. A claimed problem does
      not return through an older sibling: the collapse runs before the
      claimed filter, not after
- [x] Drawn from problems carrying two or more tags — where attribution has
      something to decide — and spread across techniques so no single one
      carries the estimate. Each draw takes the technique the order has covered
      least, so any prefix is spread and `--count` needs no quota; an attempt
      counts toward every tag its problem carries, since one claim decides all
      of them. The seed chooses within a technique, not across, so a sample is
      still described by its seed
- [x] Label before running the classifier. Reviewing its answers is the same
      labour, but anchors on them: a plausible wrong call gets waved through.
- [ ] Claim the next batch blind, stopping at whichever count answers the
      question: thirty separates usable from broken, a hundred narrows the
      interval. Blind because the first thirty were revised against the
      classifiers' readings and no longer measure agreement independently

### Technique attribution

- [x] Classifier picks among the problem's own tags rather than classifying
      freely, so it can narrow what a problem could exercise but never invent
      a technique the tags do not name. The response schema enforces them; the
      prompt names them too, since thinking is not schema-constrained and a
      reading made without knowing the candidates meets them only at emission
- [x] Write the verdict as a `TechniqueClaim`, source `classifier`, with model
      and prompt version. Reject a code `is_known` rejects — the only write
      path that could introduce one. Whole rather than per code, since a claim
      asserts one set and half of it is a set nobody made
- [x] Run it over the stored log, not only over fresh practice: every one of
      the 1785 attempts carries its code, so the whole backlog is classifiable
      today. `algo-coach classify`, newest first so a capped run improves what
      the board shows, resuming on the next run rather than paying twice
- [x] Score against the hand claims per technique, by set equality — the board
      is per technique, and a claim naming every candidate would pass a metric
      that only asks whether the right code appears. `algo-coach score`, which
      writes nothing: a machine claim on a hand-claimed attempt would be the
      later record, and the latest wins on read
- [x] Report over-claiming and under-claiming apart, since they want opposite
      fixes, and print every disagreement — the hand claims are ground truth by
      construction rather than by being right, so reading the disagreements is
      the only place a mislabelled one surfaces
- [x] Report the board with the classifier's claims against the board without
      them, per technique. `algo-coach movement`, needing no hand claim and no
      call: narrowing two or three candidates to one removes credit by
      arithmetic, so a row that barely moves is one the classifier never
      declined to name. A sanity check, never a criterion — movement says it
      decided something, and only the hand claims say it decided right
- [x] Re-derive stale machine claims by model and prompt version, leaving user
      claims untouched. `algo-coach classify --redo`, since a re-derivation
      costs a call per attempt: unclaimed first, because a first claim buys a
      number the board does not have and a re-derivation only revises one it
      does. Compared whole rather than ordered, so running an earlier prompt
      rolls back by the same path. An unchanged verdict is still written —
      the record names the classifier that reached it, and an unwritten
      agreement would be paid for again on every later run

### Storing what the classifier read

- [x] Resolve a claim user-first rather than latest-wins, so a machine claim
      lands on a hand-claimed attempt without superseding it. No attempt
      carries claims from both writers today, so the rule changes no number
      the board shows — which is the moment to change it, while the two sets
      are still disjoint. `standing_claims` beside `resolve_techniques`,
      calling `latest_by_attempt` once per writer: in what order is the log's
      question, who wins is the record's
- [x] `effort` and `prompt_hash` on the record beside model and prompt
      version. Required rather than optional, which the 25 machine claims
      already written paid for: they were deleted rather than re-derived,
      since an optional provenance field is one every reader branches on
      forever and a partly-known configuration compares with nothing. The
      ambiguity was disposable then and is permanent once the eval set is
      read at scale
- [x] `is_stale` compares model, effort and prompt version — not the hash,
      which would re-derive the backlog for a reflowed sentence
- [x] `score` stores what it reads, and reads only what it has no reading
      for at this configuration. Scoring is already a pure function over two
      mappings, so it splits into reading and scoring rather than being
      rewritten. `--limit` caps the reads, not the attempts scored: a stored
      reading is free. Reuse keys off the version, as staleness does, so a
      reused reading from another prompt text is reported — the only thing a
      forgotten bump says. Two decisions came with it: the eval set collapses
      to one attempt per problem, which the doc said and the code did not,
      and an undecided verdict is counted rather than scored
- [x] `score --model`, over the attempts both configurations read. Comparing
      each one's own sample scores against a different denominator, and the
      number would read as quality. Repeatable, and one command: a comparison
      of one is the ordinary score, since intersecting one set is that set, so
      only the rendering branches. Each is scored against the hand claims and
      never against another — the column beside it buys the shared denominator.
      Three decisions came with it: a `Configuration` value object, since a
      lookup key threaded as four keywords is one a caller can get half right;
      `--effort` alternating with `--model` so which followed which survives,
      and no `--prompt-version`, which would relabel the same prompt text; and
      `--stored`, which makes no call and asks for no credentials, so a
      comparison is reproducible once the reads are paid for

- [x] Fan the calls out, keep one writer. `--concurrency` on `classify` and
      `score`, since a backlog run is hours of waiting on a network. The write
      left the worker so the log cannot tear; abort counts consecutive failures
      by the order answered, costing up to `concurrency` of them on a broken
      key; and the progress index counts answers rather than positions, which
      jump about with calls in flight

- [x] Key reuse on what an attempt was actually sent, not on a rulebook
      version. A criterion travels with its candidate, so editing one entry
      re-derives the attempts carrying it and no others — 7 of 31 on the last
      edit. `prompt_version` is gone: a word can be forgotten while the text
      moves, a digest cannot. Costs a reflow re-deriving what it reaches, and a
      rulebook that can no longer be cited by name. `--fresh` asks anyway,
      which measuring a model against itself needs. 961 machine claims dropped
      to land it; the 48 hand claims are the only irreplaceable thing there
- [x] A call log below the claims: model, effort, prompt, digest, response,
      reasoning, tokens, error. Domain-free, so a second consumer needs no
      teaching, and it holds what a claim cannot — declines, failures, and what
      a run cost. The prompt is stored whole beside its digest, so a record
      digests to its own key. Claims cite a call and decide for themselves
      whether to ask again, so nothing on the run path reads it back

### What a code means

Twelve configurations spanning a 10× price range scored within two attempts of
each other and failed in the same cells, so the model was never the lever. The
vocabulary is 27 bare codes and the prompt asks one question of all of them,
which is well posed for a procedure and means something else for a structure, a
paradigm and a problem class.

- [x] Give each code its kind, what earns it, and the near miss it is confused
      with. The near miss is the load-bearing half: nothing failed for want of
      knowing what a traversal is, and everything failed for want of a rule
      that descending-and-pruning is not one. Written to stand on a
      complexity, redundancy or definitional argument that would hold if no
      model had ever run — a criterion whose only support is that the
      classifiers agreed has been written backwards
- [x] Render them beside the candidates rather than into the system text,
      which every call pays for whether or not the code is a candidate. The
      three worked examples the system text carries today are per-code
      criteria in the wrong file and move into their entries
- [x] Report per-decision agreement beside the share. Set equality compounds a
      per-candidate error over the candidate count — 95% of calls reads as 87%
      over three candidates — and the candidates are the denominator, since
      declining a code correctly is a decision the share never credits. The
      ladder is 90/95/98/99% across haiku, sonnet, opus and fable: the top
      three are within one label
- [x] Render a kind as its test rather than its name — a label helps only a
      reader who already knows what it selects. No measured gain at version 4:
      the cell it targeted is unchanged, sonnet lost three decisions, opus sat
      at ceiling. Kept on its own argument. The contrast with the Kahn fix is
      the lesson — a repeated cell is fixable by a rule, scattered errors are
      not
- [x] Hash the instructions and the criteria together — landed as a digest of
      the whole payload, per attempt, which subsumes this and the version with
      it
- [x] Measure a configuration against itself — three passes with `--fresh`. 1
      attempt of 31 flips for opus, 3 for haiku and sonnet: 0.5–2.2% of
      decisions. A one- or two-attempt difference is unreadable; only the tier
      gaps clear it. Flips are not random — four of six land on
      `binary-search-tree` or `tree-traversal` boundaries
- [x] Read the calibration set after each criteria edit. It cannot measure
      quality, having helped write the criteria, but it answered the diagnostic
      question: both systematic cells cleared — Kahn for every configuration,
      backtracking for the three that fell in — while the one edit aimed at a
      mechanism inferred from scattered errors moved nothing. The rule that
      came out of it: a cell several readers hit the same way is fixable by a
      rule, and scattered errors are not
- [x] Show the reader the same criteria the classifier gets. One rulebook and
      two annotators is what makes their disagreement mean something: without
      it, a disagreement is ambiguous between an unclear rule and two
      different ones

### What a claim was made against

Nothing recorded whether a hand claim was made before or after a reading of the
same attempt, and the user's latest wins — so a revision asked with the readings
in view silently became what that reading was scored against. Recorded now;
reading it back is the deferred measurement's.

- [x] `informed_by`: the calls shown when the claim was made, empty for a blind
      one. Named one by one rather than flagged, since a claim informed by one
      configuration still measures another. Not provenance — that is what
      produced a claim, this is what its author saw
- [x] `confidence`, a level rather than a float, asked on the hand pass alone:
      the drill loop's economy is one keystroke per claim. Empty leaves it
      unsaid rather than defaulting to the middle
- [x] `--disputed` unset rather than 1, so the pool is every claim. Offering
      only what a classifier contests corrected the hand claims in one
      direction. Ordering unchanged, most disputed first
- [x] Not backfilled, nothing left to name: the readings those revisions saw
      went with the 961 and their calls predate the call log. The timestamp
      rule was the unsafe direction — no surviving machine claim predates any
      revision, so it stamps all 79 blind
- [x] The log answers it anyway. `claimable` offers only unclaimed attempts and
      `revisable` only claimed ones, so a first user claim was blind and every
      later one saw readings: 79 claims, 62 attempts, 17 revisions

### Exit
- [ ] Attribution runs on real daily attempts and its claims stand. Whether the
      classifier beats the tag fallback is measured when mastery estimation
      reads claims, not here

## Phase 4 — cards (current)

How studying a technique is organised. Not an ability estimate: mastery is what
a user can solve, per technique, and it is Phase 5.

### Phase 4a — cards and recall
- [x] `Card`: the topic, its templates, and the selector a ladder resolves
      from. Names no problem, so it ships anywhere. Several per technique
- [x] Port the authoring skill, output retargeted to the structured card. Nine
      cards ported from the practice repo's notes, each authored blind first
      and then compared against the hand-written one — the diffs are what the
      skill's rules are, and every code template runs against a brute force
      before it lands
- [ ] `statement` on `ProblemPush` and `Problem`, optional. Which form a
      problem exercises is a question about what it asks, and tags answer what
      it is about. Landed first on purpose: nothing reads it until matching,
      and every export before it lands is a corpus that has to be re-pushed.
      Obliges re-copying `schema/push.py` into the practice repo — nothing
      detects that drift
- [x] `provider` on `Call`, optional: who actually served the request, which
      the model id stops answering the moment anything routes.
- [x] Replace the Anthropic transport rather than adding beside it. `ask`
      keeps the digest, the call record and the failure path; the request
      shape and the response walk move behind a neutral `Reply`. One shape at
      a time, by rule — two maintained by hand is what invites a library to
      reconcile them, and a normaliser degrades a schema where the reading
      cannot see it
- [x] Read models through OpenRouter, as the only transport: chat completions
      — `response_format` for the schema, `reasoning` for the effort,
      `choices[0].message` and `usage` on the way back, key and base URL from
      config. Pin the route rather than taking what it offers:
      `require_parameters` so a provider that cannot enforce the schema is
      never chosen, fallbacks off so a model id resolves to one backend, and
      the serving provider recorded on the call
- [x] `temperature` on the configuration, the call and the claim, greedy by
      default. Sampling is noise an eval absorbs by repeating and the backlog
      sweep cannot: it writes into an append-only log the board reads forever,
      so the same fraction of a percent is permanent and moves readings a
      criteria edit never touched. Part of the identity where the pinned
      provider is not, so two temperatures are two columns rather than one
      mixed key — and `None` is the provider's own default, a named arm that
      keeps every reading taken before the field scorable instead of discarded
- [x] The pinned endpoint on the configuration, the call and the claim, and
      required. A model id resolves to as many builds as there are endpoints
      serving it, and quantization changes the weights — so unpinned readings
      are a mixture under one key that nothing later can take apart. Compared
      like the model; who actually served it is recorded beside it and never
      compared, since the router names a company and a company serves several
      builds
- [ ] An outage falls back to another endpoint of the same shape, never to
      Anthropic direct. Its OpenAI compatibility layer ignores
      `response_format`, `strict` and `reasoning_effort`, so Claude reached
      that way answers with the schema unenforced and the effort dropped —
      the one guarantee attribution rests on, and one of its eval's axes.
      Claude with enforcement means the native transport, which is the second
      shape the rule above exists to avoid
- [ ] Seed from files through a path that stays a boundary — the private repo
      it moves behind later is a different argument, not a refactor
- [ ] `TemplateMatch`: one record per template and problem, carrying a verdict.
      Not a set per template — problems arrive a push at a time, and a set
      would rewrite settled pairs whenever the corpus grew. The negative is
      stored or every re-run re-tests every non-match forever
- [ ] Match the corpus against a card's templates after import. One call per
      problem and card, candidates in and the subset out, records per pair.
      Pre-filtered by technique, or it is every template against every problem
      for an answer that is almost always no. Procedure templates are excluded:
      a framing procedure is exercised by everything its technique reaches
- [ ] Resolve the ladder from the matches, the selector filling out to `size`.
      Requiredness derived from what a rung covers — studied means required,
      the optional template alone means optional, both means required with the
      optional riding along as the alternative approach
- [ ] Resolve the ladder at import, and never rewrite one a card has already
      been started on
- [ ] Report a studied template no problem matches. The card claims to teach
      that form, so a corpus that cannot exercise it is a fact about the store
- [ ] `CardRun`: starting is explicit, since the ladder is measured from it.
      Holds when it began and the probes assigned; later probes append
- [ ] A recall attempt is its own record, keyed to a card and a template.
      Nothing keys it to an attempt: there is no problem and no submission.
      What was hinted before a pass is part of it
- [ ] Generate probes from the corpus — a skill now, since it is judgment, and
      possibly an agent later
- [ ] The trainer: names hidden, blank-filed cold, run against the card's own
      tests, never printing the template
- [ ] Card status — recalled when, ladder outstanding, probes available. The
      inputs a graduation rule reads, and no threshold

### Phase 4b — what daily use asks for

Candidates, not commitments: a graduation rule, recall windows, a rust jog
short of the full loop. Which of them matters is what 4a's daily use answers.

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] Score template matching. The hand-written cards annotate roughly sixty
      rungs with the template each exercises, which is a labelled set for free
      and the same role the hand claims play for the classifier. Triggered
      when matching runs over the whole corpus rather than one card, since
      before that the cost of being wrong is one ladder

- [ ] Measure attribution against an independent set: the score restricted to
      blind claims, and the annotator against themselves as the ceiling — a
      re-pass over the thirty, readings hidden. Model error, annotator error
      and a rule that cannot be applied are one number today. Scores the first
      claim per attempt, not the standing one, which on 13 of 62 is a revision.
      Triggered when mastery estimation reads claims and a wrong one starts
      spending practice time
- [ ] Reconsider what the eval scores against. `score` takes one reader's
      claims as ground truth, so it measures agreement with a person and caps
      at that person's own consistency. Adjudicated labels, agreement with no
      gold set, or scoring a verdict against the rule it cites would change the
      metric and not the log. Triggered by the measurement above, which is what
      says whether the ceiling binds
- [ ] Read the architecture doc against the code, landing every divergence
      here as an item saying which side is wrong. Not that none exist — the
      doc is target state and code lags it on purpose — but that none are
      unknown: two were found by accident this phase, which is the argument
- [ ] Classify freely over the whole vocabulary and intersect with the tags in
      code, as a second rulebook — when the hand claims can score it against
      the constrained one. An out-of-tag verdict is the only signal
      that the tags are the gap, but both write the same claim, so the choice
      costs one re-run rather than a migration
- [ ] Re-derive stored problems without a push — when the mapping changes for
      problems no longer pushed. A re-push covers it until then
- [ ] Ingest assumes a single writer: two concurrent pushes can both miss the
      same `external_id`. When the web version lands, decide whether the CLI
      writes to the store or calls the API
- [ ] Duplicate detection loads the whole attempt log per call, and
      `by_external` scans every problem file per record; both become queries
      when storage swaps

## Later phases

### Phase 5 — mastery, scheduling, failure mode
- [ ] Rust against gap is per-technique state wearing a per-attempt costume:
      the two failures look identical in the record, and only whether the
      technique was ever fluent separates them. Recall history does not stand
      in — reproducing a form cold is not recognising it unprompted. It lands
      with the mastery model or not at all
- [ ] Settle `SPEED` before anything writes it — "solved but too slowly" is
      about the user, a timeout is about the solution's complexity, and only
      the second is in the record
- [ ] Narrow the failure classifier to what the record supports: reading a
      sitting's code for a mechanical slip against a conceptual miss. A
      four-way router asks it for what it cannot see
- [ ] Write the verdict as a `Diagnosis` with model and prompt version. It
      never supersedes a self-label: the eval scores one against the other
- [ ] Eval per mode rather than overall, against self-labels the loop
      produced — a router that only ever says `gap` would score well on a
      corpus of gaps

### Removed, kept in git
- [ ] The failure classifier and its eval were cut before Phase 1 shipped and
      are Phase 5's to rebuild; git holds what was removed. `Diagnosis` and the
      log's diagnosis methods stayed behind, since records outlive features and
      an append-only log cannot be retrofitted
