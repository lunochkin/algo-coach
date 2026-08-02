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
- [x] `algo-coach drill` — steps 1-4, prompting and rendering only. Invalid
      input re-asks, EOF ends the drill, and the handover says nothing is
      recorded yet rather than moving no number in silence

The rest extends that command.

- [x] Wait for the user to push, then diff the log for what appeared against
      that problem — exact, since the loop knows what was there before
- [ ] Ask for a claim and a self-label on each attempt that appeared, the
      drilled technique pre-filled and the previous answer carried forward — a
      sitting reached 29 submissions
- [x] Nothing pushed, nothing recorded: wait again or end, never hold the
      answers against a record that may not arrive

### Exit
- [ ] The loop runs on real daily attempts

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] Re-derive stored problems without a push — when the mapping changes for
      problems no longer pushed. A re-push covers it until then
- [ ] Ingest assumes a single writer: two concurrent pushes can both miss the
      same `external_id`. When the web version lands, decide whether the CLI
      writes to the store or calls the API
- [ ] Duplicate detection loads the whole attempt log per call, and
      `by_external` scans every problem file per record; both become queries
      when storage swaps

## Later phases

### Phase 3 — classification
- [ ] Classifier picks among the problem's own tags rather than classifying
      freely, so it can narrow what a problem could exercise but never invent
      a technique the tags do not name
- [ ] Write the verdict as a `TechniqueClaim`, source `classifier`, with model
      and prompt version. Reject a code `is_known` rejects — the only write
      path that could introduce one
- [ ] Run it over the stored log, not only over fresh practice: every one of
      the 1785 attempts carries its code, so the whole backlog is classifiable
      today
- [ ] Correct a claim after the fact, source `user` — overriding a classifier
      verdict, or claiming a backfilled attempt no loop ever touched. First
      capture is the loop's
- [ ] Re-derive stale machine claims by model and prompt version, leaving user
      claims untouched
- [ ] Measure how often a claim disagrees with the tag fallback. The board's
      numbers only move if it does, and 61% of attempts carry two or more tags

### Phase 4 — cards
- [ ] `Card` model and store: teaching content keyed to a technique, several
      per technique, never referenced by the log. Git holds the removed version
- [ ] Seed from the private content repo; read-only at runtime
- [ ] Cards for the techniques the board names weakest, not for all 27

### Removed, kept in git
- [ ] Failure classifier and its agreement eval, cut before Phase 1 shipped.
      `Diagnosis` and the log's diagnosis methods stayed: records outlive
      features, and an append-only log cannot be retrofitted
