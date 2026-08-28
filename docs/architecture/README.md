# Architecture

Target state. Code lags this doc; where they differ, this doc wins.

## Shape

Engine public, content private. Everything the practice loop reads is local to
the engine. Problems, cards and attempts live in datastores the engine
controls, and the technique vocabulary ships with the package. The engine never
contacts external platforms.

Consequence: no third-party dependency in the drill loop.

**Problems are the product's own, and the engine writes them.** A statement
scraped from a platform cannot ship, which is what forces the question, but the
answer is a capability rather than a licence fix. A generated problem carries
the test cases that decide it. Test cases are what make verification reachable,
and verification is what turns a canonical solution from an assertion into a
fact.

**The engine is the platform.** It serves a generated problem, times the
sitting, runs the submission against the problem's own test cases, and records
the verdict. Serving, timing and judging are all its own. Python only: a
canonical is Python, the test cases are Python-shaped, and a second language is
a runner rather than a record change.

## Terminology

- **Attempt** — a user's solution to a problem, successful or failed.
- **Canonical solution** — an exemplary solution to a problem, written to
  display the approach rather than to pass. Never an attempt.
- **Verification** — executing a solution against a problem's test cases,
  yielding pass or fail. An attempt or a canonical solution alike.
- **Diagnosis** — classifying why an attempt failed. A `Diagnosis` record
  stores the result.

## Data classes

| Class | Owner | Visibility | Write semantics | Source of truth |
|---|---|---|---|---|
| Techniques | product | global | read-only at runtime | this repo, in git |
| Cards | product | global | read-only at runtime | the store, seeded from `content/` |
| Problems | product | global | append-only | the store |
| Test cases | product | global | written with the problem | the store |
| Canonical solutions | product | global | append-only | the store |
| Template matches | product | global | append-only | the store |
| Card runs | user | private | append-only | the store |
| Recall attempts | user | private | append-only | the store |
| Attempts | user | private | append-only | the store |
| Technique claims | user | private | append-only | the store |
| Calls | user | private | append-only | the store |
| Self-labels | user | private | append-only | the store |
| Diagnoses | user | private | append-only | the store |

### Machine records

Claims, template matches and canonical solutions are written by a model. What
each carries to stay comparable is the same, and is stated here once.

- **Provenance is the configuration**: model, effort, the endpoint it was
  pinned to, temperature, the digest of what that record was sent, and the call
  that sent it. All of them or none, since a record whose configuration is
  partly unknown compares with nothing. A model asked for no effort, or one
  that rejects the parameter, records the level it ran at rather than an empty
  field.
- **A pin is part of the reading, not a note about routing.** A model id
  resolves to as many builds as there are endpoints serving it, and
  quantization changes the weights. Unpinned, the router chooses per request,
  so the records under one key are a mixture no later run can separate.
- **Who served it is recorded and never compared.** The router reports a
  company rather than an endpoint, and one company serves several builds. It
  confirms a pin held without identifying the build, and it is unknown when a
  reader asks what it has already read.
- **A reading is greedy, and says so.** Sampling turns a verdict the model
  holds at 0.9 into one it gives four times in five. An eval absorbs that by
  being repeated; a sweep writes into an append-only log the board reads
  forever. Temperature identifies a record for the same reason the pin does:
  one says which weights answered, the other how they were sampled. A
  temperature nobody set is the provider's own default — recorded absent, and
  equal only to itself, which keeps records taken before the parameter existed
  scorable rather than discarded. Generation is the exception, and says why.
- **Staleness keys on the digest of what was sent**, never on a version over
  the rulebook. A criterion travels with its candidate, so editing one entry
  re-derives what that entry reached and leaves the rest. An author can forget
  to bump a version while the text moves; a digest cannot. It costs a reflowed
  sentence re-deriving what it reaches, and a rulebook that is cited as a
  digest rather than as "prompt 3".
