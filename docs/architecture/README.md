# Architecture

Target state. Code lags this doc; where they differ, this doc wins.

## Shape

Engine public, content private. Everything the practice loop reads is local to
the engine: problems, cards, and attempts live in datastore(s) the engine
controls, and the technique vocabulary ships with the package. The engine never
contacts external platforms; user clients push data in.

Consequence: no third-party dependency in the drill loop.

## Terminology

- **Attempt** — a user's solution to a problem, successful or failed.
- **Verification** — executing an attempt against a problem's test cases,
  yielding pass or fail.
- **Diagnosis** — classifying why an attempt failed; a `Diagnosis` record
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

- **Versioned as code, not stored as data** — a file shipped with the package,
  not a datastore the engine writes.
- **A code carries the criterion for claiming it**, not only its name. The
  codes are four kinds of thing, and one question asked of all four is
  answered differently for each. Every code names its kind, what earns it, and
  the near miss it is confused with — the near miss being the load-bearing
  half, since the disputes are boundaries rather than definitions.
  - A procedure counts when the solution performs it.
  - A structure counts when its properties carry the correctness or the
    complexity.
  - A paradigm counts when it is why the solution is correct.
  - A problem class counts when it is what the problem asks for.
- **A kind reaches both readers as its test, never as its name.** The label
  helps only a reader who already knows what it selects, and a reader who does
  not judges a structure on whether it was performed. The four tests live with
  the kind rather than in the vocabulary file, so twenty-seven entries state
  them once.
- **A code is claimed beside the narrower ones, never instead of them.** What a
  solution does is true at several levels — a backtracking search descends, a
  search tree is a binary tree — and a claim names every level it worked at. An
  exclusive rule would need a containment order over the codes, which nothing
  generates, so it can only be hand-written pair by pair and disagreed with
  case by case. The exceptions are per code and stated in the entry: `recursion`
  names a language mechanism rather than an approach, so a row counting every
  self-call would name no skill.
- **What disqualifies a code is incidental use**, never that another candidate
  covers it. The near miss carries that line, and carries the whole of it: a
  sorted lookup beside a linear pass that dominates, a map standing in for an
  array. Reading it as precedence is what made the classifier drop codes the
  user claimed.
- **Inclusive claiming is what keeps a row coherent.** Attribution falls back
  to the problem's tags, and platform tags already nest, so an exclusive claim
  would count a claimed attempt and an unclaimed one on the same problem by
  different rules — and the mixture would shift as classification progressed,
  moving the board while nothing about the practice changed. A claim narrows a
  row; it never re-partitions it.
- **The criteria are the prompt.** They reach the classifier beside the
  candidates and the reader beside the code, so one rulebook answers both.
  Editing one therefore changes readings, and changes them only for the
  attempts carrying that candidate — which is why what a reading was made
  against is a digest of the text that attempt was sent, and never a version
  number covering the whole rulebook.
- **A code is never deleted**, because records carrying it outlive it.
  Retirement means an entry in an alias map, applied when grouping.
- **Membership is checked on the write path only.** A model that validated
  codes on read would make the log unreadable by its own schema the moment a
  code was retired.

### Cards

Teaching content about a technique — not the vocabulary itself.

A card organises studying one technique: what to read, what to reproduce from
memory, and what to solve. It is not an ability estimate — mastery is what a
user can solve, per technique, and the two share no data.

- **Product data, not code** — cards live in the engine datastore, seeded from
  a private repo that holds their version history.
- **Granularity follows teaching, not estimation.** One technique can carry
  several cards. Mastery is estimated per technique, so cards are never the
  unit of estimation, and the attempt log never references one.
- **A card names no problem.** It carries a selector — a technique and the
  filters that narrow it — and the ladder is derived from the corpus. Ids are
  minted per engine, so a card holding them would mean nothing in another
  store, where a selector ships anywhere.
