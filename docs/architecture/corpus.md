# Corpus

What the engine generates: a problem, the test cases that decide it, and the
solutions written for it. Part of the architecture; `README.md` is the map.

## Problems

- **Generated, and that is the only origin.** The engine writes a statement,
  the test cases that decide it, a canonical solution and a reference
  solution.
- **A problem is written from a brief: what it must be solvable by.** A
  template is the tightest kind, naming the exact form. A technique is a looser
  one, naming only the skill. Both produce a problem, and the two differ in
  what the generator knew rather than in how the problem is judged.
- **The looser brief is what reaches the rest of the vocabulary.** A paradigm
  and a problem class have no form to reproduce, so no template names them, and
  a corpus written from templates alone can never exercise them.
- **The template it was written for is stored, where there was one.**
  `generated_for` is an assertion rather than a reading, and it is what makes
  the first template match provenance. It never claims the problem exercises
  nothing else. A problem written from a technique brief carries none: nothing
  told the generator a form, so nothing may assert a pair.
- **A technique brief asserts no technique either.** An assertion is what the
  generator was told, and it was told a skill rather than a solution.
- **Provenance is required.** A problem names what produced it, as any machine
  record does.
- **A problem's techniques are derived from readings of its canonical
  solutions**, and are a view rather than stored truth: adding a canonical can
  widen them, and re-deriving is legal and expected. The reference is excluded,
  or the naive approach a form replaces would be credited as one the problem
  takes. A canonical that sorts before it searches used two techniques, and
  only a reading names the second.
- **Never derived from templates.** A template is defined by whether it can be
  reproduced from memory, not by what it classifies. A paradigm and a problem
  class have no form to type out, so templates reach about half the vocabulary,
  and a technique set folded from them would be capped by which cards happen to
  exist.
- **The statement is stored, because it is what a solver is served.** The
  announcement floor reads it, and a matcher reads it beside the canonical it
  classifies. Required and non-blank.
- **A problem is created, cleared, then served.** `created` is written and
  verified, which is not the same as fit to serve. The announcement floor is
  what clears it: whether a statement telegraphs its form is a question about
  the corpus, and the generation call cannot answer it.
- **`created` is not a resting state.** Every created problem is promoted or
  retired. Until the floor is measured, selection reads created problems too,
  so the corpus is usable before the gate exists.
- **The two bars sit at different points.** Discrimination is checked at
  generation, so a problem whose cases separate nothing never lands. The floor
  is checked over the corpus, so a problem that telegraphs its form lands and
  is then retired.
- **A problem is edited in place only where no verdict moves.** Wording that
  changes nothing a solution returns is repaired. A statement that asks for
  something else mints a new problem, and the old one keeps its attempts.
- **A corrected statement usually drags cases with it**, which is why the edit
  cannot stand. The new wording needs cases that pin it, and those would fail
  attempts already made.
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
- **Exclusion is a read-time rule, never a deletion.** The attempts stay
  readable, and the board stops counting them.

## Test cases

What decides whether a solution to a generated problem is correct.

- **The first set is written with the problem, in the same call.** Cases
  derived afterwards describe whatever the solution happens to do, where cases
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
- **They are what makes verification reachable.** The engine judges a
  submission itself rather than recording a verdict it did not produce.
- **Owned, so the git invariant binds nothing the product ships.** The cases a
  generated problem carries are the product's own.
- **Expected outputs come from the reference, never from the canonical.** A
  case the canonical produced passes by construction, and `verified` then means
  only that the solution agrees with itself. The reference is different code
  from a call that saw the statement alone, so a case it computed is a test.
- **A case records where its expected output came from.** Beyond the largest
  input the reference finishes at generation time, only the canonical can
  compute one, and that case is evidence about the cap rather than about the
  verdict. Two cases in a set are not equally strong, and nothing but the field
  says which is which.
- **A case names the call that proposed its arguments**, which is not the
  problem's own wherever a mutation round or the speedup search won it. Three
  sites write cases at three configurations, and a reader taking the problem's
  provenance would attribute a round's case to the generator.
- **A case names the round that won it, zero for the set the first round was
  run against.** Replaying the discrimination site needs that set as it stood:
  it decides which mutants survive and it goes into the prompt. A loop shown a
  case a round already won reaches other survivors and sends another digest,
  so the verdict the generation run recorded is paid for a second time.
- **Zero covers two writers, and provenance is what separates them.** The
  statement's own cases name the generator's call; a fuzz case names the call
  that wrote the input generator. Both were in the set before any round ran,
  which is what zero says, and no field has to repeat what the call already
  names.
