# Architecture

Target state. Code lags this doc; where they differ, this doc wins.

## Shape

Engine public, content private. Everything the practice loop reads is local to
the engine. Problems, cards and attempts live in datastores the engine
controls, and the technique vocabulary ships with the package. The engine never
contacts external platforms. User clients push data in.

Consequence: no third-party dependency in the drill loop.

## Terminology

- **Attempt** — a user's solution to a problem, successful or failed.
- **Verification** — executing an attempt against a problem's test cases,
  yielding pass or fail.
- **Diagnosis** — classifying why an attempt failed. A `Diagnosis` record
  stores the result.

## Data classes

| Class | Owner | Visibility | Write semantics | Source of truth |
|---|---|---|---|---|
| Techniques | product | global | read-only at runtime | this repo, in git |
| Cards | product | global | read-only at runtime | private content repo |
| Template matches | follows the problem | global if the problem is product-owned, private if pushed | append-only | the store |
| Problems | product or user | global if product-owned, user-scoped if pushed | read-only if product-owned, mutable cache if pushed | product set, or the pushing client |
| Card runs | user | private | append-only | the store |
| Recall attempts | user | private | append-only | the store |
| Attempts | user | private | append-only | the store |
| Technique claims | user | private | append-only | the store |
| Calls | user | private | append-only | the store |
| Self-labels | user | private | append-only | the store |
| Diagnoses | user | private | append-only | the store |

### Techniques

The vocabulary the append-only log references.

- **Versioned as code, not stored as data.** A file shipped with the package,
  not a datastore the engine writes.
- **A code carries the criterion for claiming it**, not only its name. The
  codes are four kinds of thing. One question is asked of all four, and
  answered differently for each. Every code names its kind, what earns it, and
  the near miss it is confused with. The near miss is the part that decides
  cases, because the disputes are about boundaries rather than definitions.
  - A procedure counts when the solution performs it.
  - A structure counts when its properties carry the correctness or the
    complexity.
  - A paradigm counts when it is why the solution is correct.
  - A problem class counts when it is what the problem asks for.
- **A kind reaches both readers as its test, never as its name.** The label
  helps only a reader who already knows what it selects. A reader who does not
  will judge a structure on whether it was performed. The four tests live with
  the kind rather than in the vocabulary file, so twenty-seven entries state
  them once.
- **A code is claimed beside the narrower ones, never instead of them.** What a
  solution does is true at several levels. A backtracking search descends, and
  a search tree is a binary tree. A claim names every level it worked at. An
  exclusive rule would need a containment order over the codes, and nothing
  generates one. It could only be hand-written pair by pair, then disagreed
  with case by case. The exceptions are per code and stated in the entry.
  `recursion` names a language mechanism rather than an approach, so a row
  counting every self-call would name no skill.
- **What disqualifies a code is incidental use**, never that another candidate
  covers it. The near miss states that line in full: a sorted lookup beside a
  linear pass that dominates, a map standing in for an array. Reading the near
  miss as precedence is what made the classifier drop codes the user claimed.
- **Inclusive claiming is what keeps a row coherent.** Attribution falls back
  to the problem's tags, and platform tags already nest. Under an exclusive
  rule, a claimed attempt and an unclaimed one on the same problem would be
  counted by different rules. The proportion of each would shift as
  classification progressed, so the board numbers would change while the
  practice behind them did not. A claim narrows a row. It never re-partitions
  it.
- **The criteria are the prompt.** They reach the classifier beside the
  candidates, and the reader beside the code, so one rulebook answers both.
  Editing an entry therefore changes readings, but only for the attempts
  carrying that candidate. So what a reading was made against is a digest of
  the text that attempt was sent, never a version number covering the whole
  rulebook.
- **A code is never deleted**, because records carrying it outlive it.
  Retirement means an entry in an alias map, applied when grouping.
- **Membership is checked on the write path only.** A model that validated
  codes on read would make the log unreadable by its own schema the moment a
  code was retired.

### Cards

Teaching content about a technique, not the vocabulary itself.

A card organises studying one technique: what to read, what to reproduce from
memory, and what to solve. It is not an ability estimate. Mastery is what a
user can solve, per technique, and the two share no data.

- **Product data, not code.** Cards live in the engine datastore, seeded from a
  private repo that holds their version history.
- **Granularity follows teaching, not estimation.** One technique can carry
  several cards. Mastery is estimated per technique, so cards are never the
  unit of estimation, and the attempt log never references one.
- **A card names no problem.** It carries a selector: a technique, and the
  filters that narrow it. The ladder is derived from the corpus. Ids are minted
  per engine, so a card holding them would mean nothing in another store, where
  a selector ships anywhere.
