# TODO

## Phase 1 — push API + techniques + drill board

### Schema (before the first real ingest)
- [x] `user_id` on `Attempt`, set by engine at ingest from the authenticated pusher
- [ ] `Problem` provenance: owner set by ingest path, origin platform, pusher
- [ ] Add `AttemptTechnique`

### Techniques
- [x] Scaffold project
- [ ] Technique vocabulary as a data file under `src/algo_coach/`, so it ships
      with the package
- [ ] Alias map beside it: retired code → current code, applied when grouping
- [ ] Membership check on the write path only — never in the pydantic model,
      or retiring a code makes historical records unreadable

### Push API
- [ ] Ingest `Problem`: validate, upsert as user-owned
- [ ] Ingest `Attempt`: validate, append, no-op on re-push
- [ ] Reject client-supplied owner and `id`; derive both from the ingest path
- [ ] Map `source_tags` to engine `techniques`; unmapped tags stay in
      `source_tags` and produce no code

### CLI
- [ ] Assign a technique to an attempt, as an `AttemptTechnique` record
- [ ] Retire `cards seed` — it writes technique codes into the cards store

### Drill board
- [ ] Per-technique view: attempt count, recency, solved/unsolved, self-label.
      Grouping key is `AttemptTechnique`, never problem tags
- [ ] `algo-coach board` CLI command

### Exit
- [ ] A week of real attempts in the store, board rendering from them

## Later phases

- [ ] Cards: teaching content referencing a technique, not the vocabulary.
      Model and store already scaffolded; `Card.name` becomes a card code