- **The ladder covers every studied template.** Its rungs come from the
  template matches, at least one per template, and the selector fills the rest
  out to `size`. A ladder drawn from the selector alone would exercise the
  technique and leave forms untouched, since a tag says what a problem is about
  and not which form solves it.
- **Requiredness is derived from what a rung covers**, never stored. A rung
  covering a studied template is required; one covering only the optional
  template is optional; one covering both is required, and the optional
  template rides on it as the alternative approach. That last case is why a
  problem matching several templates is the point rather than a nuisance.
- **A studied template with no match is a reported gap**, not a quietly shorter
  ladder. The card claims to teach that form, so a corpus that cannot exercise
  it is a fact about the store worth surfacing.
- **The recognition cue is its own field**, apart from the prose it could sit
  in. A probe asks exactly it — whether the form is recognised unprompted —
  so it is shown and withheld on its own, and the rest of what to read is one
  authored block the engine never parses.
- **The cue is carried at both levels**, answering different questions: the
  card's says to reach for the technique, a template's says which of its forms.
  Recall is per template, so a card-level cue alone would be right about the
  technique and silent about what has to be reproduced.
- **One template may sit outside the studied set.** A card carries at most one
  optional template — the capstone — and never only optional ones. It is
  authored whole and surfaced on request alone: the hard form is worth deriving
  before it is read, and a card that volunteered it would spend that once and
  for good.
- **The ladder is resolved at import**, once, and a re-import never rewrites
  the ladder of a card already started. Same rule as a problem's minted id,
  and for the same reason: something is already working through it.
- **Probes are assigned when a card is started**, not at import, and more can
  be assigned after. What was unseen at import need not still be, and the
  ordering answers it — unseen first, then least recently attempted. They are
  never drawn from the ladder, which teaches the form rather than testing
  whether it is recognised unprompted.
- **A probe is not scarce.** With nothing unseen left, the least recently
  solved stands in: someone who has solved everything in the technique is
  past the point where the distinction pays for itself.
- **Resolution is the engine's, as tag mapping is.** The selector is the
  truth and the ladder a derived view, so re-deriving it is legal — for a
  card nobody has started.

### Template matches

Which problems exercise which of a card's templates. What the ladder's coverage
is computed from, and the engine's own work: an author names no problem, so
nothing is authored here either.

- **One record per template and problem, carrying a verdict.** Not a set per
  template: problems arrive one push at a time, and a set record would rewrite
  pairs that were already settled every time the corpus grew. A claim asserts
  the whole set for one attempt because the set is the assertion; a match
  asserts one pair, and the pairs are independent.
- **A negative is stored.** Otherwise every re-run re-tests every non-match
  forever. What still needs testing is the pairs carrying no record at the
  current configuration — the rule `score` already uses for readings.
- **A problem may match several templates**, and a template many problems. Two
  approaches to one problem is the ordinary case, and it is what lets a single
  rung cover a studied template and an optional one at once.
- **Written after card import, never before.** Both references are minted — the
  template at import, the problem at ingest — so a match cannot be authored
  against a seed file.
- **A call is per problem and card, a record is per pair.** The candidates are
  that card's templates and the answer is the subset the problem exercises,
  which is the classifier's shape; the records come from one answer.
- **Candidates are pre-filtered by technique.** A problem is offered only to
  cards whose technique its tags reach, or the work is every template against
  every problem for an answer that is almost always no.
- **Procedure templates are excluded.** A framing procedure is exercised by
  every problem its technique reaches, so a per-problem verdict carries no
  information; it is covered by the ladder as a whole.
- **A card's relation to a problem is a fold over its templates**, never a
  record of its own. The technique reaches the problem and some template
  matches: that is what earns a rung, and it is derived from the pairs rather
  than stored beside them. Nothing asserts that a problem is a card's in one
  place, so nothing has to be rewritten when one template's verdict changes.
- **Re-derivation is the normal path, not an exception.** A technique claim
  asks about one attempt and the question never changes; a match is a template
  against a corpus that grows with every push.
- **Provenance as a claim carries it**: the source, and on a machine match the
  model, effort, prompt digest and call.