- **The ladder covers every studied template.** Its rungs come from the
  template matches, at least one per template, and the selector fills the rest
  out to `size`. A ladder drawn from the selector alone would exercise the
  technique and leave some forms unexercised, because a tag says what a problem
  is about and not which form solves it.
- **Requiredness is derived from what a rung covers**, never stored. A rung
  covering a studied template is required. A rung covering only the optional
  template is optional. A rung covering both is required, and the optional
  template is offered on it as the alternative approach. That last case is why
  a problem matching several templates is wanted rather than a nuisance.
- **A studied template with no match is a reported gap**, not a quietly shorter
  ladder. The card claims to teach that form, so a corpus that cannot exercise
  it is a fact about the store worth surfacing.
- **The recognition cue is its own field**, apart from the prose it could sit
  in. A probe asks exactly that question: is the form recognised unprompted. So
  the cue is shown and withheld on its own, and the rest of what to read is one
  authored block the engine never parses.
- **The cue is carried at both levels**, answering different questions. The
  card's cue says to reach for the technique. A template's cue says which of
  its forms. Recall is per template, so a card-level cue alone would be right
  about the technique and silent about what has to be reproduced.
- **One template may sit outside the studied set.** A card carries at most one
  optional template, the capstone, and never only optional ones. It is authored
  whole and surfaced on request alone. The hard form is worth deriving before
  it is read, and a card that showed it unasked would remove that chance
  permanently.
- **The ladder is resolved at import**, once, and a re-import never rewrites
  the ladder of a card already started. Same rule as a problem's minted id, and
  for the same reason: a user is already working through it.
- **Probes are assigned when a card is started**, not at import, and more can
  be assigned later. What was unseen at import need not still be unseen, and
  the ordering answers that: unseen first, then least recently attempted. They
  are never drawn from the ladder, which teaches the form rather than testing
  whether it is recognised unprompted.
- **A probe is not scarce.** With nothing unseen left, the least recently
  solved stands in. Someone who has solved everything in the technique is past
  the point where the distinction pays for itself.
- **Resolution is the engine's, as tag mapping is.** The selector is the truth
  and the ladder a derived view, so re-deriving it is legal — for a card nobody
  has started.

### Template matches

Which problems exercise which of a card's templates. The ladder's coverage is
computed from these records. They are the engine's own work: an author names no
problem, so nothing is authored here either.

- **One record per template and problem, carrying a verdict.** Not a set per
  template. Problems arrive one push at a time, and a set record would rewrite
  pairs that were already settled every time the corpus grew. A claim asserts a
  whole set for one attempt, because the set is the assertion. A match asserts
  one pair, and the pairs are independent.
- **A negative is stored.** Otherwise every re-run re-tests every non-match
  forever. What still needs testing is the pairs carrying no record at the
  current configuration, which is the rule `score` already uses for readings.
- **A problem may match several templates**, and a template many problems. Two
  approaches to one problem is the ordinary case. It is what lets a single rung
  cover a studied template and an optional one at once.
- **Written after card import, never before.** Both references are minted: the
  template at import, the problem at ingest. So a match cannot be authored
  against a seed file.
- **A call is per problem and card, a record is per pair.** The candidates are
  that card's templates, and the answer is the subset the problem exercises,
  which is the classifier's shape. The records come from one answer.
- **Candidates are pre-filtered by technique.** A problem is offered only to
  cards whose technique its tags reach. Otherwise the work is every template
  against every problem, for an answer that is almost always no.
- **Procedure templates are excluded.** A framing procedure is exercised by
  every problem its technique reaches, so a per-problem verdict carries no
  information. It is covered by the ladder as a whole.
- **A card's relation to a problem is a fold over its templates**, never a
  record of its own. A rung is earned when the technique reaches the problem
  and some template matches, and that is derived from the pairs rather than
  stored beside them. Nothing asserts in one place that a problem belongs to a
  card, so nothing has to be rewritten when one template's verdict changes.
- **Re-derivation is the normal path, not an exception.** A technique claim
  asks about one attempt, and the question never changes. A match is a template
  against a corpus that grows with every push.
- **Provenance as a claim carries it**: the source, and on a machine match the
  model, effort, prompt digest and call.
- **Two writers, and the user's stands.** A hand annotation is what a machine
  run is measured against, so it stands on read whenever it was written. A
  machine verdict on an annotated pair is a reading: stored and scored, never
  what a ladder resolves from. One rule, stated once for claims and holding
  here — the record the machine cannot recompute wins.
- **A hand record settles what stands, not what has been read.** The run path
  skips a pair only where the hand pass settled every template of that card.
  The call asks about the card whole, and a partly annotated card is a question
  still worth asking. The eval reads annotated pairs on purpose, because that
  reading is the measurement.