- **The separating case names no round.** It is appended after the loop, so it
  was never in the set the survivors were decided against. Zero would put it
  in the set a replay rebuilds, and absent is the only answer that keeps it
  out without inventing a round nothing ran.
- **Cases that separate nothing are worse than none**, because they license the
  word `verified` on a canonical that is wrong. A set that does not discriminate
  is a defect in the problem, and a problem carrying one does not land.
- **The cases define the problem, and the statement is what can disagree.** A
  finite set of arguments and returns describes some function. The statement is
  prose, so a mistake lands in the statement rather than in the cases.
- **A case set a deterministic canonical passes is already consistent.** Two
  cases with the same arguments and different returns fit no function, so no
  canonical can pass both. Nothing checks this separately.
- **Cases are appended, never revised.** An edge case, or one that forces a
  timeout, is added. What an addition leaves behind is a canonical needing
  re-verification rather than a record that is now wrong.
- **A case carries its arguments literally, and weighs at most 64 KiB.** The
  ceiling covers the arguments and the expected value together. A separating
  input is the largest a case ever holds, and separating a quadratic solution
  from a linear one takes a few thousand elements. A seed and a size would
  store less, at the cost of a case naming how it is built rather than what it
  holds, and of a run that builds an input before it can judge one.
- **The separating case is chosen against the sitting's cap**, never
  generation's. It is the size at which a submission that did not use the form
  fails, so the number a sitting judges under is what decides it.
- **A separating input over the ceiling stores no case.** The draft stops at
  the search, and the run reports what the walk found.
- **The two ways that happens assert opposite things, and are named apart.** A
  search that reached a separating size and could not store the case has
  established the speedup, and it reports the size and both measurements. One
  whose walk crossed the ceiling before the reference ever exceeded the cap has
  established nothing: a separation may sit at a size it could not look at.
- **Neither is a defect.** A run reading the three as one answer cannot tell a
  defect from an unknown.
- **The reference finishing at the largest legal input is a defect in the run,
  not in the problem.** It is briefed for the plainest solution and is never
  told which technique to avoid, so where the plain solution is the form it
  writes the form.
- **Three things produce that answer**, and nothing in the run separates them:
  the reference reached the form, the input generator built a shape the form
  does not beat, or the template claims a speedup its form does not have.
- **A problem whose template claims a speedup lands with the case that
  separates it, or it does not land.** The claim is what a rung teaches, and a
  corpus carrying problems that do not demonstrate it teaches the form on
  problems the naive solution also solves.
- **The same holds where no search ran.** A call that wrote no input generator
  leaves the claim undemonstrated as an empty search does, and the draft stops
  at the step before it.
- **It is held as a draft rather than discarded.** The statement, the cases and
  both solutions passed every gate that judges them, and discarding here would
  keep only the problems the blind model was slow at. The draft is resumed
  where it stopped, so nothing the calls bought is thrown away.
- **A held draft leaves by one of three exits**, and each names a different
  thing the run got wrong. A resumed search separates it. The template's
  `speedup` is corrected, and the next resume skips the search. Or the draft is
  rejected, which is the answer where the reference reached the form: the
  claim holds and this problem does not exercise it.
- **A corrected `speedup` is what a resume watches besides the digest.** A flag
  edit moves neither a configuration nor a prompt, so a resume reading only
  those would leave the draft where the search stopped it.
- **What a resumed search reaches is bounded.** It repairs an input generator
  that built the wrong shape. It does not reach a reference that wrote the
  form: that solution is immutable and it is still the clock, so the exit
  there is the flag or the rejection.
- **What goes unenforced is a speedup whose separating size is a million
  elements**, which is a log factor rather than the quadratic a card teaches.
  The bar is that some input separates the two, not that the separation is
  worth the card.
- **Consistent is not the same as statable.** A set fitting only "compute f,
  except return 7 on this input" is a function nobody can write a statement
  for. Such a problem does not land, and the discrimination bar is what catches
  it.
- **How discrimination is established is in `flows.md`.** A blind reference
  disagreeing on any case discards the problem, and a surviving mutant of the
  canonical names a case that has to exist.
- **The mutation loop stops after two rounds**, at one call each. A survivor
  two rounds did not kill is usually equivalent to the canonical, and no case
  kills an equivalent mutant. A round that kills nothing stops the loop
  early, since the next one asks the same question of the same survivors. The
  number was set before a corpus existed, and what revises it is how much the
  second round still kills.