- **Two writers, and the user's stands.** A hand annotation is what a machine
  run is measured against, so it stands on read whenever it was written, and a
  machine verdict on an annotated pair is a reading — stored and scored, never
  what a ladder resolves from. One rule, stated once for claims and holding
  here: the record the machine cannot recompute wins.
- **A hand record settles what stands, not what has been read.** The run path
  skips a pair only where the hand settled every template of that card, since
  the call asks about the card whole and a partly annotated one is a question
  still worth asking. The eval reads annotated pairs on purpose — that reading
  is the measurement.
- **Agreement is per pair, grouped per template.** A match asserts one pair, so
  the pair is what agrees or disagrees; the call that carried six of them is an
  economy of asking, not a unit of truth. Grouped per template because the
  ladder is per template: a form the matcher over-matches fills its rung with
  problems that do not teach it, and one number over the card averages that
  away.
- **Nothing is scored as a set.** A claim is scored whole because it asserts a
  whole set, and only equality catches the claim that names every candidate. A
  match asserts a pair, and the matcher that says yes to everything is already
  visible as a false positive on every template — the same signal, without a
  second number and without a metric that calls six verdicts wrong for one bad
  one.
- **Accuracy over the pairs is not the metric either.** Most pairs are
  negative, so a matcher that names nothing scores in the nineties and resolves
  an empty ladder. What is scored is the positive verdicts, both directions:
  what the annotator named and the machine missed, and what the machine named
  and the annotator did not.
- **An empty answer is negatives, not a decline.** A claim naming nothing
  answers nothing and leaves the tags standing; a call naming no template
  asserts that each of them does not match, which is a verdict on every pair
  and is scored as one. The record shape decides that, not the model's
  behaviour.
- **The first hand pass calibrates, a blind one measures.** Annotating is where
  the line between exercising a form and merely admitting it gets drawn, so a
  score taken over the pairs that drew it is agreement with itself. The eval
  set is annotated from the templates alone, and configurations are compared
  over the pairs both read — the claims rule, unchanged.

### Card runs

Studying a card is an act, not a state that drifts into being.

- **Starting is explicit**, because the ladder is measured from it. A ladder
  problem solved before the card began does not count toward it — the card
  teaches the form, and having solved the problem once is not having studied
  it.
- **The run holds what the start produced**: when it began and the probes it
  was given. Later probes append rather than replacing the set, so what was
  offered and when stays readable.
- **Derived from it, never stored**: ladder progress, recall state per
  template, and whether the card is done. Aggregates are views. "Done" is only
  a view for now — graduation becomes a process later, once there are numbers
  to set its box and its probe count from.

### Recall attempts

One template reproduced from memory, and how it went.

- **Not an `Attempt`.** No problem, no platform, no submission — nothing to
  key to an attempt, so it is its own record, keyed to a card and a template.
- **The unit is the template, not the card.** A card's forms are learned and
  lost separately, and a card-level number would average them into silence.
- **A hinted pass is not a pass.** What was taken before succeeding is part of
  the record, or a decaying form reads as a fluent one.
- **Recall fluency is not solving fluency.** Reproducing a form cold is not
  recognising it unprompted, so this never stands in for mastery — the gap
  between them is exactly the false fluency that blocked practice trains.

### Problems

- **Provenance is required.** Product problems need a rights record; pushed
  problems need an origin platform and a pushing user.
- **Two origins.** User-pushed problems arrive through the push API.
  Product-owned problems come from a content pipeline in a separate private
  repo.
- **Push identity is `(user_id, external_id)`**, so a re-push updates rather
  than duplicates. The engine mints the `id`, and it never moves on update,
  because attempts reference it.
- **Tag mapping is owned by the engine.** A pushed problem carries the origin
  platform's tags verbatim and the engine derives its own codes beside them.
  Raw tags are the truth, codes are a derived view, so re-running the mapping
  is legal and expected.