- **Agreement is per pair, grouped per template.** A match asserts one pair, so
  the pair is what agrees or disagrees. A call carrying six of them saves
  requests; it is not a unit of truth. Grouping is per template because the
  ladder is per template. A form the matcher over-matches fills its rung with
  problems that do not teach it, and one number over the card would average
  that away.
- **Nothing is scored as a set.** A claim is scored whole because it asserts a
  whole set, and only equality catches the claim that names every candidate. A
  match asserts a pair. A matcher that says yes to everything is already
  visible as a false positive on every template. That is the same signal,
  without a second number, and without a metric that calls six verdicts wrong
  for one bad one.
- **Accuracy over the pairs is not the metric either.** Most pairs are
  negative, so a matcher that names nothing scores in the nineties and resolves
  an empty ladder. What is scored is the positive verdicts, both directions:
  what the annotator named and the machine missed, and what the machine named
  and the annotator did not.
- **An empty answer is negatives, not a decline.** A claim naming nothing
  answers nothing, and the tags keep standing. A call naming no template
  asserts that each of them does not match, which is a verdict on every pair
  and is scored as one. The record shape decides this, not the model's
  behaviour.
- **The first hand pass calibrates, a blind one measures.** Annotating is where
  the line gets drawn between exercising a form and merely admitting it. A
  score taken over the pairs that drew that line measures agreement with
  itself. The eval set is annotated from the templates alone, and
  configurations are compared over the pairs both read — the claims rule,
  unchanged.

### Card runs

Studying a card is an explicit act, not a state the system infers.

- **Starting is explicit**, because the ladder is measured from it. A ladder
  problem solved before the card began does not count toward it. The card
  teaches the form, and having solved the problem once is not having studied
  it.
- **The run holds what the start produced**: when it began and the probes it
  was given. Later probes append rather than replacing the set, so what was
  offered and when stays readable.
- **Derived from it, never stored**: ladder progress, recall state per
  template, and whether the card is done. Aggregates are views. "Done" is only
  a view for now. Graduation becomes a process later, once there are numbers to
  set its box and its probe count from.

### Recall attempts

One template reproduced from memory, and how it went.

- **Not an `Attempt`.** No problem, no platform, no submission. Nothing keys it
  to an attempt, so it is its own record, keyed to a card and a template.
- **The unit is the template, not the card.** A card's forms are learned and
  lost separately, and a card-level number would average them together and show
  neither.
- **A hinted pass is not a pass.** Which hints were taken before succeeding is
  part of the record. Without it, a decaying form scores the same as a fluent
  one.
- **Recall fluency is not solving fluency.** Reproducing a form cold is not
  recognising it unprompted, so this never stands in for mastery. The gap
  between them is exactly the false fluency that blocked practice trains.

### Problems

- **Provenance is required.** Product problems need a rights record. Pushed
  problems need an origin platform and a pushing user.
- **Two origins.** User-pushed problems arrive through the push API.
  Product-owned problems come from a content pipeline in a separate private
  repo.
- **Push identity is `(user_id, external_id)`**, so a re-push updates rather
  than duplicates. The engine mints the `id`, and it never moves on update,
  because attempts reference it.
- **Tag mapping is owned by the engine.** A pushed problem carries the origin
  platform's tags verbatim, and the engine derives its own codes beside them.
  Raw tags are the truth and codes are a derived view, so re-running the
  mapping is legal and expected.
- **An unmapped tag blocks nothing.** It produces no code and the problem still
  ingests. A metadata mismatch must never cost a real attempt.
- **The statement is stored, and matching is why.** Which form a problem
  exercises is a question about what it asks, and tags answer what it is about.
  The invariant against third-party statements is about git, and `data/` is
  gitignored. The engine stores what a user pushed to their own store, and no
  repo carries it.
- **Required, and non-blank. The one metadata gap that does block.** It landed
  optional, was backfilled across the corpus, then tightened while nothing
  stored carried the loose shape. It is not treated like an unmapped tag for
  one reason. A missing code costs one problem its place in one board row. A
  missing statement is a problem that can never be matched, and nothing reports
  it. Preventing that silence is why the field exists, so it fails at the
  boundary instead — per record, and the push is re-runnable once the scrape
  catches up. A blank string is an absence that passes a presence check, so it
  is rejected too.

### Attempts

- **One source per problem.** The user if the problem is user-pushed, otherwise
  the engine.
- **Identity is the engine's.** A pushed attempt carries a client-minted id,
  unique per user, so re-pushing an ingested one is a no-op. The engine mints
  its own id and never accepts one from a client.
