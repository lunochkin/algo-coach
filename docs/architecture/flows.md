# Flows

Sequences. The other files say what the system holds and where it ends. A
flow says in what order, and what each step may not do.

## Generating a problem

A problem, its test cases and its solutions are written across four calls.
The order matters because each step can reject what came before.

1. The brief: a template, naming the form the problem must be solvable by, or
   a technique, naming only the skill.
2. The statement, the canonical solution and the first test cases, from one
   call.
3. The canonical runs, and its outputs are checked against the expected
   values the same call declared.
4. The reference solution, from the statement alone.
5. The reference runs, and the two solutions' outputs are settled: they agree
   on every case, or the problem is discarded.
6. Code that builds an input of a given size and seed, from the statement
   alone.
7. Where the template claims a speedup, the smallest input separating the
   reference from the canonical under the cap is searched for.
8. Mutants of the canonical run against the cases, then against inputs that
   code builds. A call asks for the cases that kill whichever mutant survived
   both, and the ones that killed are appended to the set.
9. The case at the separating size is appended after them.
10. All of it lands together, with the template match the generation asserts
    on its canonical.

- **Problems for one template are written one at a time.** Each call is shown
  the statements the form already has, so two in flight would be shown the same
  list and could write the same problem twice. Concurrency saves minutes and
  costs the diversity the brief exists to enforce.
- **Nothing lands half-verified.** A draft failing any step stops there, and
  only one that passed every gate becomes a problem. It is kept where it
  stopped rather than discarded, which is what lets a fixed step resume.
- **The reference is written blind.** Shown the canonical, it inherits that
  solution's reading of the statement. Agreement then shows only that one model
  is consistent. Blind, agreement is evidence that the statement has one
  reading, and disagreement on any case discards the problem.
- **The generator's own expected values are a gate, not a source.** The call
  that wrote the canonical also declared what each case returns, so a
  disagreement between them means it wrote one of the two wrong. What a landing
  case stores is still the reference's answer.
- **A disagreement is the statement's fault, not either solution's.** Two
  correct-looking solutions returning different answers means the prose admits
  two readings. That is what an in-place edit cannot repair, since the cases
  would move with the wording.
- **Every run at generation is capped**, well above the drill loop's cap. The
  largest input the reference finishes at is what decides which cases carry its
  answer, and an uncapped run is a non-terminating reference hanging the run.
- **The scale case is tautological, and harmlessly so.** Correctness was
  established on the cases the reference computed, and this one exists for the
  cap rather than for the verdict. It still catches a crash or a recursion
  limit at size. It cannot catch a canonical correct small and wrong large.
- **Where an alternative canonical exists, it restores that independence.** It
  is a second efficient solution from a different form, so a scale case can be
  cross-checked between two of them rather than taken from one. Enumeration is
  what produces one, so the cross-check is available on a later pass rather
  than at landing.
- **No model is asked how good the cases are.** One asked whether its own cases
  suffice says yes, and one asked to break its own solution writes the mistakes
  it expects a solver to make — a sample nobody chose and no run reproduces. A
  tree walk enumerates the mutants instead, so the set is deterministic and
  re-derivable, and nothing about it is stored.
- **A mutant is the canonical with one semantic change**, made on the parsed
  tree rather than the text, so a comparison inside a string is untouched. It
  is killed when it fails at least one case, and a surviving one is a case that
  has to exist.
- **A mutant runs under a cap paced by the canonical**, never under the one the
  reference needs. A change that breaks a loop's progress never returns, and
  what a mutant has to beat is the solution it is a copy of.
- **An operator changes one decision the code makes**, and each is a mistake a
  solver makes. A mutant nobody would write asks for a case that catches
  nothing. The set itself is in `algo_coach.mutation`.
- **The call that answers a survivor proposes arguments, never returns.** The
  reference computes what they return, so no model writes an expected output
  that could agree with the mistake the case was asked for.
- **A proposed case that killed nothing does not land.** Every later
  verification runs the stored set, and a case no mutant fails catches nothing
  a case already there does not. Which mutants each proposal killed is read
  from the kill pass the round already pays for, so nothing extra runs.
- **Two proposals killing one mutant land the first.** The second decides
  nothing the set does not already decide, so what settles it is the order the
  round proposed them in. The fuzz pass keeps its inputs by the same rule.
- **A dropped proposal is still shown to the next round.** It is not in the
  set, and a round shown neither the set nor it could propose an input that
  already killed nothing.
- **The set written with the statement is exempt.** Those cases describe what
  the problem asks rather than what a mutant fails, so they land whether or not
  they kill.
- **A proposed input the canonical cannot answer drops the case, not the
  problem.** Nothing checks an input against the constraints the statement
  gives, so a crash or a timeout there is as likely to be an input the problem
  excludes as a defect in the solution. The canonical was already run against
  the cases written with the statement, and those are what decide it.
- **A proposed case the two solutions answer differently discards the
  problem**, as a disagreement on any other case does. The round asks for
  boundary inputs, and a canonical wrong at a boundary the first set never
  reached is what the loop exists to find.
