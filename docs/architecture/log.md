# The log

The user's private append-only record: what was attempted, what it used, why it
went the way it did, and the study a card run tracks. Part of the architecture;
`README.md` is the map.

## Attempts

- **The drill loop is the only source.** The engine served the problem and
  watched the sitting, so nothing else is in a position to assert one.
- **The verification is its own record**, as a canonical's is, and how it
  keys to an attempt is settled in Phase 8. `solved` is the projection over
  its results, and the raw result carries what the projection drops. A timeout
  and a wrong answer are both unsolved, and only one is evidence of
  slowness.
- **Problem techniques are never denormalized onto an attempt.** They are
  re-derivable and the log is not, so a copy taken when the attempt was written
  would drift with no way to tell which is right.

## Technique claims

Which techniques an attempt used. Per-technique progress is measured from this.
A claim rather than a fact, and open to revision, so it is its own record
rather than a field on the attempt.

- **Attribution resolves, it is not required.** The claim that stands if one
  exists, otherwise the problem's techniques. Resolution happens on read and is
  never stored, so re-deriving a problem's techniques reaches every unclaimed
  attempt.
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
- **How sure its author was is a level, not a float.** A judgement made in
  seconds carries no more resolution. It is absent on every claim written
  before it was asked for, and a level nobody gave is not a low one.
- **One list of columns, whichever renderer prints a score.** A metric added to
  one renderer and not the other prints a number that stopped being true.
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
  an earlier claim as any reading does.
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

## Self-labels

The user's own verdict on why an attempt went the way it did. Reported, not
inferred. Its own record rather than a field on the attempt, for the same
reason a claim is.

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

## Diagnoses

Why an attempt failed, inferred rather than reported. Keyed to an attempt and
carrying provenance as any machine record does, so every attempt can be
re-diagnosed and compared.

- **The machine counterpart of a self-label, never its replacement.** Neither
  supersedes the other, and agreement between them is the eval. A later
  diagnosis is a second reading rather than a correction.

## What every record keyed to an attempt carries

Claims, self-labels and diagnoses share a base: an engine-minted `id`, the
`attempt_id` they assert about, and `created_at`. One reader orders all three,
latest first, with append order breaking a tie. The `id` lets a record be
cited, by an eval naming the diagnosis it scored or by a user correcting a
claim.

Ordering is not what stands. The shared reader answers "in what order", and
each record's own section says who wins.

## Card runs

Studying a card is an explicit act, not a state the system infers.

- **Starting is explicit**, because the ladder is measured from it. A ladder
  problem solved before the card began does not count toward it. The card
  teaches the form, and having solved the problem once is not having studied
  it.
- **The run holds what the start produced**: when it began and the probes it
  was given. Later probes append rather than replacing the set, so what was
  offered and when stays readable.
- **Derived from it, never stored**: ladder progress, recall state per
  template, and whether the card is done. "Done" is only a view for now.
  Graduation becomes a process later, once there are numbers to set its box and
  its probe count from.

## Recall attempts

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