- **The problem reference is resolved at ingest**, from the platform's id to
  the minted one. An append-only record must not hold a reference nothing can
  follow, so an unresolvable one is rejected. Problems are therefore pushed
  first. Rejection is per record, and re-pushing later is a no-op on what
  landed.
- **Origin is who produced the attempt**: the push API, or the engine's own
  drill loop. It is stamped by the ingest path, never sent by a client. Whether
  the verdict rests on a real test run is a separate fact, recorded once the
  engine can verify. The drill loop produces attempts on pushed problems, and
  it cannot verify those.
- **The platform's own status is kept verbatim.** `solved` is the projection
  over it, and the raw value carries what the projection drops. A timeout and a
  wrong answer are both unsolved, and only one is evidence of slowness.
- **Problem techniques are never denormalized onto an attempt.** Tags are
  re-derivable and the log is not, and a copy taken at ingest would drift with
  no way to tell which is right.

### Technique claims

Which techniques an attempt used. Per-technique progress is measured from this.
A claim rather than a fact, and open to revision, so it is its own record
rather than a field on the attempt.

- **Attribution resolves, it is not required.** The claim that stands if one
  exists, otherwise the problem's techniques. Nothing has to be labelled for an
  attempt to count, which is what makes a history of past attempts usable.
- **Resolution happens on read and is never stored**, so re-deriving the tag
  mapping reaches every unclaimed attempt.
- **The fallback answers a different question.** A tag says what a problem
  could exercise, a claim what the solution did. Tags over-credit broad
  techniques, which skews scheduling away from the weakest ones.
- **Two writers, user first.** The drill loop asks at the moment of solving,
  and a hand pass reaches attempts no loop touched. A classifier fills the rest,
  and a later user claim corrects it.
- **The classifier reads code because no training data exists for this label.**
  Public corpora tag problems, not solutions, so a model trained on them
  predicts the fallback rather than improving on it. Nobody has labelled what a
  given solution did, because doing so means reading it — which is the work the
  classifier is there to do. So it is a prompted model reading the solution,
  not a trained one.
- **Recognising an approach in code is semantic work.** A problem's tags span
  what it admits: several approaches to it, or one solution combining several
  techniques. Choosing among them means reading which the code took.
  Two-pointers and sliding-window differ in their invariant, not their syntax.
  Backtracking is depth-first search plus an undo. Greedy is a property of why
  a choice is correct rather than a construct. A scan of imports and keywords
  is weakest exactly where the claim is worth making.
- **A claim is scored against the user's own**, per technique rather than
  overall. The board is per technique, and a classifier that over-claims one
  code skews it. Set equality, not overlap: a claim naming every candidate
  agrees with the tags and decides nothing, but would score well on a metric
  that only asks whether the right code appears.
- **How often a claim names every candidate is reported beside the score.**
  Claiming inclusively removes the reason to withhold a code, so the way it
  fails is by naming all of them. That is the fallback, scored on whatever the
  tags happened to get right. Set equality does not catch it, because agreeing
  with the tags scores well whenever the tags are right. The hand claims are
  the reference the machine's share is read against.
- **Those claims are an eval set and a correction path**, never training data.
  Nothing in the engine is trained.
- **What invalidates a label is which reader informed it, not that one did.** A
  claim made with the scored configuration's reading in view measures that
  configuration against itself. The first hand pass over a rulebook still being
  written is agreement with itself, for the same reason. A claim adjudicated
  against a reader that is never scored is neither — it is how the boundary
  gets drawn. So `informed_by` names the readings its author saw, one by one,
  and a set can be read back for either question.
- **The eval set holds one attempt per problem**, its latest carrying code. A
  retry asks the identical question: same solution, same candidate tags. A
  repeat would measure one decision twice rather than measuring two. The drill
  loop still asks about every attempt of a sitting, where the answer costs a
  keystroke and the count is per submission.
- **One claim per attempt**, naming every technique it used, since a solution
  can use several. A later claim replaces the whole set rather than rewriting
  the earlier one.
- **A verdict naming no candidate is a reading, and is stored.** The classifier
  read the code and found the candidates did not cover it. That is evidence
  about the code rather than an absence of it, and the answer does not change
  while the question does not. Left unstored, it was re-read by every later
  run, paying again for the same decline.
- **An empty claim answers nothing, so the fallback stands.** The resolver
  reads a claim's *techniques* rather than its existence. The tags therefore
  keep answering an attempt whose reading declined, and the board is exactly as
  it was when such a verdict went unrecorded.