- **An unmapped tag blocks nothing.** It produces no code and the problem still
  ingests: a metadata mismatch must never cost a real attempt.
- **The statement is stored, and matching is why.** Which form a problem
  exercises is a question about what it asks, and tags answer what it is about.
  The invariant against third-party statements is about git, and `data/` is
  gitignored: the engine stores what a user pushed to their own store, and no
  repo carries it.
- **Required, and non-blank — the one metadata gap that does block.** It landed
  optional, was backfilled across the corpus, then tightened while nothing
  stored carried the loose shape. The reason it is not an unmapped tag: a
  missing code costs one problem its place in one board row, where a missing
  statement is a problem that can never be matched and says so nowhere. That
  silence is what the field exists to prevent, so it fails at the boundary
  instead — per record, and the push is re-runnable once the scrape catches up.
  A blank string is the same absence wearing a value, so it is rejected too.

### Attempts

- **One source per problem** — the user if the problem is user-pushed,
  otherwise the engine.
- **Identity is the engine's.** A pushed attempt carries a client-minted id,
  unique per user, so re-pushing an ingested one is a no-op. The engine mints
  its own id and never accepts one from a client.
- **The problem reference is resolved at ingest**, from the platform's id to
  the minted one. An append-only record must not hold a reference nothing can
  follow, so an unresolvable one is rejected — hence problems are pushed
  first. Rejection is per-record, and re-pushing later is a no-op on what
  landed.
- **Origin is who produced the attempt** — the push API or the engine's own
  drill loop — and is stamped by the ingest path, never sent by a client.
  Whether the verdict rests on a real test run is a separate fact, recorded
  once the engine can verify: the drill loop produces attempts on pushed
  problems, which it cannot verify.
- **The platform's own status is kept verbatim.** `solved` is the projection
  over it, and the raw value carries what the projection drops — a timeout and
  a wrong answer are both unsolved, and only one is evidence of slowness.
- **Problem techniques are never denormalized onto an attempt.** Tags are
  re-derivable, the log is not, and a copy taken at ingest would drift with no
  way to tell which is right.

### Technique claims

Which techniques an attempt used — what per-technique progress is measured
from. A claim rather than a fact, and open to revision, so it is its own record
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
  and a hand pass reaches attempts no loop touched; a classifier fills the
  rest and is what a later user claim corrects.
- **The classifier reads code because no training data exists for this label.**
  Public corpora tag problems, not solutions, so a model trained on them
  predicts the fallback rather than improving on it. Nobody has labelled what
  a given solution did, because doing so means reading it — which is the work
  the classifier is there to do. So it is a prompted model reading the
  solution, not a trained one.
- **Recognising an approach in code is semantic work.** A problem's tags span
  what it admits — several approaches to it, or one solution combining several
  techniques — so choosing among them means reading which the code took.
  Two-pointers and sliding-window differ in their invariant, not their syntax;
  backtracking is depth-first search plus an undo; greedy is a property of why
  a choice is correct rather than a construct. A scan of imports and keywords
  is weakest exactly where the claim is worth making.
- **A claim is scored against the user's own**, per technique rather than
  overall, since the board is per technique and a classifier that over-claims
  one code skews it. Set equality, not overlap: a claim naming every candidate
  agrees with the tags, decides nothing, and would score well on a metric that
  only asks whether the right code appears.
- **How often a claim names every candidate is reported beside the score.**
  Claiming inclusively removes the reason to withhold a code, so the way it
  fails is by naming all of them — which is the fallback, wearing the score of
  whatever the tags happened to get right. Set equality does not catch it,
  since agreeing with the tags scores well whenever the tags are right. The
  hand claims are the reference the machine's share is read against.
- **Those claims are an eval set and a correction path**, never training data:
  nothing in the engine is trained.
- **What invalidates a label is which reader informed it, not that one did.** A
  claim made with the scored configuration's reading in view measures that
  configuration against itself, and the first hand pass over a rulebook still
  being written is agreement with itself for the same reason. A claim
  adjudicated against a reader that is never scored is neither — it is how the
  boundary gets drawn — so `informed_by` names the readings its author saw one
  by one, and a set can be read back for either question.
