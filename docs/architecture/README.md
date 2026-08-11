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
| Problems | product or user | global if product-owned, user-scoped if pushed | read-only if product-owned, mutable cache if pushed | product set, or the pushing client |
| Attempts | user | private | append-only | the store |
| Technique claims | user | private | append-only | the store |
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
  Editing one therefore changes readings: it is a prompt change, it belongs in
  the prompt hash, and a meaningful edit bumps the prompt version.
- **A code is never deleted**, because records carrying it outlive it.
  Retirement means an entry in an alias map, applied when grouping.
- **Membership is checked on the write path only.** A model that validated
  codes on read would make the log unreadable by its own schema the moment a
  code was retired.

### Cards

Teaching content about a technique — not the vocabulary itself.

- **Product data, not code** — cards live in the engine datastore, seeded from
  a private repo that holds their version history.
- **Granularity follows teaching, not estimation.** One technique can carry
  several cards. Mastery is estimated per technique, so cards are never the
  unit of estimation and are never referenced by the log.

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
- **A set claimed against the readings calibrates; only a blind one measures.**
  Writing the criteria means labelling, and labelling against a second reader
  is how the boundaries surface — so the first hand pass is a rulebook being
  written, and its product is the criteria rather than the labels. Agreement
  measured on it afterwards is agreement with itself. The eval set is claimed
  from the criteria alone, which is what makes the number mean anything; the
  calibration set stays useful for a different question, whether a later edit
  silently reclassifies what was already settled.
- **The eval set holds one attempt per problem**, its latest carrying code. A
  retry asks the identical question — same solution, same candidate tags — so
  a repeat measures one decision twice rather than measuring two. The drill
  loop still asks about every attempt of a sitting, where the answer costs a
  keystroke and the count is per submission.
- **One claim per attempt**, naming every technique it used, since a solution
  can use several. A later claim replaces the whole set rather than rewriting
  the earlier one.
- **A verdict naming no candidate is not a claim.** The resolver takes a
  claim's existence as its answer, so an empty one drops the attempt off the
  board rather than leaving the fallback standing. Unstorable, and unscored
  because missing evidence is not a disagreement, so every later run asks
  again. The count is reported: a dropped decline shrinks the denominator and
  flatters the share.
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
  model, effort, prompt version, prompt hash. Both count the same toward
  progress, but a machine claim can be recomputed by a better classifier and a
  user's cannot, so re-deriving has to find the stale ones and leave the rest.
  All four or none, since a reading whose configuration is partly unknown
  compares with nothing — and a user's claim carries none of them, because
  nothing re-derives it. A model asked for no effort, or one that rejects the
  parameter, records the level it ran at rather than an empty field: the
  model's own default is a fact about the reading, not a gap in it.
- **What produced a claim is compared whole, never ordered.** A version is an
  identity, not a number to be greater than, so running an earlier prompt on
  purpose re-derives what a later one wrote and a rollback needs no separate
  path.
- **The prompt is named twice, deliberately.** The version is the author's
  statement that the reading changed meaningfully and is what marks a stored
  claim stale; the hash is the mechanical fact of the text that was sent —
  the instructions and the criteria both, since both shape every reading —
  and marks nothing. A forgotten bump would otherwise be invisible forever —
  with both, two hashes under one version say so, and a re-derivation fixes
  it. Driving staleness from the hash instead would re-derive the backlog for
  a reflowed sentence: the hash is a syntactic boundary and the version a
  semantic one, and only the semantic one should cost money.
- **Configurations are compared over the attempts both read**, not over each
  one's own. A cheaper classifier measured on a smaller sample scores against
  a different denominator, and the number would read as quality.

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
  witnessed them. `origin: engine` stays reserved for Phase 5, where the
  engine produces attempts by verifying them.
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
  user's until Phase 4.

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
  Cards are teaching content and are never referenced by the log.
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