- **It is scored all the same.** The board and the eval ask different
  questions. A decline gives the board nothing to render, and it gives the eval
  an assertion: none of these candidates apply. A hand claim naming one of them
  contradicts that, so it is a disagreement and counts as a miss against every
  technique the user named. Calling it missing evidence was inconsistent with
  storing it as evidence, and it paid a classifier to decline — every decline
  left a smaller denominator behind and a better share over it. What is still
  unscored is an attempt with no verdict at all, where nothing was read. The
  count is reported beside the share, because how often a reader finds the
  candidates wanting is worth seeing on its own.
- **A decline supersedes an earlier claim, as any later reading does.** One
  rule orders the log. A reading saying the candidates do not fit is not weaker
  evidence than an older one made against a rulebook it disagrees with. What it
  costs is that the older claim's answer gives way to the tags.
- **A decline is stated, never inferred from an empty set.** Either writer may
  name none of the candidates. The user says so with `declined`, because the
  drill loop records nothing where they skip, and emptiness alone would make a
  lost answer and a stated verdict the same record. The classifier needs no
  flag: it answers or it fails, and a failure writes no claim.
- **The eval set can hold a correct decline, and could not before.**
  Adjudication sometimes ends at "no candidate applies". Without a way to say
  it, such a claim could only be deleted. Membership is keyed on a hand claim
  existing, so deleting it drops the attempt from the set. The classifier's
  declines were stored and scored while the user's could not be recorded, and
  the field removes that asymmetry.
- **The user's claim wins on read, the latest of each writer's otherwise.**
  Under latest-wins alone, whichever writer wrote last would decide, and the
  classifier writes far more often. Ground truth would last only until
  something re-derived over it. This rule is what makes a machine claim safe to
  store on an attempt the user has claimed. A claim scored against the user's own has to be stored, or
  an eval run leaves no record once it has finished printing.
- **Which is why it is a rule rather than a discipline.** Skipping claimed
  attempts on the write path depends on one writer remembering to. A writer
  that forgets overwrites the evidence, and an append-only log cannot take it
  back. A reader that prefers the user's claim makes that unrepresentable. The
  classifier still skips them, but only to save a call whose verdict could
  never stand — not as what protects the eval.
- **A machine claim on a hand-claimed attempt is a reading, not a candidate.**
  It never becomes the standing claim, never reaches the board, and exists to
  be scored. Storing it makes an eval a dataset rather than a run: what a
  configuration answered stays readable, and a second configuration is paid for
  only where it has not read.
- **One record for both writers, not two.** Splitting them would mirror
  `SelfLabel` and `Diagnosis`. But the classifier claims already written stay
  in the log forever, so a reader carries the old shape whatever else changes.
  A third record written only by the eval needs no migration, and is worse: the
  same verdict would be a claim or a reading depending on what else was claimed
  on the attempt, so other records would decide its type.
- **Every claim records its source.** A machine claim also records what
  produced it: model, effort, the endpoint it was pinned to, temperature, the
  digest of what that attempt was sent, and the call that sent it. Both count
  the same toward progress. But a machine claim can be recomputed by a better
  classifier and a user's cannot, so re-deriving has to find the stale ones and
  leave the rest. All of them or none, since a reading whose configuration is
  partly unknown compares with nothing. A user's claim carries none of them,
  because nothing re-derives it. A model asked for no effort, or one that
  rejects the parameter, records the level it ran at rather than an empty
  field: the model's own default is a fact about the reading, not a gap in it.
- **The digest is of the question, not of the rulebook.** A criterion travels
  with its candidate, so editing one entry changes what a few attempts are
  asked and leaves every other one untouched. Keying staleness on the digest
  therefore re-derives the slice an edit reached and nothing else, where a
  rulebook-wide version re-derived the backlog for a sentence most attempts
  never saw.
- **There is no version beside it.** A version number was an author's word for
  "the reading changed". An author can forget to bump it while the text moves;
  a digest cannot. What it costs is that a reflowed sentence re-derives the
  attempts it reaches, which is the intended trade: nothing licenses calling an
  edit cosmetic on a model's behalf, and the scope is now the entries actually
  touched. What it also costs is a name. A rulebook can no longer be cited as
  "prompt 3", only as the digest of what was sent, and diffed by reading the
  prompts two calls carry.
- **A pin is part of the reading, not a note about routing.** A model id
  resolves to as many builds as there are endpoints serving it, and
  quantization changes the weights. An fp4 endpoint and a bf16 one are two
  different readers. Unpinned, the router chooses per request, so the readings
  under one key are a mixture no later run can separate. The pin is therefore
  required rather than optional, and compared like the model itself.
- **Who served it is recorded and never compared.** The router reports a
  company, not an endpoint, and one company serves several builds of a model.
  It confirms a pin held, without identifying the build. It is also unknown
  when a reader asks what it has already read, which is the question the
  comparison exists to answer.
