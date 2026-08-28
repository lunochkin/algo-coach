# Flows

Sequences. The other files say what the system holds and where it ends. A
flow says in what order, and what each step may not do.

## Generating a problem

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
  edits means the rulebook is becoming a transcript of one model. A real share
  of criteria edits means it is doing its own work.
- **What the set cannot show** is a classifier that is right where the frontier
  was wrong. Such a case is recorded as an error, and the attempts both readers
  got wrong the same way are never detected. That is the cost of a fixed
  reference, and it is accepted.