- **The record's own copy of the configuration cannot drift**, because a call
  is append-only and the copy is made in the same write. It is there so the log
  reads alone: loading the calls to learn which model produced a record would
  put a megabyte-scale read on every command.
- **The user's record stands over the machine's answer to the same question**,
  whichever was written later. The machine's is stored and scored, never
  promoted. A reader that prefers the user's makes overwriting the evidence
  unrepresentable, where a write path that skips what the user answered depends
  on every writer remembering to.
- **Each configuration is scored over what it read**, and the denominator is
  printed rather than assumed. Scoring over the intersection alone charges
  every column for the records one of them failed on. A share prints as
  `92/98`, so two columns over different samples cannot be read as one rate.
  The reader still supplies the judgement that the harder sample reads as the
  worse reader.

### Techniques

The vocabulary the append-only log references.

- **Versioned as code, not stored as data.** A file shipped with the package,
  not a datastore the engine writes.
- **A code carries the criterion for claiming it**, not only its name: its
  kind, what earns it, and the near miss it is confused with. The near miss
  decides cases, because disputes are about boundaries rather than definitions.
  The codes are four kinds of thing, and one question is answered differently
  for each.
  - A procedure counts when the solution performs it.
  - A structure counts when its properties carry the correctness or the
    complexity.
  - A paradigm counts when it is why the solution is correct.
  - A problem class counts when it is what the problem asks for.
- **A kind reaches both readers as its test, never as its name.** The label
  helps only a reader who already knows what it selects; one who does not will
  judge a structure on whether it was performed. The four tests live with the
  kind, so twenty-seven entries state them once.
- **A code is claimed beside the narrower ones, never instead of them.** What a
  solution does is true at several levels: a backtracking search descends, and
  a search tree is a binary tree. An exclusive rule would need a containment
  order over the codes, and nothing generates one — it could only be written by
  hand pair by pair, then disagreed with case by case. Exceptions are per code
  and stated in the entry: `recursion` names a language mechanism rather than
  an approach, so a row counting every self-call would name no skill.
- **What disqualifies a code is incidental use**, never that another candidate
  covers it. The near miss states that line in full: a sorted lookup beside a
  linear pass that dominates, a map standing in for an array. A reader taking
  the near miss for precedence drops codes the user claimed.
- **Inclusive claiming is what keeps a row coherent.** The fallback is the
  problem's own techniques, and those nest already. Under an exclusive rule a
  claimed attempt and an unclaimed one on the same problem would be counted
  differently, so board numbers would move as classification progressed while
  the practice behind them did not. A claim narrows a row; it never
  re-partitions it.
- **The criteria are the prompt.** They reach the classifier beside the
  candidates and the reader beside the code, so one rulebook answers both.
  Editing an entry changes readings, but only for the attempts carrying that
  candidate.
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

- **Product data, not code.** Cards live in the engine datastore, seeded from
  `content/`, which is gitignored like `data/`. One location, whatever the
  content turns out to be worth keeping private.
- **Granularity follows teaching, not estimation.** One technique can carry
  several cards. Mastery is estimated per technique, so cards are never the
  unit of estimation, and the attempt log never references one.
- **A card names no problem.** It carries a selector: a technique, and the
  filters that narrow it. The ladder is derived from the corpus. Ids are minted
  per engine, so a card holding them would mean nothing in another store, where
  a selector ships anywhere.
- **The ladder covers every studied template.** Its rungs come from the
  template matches, at least one per template, and the selector fills the rest
  out to `size`. Drawn from the selector alone it would exercise the technique
  and leave some forms untouched, since a technique says what a problem is
  about rather than which form solves it.
- **Requiredness is derived from what a rung covers**, never stored. A rung
  covering a studied template is required. A rung covering only the optional
  template is optional. A rung covering both is required, and the optional
  template is offered on it as the alternative approach. That last case is why
  a problem matching several templates is wanted rather than a nuisance.
