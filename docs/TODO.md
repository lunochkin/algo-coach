# TODO

## Phase 1 — push API + techniques + drill board

### Schema (before the first real ingest)
- [x] `user_id` on `Attempt`, set by engine at ingest from the authenticated pusher
- [x] `Problem` provenance: owner set by ingest path, origin platform, pusher
- [x] Add `AttemptTechnique` — the record exists and is exported; nothing
      writes or reads it yet
- [ ] Claim source on `AttemptTechnique`: who asserted the technique, and for
      a machine claim, the model and prompt version — the shape `Diagnosis`
      already has. Without it, user and classifier claims are
      indistinguishable and their disagreement cannot be measured, which is
      the reason the record is separate at all
- [ ] Verdict provenance on `Attempt`: whether `solved` and `tests` were
      claimed by the client or produced by engine verification. Unambiguous
      only while every attempt is pushed; from Phase 5 both land in the same
      fields

### Techniques
- [x] Scaffold project
- [x] Technique vocabulary as a data file under `src/algo_coach/`, so it ships
      with the package. Verified present in the built wheel
- [x] `is_known` for the write path only — never in the pydantic model, so a
      retired code cannot make historical records unreadable

### Push API
- [x] Ingest `Attempt`: validate, append, no-op on re-push. Duplicates are not
      errors; a batch ingests partially so one bad line costs only itself
- [x] Reject client-supplied `id` and `user_id`; stamp both from the adapter
- [x] `algo-coach push <attempts|problems> <file|->`, `--user` standing in for
      authentication
- [x] Ingest `Problem`: validate, upsert as user-owned. A re-push updates the
      descriptive fields and never moves the minted id
- [x] Reject client-supplied owner, id, user_id and techniques; the engine
      assigns all four
- [x] Map `source_tags` to engine `techniques`; unmapped tags stay in
      `source_tags` and produce no code. Re-derived on every push, so a mapping
      change reaches problems already in the store
- [x] Resolve `problem_external_id` to the minted `problem_id` at ingest, and
      reject what does not resolve. Problems must be pushed before their
      attempts; rejection is per-record, so re-pushing after they land is a
      no-op on what already ingested

### CLI
- [ ] Assign a technique to an attempt, as an `AttemptTechnique` record.
      Reject a code `is_known` returns False for — this is the only write path
      that could introduce one, since `map_tags` already filters
- [x] Retire `cards seed` — it wrote technique codes into the cards store, and
      the vocabulary ships in git now, so there is nothing left to seed

### Drill board
- [ ] Per-technique view: attempt count, recency, solved/unsolved, self-label.
      Grouping key is `AttemptTechnique`, never problem tags
- [ ] `algo-coach board` CLI command

### Exit
- [ ] A week of real attempts in the store, board rendering from them

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] Re-derive stored problems without a push — when the mapping changes for
      problems no longer being pushed. A re-push covers it until then
- [ ] Ingest assumes a single writer: duplicate detection reads the log, so two
      concurrent pushes can both miss the same `external_id`. Decide when the
      web version lands whether the CLI writes to the store or calls the API
- [ ] Duplicate detection loads the whole attempt log per call, and
      `by_external` scans every problem file per record; both become queries
      when storage swaps

## Later phases

- [ ] Cards: teaching content referencing a technique, not the vocabulary.
      Model and store existed once and were removed; git holds them
- [ ] Classifier and the agreement eval, removed with the same reasoning.
      `Diagnosis` and the log's diagnosis methods stayed — records outlive
      features, and an append-only log cannot be retrofitted
