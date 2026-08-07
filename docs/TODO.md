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

## Phase 3 — technique attribution (current)

Which techniques a solution used. A checkable question — the code answers it,
and two careful readers agree — so the classifier can be scored against a hand
answer given retroactively. Why an attempt failed is a different kind of
question and moved to Phase 4.

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
      sittings are Phase 4's
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
      Ordering is not what holds it: the hand pass prints the code and the
      problem's tags and never an existing claim, so a machine verdict cannot
      anchor one. A machine claim therefore leaves an attempt in the pool —
      the classifier fills what no hand reached, and only the user's own
      answer settles a problem
- [ ] Thirty separates usable from broken, a hundred narrows the interval.
      Stop at whichever answers the question

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

### Exit
- [ ] Attribution runs on real daily attempts, carrying a measured agreement
      number rather than an asserted one
- [ ] The architecture doc read against the code, every divergence landing
      here as an item. A doc that wins on conflict is only worth having while
      the conflict is known, and the last one — a hand pass that skipped
      machine-claimed attempts, against a doc saying a user claim corrects
      them — surfaced by accident

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] Classify freely over the whole vocabulary and intersect with the tags in
      code, as a second prompt version — when the hand claims can score it
      against the constrained one. An out-of-tag verdict is the only signal
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

### Phase 4 — mastery, cards, failure mode
- [ ] `Card` model and store: teaching content keyed to a technique, several
      per technique, never referenced by the log. Git holds the removed version
- [ ] Seed from the private content repo; read-only at runtime
- [ ] Cards for the techniques the board names weakest, not for all 27
- [ ] Rust against gap is per-technique state wearing a per-attempt costume:
      the two failures look identical in the record, and only whether the
      technique was ever fluent separates them. It lands with the mastery
      model or not at all
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
      are Phase 4's to rebuild; git holds what was removed. `Diagnosis` and the
      log's diagnosis methods stayed behind, since records outlive features and
      an append-only log cannot be retrofitted