- **A studied template with no match is a reported gap**, not a quietly shorter
  ladder, and the gap is the input to the next generation run: a form the
  corpus cannot exercise names its own remedy. It creates the work and never
  does it — a ladder that filled itself would be one nobody inspected, and the
  corpus is the product.
- **The recognition cue is its own field**, apart from the prose it could sit
  in, because a probe asks exactly that question: is the form recognised
  unprompted. So it is shown and withheld on its own, where the rest of what to
  read is one authored block the engine never parses. It is carried at both
  levels — the card's says to reach for the technique, a template's says which
  of its forms — because recall is per template.
- **One template may sit outside the studied set.** A card carries at most one
  optional template, the capstone, authored whole and surfaced on request
  alone. The hard form is worth deriving before it is read, and a card showing
  it unasked would remove that chance permanently.
- **The ladder is resolved at import**, once. The selector is the truth and the
  ladder a derived view, so re-deriving it is legal — but never for a card
  already started, since a user is working through it.
- **Probes are assigned when a card is started**, not at import, since what was
  unseen at import need not still be unseen. Unseen first, then least recently
  attempted, and never drawn from the ladder, which teaches the form rather
  than testing whether it is recognised unprompted.

### Template matches

Which problems exercise which of a card's templates. The ladder's coverage is
computed from these records. They are the engine's own work: an author names no
problem, so nothing is authored here either.

- **A generated problem asserts its own first match.** It was written for one
  template, so that pair is provenance rather than a reading, and the record
  names `generator` as its source. Nothing pays a call to learn what the
  generator was told to write.
- **The matcher answers what generation cannot assert**: which templates a
  problem exercises besides the one it was written for, and whether the
  generator's own claim holds. The first is why a rung can cover a studied
  template and an optional one at once, the second the only check on a
  generator drifting from its brief.
- **Three writers, ordered by what each of them knew.** A hand annotation
  stands over both machine sources. A generator's assertion stands over a
  matcher's reading of the same pair, because the generator knew and the
  matcher inferred.
- **One record per template and problem, carrying a verdict.** Not a set per
  template: problems arrive one at a time, and a set record would rewrite pairs
  already settled every time the corpus grew. A claim asserts a whole set
  because the set is the assertion; a match asserts one pair, and pairs are
  independent. A problem matching several templates is the ordinary case.
- **A negative is stored.** Otherwise every re-run re-tests every non-match
  forever. What still needs testing is the pairs carrying no record at the
  current configuration, which is the rule `score` already uses for readings.
- **Written after card import, never before.** Both references are minted: the
  template at import, the problem at generation. So a match cannot be authored
  against a seed file.
- **A call is per problem and card, a record is per pair.** The candidates are
  that card's templates, and the answer is the subset the problem exercises,
  which is the classifier's shape. The records come from one answer.
- **Not every pair is asked about.** A problem is offered only to cards whose
  technique it carries, or the work is every template against every problem for
  an answer that is almost always no. Procedure templates are excluded
  outright: a framing procedure is exercised by every problem its technique
  reaches, so a per-problem verdict carries no information.
- **A card's relation to a problem is a fold over its templates**, never a
  record of its own. A rung is earned when the technique reaches the problem
  and some template matches. Nothing asserts in one place that a problem
  belongs to a card, so nothing is rewritten when one verdict changes.
- **Re-derivation is the normal path, not an exception.** A technique claim
  asks about one attempt, and the question never changes. A match is a template
  against a corpus that grows with every generation run.
- **A hand record settles what stands, not what has been read.** The run path
  skips a pair only where the hand pass settled every template of that card.
  The call asks about the card whole, and a partly annotated card is a question
  still worth asking. The eval reads annotated pairs on purpose, because that
  reading is the measurement.
- **Agreement is per pair, grouped per template.** A call carrying six pairs
  saves requests; it is not a unit of truth. Grouping follows the ladder: a
  form the matcher over-matches fills its rung with problems that do not teach
  it, and one number over the card would average that away.