- **The eval set holds one attempt per problem**, its latest carrying code. A
  retry asks the identical question — same solution, same candidate tags — so
  a repeat measures one decision twice rather than measuring two. The drill
  loop still asks about every attempt of a sitting, where the answer costs a
  keystroke and the count is per submission.
- **One claim per attempt**, naming every technique it used, since a solution
  can use several. A later claim replaces the whole set rather than rewriting
  the earlier one.
- **A verdict naming no candidate is a reading, and is stored.** The
  classifier read the code and found the candidates did not cover it, which is
  evidence about the code rather than an absence of it — and an answer that
  does not change while the question does not. Left unstored it was re-read by
  every later run, paying again for the same decline.
- **An empty claim answers nothing, so the fallback stands.** The resolver
  reads a claim's *techniques* rather than its existence, so the tags keep
  answering an attempt whose reading declined — the board is exactly as it was
  when such a verdict went unrecorded. It is unscored for the same reason:
  missing evidence is not a disagreement. The count is reported, since a
  decline shrinks the denominator and flatters the share.
- **A decline supersedes an earlier claim, as any later reading does.** One
  rule orders the log, and a reading saying the candidates do not fit is not
  weaker evidence than an older one made against a rulebook it disagrees with.
  What it costs is that the older claim's answer gives way to the tags.
- **Only the machine may name nothing.** The drill loop records nothing where
  the user skips, so an empty user claim would be a lost answer wearing the
  shape of a stated one.
- **The user's claim wins on read, the latest of each writer's otherwise.**
  Latest alone would make the two writers race, and the classifier writes far
  more often, so ground truth would last exactly until something re-derived
  over it. The rule is what makes a machine claim safe to store on an attempt
  the user has claimed — and a claim scored against the user's own has to be
  stored, or an eval run is evidence that exists only while it prints.
- **Which is why it is a rule rather than a discipline.** Skipping claimed
  attempts on the write path is one writer remembering to; a writer that
  forgets overwrites the evidence, and an append-only log cannot take it back.
  A reader that prefers the user's makes that unrepresentable. The classifier
  still skips them, but as an economy — a call whose verdict could never
  stand — rather than as what protects the eval.
- **A machine claim on a hand-claimed attempt is a reading, not a candidate.**
  It never becomes the standing claim, never reaches the board, and exists to
  be scored. Storing it makes an eval a dataset rather than a run: what a
  configuration answered stays readable, and a second configuration is paid
  for only where it has not read.
- **One record for both writers, not two.** Splitting them would mirror
  `SelfLabel` and `Diagnosis`, but the classifier claims already written stay
  in the log forever, so a reader carries the old shape whatever else changes.
  A third record written only by the eval needs no migration and is worse: the
  same verdict would be a claim or a reading depending on what else happens to
  be claimed on the attempt, its type decided by its neighbours.
- **Every claim records its source**, and a machine claim what produced it:
  model, effort, the endpoint it was pinned to, temperature, the digest of what
  that attempt was sent, and the call that sent it. Both count the same toward progress, but a machine claim can be
  recomputed by a better classifier and a user's cannot, so re-deriving has to
  find the stale ones and leave the rest. All four or none, since a reading
  whose configuration is partly unknown compares with nothing — and a user's
  claim carries none of them, because nothing re-derives it. A model asked for
  no effort, or one that rejects the parameter, records the level it ran at
  rather than an empty field: the model's own default is a fact about the
  reading, not a gap in it.
- **The digest is of the question, not of the rulebook.** A criterion travels
  with its candidate, so editing one entry changes what a few attempts are
  asked and leaves every other one untouched. Keying staleness on it therefore
  re-derives the slice an edit reached and nothing else, where a rulebook-wide
  version re-derived the backlog for a sentence most attempts never saw.
