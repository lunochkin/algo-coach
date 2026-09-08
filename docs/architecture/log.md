# The log

The user's private append-only record: what was attempted, what it used, why it
went the way it did, and the study a card run tracks. Part of the architecture.
`README.md` is the map.

## Attempts

- **The drill loop is the only source.** The engine served the problem and
  watched the sitting, so nothing else is in a position to assert an attempt.
- **The verification is its own record**, as a canonical's is, and how the
  verification keys to an attempt is settled in Phase 8. `solved` is the
  projection over the verification's results, and the raw result carries what
  the projection drops. A timeout and a wrong answer are both unsolved, and
  only the timeout is evidence of slowness.
- **Problem techniques are never denormalized onto an attempt.** Problem
  techniques are re-derivable and the log is not, so a copy taken when the
  attempt was written would drift with no way to tell which is right.

## Attempt claims

Which techniques an attempt used. Per-technique progress is measured from this.
A claim is open to revision, so it is its own record rather than a field on the
attempt.

- **Attribution is resolved, not required.** An attempt's techniques are the
  claim that stands, if one exists, and otherwise the problem's techniques.
  Resolution happens on read and is never stored, so re-deriving a problem's
  techniques reaches every unclaimed attempt.
- **The fallback answers a different question.** A problem's techniques say
  what solving the problem can take. A claim says what one solution did. The
  fallback over-credits techniques a canonical used incidentally, which skews
  scheduling away from the weakest ones.
- **A claim has two writers, and the user's stands first.** The drill loop
  asks at the moment of solving, and a hand pass reaches attempts no loop
  touched. A classifier fills the rest, and a later user claim corrects it.
- **The classifier is prompted, not trained.** Public corpora tag problems
  rather than solutions, so a model trained on them predicts the fallback
  instead of improving on it, and nobody has labelled what a given solution did
  because doing so means reading it. Reading a solution is semantic work:
  two-pointers and sliding-window differ in their invariant rather than their
  syntax, backtracking is depth-first search plus an undo, and greedy is a
  property of why a choice is correct rather than a construct. A scan of imports
  and keywords is weakest exactly where the claim is worth making.
- **Showing the classifier anything besides the code is deferred.** The code
  is the subject and stays. A measured comparison decides whether the problem's
  canonicals or the candidates' templates improve a machine claim.
- **A richer prompt can change the question rather than the answer.** Shown a
  problem's canonicals, a classifier can report which canonical the attempt
  resembles instead of which techniques its code used. Those are two different
  labels, and the hand claims were made against the second label. A
  configuration that moves the question is not comparable to one that answers
  it better.
- **A claim is scored against the user's own**, per technique rather than
  overall, by set equality rather than overlap. The board is per technique, so
  a classifier that over-claims one code skews the board, and a claim naming
  every candidate decides nothing while scoring well on a metric that only asks
  whether the right code appears.
- **How often a claim names every candidate is reported beside the score.**
  Claiming inclusively removes the reason to withhold a code, so a claim fails
  by naming all of them. A claim naming every candidate is the fallback, and it
  agrees with the user's claim whenever the fallback is right. Set equality
  cannot catch that.
- **The author's confidence on a claim is a level, not a float.** A judgement
  made in seconds carries no more resolution. The level is absent on every
  claim written before the loop asked for one, and a level nobody gave is not a
  low one.
- **One list of columns serves whichever renderer prints a score.** A metric
  added to one renderer and not the other prints a number that stopped being
  true.
- **The hand claims are an eval set and a correction path**, never training
  data. The engine trains nothing.
- **A label is invalidated by which classifier informed it, not by the fact
  that one did.** A claim made with the scored configuration's claim in view
  measures that configuration against itself. A claim adjudicated against a
  classifier that is never scored measures no configuration against itself. That
  adjudication draws the boundary. So `informed_by` names the machine claims its
  author saw, one by one, and a set of claims can be read back for either
  question: which claims a scored classifier informed, and which claims any
  classifier
  informed.
- **The eval set holds one attempt per problem**, the latest attempt carrying
  code, since a retry asks the identical question and a repeat would measure
  one decision twice. The drill loop still asks about every attempt of a
  sitting, where the answer costs a keystroke.
- **One claim per attempt names every technique the attempt used**, since a
  solution can use several. A later claim replaces the whole set rather than
  rewriting the earlier one.
- **A verdict naming no candidate is a machine claim, and is stored.** The
  verdict is evidence about the code rather than an absence of it, and an
  unstored verdict would be re-read by every later run. A reply cut short by the
  token cap also names nothing and is stored for the same reason, but that reply
  is a fact about the configuration instead. The call's `stop_reason` separates
  a decline from a cut-short reply, and the report counts them apart.
