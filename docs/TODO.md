# TODO

## Phase 1 — push API + cards + drill board

### Schema (before the first real ingest)
- [ ] Subject id on `Attempt`
- [ ] Card assignment on `Attempt` (user-marked technique)
- [ ] Push idempotency key: `(subject, origin platform, id)`
- [ ] `Problem` provenance: owner set by ingest path, origin platform, pusher

### Cards
- [x] Scaffold project
- [x] Simple cards store and init logic
- [ ] Cards list
- [ ] Seed the technique vocabulary from the content repo

### Push API
- [ ] Ingest `Problem`: validate, upsert as user-owned
- [ ] Ingest `Attempt`: validate, append, no-op on re-push
- [ ] Reject client-supplied owner; derive from ingest path

### Drill board
- [ ] Per-card view: attempt count, recency, solved/unsolved, self-label
- [ ] `algo-coach board` CLI command

### Exit
- [ ] A week of real attempts in the store, board rendering from them