- **There is no version beside it.** A version was an author's word for "the
  reading changed", and a word can be forgotten while the text moves — the
  digest cannot. What it costs is that a reflowed sentence re-derives the
  attempts it reaches, which is the intended trade: nothing licenses calling an
  edit cosmetic on a model's behalf, and the blast radius is now the entries
  actually touched. What it also costs is a name — a rulebook can no longer be
  cited as "prompt 3", only as the digest of what was sent, and diffed by
  reading the prompts two calls carry.
- **A pin is part of the reading, not a note about routing.** A model id
  resolves to as many builds as there are endpoints serving it, and
  quantization changes the weights — an fp4 endpoint and a bf16 one answer as
  two readers. Unpinned, the router chooses per request, so the readings under
  one key are a mixture that no later run can take apart; the pin is therefore
  required rather than optional, and compared like the model itself.
- **Who served it is recorded and never compared.** The router reports a
  company, not an endpoint, and one company serves several builds of a model —
  so it confirms a pin held without identifying the build. It is also unknown
  when a reader asks what it has already read, which is the question the
  comparison exists to answer.
- **A reading is greedy, and says so.** Sampling turns a verdict the model
  holds at 0.9 into one it gives four times in five, which an eval absorbs by
  being repeated and the backlog sweep cannot: it writes into an append-only
  log the board reads forever, so the same fraction of a percent is permanent
  and moves readings a criteria edit never touched. The temperature is part of
  what identifies a reading for the same reason the pin is: one says which
  weights answered, the other how they were sampled.
- **A temperature nobody set is an arm, not a gap.** `None` is the provider's
  own default, which moves without notice, so it is recorded absent rather than
  guessed at — and it compares equal only to itself. That is what makes every
  reading taken before the parameter existed scorable beside a greedy one
  instead of discarded, and it is the same rule as an unsent effort.
- **The claim's copy cannot drift**, because a call is append-only and the
  copy is made in the same write. It is there so the claims log reads
  on its own: a board renders from it, and loading the calls to learn which
  model produced a claim would put a megabyte-scale read on every command.
- **Configurations are compared over the attempts both read**, not over each
  one's own. A cheaper classifier measured on a smaller sample scores against
  a different denominator, and the number would read as quality.

### Calls

One request to a model and what came back. A layer below the claims: a claim
cites a call and reads its own meaning into the response, and the call knows
nothing about what the answer was for.

- **Domain-free on purpose.** No attempt, no techniques, no vocabulary — only
  what was asked, of whom, and what returned. That is what lets a second domain
  reuse the log without being taught anything, and what keeps the run loop's
  decisions in the domain where they belong.
- **The prompt is stored whole, beside its digest**, so the record digests to
  its own key and a renderer that changes later cannot make an old one
  unreadable. Inline rather than deduplicated into a store of its own: one
  append cannot half-succeed, where a file plus a log line can leave a call
  naming a prompt that is not there.
- **It holds what a claim structurally cannot** — the tokens a run cost, the
  reasoning behind a verdict, and the calls that produced no claim at all. A
  decline names no candidate and a failure names nothing; both were counters
  that printed once and vanished.
- **One transport, one shape.** Every model is reached as chat completions
  through a router, so adding a model is a string and adding a provider is a
  base URL. Two provider shapes maintained by hand is what invites a library
  to reconcile them, and a library that reconciles them can downgrade a schema
  into a prompt where the record cannot show it happened.
- **What was sampled at is recorded beside who served it.** A reading's
  configuration has to be recoverable from the record that holds it, and the
  claim's copy is taken from here.
- **Every request names one endpoint.** A provider that cannot honour the
  response schema is never chosen, and a request fails rather than falling back
  to a backend the record would not name. The pin is stored beside who answered
  it: the first says which build was asked for and is what a re-run needs, the
  second says whether anything answered at all.
- **Reasoning is what the reading produced, not what was asked for.** A model
  deciding a question needs no thought returns none, and the field is empty —
  a fact about that reading rather than a gap in the record. Two calls on one
  prompt can differ here, which is the same adaptive behaviour the noise floor
  already measures.
