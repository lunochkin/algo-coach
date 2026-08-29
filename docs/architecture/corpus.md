# Corpus

What the engine generates: a problem, the test cases that decide it, and the
canonical solutions that display the approach. Part of the architecture;
`README.md` is the map.

## Problems

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
- **A problem is created, cleared, then served.** `created` is written and
  verified, which is not the same as fit to serve. The announcement floor is
  what clears it: whether a statement telegraphs its form is a question about
  the corpus, and the generation call cannot answer it.
- **`created` is not a resting state.** Every created problem is promoted or
  retired. Until the floor is measured, selection reads created problems too,
  so the corpus is usable before the gate exists.
- **Retirement does not imply the problem was served.** One failing the floor
  is retired as telegraphed having never been active. The rule that its
  attempts are kept holds either way, and is about nothing where it has none.
- **The two bars sit at different points.** Discrimination is checked at
  generation, so a problem whose cases separate nothing never lands. The floor
  is checked over the corpus, so a problem that telegraphs its form lands and
  is then retired.
- **A problem is edited in place only where no verdict moves.** Wording that
  changes nothing a solution returns is repaired. A statement that asks for
  something else mints a new problem, and the old one keeps its attempts.
- **A corrected statement usually drags cases with it**, which is why the edit
  cannot stand. The new wording needs cases that pin it, and those would fail
  attempts already made. So the verdicts an in-place edit meant to preserve do
  not survive it.
- **Retirement names its reason, because readers treat the two apart.**
  `defective` is a statement that asked for something its cases do not decide.
  `telegraphed` is one that names the approach, which the announcement floor
  rejects.
- **A defective problem's attempts are excluded from mastery, both
  directions.** The failure was the problem's fault, and the self-label the
  loop asked for blamed the user instead. Excluding only the failures would
  raise a technique's solve rate because a problem was broken.
- **A telegraphed problem's attempts are kept.** Its statement asked what its
  cases decide, so the verdict is a fact about the solution. Whether such a
  solve counts for less than an unprompted one is deferred, since it needs a
  weighting nothing has.
- **Exclusion is a read-time rule, never a deletion.** Aggregates are derived
  views. The attempts stay readable, and the board stops counting them.

## Test cases

What decides whether a solution to a generated problem is correct.

- **The first set is written with the problem, in the same call.** Cases
  derived afterwards describe whatever the solution happens to do. Cases
  written with the statement describe what the problem asks. Later additions
  append to that set rather than replacing it.
- **A case is arguments and an expected return.** Parsing stdin would make a
  case describe how a solution was driven rather than what it must compute.
  The arguments are positional, so a canonical names its parameters whatever
  reads best.
- **The entry point is fixed rather than stored.** Every solution defines one
  module-level function named `solve`. A stored name lets a generator write a
  statement naming one function and a canonical defining another, and the
  runner then fails a correct solution. A fixed name makes that state
  unreachable.
- **A fixed name also stops the signature announcing the approach.** A
  function called `longest_palindromic_substring` tells the solver what the
  statement was written to withhold. What the announcement floor measures on a
  statement applies to a signature too.
- **A problem needing more than one entry point is not expressible**, and that
  is accepted. A structure asked for by its operations has no single function.
  If one is ever wanted, `entrypoint` is an additive field whose absence means
  the convention.
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
- **The cases define the problem, and the statement is what can disagree.** A
  finite set of arguments and returns describes some function. The statement is
  prose, and prose is where the mistake lands.
- **A case set a deterministic canonical passes is already consistent.** Two
  cases with the same arguments and different returns fit no function, so no
  canonical can pass both. Nothing checks this separately.
- **Cases are appended, never revised.** An edge case, or one that forces a
  timeout, is added. What an addition leaves behind is a canonical needing
  re-verification rather than a record that is now wrong.
- **A case that turns out to be wrong is discarded with its problem.** Under
  the rule above the fault is the statement's, so the repair mints a new
  problem and the old cases go with the old one.
- **Consistent is not the same as statable.** A set fitting only "compute f,
  except return 7 on this input" is a function nobody can write a statement
  for. Such a problem does not land, and the discrimination bar is what catches
  it.
- **How discrimination is established is deferred.** Candidates: two canonicals
  from different approaches agreeing on every case, a mechanically broken
  canonical failing, the near miss the technique entry names failing. Which is
  the bar is a question a real corpus answers and an argument does not.

## Canonical solutions

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
- **Immutable once written.** Whether it passes is a fact about a run, so
  nothing about how it ran is stored here.

## Verification runs

One execution of a solution against a problem's cases.

- **Its own record, because the outcome is a fact about the run.** The cap and
  the machine decide a timeout, and a crash can come from the runner rather
  than the solution. A result stored on the solution would claim a permanence
  it does not have.
- **Re-running is legal and expected**, as re-deriving a reading is. Two runs
  of one solution are two records, and neither supersedes the other.
- **The cap is stored beside the results.** It is what decided any timeout,
  and two runs under different caps are not comparable. Nothing else would
  show that they differ.
- **What the environment contributes is deferred.** The machine and the
  interpreter version decide a timeout or a crash as much as the cap does, and
  the shape recording them is not settled.
- **The verification result is per case, and names how each one went**:
  passed, wrong, timed out or crashed. A share cannot say which input timed
  out, and the set of cases that passed cannot say why the rest did not. A
  failure mode reads both halves. Phase 8 stores the same result for an
  attempt.
- **A run covers the whole case set**, including the cases it answered
  before. One answering only what was added since would fold to their outcome
  alone and say nothing about the rest. Executing code is cheap where a model
  call is not.
- **The outcome over the run is folded, never stored**, and it is the four
  words a case uses. A timeout is a fact about the run that surfaces at one
  case, so the level it is read at does not change what it means.
- **The most severe failure stands in that fold.** A solution that only ran
  slowly is otherwise correct, which is a different remedy from one returning
  a wrong answer. An empty set folds to nothing rather than to passed, or it
  would claim a verification that never ran.