- **Nothing is scored as a set, and accuracy is not the metric.** A match
  asserts a pair, and a matcher that says yes to everything is already visible
  as a false positive on every template. Most pairs are negative, so a matcher
  naming nothing would score in the nineties and resolve an empty ladder. What
  is scored is the positive verdicts, both directions: what the annotator named
  and the machine missed, and what the machine named and the annotator did
  not.
- **An empty answer is negatives, not a decline.** A claim naming nothing
  answers nothing, and the problem's own techniques keep standing. A call
  naming no template asserts that each of them does not match, which is a
  verdict on every pair and is scored as one. The record shape decides this,
  not the model's behaviour.
- **An annotation records the verdicts its author saw**, as a claim does.
  `informed_by` names them one by one, so a record made after seeing one
  matcher is still independent of another. It is written on every pair the
  answer settles, negatives included, because what the reader saw is a fact
  about the sitting rather than about the verdict.
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

- **Not an `Attempt`.** No problem and no submission. Nothing keys it to an
  attempt, so it is its own record, keyed to a card and a template.
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

- **Generated, and that is the only origin.** The engine writes a problem for
  one of a card's templates: a statement, the test cases that decide it, and at
  least one canonical solution. Nothing lands until the canonical passes.
- **The template it was written for is stored.** `generated_for` is an
  assertion rather than a reading, and it is what makes the first template match
  provenance. It never claims the problem exercises nothing else.
- **Provenance is required.** A problem names what produced it, as any machine
  record does.
- **A problem's techniques are derived from its canonical solutions**, and are
  a view rather than stored truth: adding a canonical can widen them, and
  re-deriving is legal and expected. The card's technique names only what the
  problem was written for. A canonical that sorts before it searches used two
  techniques, and only the derivation names the second.
- **Which is why the fallback answers the right question.** They name what
  solving the problem can take, over every canonical it carries, where a claim
  names what one attempt did.
- **The statement is stored, because the matcher reads it.** Which template a
  problem exercises is a question about what it asks. Its techniques answer
  only what it is about. Required and non-blank.

### Test cases

What decides whether a solution to a generated problem is correct.

- **Written with the problem, in the same call.** Cases derived afterwards
  describe whatever the solution happens to do. Cases written with the statement
  describe what the problem asks.
- **They are what makes verification reachable.** Every problem carries the
  cases that decide it, so the engine judges a submission itself rather than
  recording a verdict it did not produce.
- **Owned, so the git invariant binds nothing the product ships.** The rule
  against third-party test cases in git holds, and the cases a generated problem
  carries are the product's own.
- **Expected outputs taken from the canonical make verification a tautology.**
  It passes by construction, and `verified` then means only that the solution
  agrees with itself. That is the fact a quality bar has to answer.
- **Cases that separate nothing are worse than none**, because they license the
  word `verified` on a canonical that is wrong. A set that does not discriminate
  is a defect in the problem, and a problem carrying one does not land.
- **How discrimination is established is deferred.** Candidates: two canonicals
  from different approaches agreeing on every case, a mechanically broken
  canonical failing, the near miss the technique entry names failing. Which is
  the bar is a question a real corpus answers and an argument does not.

### Canonical solutions

An exemplary solution to a problem, written to display the approach. Not an
attempt: no user and no sitting.

- **Exemplary and verified are different properties**, and the record needs
  both. A user's solved attempt is verified and idiosyncratic. A generated
  solution is exemplary and asserted. Only one that passes the problem's test
  cases is both.
- **It is what a template match reads.** Which form a problem exercises is a
  question about the solution, and a statement only implies one. The matcher
  reads the canonical beside the statement.
- **Several per problem, and the set is the assertion.** Two approaches to one
  problem is the ordinary case, and it is what lets one rung cover a studied
  template and an optional one. A problem carrying one canonical can teach one
  form.