- **A reading is greedy, and says so.** Sampling turns a verdict the model
  holds at 0.9 into one it gives four times in five. An eval absorbs that by
  being repeated. The backlog sweep cannot: it writes into an append-only log
  the board reads forever, so the same fraction of a percent is permanent, and
  it moves readings a criteria edit never touched. Temperature identifies a
  reading for the same reason the pin does. One says which weights answered,
  the other how they were sampled.
- **A temperature nobody set is an arm, not a gap.** `None` is the provider's
  own default, which moves without notice, so it is recorded absent rather than
  guessed at, and it compares equal only to itself. That is what makes every
  reading taken before the parameter existed scorable beside a greedy one
  instead of discarded. Same rule as an unsent effort.
- **The claim's copy cannot drift**, because a call is append-only and the copy
  is made in the same write. It is there so the claims log reads on its own: a
  board renders from it, and loading the calls to learn which model produced a
  claim would put a megabyte-scale read on every command.
- **Configurations are compared over the attempts both read**, not over each
  one's own. A cheaper classifier measured on a smaller sample scores against a
  different denominator, and the number would read as quality.

### Calls

One request to a model and what came back. A layer below the claims. A claim
cites a call and reads its own meaning into the response, and the call record
holds nothing about what the answer was for.

- **Domain-free on purpose.** No attempt, no techniques, no vocabulary — only
  what was asked, of whom, and what returned. That is what lets a second domain
  reuse the log without being taught anything, and what keeps the run loop's
  decisions in the domain where they belong.
- **The prompt is stored whole, beside its digest.** The record therefore
  digests to its own key, and a renderer that changes later cannot make an old
  one unreadable. It is inline rather than deduplicated into a store of its
  own: one append cannot half-succeed, where a file plus a log line can leave a
  call naming a prompt that is not there.
- **It holds what a claim structurally cannot**: the tokens a run cost, the
  reasoning behind a verdict, and the calls that produced no claim at all. A
  decline names no candidate and a failure names nothing. Before this record,
  both were counters that printed once and were lost.
- **One transport, one shape.** Every model is reached as chat completions
  through a router, so adding a model is a string and adding a provider is a
  base URL. Two provider shapes maintained by hand would create pressure to
  adopt a library that reconciles them, and such a library can downgrade a
  schema into a prompt where the record cannot show it happened.
- **What was sampled at is recorded beside who served it.** A reading's
  configuration has to be recoverable from the record that holds it, and the
  claim's copy is taken from here.
- **Every request names one endpoint.** A provider that cannot honour the
  response schema is never chosen, and a request fails rather than falling back
  to a backend the record would not name. The pin is stored beside who answered
  it. The first says which build was asked for and is what a re-run needs, the
  second says whether anything answered at all.
- **Reasoning is what the reading produced, not what was asked for.** A model
  that decides a question needs no thought returns none, and the field is
  empty. That is a fact about the reading rather than a gap in the record. Two
  calls on one prompt can differ here, which is the same adaptive behaviour the
  noise floor already measures.
- **`prompt_hash` is not unique.** A retry after a rate limit repeats it, and
  sampling one prompt on purpose repeats it deliberately. A reader looking one
  up must say which it wants rather than assume there is one.
- **A call is timed at two levels.** What the caller waited, and how many
  requests that took. Beside it, what the last request took on its own: the one
  that answered, or the one that failed. Their difference is the endpoint's
  backoff, and without it a run held behind a per-minute cap reads as a slow
  model.
- **Nothing on the run path reads it back.** Whether to ask again is decided
  from the claims, which already carry the model, effort and digest. This file
  is written by every run and loaded only by whoever sits down to analyse one.
  A cache over the calls themselves would serve prompts shared by two attempts,
  and is not built: the log is shaped for it, and the saving is small while
  there is one domain.

### Self-labels

The user's own verdict on why an attempt went the way it did. Reported, not
inferred. A judgement made after the fact and open to revision, so it is its
own record rather than a field on the attempt, for the same reason a claim is.

- **Only ever the user's.** A machine answering the same question produces a
  `Diagnosis`. The two are separate records because the eval scores one against
  the other, and a shared record read latest-first would let the machine
  supersede the evidence it is measured against.
- **One label per attempt**, latest wins on read.
- **The drill loop is the only writer.** A pushed attempt carries no label,
  because the platform never prompted for one.
- **A label cannot be given later.** Why an attempt went the way it did is a
  memory of the sitting. What is still recoverable from the record months
  after — a timeout, a compile error — is what a `Diagnosis` reads. A label
  recalled that late is either invention, or the classifier's own input handed
  back as evidence against it.
