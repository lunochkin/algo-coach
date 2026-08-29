# TODO

The phases still open. A ticked item stays while its phase is open. When the
phase closes it is harvested into `docs/ROADMAP.md` and removed whole.

## Phase 6 — problem generation (current)

The engine writes problems: a statement, the test cases that decide it, and at
least one canonical solution. Flow and its rules:
`docs/architecture/flows.md`, "Generating a problem".

Generation lands before the matcher is scored. The Phase 5 reset took every
template match with it, so no pair carries a hand reference, and none can
until the engine has written problems to annotate.

### The records

- [x] `generated_for` on `Problem`, naming the template it was written for. An
      assertion rather than a reading, which is what makes the first
      `TemplateMatch` provenance
- [x] `MachineProvenance` on `Problem`, required as it is on a match. A problem
      generated before the field exists carries none for good, and no
      configuration could then be compared over the corpus
- [x] `mint.generated_problem`, as `machine_match` mints a match. Minting in
      one place is what keeps a call site from filling provenance partly
- [x] `TestCase`, keyed to a problem, carrying arguments and an expected
      return. The first set is written in the same call as the statement, so
      the cases describe what the problem asks rather than what a solution did
- [x] `Problem.status` — created, active or retired — beside a
      `retired_reason` of `defective` or `telegraphed`. A validator ties them,
      since only the reason says whether the attempts count
- [x] `CanonicalSolution`: the code and its provenance, and nothing about how
      it ran. Immutable, since whether it passes is a fact about a run
- [x] `Verification`: one run of a solution, carrying the cap and a result per
      case. Its own record, since the cap and the machine decide a timeout
      where the code does not. The run's own outcome folds from the cases
- [x] Several canonicals per problem, appended. A rung covers a studied
      template and an optional one only where two approaches are stored
- [x] Append-only stores for cases, canonicals and verifications. A case is
      added and never revised, and two runs of one solution are two records
- [x] A `MatchSource.GENERATOR` arm, carrying no provenance as a hand match
      does not. The generator knew what it was told to write, where a matcher
      infers it
- [ ] Resolve a pair by that order rather than latest-wins, as a claim resolves
      user-first. A matcher's later reading must not supersede the assertion it
      audits

### Generation

- [ ] One template, one call, and read the reply out of the call log before any
      of the rest. Whether a model writes a statement, a canonical and
      discriminating cases in one call is what shapes everything below
- [ ] The prompt: a template and its cue in, a statement, a canonical and the
      cases out. One call, or the cases describe the solution rather than the
      problem
- [ ] One response schema over all three parts, so a reply missing any of them
      fails rather than landing a problem to repair later
- [ ] Sampled rather than greedy, the exception the provenance rule names. One
      model's habits would otherwise become the whole corpus
- [ ] Its own configuration, as the matcher has its own. Generation asks for an
      artifact where a reading asks for a verdict
- [ ] `algo-coach generate`, a template in and problems out, through the
      transport the classifier and the matcher already share
- [ ] Progress per problem, as the other run loops report it: the template, the
      case run's verdict, and whether it landed

### The runner

Executing a solution against a problem's cases. One subject today, a canonical.
Phase 8 puts an attempt on the same path.

It comes after generation because the convention is fixed by `TestCase` and the
output is then real. Landing closes here: nothing is stored until a canonical
has passed.

- [ ] Reject a solution defining no `solve`. The convention is what makes a
      stored entry point unnecessary, so nothing else checks it
- [ ] Execute in a subprocess under a wall-clock cap per case. The engine runs
      code a model wrote, and a non-terminating one must cost one case rather
      than the run
- [ ] Decide every case rather than stopping at the first failure. The
      canonical stores a count, and a count needs every case decided
- [ ] Separate a wrong answer from a crash and from a timeout. Phase 8 reads
      the same result for an attempt, where only one of the three is evidence
      of slowness
- [ ] Decide how a case compares outputs where several answers are correct.
      Equality on the returned value fails a correct solution to such a problem
- [ ] Run the canonical before anything lands, and discard the problem whole
      where it fails. The call is recorded either way, so what was paid for and
      thrown away stays readable
- [ ] Write the problem, its cases, the canonical and the asserted match in one
      act. A half-written problem is one the matcher would read as finished

### What the corpus derives

Folds over what generation and the runner stored. The first run is aimed by
hand at the studied templates. Every later one is aimed by the report.

- [ ] Derive a problem's techniques from its canonical solutions. A view, so
      adding a canonical can widen them and re-deriving is legal
- [ ] Report a studied template no problem matches. The card claims to teach
      that form, so a corpus that cannot exercise it is a fact about the store
- [ ] Aim a run at the templates carrying no match. A form the corpus cannot
      exercise names its own remedy

### The discrimination bar

Settled on the first corpus, then enforced before a problem lands. Cases that
separate nothing license `verified` on a canonical that is wrong.

- [ ] Break a canonical mechanically and require the cases to fail it. The
      cheapest of the discrimination candidates, and testable before the corpus
      exists
- [ ] Settle which check is the bar on a real corpus, then enforce it. Which
      check it is comes from a corpus rather than from an argument

### Annotating the generated corpus

The hand pass does two jobs at once. It writes the matcher's reference, and it
is the only reading of a generated problem that no model produced. A generator
that wandered from its brief shows up there whatever the matcher says.

- [ ] Aim the first run at the studied templates, 38 of the 45 across nine
      cards, and annotate a sample of what lands
- [ ] Annotate through `algo-coach annotate` unchanged. It already samples
      across templates, and the cards are seeded