- **Never counted as an attempt.** It answers no board row and earns no
  progress. A user who reads one has not solved the problem.
- **Sampled, not greedy — the exception Machine records names.** Generation
  produces the artifact rather than a verdict about one, so no verdict needs
  protecting from variance, and variance is what stops one model's habits
  becoming the whole corpus. The cost is a canonical that is re-runnable and
  never reproducible, which is also why nothing re-derives it.
- **The verification result is stored, never inferred**: which cases it passed
  and how many the problem had. A count rather than a flag, for the same reason
  a share prints its denominator.

### Attempts

- **The drill loop is the only source.** The engine served the problem and
  watched the sitting, so nothing else is in a position to assert one.
- **Identity is the engine's.** It mints the `id`, and there is no other writer
  to accept one from.
- **The verification result is kept whole**, not only its verdict. `solved` is
  the projection over it, and the raw result carries what the projection drops.
  A timeout and a wrong answer are both unsolved, and only one is evidence of
  slowness.
- **Problem techniques are never denormalized onto an attempt.** They are
  re-derivable and the log is not, so a copy taken when the attempt was written
  would drift with no way to tell which is right.

### Technique claims

Which techniques an attempt used. Per-technique progress is measured from this.
A claim rather than a fact, and open to revision, so it is its own record
rather than a field on the attempt.

- **Attribution resolves, it is not required.** The claim that stands if one
  exists, otherwise the problem's techniques. Nothing has to be labelled for an
  attempt to count. Resolution happens on read and is never stored, so
  re-deriving a problem's techniques reaches every unclaimed attempt.
- **The fallback answers a different question.** A problem's techniques say
  what solving it can take, a claim what one solution did. The fallback
  over-credits techniques a canonical used incidentally, which skews scheduling
  away from the weakest ones.
- **Two writers, user first.** The drill loop asks at the moment of solving,
  and a hand pass reaches attempts no loop touched. A classifier fills the rest,
  and a later user claim corrects it.
- **The classifier is prompted, not trained.** Public corpora tag problems
  rather than solutions, so a model trained on them predicts the fallback
  instead of improving on it, and nobody has labelled what a given solution did
  because doing so means reading it. Reading it is semantic work: two-pointers
  and sliding-window differ in their invariant rather than their syntax,
  backtracking is depth-first search plus an undo, and greedy is a property of
  why a choice is correct rather than a construct. A scan of imports and
  keywords is weakest exactly where the claim is worth making.
- **What the classifier is shown besides the code is deferred.** The code is
  the subject and stays; whether the problem's canonicals or the candidates'
  templates improve a reading is a question a measured comparison answers.
- **A richer prompt can change the question rather than the answer.** Shown a
  problem's canonicals, a classifier can report which one the attempt resembles
  instead of which techniques its code used. Those are different labels, and
  the hand claims were made against the second. A configuration that moves the
  question is not comparable to one that answers it better.
- **A claim is scored against the user's own**, per technique rather than
  overall, by set equality rather than overlap. The board is per technique, so
  a classifier that over-claims one code skews it, and a claim naming every
  candidate decides nothing while scoring well on a metric that only asks
  whether the right code appears.
- **How often a claim names every candidate is reported beside the score.**
  Claiming inclusively removes the reason to withhold a code, so the way it
  fails is by naming all of them — which is the fallback, and agrees with it
  whenever the fallback is right. Set equality cannot catch that.
- **The hand claims are an eval set and a correction path**, never training
  data. Nothing in the engine is trained.
- **What invalidates a label is which reader informed it, not that one did.** A
  claim made with the scored configuration's reading in view measures that
  configuration against itself. A claim adjudicated against a reader that is
  never scored is neither — it is how the boundary gets drawn. So `informed_by`
  names the readings its author saw, one by one, and a set can be read back for
  either question.
- **The eval set holds one attempt per problem**, its latest carrying code,
  since a retry asks the identical question and a repeat would measure one
  decision twice. The drill loop still asks about every attempt of a sitting,
  where the answer costs a keystroke.