- **A claim is retroactive, a label is not.** The evidence for a claim is the
  code, which does not decay. The evidence for a label is recall, which does.
  That is why they are asked separately rather than as two halves of one
  prompt.

### Diagnoses

Why an attempt failed, inferred rather than reported. Keyed to an attempt, and
versioned by model and prompt version, so every attempt can be re-diagnosed and
compared.

- **The machine counterpart of a self-label, never its replacement.** Neither
  supersedes the other. Agreement between them is the eval.
- **Kept per model and prompt version**, so a later diagnosis is a second
  reading rather than a correction.

### What every record keyed to an attempt carries

Claims, self-labels and diagnoses share a base: an engine-minted `id`, the
`attempt_id` they assert about, and `created_at`. One reader orders all three,
latest by `created_at`, with append order breaking a tie. The `id` lets a
record be cited, by an eval naming the diagnosis it scored or by a user
correcting a claim.

Ordering is not the same question as what stands. A self-label has one writer,
so the latest is what stands. A claim has two writers, and the user's stands
over any machine claim however late. A diagnosis never supersedes a self-label
at all. The shared reader answers "in what order", and each record says who
wins.

## Boundaries

- **Push API** — the platform's only runtime ingest path, carrying user-pushed
  problems and attempts. A format contract, not a protocol: clients emit
  `AttemptPush` and `ProblemPush` (`src/algo_coach/schema/push.py`), which are
  the payloads the stored records are built from, not the records themselves.
  - The payload has no field for what the engine stamps, so identity and
    provenance cannot be forged by sending them. Unknown keys are ignored, so a
    newer client stays pushable to an older engine.
  - Attempts append, problems upsert.
  - Each attempt's problem reference is resolved to the engine's own id, so
    attempts are pushed after the problems they name.
  - A batch ingests per record: a bad one is rejected by index, the rest still
    land. One malformed line must not cost the attempts around it.
  - An already-ingested record is counted, not an error, so retrying is safe.
- **Verification** — runs locally, against test cases the engine owns. Product
  problems only. Pushed problems carry no test cases, so their attempts happen
  outside the engine.
- **Storage** — concrete for now (JSON files under a gitignored directory), a
  database later. The schema is the contract, and storage swaps underneath it.
- **Product content ingest** — cards, problems, and test cases are produced by
  an offline content pipeline in a separate private repo, and seeded into the
  engine datastore. File-based for now. The technique vocabulary is the
  exception: it ships with the package, in git.
  - What an author writes has its own shape, as a client's push does.
    `CardSeed` (`src/algo_coach/schema/seed.py`) is the payload the stored card
    is built from, not the card. Identity is the engine's at both boundaries,
    so the payload has no field for it and an author cannot supply one by
    writing it.
  - A card and each of its templates are matched by their authored slug, which
    is what makes re-seeding refresh rather than duplicate. A new slug is a new
    card: the runs and the recall history stay with the old one, so renaming is
    a title change.

## Flows

Sequences. The sections above say what the system holds and where it ends. A
flow says in what order, and what each step may not do.

### Drill loop

Practice on a pushed problem. The engine points, the platform serves and times,
and the loop records what neither of them can know.

1. The board, ordered by staleness. The user picks a technique.
2. Candidates for it — least recently attempted first, lowest solve rate
   breaking a tie. The user picks one.
3. The technique's card, before the attempt rather than after it.
4. The problem's origin URL. Solving happens on the platform.
5. On return, the user pushes as they always do. The loop waits, then reads
   the log for what appeared against that problem.
6. Keyed to each attempt that appeared, the loop asks for a technique claim
   and a self-label.

- **The loop mints no attempt.** The records come from the platform that
  witnessed them. `origin: engine` stays reserved for the phase where the
  engine produces attempts by verifying them. It is named as a capability
  rather than a phase number, because a stored value's meaning must not change
  when phases are renumbered.
- **Timing is the platform's**, because the work happens there. An attempt it
  did not time stays untimed, rather than carrying a duration the engine
  reconstructed.
- **A drill can mint several attempts.** A sitting is usually several
  submissions, and each is asked about in turn. A submission that failed on
  syntax and the one that passed are different evidence, and labelling only the
  last would leave the counts on two denominators: attempts per submission,
  labels per sitting.
- **The drilled technique is the claim's default.** Selection picked the
  problem by its own tags, so what was just practised is always a legal claim.
  Confirming costs a keystroke, and the problem's other tags are the
  alternatives.
- **The label and the claim are cheap only here.** The candidates are the
  problem's own two or three tags, and the attempt is minutes old. The two
  facts a classifier has to infer later cost a keystroke each at this moment.
- **Nothing pushed, nothing recorded.** Until an attempt exists, the label and
  the claim have nothing to key to, so the loop waits or ends rather than
  holding them against a record that may never arrive.