- **A round's proposal lands only where it killed.** The round is paid for by
  the call rather than by the cases it returns, so a proposal no mutant fails
  is a case every later verification runs for nothing. `flows.md` gives how the
  kill is attributed.
- **The fuzz pass runs before the first round, and costs no call.** The input
  generator builds at several sizes and seeds, and the mutants still standing
  are run against those inputs. Only what survives it reaches a round.
- **The canonical is the oracle for killing, and the reference still settles
  the case.** A mutant is killed by answering a built input differently from
  the solution it is a copy of, which needs no expected value. What is then
  stored carries the reference's answer, as every other case does.
- **Only an input that killed is kept.** One that killed nothing catches
  nothing, and every later verification would run it. The reference is run on
  the kept ones alone, so the rest cost one execution each.
- **The first input that kills a mutant is the one kept.** The pass builds
  smallest first, so the kept case is the smallest that separates. A second
  input killing the same mutant adds a case that decides nothing new.
- **A kept input is shrunk before it is stored.** It is as large as the size it
  was built at, where the mistake it catches usually needs a few elements. The
  shrink is paid once, and what it saves is paid back by every verification
  that runs the case.
- **What it shrinks against is the mutants that input killed**, not the whole
  set. A smaller input killing fewer of them would lose a kill the pass already
  counted, and nothing else would catch it.
- **Only lists shrink.** A shorter list is the same question asked of less,
  where a smaller number is a different question the statement answers, and
  nothing says the smaller one is still legal.
- **The shrunk input carries its own answer.** The canonical is run again on
  it, since a case keeping the answer to the input it was shrunk from would
  fail the solution it was written from.
- **The ceiling is checked after the shrink.** An input over it is storable
  once it is only as large as the kill needs, where checking first would
  discard the kill with the size.
- **The shrink runs on a budget of candidate inputs.** Each costs a run of the
  canonical and one per mutant it must keep killing, so an input nothing
  shrinks would otherwise spend the pass's whole runtime.
- **A built input the canonical cannot answer drops the case**, as a proposed
  one does. Nothing checks a built input against the constraints the statement
  gives, so a crash there is as likely to be an input the problem excludes.
- **A kept input the two solutions answer differently discards the problem**,
  as a round's proposal does. The pass reaches boundaries the first set never
  did, and a canonical wrong at one of them is what it exists to find.

## Solutions

A solution the engine wrote for a problem, in one of two roles.

- **The canonical displays the template's form**, and is what a rung teaches.
  Exemplary rather than merely correct.
- **The reference is written from the statement alone.** It computes the
  expected outputs and it is what a timing bar measures against. Independence
  is its whole purpose, so a solution displaying the form could not serve as
  one.
- **The role is stored, because both are verified against the same cases.**
  Passing says nothing about which of the two a solution is, and a reader
  taking a reference for a canonical would teach the approach the card exists
  to replace.
- **It is what a template match is keyed to.** A form is displayed by code, so
  which form is a question about the solution and a statement only implies one.
  The matcher reads the canonical beside the statement, and the verdict is
  about the canonical.
- **Several per problem, and the set is the assertion.** Two approaches to one
  problem is the ordinary case, and it is what lets one rung cover a core
  template and an optional one. A problem carrying one canonical can teach one
  form.
- **A template is where a problem comes from, never where its later solutions
  come from.** The rest are enumerated: a call over a landed problem proposes
  the approaches that solve it, and each proposal is generated as its own
  canonical. Asking for one by template would reach only forms someone
  authored, where enumeration reaches the techniques no card covers.
- **A later canonical carries less assurance than the first.** The case set was
  built to kill mutants of the first canonical, so a second approach passing
  those cases was never tested on its own failure modes. It is stored and it
  teaches, and re-running the mutation loop over it is what would close the
  gap.
- **Never counted as an attempt**: no user and no sitting. It answers no board
  row and earns no progress, and a user who reads one has not solved the
  problem.
- **Sampled, not greedy — the exception Machine records names.** Generation
  produces the artifact rather than a verdict about one, so no verdict needs
  protecting from variance, and variance is what stops one model's habits
  becoming the whole corpus. The cost is a canonical that is re-runnable and
  never reproducible, which is also why nothing re-derives it.
- **Immutable once written.** Whether it passes is a fact about a run, so
  nothing about how it ran is stored here.

## Technique readings

Which techniques a solution used. Product-owned and global, as the solution is.