- [ ] The first hand pass calibrates and a blind one measures, the claims rule
      unchanged. A score over the pairs that drew the line is agreement with
      itself

### Scoring the matcher

Generation asserts a match and the matcher audits it, so an unmeasured matcher
audits at an unknown error rate. What that blocks is trusting the audit, not
generating.

- [ ] Score the matcher per pair, grouped per template, over the pairs both
      read. Not as a set: a match asserts a pair
- [ ] Report the positive verdicts in both directions. Accuracy would score a
      matcher that names nothing in the nineties
- [ ] Skip a pair the hand settled on the run path, and read it in the eval.
      The skip needs every template of the card settled, since the call asks
      about the card whole
- [ ] Lift the scorer out of `claims` rather than copying it. It already prints
      denominators and reports both directions, which is the shape a per-pair
      score needs
- [ ] Let the matcher read the pair generation asserted, and report the
      disagreements. Actionable once the matcher carries a score

### The announcement floor

The archive half can start as soon as the matcher runs, and needs no scored
matcher. The floor is one matcher over two corpora, so a systematic error
largely cancels in the comparison.

- [ ] Settle how `data/old/` is read for a measurement. It is a corpus rather
      than a store, so nothing on the run path may point at it
- [ ] Measure the announcement floor over the archived statements: how often
      the matcher names a form from the statement alone
- [ ] Clear a created problem or retire it as telegraphed. `created` is not a
      resting state, so nothing may leave a problem sitting in it
- [ ] Read the generated corpus against that floor before growing it. A problem
      the matcher names instantly was telegraphed, and teaches recognition of
      nothing

### Exit
- [ ] A card's reported gaps are filled by generated problems, and Phase 7
      resolves a ladder over them

## Phase 7 — ladder, recall and card runs

- [ ] Resolve the ladder from the matches, the selector filling out to `size`.
      A retired problem fills no rung
- [ ] Derive requiredness from what a rung covers: studied means required, the
      optional template alone means optional, both means required with the
      optional template offered as the alternative
- [ ] Re-derive the ladder whenever the corpus moves under it, a started card
      included. Progress is a fold over attempts, so nothing is lost
- [ ] `CardRun`: starting is explicit, since the ladder is measured from it.
      Holds when it began and the probes assigned; later probes append
- [ ] A recall attempt is its own record, keyed to a card and a template. There
      is no problem and no submission. What was hinted before a pass is part of
      it
- [ ] Generate probes from the corpus. A skill now, since it is judgment, and
      possibly an agent later
- [ ] The trainer: names hidden, blank-filed cold, run against the card's own
      tests, never printing the template
- [ ] Card status — recalled when, ladder outstanding, probes available. The
      inputs a graduation rule reads, and no threshold

### Exit
- [ ] Recall and the ladder run daily

## Phase 8 — in-engine drill loop

The first attempts the engine produces itself.

- [ ] Serve active problems, and created ones while the floor has not run.
      Reading only active would serve nothing until the gate exists
- [ ] Serve a generated problem, time the sitting, run the submission against
      the problem's own cases, and mint the attempt
- [ ] The verification result on `Attempt`. Additive, and meaningless before
      Phase 6
- [ ] Feed the claim classifier its candidates from the problem's derived
      techniques. Nothing else supplies them now the tag mapping is gone
- [ ] The loop marks a problem defective rather than asking for a self-label
      on it. A statement that asked the wrong thing would otherwise be recorded
      as the user's own gap
- [ ] Exclude a defective problem's attempts from the board, both directions.
      Dropping only the failures would raise a technique's solve rate because
      a problem was broken
- [ ] Ask for a claim and a self-label as Phase 2 asked them. What changes is
      who witnessed the sitting, not who writes

### Exit
- [ ] Daily practice runs here, on problems the engine wrote and judged

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] The annotator against themselves as the ceiling: a re-pass over thirty
      attempts, readings hidden. Triggered when mastery estimation reads
      claims, and a wrong one starts spending practice time
- [ ] Read the architecture doc against the code, landing every divergence
      here. The goal is not that none exists, since the doc is target state.
      The goal is that none is unknown
- [ ] Classify freely over the whole vocabulary and intersect in code, once the
      hand claims can score it against the constrained one. A verdict outside
      the problem's own techniques is the only signal that they are the gap
- [ ] Settle how a case forcing a timeout carries its input. Literal arguments
      put a megabyte of JSON in the store per case, where a seed and a size do
      not. Triggered when the first performance case is written
- [ ] Record what the environment contributed to a verification run. The
      machine and the interpreter version decide a timeout or a crash as much
      as the cap does. Triggered when two runs of one solution disagree
- [ ] An outage falls back to another endpoint of the same shape, never to
      Anthropic direct, whose compatibility layer ignores `response_format`,
      `strict` and `reasoning_effort`. Triggered when an outage blocks a run

## Later phases

### Phase 9 — mastery, scheduling, failure mode
- [ ] Rust against gap is a question about per-technique state, asked of a
      single attempt. Only whether the technique was ever fluent separates
      them, so it lands with the mastery model or not at all
- [ ] Settle `SPEED` before anything writes it. "Solved but too slowly" is
      about the user, a timeout is about the solution's complexity, and only
      the second is in the record
- [ ] Narrow the failure classifier to what the record supports: a mechanical
      slip against a conceptual miss. A four-way router would ask it for what
      it cannot see
- [ ] Write the verdict as a `Diagnosis` with model and prompt version. It
      never supersedes a self-label, because the eval scores one against the
      other
- [ ] Eval per mode rather than overall, against self-labels the loop
      produced. A router that only ever says `gap` would score well on a corpus
      of gaps