- **`prompt_hash` is not unique.** A retry after a rate limit repeats it, and
  sampling one prompt on purpose repeats it deliberately, so a reader looking
  one up must say which it wants rather than assume there is one.
- **Nothing on the run path reads it back.** Whether to ask again is decided
  from the claims, which carry the model, effort and digest already — so this
  file is written by every run and loaded only by whoever sits down to analyse
  one. A cache over the calls themselves would serve prompts shared by two
  attempts, and is not built: the log is shaped for it, and the saving is small
  while there is one domain.

### Self-labels

The user's own verdict on why an attempt went the way it did. Reported, not
inferred — a judgement made after the fact and open to revision, so it is its
own record rather than a field on the attempt, for the same reason a claim is.

- **Only ever the user's.** A machine answering the same question produces a
  `Diagnosis`. The two are separate records because the eval scores one against
  the other, and a shared record read latest-first would let the machine
  supersede the evidence it is measured against.
- **One label per attempt**, latest wins on read.
- **The drill loop is the only writer.** A pushed attempt carries no label:
  the platform never asked.
- **A label cannot be given later.** Why an attempt went the way it did is a
  memory of the sitting; what is still recoverable from the record months
  after — a timeout, a compile error — is what a `Diagnosis` reads, so a
  recalled label is either invention or the classifier's own input handed back
  as evidence against it.
- **A claim is retroactive, a label is not.** The evidence for a claim is the
  code, which does not decay; the evidence for a label is recall, which does.
  That is why they are asked separately rather than as two halves of one
  prompt.

### Diagnoses

Why an attempt failed, inferred rather than reported. Keyed to an attempt,
versioned by model and prompt version, so every attempt can be re-diagnosed and
compared.

- **The machine counterpart of a self-label, never its replacement.** Neither
  supersedes the other; agreement between them is the eval.
- **Kept per model and prompt version**, so a later diagnosis is a second
  reading rather than a correction.

### What every record keyed to an attempt carries

Claims, self-labels and diagnoses share a base: an engine-minted `id`, the
`attempt_id` they assert about, and `created_at`. One reader orders all
three — latest by `created_at`, append order breaking a tie — and the `id`
lets a record be cited, by an eval naming the diagnosis it scored or a user
correcting a claim.

Ordering is not the same question as what stands. A self-label has one writer,
so the latest is what stands. A claim has two, and the user's stands over any
machine claim however late; a diagnosis never supersedes a self-label at all.
The shared reader answers "in what order", and each record says who wins.

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
  problems only: pushed problems carry no test cases, so their attempts happen
  outside the engine.
- **Storage** — concrete for now (JSON files under a gitignored directory), a
  database later. The schema is the contract; storage swaps underneath it.
- **Product content ingest** — cards, problems, and test cases are produced by
  an offline content pipeline in a separate private repo, and seeded into the
  engine datastore. File-based for now. The technique vocabulary is the
  exception: it ships with the package, in git.
  - What an author writes is its own shape, as a client's push is: `CardSeed`
    (`src/algo_coach/schema/seed.py`) is the payload the stored card is built
    from, not the card. Identity is the engine's at both boundaries, so the
    payload has no field for it and an author cannot supply one by writing it.
  - A card and each of its templates are matched by their authored slug, which
    is what makes re-seeding refresh rather than duplicate. A new slug is a new
    card: the runs and the recall history stay with the old one, so renaming is
    a title change.

## Flows

Sequences. The sections above say what the system holds and where it ends; a
flow says in what order, and what each step may not do.

### Drill loop

Practice on a pushed problem. The engine points, the platform serves and times,
the loop records what neither of them can know.

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
  engine produces attempts by verifying them — named as a capability rather
  than a number, since a stored value's meaning cannot move when phases do.
- **Timing is the platform's** — the work happens there. An attempt it did not
  time stays untimed rather than carrying a duration the engine reconstructed.