- **One claim per attempt**, naming every technique it used, since a solution
  can use several. A later claim replaces the whole set rather than rewriting
  the earlier one.
- **A verdict naming no candidate is a reading, and is stored.** It is evidence
  about the code rather than an absence of it, and unstored it would be re-read
  by every later run. A reply cut short by the token cap also names nothing and
  is stored for the same reason, but it is a fact about the configuration
  instead. The call's `stop_reason` separates them, and the report counts them
  apart.
- **An empty claim answers nothing, so the fallback stands.** The resolver
  reads a claim's *techniques* rather than its existence, so the problem's own
  keep answering an attempt whose reading declined. A later decline supersedes
  an earlier claim as any reading does, and what that costs is the older
  answer giving way to the fallback.
- **A decline is scored all the same.** It asserts that none of these
  candidates apply, so a hand claim naming one is a miss against every
  technique the user named. Unscored, declining would pay: each one would leave
  a smaller denominator and a better share over it. Only an attempt nothing
  read stays unscored, and the count of declines prints beside the share.
- **A decline is stated, never inferred from an empty set.** The user says so
  with `declined`, since the loop records nothing where they skip and emptiness
  would make a lost answer and a stated verdict one record. The classifier
  needs no flag: it answers or it fails, and a failure writes no claim. The
  eval set holds a correct decline, or the attempt could only leave the set by
  deletion.
- **A machine claim on a hand-claimed attempt is a reading, not a candidate.**
  It never stands and never reaches the board; it exists to be scored. Storing
  it makes an eval a dataset rather than a run, and a second configuration is
  then paid for only where it has not read. The classifier still skips such
  attempts, but only to save a call whose verdict could never stand.
- **One record for both writers, not two.** Splitting would mirror `SelfLabel`
  and `Diagnosis`, but claims already written stay in the log forever, so a
  reader carries the old shape regardless. A third record written only by the
  eval is worse: the same verdict would be a claim or a reading depending on
  what else was claimed.
- **Every claim records its source.** A user's carries no provenance, because
  nothing re-derives it; a machine claim carries all of it, which is how a
  re-derivation finds the stale ones and leaves the rest. Both count the same
  toward progress.

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
  decline names no candidate and a failure names nothing, so neither reaches a
  claim at all. Without this record both are counters that print once.
- **One transport, one shape.** Every model is reached as chat completions
  through a router, so adding a model is a string and adding a provider is a
  base URL. Two provider shapes maintained by hand would create pressure to
  adopt a library that reconciles them, and such a library can downgrade a
  schema into a prompt where the record cannot show it happened.
- **Every request names one endpoint, and records who answered.** A provider
  that cannot honour the response schema is never chosen, and a request fails
  rather than falling back to a backend the record would not name. The pin says
  which build was asked for and is what a re-run needs; the server says whether
  anything answered at all. What it was sampled at is recorded beside them, and
  a claim's copy is taken from here.
- **Reasoning is what the reading produced, not what was asked for.** A model
  that decides a question needs no thought returns none, and the empty field is
  a fact about the reading rather than a gap in the record.
- **A call is timed at two levels**: what the caller waited and how many
  requests that took, beside what the last request took alone. Their difference
  is the endpoint's backoff, and without it a run held behind a per-minute cap
  reads as a slow model.
- **Nothing on the run path reads it back.** Whether to ask again is decided
  from the claims, which carry the configuration already. The file is written
  by every run and loaded only to analyse one.

### Self-labels

The user's own verdict on why an attempt went the way it did. Reported, not
inferred. A judgement made after the fact and open to revision, so it is its
own record rather than a field on the attempt, for the same reason a claim is.

- **Only ever the user's.** A machine answering the same question produces a
  `Diagnosis`. The two are separate records because the eval scores one against
  the other, and a shared record read latest-first would let the machine
  supersede the evidence it is measured against.