- **The engine still calls nothing.** It waits on a push and diffs its own log,
  and the diff is exact because the engine knows what was already there. So the
  drill loop needs no client of its own, and works whatever the user pushes
  with.
- **Selection never schedules.** Ordering is a view. What to drill is the
  user's choice until the scheduler lands.

### Adjudicating the eval set

What the classifier is scored against. One reader's blind claims cap at that
reader's own consistency. The reference is therefore a set two readers reached:
the user's blind pass, a frontier model reading the same attempts, and every
divergence resolved by hand.

1. The blind hand claims stand as pass one. Nothing is added to them while a
   reading is in view.
2. The frontier model reads those same attempts as a scored configuration. Its
   claims are readings — stored, never standing.
3. Each divergence is reviewed alone and resolved one of two ways: the
   criterion is edited, or the user's claim is.
4. A criteria edit changes the digest of the attempts it reaches, and the
   frontier reads those again.
5. Repeat until it disagrees with nothing. That is the stopping signal.
6. The set is frozen, and the cheap classifiers are scored against it.

- **The adjudicator is never the classifier.** Its number on this set is 100%
  by construction, because the gold is its own labels wherever the user did not
  overturn them. The number says that adjudication finished, not that the model
  reads well. Anything short of it is either sampling noise or a criterion that
  still does not decide the case.
- **Consistency is what the model is there for.** It applies the same rule at
  the sixtieth attempt as at the first, where a human drifts across one
  sitting. Consistency is not correctness, which is why every divergence is
  decided by hand rather than taken.
- **The blind pass is what keeps the reference independent.** Reviewing a
  proposed label is easier and more permissive than producing one. A claim made
  with a reading in view therefore records what it saw, and never stands in for
  pass one.
- **Which way the divergences went is the check on the process.** Mostly claim
  edits means the rulebook is becoming a transcript of one model. A real share
  of criteria edits means it is doing its own work.
- **What the set cannot show** is a classifier that is right where the frontier
  was wrong. Such a case is recorded as an error, and the attempts both readers
  got wrong the same way are never detected. That is the cost of a fixed
  reference, and it is accepted.

## Invariants

Properties the system holds at all times.

- Attempts, technique claims, self-labels and diagnoses are append-only. The
  guarantee is the running system's: no record is ever revised or removed in
  place. Discarding a private log wholesale, while it holds nothing
  irreplaceable, is a different act. It destroys no evidence, because there is
  none yet to destroy. That window closes the first time a record is worth
  keeping, and does not reopen.
- Every record keyed to an attempt carries an engine-minted `id`, its
  `attempt_id` and `created_at`, so one reader orders any of them.
- The user's own record stands over the machine's answer to the same question,
  whichever was written later: a technique claim resolves user-first, and a
  diagnosis never supersedes a self-label. What the machine wrote is kept and
  scored, never discarded and never promoted.
- Every reference in an append-only record is engine-minted. External ids are
  resolved at the boundary and never stored on an attempt, so the log stays
  readable without the platform that produced it.
- Aggregates are derived views, never stored truth.
- A problem's owner (product or user) is stored state, and determines its
  visibility, test-case availability, attempt origin, verifiability, and
  eligibility for cross-user aggregates. Those are derived, never stored
  independently. The owner is set by the ingest path and never supplied by a
  client.
- Pushed attempts cannot be verified by the platform and never enter cross-user
  aggregates.
- The technique vocabulary is product-owned and global. There are no
  user-authored techniques or cards. Technique codes are stable identifiers
  with a migration path, since attempts, problems, and future user annotations
  reference them. Cards are teaching content and are never referenced by the
  attempt log. A template match references one, but it is a fact about the
  corpus rather than about a sitting, and mastery still reads no card.
- Domain logic stays adapter-free and directly callable. The CLI is one
  adapter, and a web API will be another.
- No third-party problem statements or test cases in git — in any repo.

## Repo constraints

Rules on how this repo is built, rather than properties of the running system.

- No concrete third-party problem-platform client ever enters this repo.
- Schema changes must be additive (new optional fields), never breaking. A
  change may tighten instead — a field made required, a validator widened —
  only while no stored record carries the loose shape, which in practice means
  deleting the ones that do. Weigh what is deleted, not how many. The rule
  exists so the log stays readable by its own schema, and an optional field
  kept for the sake of a handful of disposable records is one every reader
  branches on forever.
- `data/` is gitignored; only the schema is public.
- Prefer tools and functions over agents. A pipeline earns multi-agent, not the
  other way around.

## Meta-rule

Ship thin on features, and let the record schema run one phase ahead.
Component boundaries can be refactored. An append-only log cannot.
