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

### CLI
- [x] Retire `cards seed` — it wrote technique codes into the cards store, and
      the vocabulary ships in git now

### Drill board
- [ ] Resolve an attempt's techniques: its claim if one exists, otherwise the
      problem's. Read-time only — never stored, so re-deriving the tag mapping
      reaches every unclaimed attempt
- [ ] Per-technique view: attempt count, recency, solved/unsolved, self-label
- [ ] `algo-coach board` CLI command
- [ ] Count how much of the backlog carries more than one tag — it sets how
      badly Phase 2's classifier is needed

### Exit
- [ ] A week of real attempts in the store, board rendering from them

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] Assign techniques to an attempt, as a `TechniqueClaim` record — when a
      resolved default is wrong often enough to be worth correcting. Reject a
      code `is_known` rejects: the only write path that could introduce one,
      since `map_tags` already filters
- [ ] Re-derive stored problems without a push — when the mapping changes for
      problems no longer pushed. A re-push covers it until then
- [ ] Ingest assumes a single writer: two concurrent pushes can both miss the
      same `external_id`. When the web version lands, decide whether the CLI
      writes to the store or calls the API
- [ ] Duplicate detection loads the whole attempt log per call, and
      `by_external` scans every problem file per record; both become queries
      when storage swaps

## Later phases

- [ ] Cards: teaching content referencing a technique. Model and store were
      removed; git holds them
- [ ] Classifier and the agreement eval, removed likewise. `Diagnosis` and the
      log's diagnosis methods stayed: records outlive features, and an
      append-only log cannot be retrofitted
