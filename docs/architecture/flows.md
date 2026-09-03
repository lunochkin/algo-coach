# Flows

Sequences. The other files say what the system holds and where it ends. A
flow says in what order, and what each step may not do.

## Generating a problem

A problem, its test cases and its solutions are written across three calls.
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
6. Mutants of the canonical run against the cases, and a call asks for the
   cases that kill whichever mutant survived.
7. Where the template claims a speedup, the smallest input separating the
   reference from the canonical under the cap is searched for, and the case at
   that size is stored.
8. All of it lands together, with the template match the generation asserts on
   its canonical.

- **Problems for one template are written one at a time.** Each call is shown
  the statements the form already has, so two in flight would be shown the same
  list and could write the same problem twice. Concurrency saves minutes and
  costs the diversity the brief exists to enforce.
- **Nothing lands half-verified.** A problem failing any step is discarded
  whole rather than stored for repair. Every call is recorded, so what was paid
  for and thrown away stays readable.
- **Two solution roles, and no solution holds both.** The canonical displays
  the template's form and is what a rung teaches. The reference is written from
  the statement alone, and is what computes expected outputs and what a timing
  bar measures against. Independence is the reference's whole purpose, so a
  solution displaying the form could not also serve as one.
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
- **Expected outputs come from the reference wherever it can compute them.**
  That is every case at or below the largest input it finishes at generation
  time, under a generation cap set well above the drill loop's. Beyond that
  point the expected output comes from the canonical. A reference that computes
  none of them discards the problem. Every run is capped: an uncapped one is a
  non-terminating reference hanging the run.
- **The scale case is tautological, and harmlessly so.** Correctness was
  established on the cases the reference computed, and this one exists for the
  cap rather than for the verdict. It still catches a crash or a recursion
  limit at size. It cannot catch a canonical correct small and wrong large.
- **Where an alternative canonical exists, it restores that independence.** It
  is a second efficient solution from a different form, so a scale case can be
  cross-checked between two of them rather than taken from one. Enumeration is
  what produces one, so the cross-check is available on a later pass rather
  than at landing.
- **Whether the cases are enough is decided by execution, never by a model.** A
  model asked whether its own cases suffice says yes. A surviving mutant is a
  case that has to exist, and it names the mistake that case must catch.
- **A mutant is the canonical with one semantic change**, made on the parsed
  tree rather than the text, so a comparison inside a string is untouched. It
  is killed when it fails at least one case, by a wrong answer, a crash or a
  timeout. Mutants run locally and cost nothing, and only the call that writes
  the new cases is paid for.
- **A mutant runs under a cap paced by the canonical**, never under the one the
  reference needs. A change that breaks a loop's progress never returns, and a
  handful of those at the generation cap cost more seconds than every call in
  the run. What a mutant has to beat is the solution it is a copy of.
- **Mutants are made mechanically, with no model call.** A tree walk
  enumerates them, so the set is deterministic and re-derivable from the
  canonical. A model asked to break its own solution writes the mistakes it
  expects a solver to make, which is a sample nobody chose and no run
  reproduces. No mutant is stored: they are re-derived whenever the operator
  set changes.
- **An operator changes one decision the code makes**: a comparison's boundary
  or its direction, an arithmetic operator, a connector, a dropped `not`, an
  integer by one, `min` against `max`, `break` against `continue`. Each is a
  mistake a solver makes, where a mutant nobody would write asks for a case
  that catches nothing.
- **The call that answers a survivor proposes arguments, never returns.** The
  reference computes what they return, so no model writes an expected output
  that could agree with the mistake the case was asked for.
- **A proposed input the canonical cannot answer drops the case, not the
  problem.** Nothing checks an input against the constraints the statement
  gives, so a crash or a timeout there is as likely to be an input the problem
  excludes as a defect in the solution. The canonical was already run against
  the cases written with the statement, and those are what decide it.
- **A proposed case the two solutions answer differently discards the
  problem**, as a disagreement on any other case does. The round asks for
  boundary inputs, and a canonical wrong at a boundary the first set never
  reached is what the loop exists to find.
- **A round whose call fails costs the measurement, not the problem.** The
  problem passed every gate that judges it, and the run reports its set as
  unmeasured against the bound.
- **The loop stops on a bound, never on a score.** A mutant can be equivalent
  to the original, and equivalence is undecidable, so no case kills it and the
  score never reaches full. `corpus.md` carries the number of rounds.
- **Whether a form is a speedup is authored on the template.** Backtracking and
  exhaustive search are their own optimum, so no input separates the two
  solutions there. A timing run cannot tell that from a reference written
  cleverly by mistake. The template states which it is, and a missing
  separating input is a defect only where a speedup was claimed.
- **The separating case is settled as any other case.** The reference is
  measured well above the sitting's cap, so it usually computes the value the
  case stores. A disagreement there discards the problem, and it is what
  catches a canonical correct on the small cases and wrong at scale.
- **The input the search measured is the input the case stores.** A generator
  is asked to build one input per size, and building it again would be a second
  run of model-written code. What was measured is what the verdict was taken
  on.
- **A search that fails costs the case, not the problem.** The generator call
  can refuse and the code it wrote can crash, and neither says anything about
  the statement. What is lost is the timing case, and the run reports that it
  went unwritten.
- **A statement may not name the domain its template's cue names.** The
  monotonic stack's cue says "temperatures" and "a next warmer day", and the
  first generation call returned Daily Temperatures verbatim. A solver who
  recognises a problem has not derived its form.
- **The generator's assertion is not the matcher's verdict.** They are two
  records on one pair, and a disagreement is how a generator drifting from its
  brief is found.
- **A canonical that passes demonstrates a match**, where the matcher infers
  one. The assertion is stored only for a canonical the cases kept: one that
  failed showed nothing about the form.
- **Failing means two things on the cases written with the statement.** The
  first canonical is run before any expected value is settled, so it fails only
  by yielding no value on some case, and the problem is discarded. A later
  canonical is judged by the cases the problem carries, so it fails as any
  solution does, and nothing is discarded.
- **Announcement is measured, not assumed.** What is being trained is reaching
  for a form unprompted, so the enabling property has to be derivable from the
  statement rather than stated in it. A form a matcher names instantly from the
  statement alone was telegraphed, and such a problem teaches recognition of
  nothing. The archived corpus sets that floor and the generated one is read
  against it.

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

- **It runs over the corpus, never in the landing path.** Enumeration cannot
  gate a problem, since a proposal nobody could write says nothing about the
  statement. In the landing path it would discard problems for reasons
  unrelated to their own correctness.
- **The list needs no gate, because execution is the gate.** Its length tracks
  the model's verbosity rather than the problem. A proposal that is wrong costs
  one call and lands nothing.
- **One call per approach, never one reply carrying all of them.** A single bad
  entry would otherwise fail the whole batch, where each canonical is judged on
  its own.
- **It replaces asking a matcher which templates the problem could use.** That
  question reaches only forms someone authored a template for. Enumeration
  reaches the techniques no card covers, which is most of the vocabulary.
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