- **Its own record, not a technique claim.** A claim is testimony about the
  user's own attempt and is private; a reading is a verdict about code the
  engine wrote, and it ships with the corpus. One record type would also make
  the fallback a fold over records of the type it falls back for.
- **The candidates are the whole vocabulary**, where an attempt is classified
  against the problem's own techniques. Those techniques are derived from these
  readings, so constraining a reading by them is circular.
- **One reader, two records.** The prompt, the transport and the staleness rule
  are shared with the attempt classifier. Two prompts asking one question would
  drift, and neither score would compare.
- **A machine record like any other**: provenance whole, staleness keyed on the
  digest of what was sent, and re-derivable at any time. Where a claim carries
  one problem's criteria, a reading carries the whole vocabulary's, so any
  criteria edit re-reads every canonical.
- **Two writers, user first**, as a claim resolves. A hand record here
  adjudicates rather than testifies: nobody sat for a canonical, so what the
  user writes is a reading of code they did not produce. It stands all the
  same, and it is the reference a configuration is scored against.
- **It is what a problem's techniques are folded from.** The union over the
  standing readings of its canonicals, with the reference excluded.

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
- **The backend and the interpreter are named, as one opaque string.** A local
  subprocess and a container under a CPU limit decide a timeout differently,
  and nothing else separates two runs that disagree. Full environment
  provenance is deferred, and subsumes this field rather than replacing it.
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

## Execution

How a solution is run. The runner is a component and can be replaced; a
`Verification` is append-only and cannot. So what a stored result means is
fixed here rather than by whatever executed it.

- **The cap is wall clock around the `solve` call, measured in the child.**
  Interpreter start is excluded, since it moves with the machine's load. Two
  runs storing one number would otherwise not be comparable.
- **A case is decided by JSON equality on the returned value**, encoded with
  sorted keys. A tuple and a list are one answer under that rule, where `True`
  and `1` are two.
- **A problem admitting several correct returns does not land.** The
  alternative is a checker per problem, and every stored verdict would then
  depend on code the record does not name. The statement says how ties are
  broken, and a canonical and a reference disagreeing is what catches one that
  does not. What this excludes is the problem asking for any valid answer of
  many, and that cost is accepted until a core template needs one.
- **A return that JSON cannot encode is `CRASHED`.** The fault is the
  solution's rather than the case's. `WRONG` would file it beside an answer
  that was computed and is merely incorrect. The child does the encoding, so
  every backend uses the encoder `as_json` uses, or the same return would be
  decided differently by where it ran.
- **A solution defining no module-level `solve` fails every case as
  `CRASHED`.** Code that does not parse is rejected the same way. A verdict
  rather than an error, because
  Phase 8 reads this path for an attempt, and a submission with a syntax error
  is the ordinary case.
- **No case observes another.** A solution memoising in a module global would
  otherwise answer one case from a cache built for a different one, and a wrong
  key would pass. Which mechanism gives that isolation is the runner's to
  choose.
- **A runner fault is raised, never recorded.** A subprocess that fails to
  start says nothing about the solution, and a stored `CRASHED` would discard a
  sound problem over the runner's own defect.
- **A run is comparable only within one backend.** A CPU limit changes what a
  timing bar measures, so the smallest input separating a reference from a
  canonical is a fact about the backend that found it.
- **Comparison stays outside the executor.** A backend is handed code, the
  arguments and a cap, and returns what each call produced. It is never told
  what a case expects, so the rule deciding a case cannot vary by where the
  code ran.
- **A case yielding no value is read by the solution's role.** A canonical that
  crashed or timed out discards the problem, since nothing establishes what the
  case returns. A reference that did so is the ordinary path beyond its reach,
  and the case takes the canonical's answer with `expected_from` naming it.
- **A reference that computed no case discards the problem.** Every expected
  output would then be the canonical's own, and `verified` would mean only that
  the solution agrees with itself. Some cases beyond its reach is the ordinary
  path; all of them is no independent reading at all.
- **The stored cap is the child's**, since that is the number the case was
  judged by. The parent runs a slack timer of its own, which the runner owns.
- **A child reporting nothing is read from how it died.** The parent's timer
  firing is `TIMEOUT`. A signal is `CRASHED`, which is where a segfault and a
  kill under memory pressure land. Anything else is the runner's own fault and
  is raised, since it says nothing about the solution.
- **A case result carries what the child measured.** The separating input a
  speedup search looks for is found from those numbers, and a result holding
  only the outcome would make every later search re-run the whole set.