- **One label per attempt**, latest wins on read.
- **The drill loop is the only writer.** The question is asked at the moment of
  solving, and nothing else is there to ask it.
- **A label cannot be given later, where a claim can.** The evidence for a
  claim is the code, which does not decay; for a label it is recall, which
  does. What survives months on — a timeout, a compile error — is what a
  `Diagnosis` reads, and a label recalled that late is either invention or the
  classifier's own input handed back as evidence against it.

### Diagnoses

Why an attempt failed, inferred rather than reported. Keyed to an attempt and
carrying provenance as any machine record does, so every attempt can be
re-diagnosed and compared.

- **The machine counterpart of a self-label, never its replacement.** Neither
  supersedes the other, and agreement between them is the eval. A later
  diagnosis is a second reading rather than a correction.

### What every record keyed to an attempt carries

Claims, self-labels and diagnoses share a base: an engine-minted `id`, the
`attempt_id` they assert about, and `created_at`. One reader orders all three,
latest first, with append order breaking a tie. The `id` lets a record be
cited, by an eval naming the diagnosis it scored or by a user correcting a
claim.

Ordering is not what stands. A self-label has one writer, so the latest stands.
A claim has two, and the user's stands over any machine claim however late. A
diagnosis never supersedes a self-label at all. The shared reader answers "in
what order", and each record says who wins.

## Boundaries

- **Verification** — runs locally, against test cases the engine owns. Every
  problem carries them, so every submission is judged by whatever ran it.
- **Storage** — concrete for now (JSON files under a gitignored directory), a
  database later. The schema is the contract, and storage swaps underneath it.
- **Calibration corpus** — what the pivot to generated problems left behind,
  under `data/old/`: a platform's problems, the attempts against them, the
  claims and the calls. It is a corpus, not a store. No store points there, and
  nothing on the run path reads it.
  - It is kept for one measurement. The announcement floor is how often a form
    is named from the statement alone, and a corpus no generator wrote is what
    sets that floor. How it is read is deferred to taking that measurement.
- **Content generation** — problems, their test cases and their canonical
  solutions are written by the engine, as a command beside the classifier and
  the matcher. It reuses one transport, one call log and one provenance base,
  rather than standing a second copy of each somewhere else.
  - Extraction to a pipeline of its own stays possible and is not planned. What
    it would have to preserve is the minted ids, since the attempt log
    references them.
- **Card ingest** — cards are authored in `content/` and seeded into the
  datastore. File-based for now, and gitignored like `data/`. The technique
  vocabulary is the exception: it ships with the package, in git.
  - What an author writes has its own shape. `CardSeed`
    (`src/algo_coach/schema/seed.py`) is the payload the stored card is built
    from, not the card, and it has no field for the identity the engine mints.
  - A card and each template are matched by their authored slug, which makes
    re-seeding refresh rather than duplicate. A new slug is a new card: the
    runs and the recall history stay with the old one, so renaming is a title
    change.

## Flows

Sequences. The sections above say what the system holds and where it ends. A
flow says in what order, and what each step may not do.

### Generating a problem

A problem, its test cases and its canonical solution are written together. The
order matters because each step can reject what came before.

1. A card's template, and the brief: write a problem this form solves.
2. The statement, the canonical solution and the test cases, from one call.
3. The canonical runs against the cases.
4. All of it lands together, with the template match the generation asserts.
5. The matcher reads the problem later, for the templates it was not written
   for.

- **Nothing lands half-verified.** A problem whose canonical fails is discarded
  whole rather than stored for repair. The call is recorded either way, so what
  was paid for and thrown away stays readable.
- **The generator's assertion is not the matcher's verdict.** They are two
  records on one pair, and a disagreement is how a generator drifting from its
  brief is found.