- **An empty claim answers nothing, so the fallback stands.** The resolver
  reads a claim's *techniques* rather than its existence, so the problem's own
  techniques keep answering an attempt whose machine claim declined. A later
  decline
  supersedes an earlier claim as any machine claim does.
- **A decline is scored all the same.** A decline asserts that none of these
  candidates apply, so a hand claim naming one is a miss against every
  technique the user named. Unscored, declining would pay: each decline would
  leave a smaller denominator and a better share over it. Only an attempt
  nothing read stays unscored, and the count of declines prints beside the
  share.
- **A decline is stated, never inferred from an empty set.** The user says so
  with `declined`, since the loop records nothing where they skip and emptiness
  would make a lost answer and a stated verdict one record. The classifier
  needs no flag: the classifier answers or fails, and a failure writes no
  claim. The eval set holds a correct decline, or the attempt could only leave
  the set by deletion.
- **A machine claim on a hand-claimed attempt is scored, never a candidate.**
  Such a claim never stands and never reaches the board. It exists to be
  scored. Storing the machine claim makes an eval a dataset rather than a run,
  and a
  second configuration is then paid for only where it has not read. The
  classifier still skips such attempts, but only to save a call whose verdict
  could never stand.
- **One record for both writers, not two.** Splitting would mirror `SelfLabel`
  and `Diagnosis`, but claims already written stay in the log forever, so a
  reader carries the old shape regardless. A third record written only by the
  eval is worse: the same verdict would land in one record or the other
  depending on
  what else was claimed.
- **Every claim records its source.** A user's claim carries no provenance,
  because nothing re-derives a user's claim. A machine claim carries all of its
  provenance, and a re-derivation reads that provenance to find the stale
  claims and leave the rest. A user's claim and a machine claim count the same
  toward progress.

## Self-labels

The user's own verdict on why an attempt went the way it did. A self-label is
reported, not inferred. It is its own record rather than a field on the
attempt, for the same reason a claim is.

- **A self-label is only ever the user's.** A machine answering the same
  question produces a `Diagnosis`. Self-label and diagnosis are separate
  records because the eval scores one against the other, and a shared record
  read latest-first would let the machine supersede the evidence it is measured
  against.
- **One label per attempt**, and the latest wins on read.
- **The drill loop is the only writer.** The question is asked at the moment of
  solving, and nothing else is there to ask it.
- **A label cannot be given later, where a claim can.** The evidence for a
  claim is the code, which does not decay. The evidence for a label is recall,
  which does decay. A `Diagnosis` reads what survives months on: a timeout, a
  compile error. A label recalled that late is either invention or the
  classifier's own input handed back as evidence against it.

## Diagnoses

Why an attempt failed, inferred rather than reported. Keyed to an attempt and
carrying provenance as any machine record does, so every attempt can be
re-diagnosed and compared.

- **A diagnosis is the machine counterpart of a self-label, never its
  replacement.** A diagnosis and a self-label never supersede each other, and
  agreement between them is the eval. A later diagnosis is a second verdict
  rather than a correction.

## What every record keyed to an attempt carries

Claims, self-labels and diagnoses share a base: an engine-minted `id`, the
`attempt_id` they assert about, and `created_at`. One reader orders all three,
latest first, with append order breaking a tie. The `id` lets a record be
cited, by an eval naming the diagnosis it scored or by a user correcting a
claim.

Ordering does not decide which record stands. The shared reader answers "in
what order", and each record's own section says who wins.

## Card runs

Studying a card is an explicit act, not a state the system infers.

- **Starting is explicit**, because the ladder is measured from the start. A
  ladder problem solved before the card began does not count toward the
  ladder. The card teaches the form, and having solved the problem once is not
  having studied the form.
- **The run holds what the start produced**: when the run began and the probes
  it was given. Later probes append rather than replacing the set, so what was
  offered and when stays readable.
- **Derived from the run, never stored**: ladder progress, recall state per
  template, and whether the card is done. "Done" is only a view for now.
  Graduation becomes a process later, once there are numbers to set its box and
  its probe count from.

## Recall attempts

One template reproduced from memory, and how it went.

- **A recall attempt is not an `Attempt`.** No problem and no submission. No
  field keys a recall attempt to an attempt, so it is its own record, keyed to
  a card and a template.
- **The unit is the template, not the card.** A card's forms are learned and
  lost separately, and a card-level number would average them together and show
  neither.
- **A hinted pass is not a pass.** Which hints were taken before succeeding is
  part of the record. Without that field, a decaying form scores the same as a
  fluent one.
- **Recall fluency is not solving fluency.** Reproducing a form cold is not
  recognising it unprompted, so recall fluency never stands in for mastery. The
  gap between recall fluency and solving fluency is the false fluency that
  blocked practice trains.