- **A round whose call fails holds the draft.** The problem passed every gate
  that judges it, and its set was never measured against the bound. Landing it
  would store a set no round was paid for, where a resume asks the loop again.
- **The loop stops on a bound, never on a score**, for the reason `corpus.md`
  gives.
- **The search runs before the loop and its case is appended after it.** The
  survivors are decided against the set as the statement left it, so what the
  case may not do is join that set. Searching first catches a canonical wrong
  at scale before a round is paid for.
- **The separating case is settled as any other case.** The reference is
  measured well above the sitting's cap, so it usually computes the value the
  case stores. A disagreement there discards the problem, and it is what
  catches a canonical correct on the small cases and wrong at scale.
- **The input the search measured is the input the case stores.** A generator
  is asked to build one input per size, and building it again would be a second
  run of model-written code.
- **The input generator is written for every problem**, whatever the brief
  named, and before the mutation loop. The fuzz pass kills mutants with the
  inputs it builds, so a round is paid for the survivors alone.
- **The fuzz pass runs only where a mutant is standing.** A case set that
  already kills every one of them builds nothing, so a problem the statement's
  own cases decide costs no execution here.
- **A round is shown what the pass kept.** Those cases are in the set the
  survivors were decided against, so re-proposing one would win a case that
  kills nothing.
- **A search that fails holds the draft, as one that separated nothing does.**
  The input generator's code can crash, which says nothing about the statement.
  What is missing is the case a landing needs, and the run reports what the
  search stopped at.
- **A call that wrote no input generator holds it too**, where a speedup is
  claimed. No search ran, so the claim is undemonstrated for the same reason,
  and a resume starts at the builder rather than at the search. It costs the
  fuzz pass besides.
- **Nothing is repaired after landing.** A stored problem carries attempts and
  its cases are append-only, so every fix is a resumed draft. A step that has
  no answer therefore stops the writing rather than lowering what a landing
  requires.
- **Every step's verdict is recorded, not only reported.** A run prints each
  stage and the process then ends, so a discarded draft would leave only the
  calls it paid for. `machine.md` gives what a site's record carries.
- **A statement may not name the domain its template's cue names.** The
  monotonic stack's cue says "temperatures" and "a next warmer day". A solver
  who recognises a problem has not derived its form.
- **Failing means two things on the cases written with the statement.** The
  first canonical is run before any expected value is settled, so it fails only
  by yielding no value on some case, and the problem is discarded. A later
  canonical is judged by the cases the problem carries, so it fails as any
  solution does, and nothing is discarded.
- **Announcement is measured, not assumed.** What is being trained is reaching
  for a form unprompted, so the enabling property has to be derivable from the
  statement rather than stated in it. A form a matcher names instantly from the
  statement alone was telegraphed, and such a problem teaches recognition of
  nothing.

## Writing a problem, as states

The sequence above, held as durable state. A draft is stored as it is written,
so a step that fails leaves it where it stopped instead of throwing the calls
before it away.

- **Two machines, meeting at landing.** `ProblemStatus` governs a problem that
  exists: created, active, retired. This one governs the writing, and its last
  state is that one's first.
- **They stay apart.** One enum carrying both would put `drafted` beside
  `active`, and every reader would have to know which half it was looking at.
- **The draft is identified by the writing id.** `SiteOutcome` already mints
  one per attempt, so the four site records of one draft group with no new
  reference.
- **A state per step that can fail**: drafted, checked, referenced, agreed,
  built, searched, hardened, landed. The names are the steps above and the
  order is theirs.
- **A search that separated nothing stops the draft at `searched`.** What it
  found is recorded either way, and `corpus.md` gives the three exits a held
  draft leaves by.
- **A draft that never reached the search stops earlier.** A speedup is
  claimed and no input generator was written, so it is held at `agreed` and a
  resume runs the builder.
- **A loop whose round failed stops the draft before `hardened`**, at whatever
  the steps before it reached. A resume runs the loop over the set as the
  statement left it, which is the set the survivors were decided against.
- **`rejected` is terminal and names the gate that reached it**, which is the
  same `Discard` a site outcome carries. Terminal means no resume rather than
  no record.
- **A draft holds what a call produced and no local run re-derives**: the
  statement, the canonical, the declared cases and the difficulty; the
  reference; the settled cases; the builder's code and its bound; the cases the
  mutation loop appended; the separating case.
- **The mutants and the survivors are not in it.** A tree walk enumerates them
  and subprocesses kill them, so a resume re-derives both without a call.
- **The loop's counters are not in it either.** They sit on the site outcomes
  of the same writing id, which is where a report reads them.
- **Each step's configuration is copied onto the draft.** The four site
  outcomes are written once the loop has run, so a draft that stopped before
  that has none to read a configuration from.
- **What a resume starts at** is the first step whose configuration or digest
  moved, which is why both are on the draft rather than only the outputs.
- **A resume goes forward only.** A step's prompt is a function of the outputs
  before it, so editing one site's prompt invalidates that step and what
  follows it.
- **Editing the generator's prompt invalidates no stored draft.** The draft is
  that step's output, and the new prompt writes a different problem rather than
  the same one again.