- **A drill can mint several attempts**, since a sitting is usually several
  submissions, and each is asked about in turn. A submission that failed on
  syntax and the one that passed are different evidence, and labelling only
  the last would leave the counts on two denominators: attempts per
  submission, labels per sitting.
- **The drilled technique is the claim's default.** Selection picked the
  problem by its own tags, so what was just practised is always a legal claim:
  confirming costs a keystroke, and the problem's other tags are the
  alternatives.
- **The label and the claim are cheap only here.** The candidates are the
  problem's own two or three tags, and the attempt is minutes old — the two
  facts a classifier has to infer later are a keystroke each at this moment.
- **Nothing pushed, nothing recorded.** Until an attempt exists, the label and
  the claim have nothing to key to, so the loop waits or ends rather than
  holding them against a record that may never arrive.
- **The engine still calls nothing.** It waits on a push and diffs its own
  log — which is exact, since it knows what was already there — so the drill
  loop needs no client of its own and works whatever the user pushes with.
- **Selection never schedules.** Ordering is a view; what to drill is the
  user's until the scheduler lands.

### Adjudicating the eval set

What the classifier is scored against. One reader's blind claims cap at that
reader's own consistency, so the reference is a set two readers reached: the
user's blind pass, a frontier model reading the same attempts, and every
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
  by construction — the gold is its own labels wherever the user did not
  overturn them — so what the number says is that adjudication finished, not
  that the model reads well. Anything short of it is either sampling noise or a
  criterion that still does not say.
- **Consistency is what the model is there for.** It applies the same rule at
  the sixtieth attempt as at the first, where a human drifts across one
  sitting. Consistency is not correctness, which is why every divergence is
  decided by hand rather than taken.
- **The blind pass is what keeps the reference independent.** Reviewing a
  proposed label is easier and more permissive than producing one, so a claim
  made with a reading in view records what it saw and never stands in for pass
  one.
- **Which way the divergences went is the health check.** Mostly claim edits
  means the rulebook is becoming a transcript of one model; a real share of
  criteria edits means it is doing its own work.
- **What the set cannot show** is a classifier that is right where the frontier
  was wrong: it reads as an error, and the attempts both readers got wrong the
  same way stay invisible. That is the price of a fixed reference, and it is
  paid knowingly.

## Invariants

Properties the system holds at all times.

- Attempts, technique claims, self-labels and diagnoses are append-only. The
  guarantee is the running system's: no record is ever revised or removed in
  place. Discarding a private log wholesale, while it holds nothing
  irreplaceable, is a different act — it destroys no evidence, because there is
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
  independently, and the owner is set by the ingest path — never supplied by a
  client.
- Pushed attempts cannot be verified by the platform and never enter cross-user
  aggregates.
- The technique vocabulary is product-owned and global; no user-authored
  techniques or cards. Technique codes are stable identifiers with a migration
  path, since attempts, problems, and future user annotations reference them.
  Cards are teaching content and are never referenced by the attempt log — a
  template match references one, but it is a fact about the corpus rather than
  about a sitting, and mastery still reads no card.
- Domain logic stays adapter-free and directly callable; the CLI is one
  adapter, a web API will be another.
- No third-party problem statements or test cases in git — in any repo.

## Repo constraints

Rules on how this repo is built, rather than properties of the running system.

- No concrete third-party problem-platform client ever enters this repo.
- Schema changes must be additive (new optional fields), never breaking. A
  change may tighten instead — a field made required, a validator widened —
  only while no stored record carries the loose shape, which in practice means
  deleting the ones that do. Weigh what is deleted, not how many: the rule
  exists so the log stays readable by its own schema, and an optional field
  kept for the sake of a handful of disposable records is one every reader
  branches on forever.
- `data/` is gitignored; only the schema is public.
- Prefer tools and functions over agents; a pipeline earns multi-agent, not the
  other way around.

## Meta-rule

Ship thin on features; let the record schema run one phase ahead.
Component boundaries can be refactored. An append-only log cannot.