- **Announcement is measured, not assumed.** What is being trained is reaching
  for a form unprompted, so the enabling property has to be derivable from the
  statement rather than stated in it. A form a matcher names instantly from the
  statement alone was telegraphed, and such a problem teaches recognition of
  nothing. The archived corpus sets that floor and the generated one is read
  against it.

### Drill loop

Practice on a generated problem. The engine serves the statement, times the
sitting and judges the submission, and records what only the user can say.

What is not designed here is the interaction: how a solution is entered, what
the loop does with a failing run, and whether a sitting can be resumed. Those
are answered by using it.

1. The board, ordered by staleness. The user picks a technique.
2. Candidates for it — least recently attempted first, lowest solve rate
   breaking a tie. The user picks one.
3. The technique's card, before the attempt rather than after it.
4. The statement, and the clock starts.
5. The submission runs against the problem's own test cases, and the attempt is
   minted carrying the result.
6. Keyed to each attempt, the loop asks for a technique claim and a self-label.

- **The engine witnessed the sitting, so it mints the attempt.** Serving,
  timing and judging are one act. An attempt nobody timed stays untimed, rather
  than carrying a duration reconstructed after the fact.
- **A drill can mint several attempts**, and each is asked about in turn. A
  submission that failed on syntax and the one that passed are different
  evidence, and labelling only the last would leave the counts on two
  denominators: attempts per submission, labels per sitting.
- **The label and the claim are cheap only here.** The candidates are the
  problem's own two or three techniques, the drilled one is the default since
  selection picked the problem by it, and the attempt is minutes old. Two facts
  a classifier has to infer later cost a keystroke each at this moment.
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
  by construction, since the gold is its own labels wherever the user did not
  overturn them, so the number says adjudication finished rather than that the
  model reads well.
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

- Attempts, technique claims, self-labels and diagnoses are append-only: no
  record is ever revised or removed in place. Discarding a private log
  wholesale while it holds nothing irreplaceable is a different act, and that
  window closes the first time a record is worth keeping.
- Every record keyed to an attempt carries an engine-minted `id`, its
  `attempt_id` and `created_at`, so one reader orders any of them.
- The user's own record stands over the machine's answer to the same question,
  whichever was written later: a technique claim resolves user-first, and a
  diagnosis never supersedes a self-label. What the machine wrote is kept and
  scored, never discarded and never promoted.
- Every reference in an append-only record is engine-minted, so the log stays
  readable without anything outside the engine.
- Aggregates are derived views, never stored truth.
- Every problem is the product's own, written by the engine.
- A problem never lands without the test cases that decide it and a canonical
  solution that passed them. One whose canonical fails is not stored for
  repair; it is not stored.
- The technique vocabulary and the cards are product-owned and global, with no
  user-authored ones of either. Codes are stable identifiers with a migration
  path, since the log references them. The attempt log never references a card;
  a template match does, but it is a fact about the corpus rather than about a
  sitting, and mastery reads no card.
- Domain logic stays adapter-free and directly callable. The CLI is one
  adapter, and a web API will be another.
- No third-party problem statements or test cases in git — in any repo.

## Repo constraints

Rules on how this repo is built, rather than properties of the running system.

- No concrete third-party problem-platform client ever enters this repo.
- Schema changes must be additive (new optional fields), never breaking. A
  change may tighten instead — a field made required, one removed, a validator
  widened — only while no stored record carries the loose shape, which in
  practice means deleting the ones that do. Weigh what is deleted, not how
  many: the log has to stay readable by its own schema, and a field kept for a
  handful of disposable records is one every reader branches on forever.
- `data/` and `content/` are gitignored; only the schema is public. The
  generated corpus could be committed, since the product owns it, and is not:
  those directories also hold the private log, and storage moves to a database
  before the corpus ships anywhere.
- Prefer tools and functions over agents. A pipeline earns multi-agent, not the
  other way around.

## Meta-rule

Ship thin on features, and let the record schema run one phase ahead.
Component boundaries can be refactored. An append-only log cannot.