- **A resumed step writes a second site outcome**, never an amendment, as a
  re-run of any site over one item does.
- **A resume never serves.** Landing is the only transition into `created`, and
  it still requires every gate this flow requires.
- **A rejected draft is not resumed.** Its gate says the answer was wrong, so a
  resume skipping that gate would land what the gate rejected. Re-running the
  rejecting step mints a new draft, citing the one it came from.
- **The draft store is working state rather than a log.** States move and
  records are revised, so it can be refactored where the append-only logs
  cannot.
- **A draft names the problem it landed as.** A crash between landing and
  clearing then leaves a draft the next run can clear, rather than one it would
  write a second time.
- **Deferred: how a resume is invoked, whether drafts are listed from the CLI,
  and how long a rejected draft is kept.** Each needs a corpus of drafts to
  answer.

## Enumerating a problem's other solutions

A landed problem carries one canonical, written for what its brief named. Every
other way to solve it is found afterwards, over the stored problem.

1. The statement, the cases it carries and the canonical it already has.
2. A call proposes the approaches that solve it, each as a name and a one-line
   idea.
3. A canonical is generated per approach, one call each.
4. Each runs against the cases the problem already carries, and one that fails
   is not stored.
5. Each stored canonical is read for its techniques and for the templates it
   displays.

- **It runs over the corpus, never in the landing path.** A proposal nobody
  could write says nothing about the statement, so enumeration cannot gate a
  problem. The list needs no gate of its own either: its length tracks the
  model's verbosity, and a wrong proposal costs one call and lands nothing.
- **One call per approach, never one reply carrying all of them.** A single bad
  entry would otherwise fail the whole batch, where each canonical is judged on
  its own.
- **It sees the first canonical.** Independence is the reference's purpose
  rather than this call's. This call is asked for approaches that differ from
  what is stored, and that needs the stored one in view.
- **A canonical it produced is not a reference.** It saw the statement, the
  cases and another solution, so it is no independent reading. It cannot
  discard a problem, and its failure says nothing about the statement.
- **Duplicates are what execution cannot catch.** Top-down and bottom-up
  dynamic programming pass the same cases, and only a reading separates them.
  What to do with two canonicals of one form is deferred until a corpus shows
  how often it happens.

## Replaying a site

The three answering sites over a stored problem, at a configuration the corpus
has not been read by. Generation writes a new problem every call, so nothing
there is ever asked twice and no two configurations meet the same item.

1. The stored problems, minus the retired ones and any missing a solution in
   either role.
2. Per site, the digest it would send now. A pair this configuration has
   answered at that digest is skipped.
3. The blind site writes a reference from the statement, settled against the
   cases the problem carries rather than against the canonical.
4. The discrimination site runs the mutation loop over the stored canonical,
   against the cases written with the statement alone.
5. The inputs site builds and searches, where the template claims a speedup.
6. Each site's answer is recorded as its outcome, keyed to the problem.

- **It writes nothing to the corpus.** A case a round wins here is discarded,
  or the next configuration would be measured against a different problem.
- **The loop is replayed against the set as it stood.** A case a later round
  won and the separating case are excluded, since neither was there when the
  survivors were decided. Counting them changes the survivors and the digest,
  and the generation run's own record would then answer for nothing.
- **The discrimination digest is known only after the local kill pass.** The
  survivors are in the prompt, and killing costs subprocesses rather than a
  call, so the skip is decided after that pass and before the call.
- **A retired problem is not replayed.** A defective one was never a fair test,
  and a telegraphed one is not what a later corpus will hold.
- **The inputs site is asked only where a speedup is claimed**, where the
  landing path builds for every problem. What a replay records is the verdict a
  gate reached on an answer, and nothing here runs the code the call wrote
  unless a search does.

## Drill loop

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
6. Keyed to each attempt, the loop asks for a technique claim and a
   self-label, or the user marks the problem defective instead.

- **An attempt nobody timed stays untimed**, rather than carrying a duration
  reconstructed after the fact.
- **A drill can mint several attempts**, and each is asked about in turn. A
  submission that failed on syntax and the one that passed are different
  evidence, and labelling only the last would leave the counts on two
  denominators: attempts per submission, labels per sitting.
- **The label and the claim are cheap only here.** The candidates are the
  problem's own two or three techniques, the drilled one is the default since
  selection picked the problem by it, and the attempt is minutes old. Two facts
  a classifier has to infer later cost a keystroke each at this moment.
- **A statement that asked the wrong thing is marked, not labelled.** The loop
  offers marking the problem defective in place of the self-label. Asking why
  the sitting failed would otherwise record the problem's fault as the user's
  own gap, and a self-label cannot be revised later.
- **Selection never schedules.** Ordering is a view. What to drill is the
  user's choice until the scheduler lands.

## Adjudicating the eval set

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
  edits means the eval set is becoming a copy of one model's readings. A real
  share of criteria edits means the criteria are being corrected instead.
- **What the set cannot show** is a classifier that is right where the frontier
  was wrong. Such a case is recorded as an error, and the attempts both readers
  got wrong the same way are never detected. That is the cost of a fixed
  reference, and it is accepted.

