# Corpus

The engine generates a problem, the test cases that decide it, and the
solutions written for it. This file specifies those records. Part of the
architecture, and `README.md` is the map.

## Problems

- **Generated, and that is the only origin.** The engine writes a statement,
  the test cases that decide it, a canonical solution and a reference
  solution.
- **A problem is written for a target: what it must be solvable by.** A
  template is the tightest kind, naming the exact form. A technique is a looser
  one, naming only the skill. Each kind produces a problem. A template target
  and a technique target differ in what the generator knew, and not in how the
  problem is judged.
- **The looser target reaches the rest of the vocabulary.** A paradigm and a
  problem class have no form to reproduce, so no template names them, and a
  corpus written from templates alone can never exercise them.
- **The template it was written for is stored, where there was one.**
  `generated_for` records what the generator was told rather than what a
  reader inferred, and it makes the
  first template match provenance. It never claims the problem exercises
  nothing else. A problem written for a technique target carries no
  `generated_for`: the generator was told no form, so no pair can be asserted.
- **A technique target asserts no technique either.** The generator's match
  records what the generator was told, and a technique target told it a skill
  rather than a solution.
- **Provenance is required.** A problem names what produced it, as any machine
  record does.
- **A problem's techniques are derived from readings of its canonical
  solutions**, and are a view rather than stored truth: adding a canonical can
  widen the set, and re-deriving is legal and expected. The reference is
  excluded from those readings. Otherwise the naive approach a form replaces
  would be credited as an approach the problem takes. A canonical that sorts
  before it searches used two techniques, and only a reading names the second.
- **Never derived from templates.** A template is defined by whether its form
  can be reproduced from memory. That definition says nothing about what the
  template classifies. A paradigm and a
  problem class have no form to type out, so templates reach about half the
  vocabulary, and a technique set folded from them would be capped by which
  cards happen to exist.
- **The statement is stored, because a solver is served it.** A matcher also
  reads the statement beside the canonical it classifies. Required and
  non-blank.
- **A created problem is served.** `created` means written and verified, and
  no later gate stands between that and serving. Retirement is the only status
  move.
- **Whether a statement gives its form away is not checked.** A statement can
  name its approach, or reuse the example its template's trigger names, and a
  solver who recognises the problem has not derived the form. A gate over the
  corpus for this is deferred to Phase 13 in `ROADMAP.md`. It needs a corpus
  to measure and a baseline no generator wrote, and a status the gate promotes
  to is an additive change when it comes.
- **A problem is never edited, and only its status moves.** A statement that
  says the wrong thing is retired `defective` and a new problem is written.
  The retired problem's attempts stay with the record they were made against,
  and no case moves under them. A generated statement passes every gate or is
  retired, so a write path for wording would buy nothing and could change what
  a verdict means.
- **Retirement names its reason.** `defective` is a statement that asked for
  something its cases do not decide, and it is the only reason today. A reason
  whose attempts are kept is additive when a gate needs one.
- **A defective problem's attempts are excluded from mastery, both
  directions.** The failure was the problem's fault, and the self-label the
  loop asked for blamed the user instead. Excluding only the failures would
  raise a technique's solve rate because a problem was broken.
- **Exclusion is a read-time rule, never a deletion.** The attempts stay
  readable, and the board stops counting them.

## Test cases

The test cases decide whether a solution to a generated problem is correct.

- **The first set is written with the problem, in the same call.** Cases
  written with the statement describe what the problem asks. Cases derived
  afterwards from a solution describe whatever that solution happens to do.
  Later additions append to the first set rather than replacing it.
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
  statement was written to withhold. A signature can name the form as a
  statement can, so the same rule covers both.
- **The statement carries the signature, because the parameter order has to
  be stated somewhere.** A fixed name leaves the parameter order to be
  inferred from prose, and three prompts infer it separately. A reference took
  `solve(capacity, times, sizes)` where the canonical took `solve(times,
  sizes, capacity)`, answered no case, and the problem was discarded as
  untested.
- **A statement whose signature contradicts its canonical does not land.** The
  reference and the naive solution are written to the statement, so a wrong
  signature there is worse than a missing one. The signature and the canonical
  are both read off the generation call's reply, so the check runs as that
  reply is read.
- **A problem needing more than one entry point is not expressible**, and that
  is accepted. A structure asked for by its operations has no single function.
  If one is ever wanted, `entrypoint` is an additive field whose absence means
  the convention.
- **Test cases make verification reachable.** The engine judges a submission
  itself rather than recording a verdict it did not produce.
- **The cases are owned, so the git invariant binds nothing the product
  ships.** The git invariant forbids third-party test cases in any repo, and
  the cases a generated problem carries are the product's own.
- **Expected outputs come from the reference, never from the canonical.** A
  case the canonical produced passes by construction, and `verified` then
  means only that the solution agrees with itself. The reference is different
  code from a call that saw the statement alone, so a case the reference
  computed is a test.
- **The value the generator declared is neither a source nor a gate.** One call
  wrote the canonical and the declaration, so a contradiction between them is
  that call's arithmetic rather than a second reading of the statement. The
  count of contradictions sits on the generator's site outcome, and the
  reference decides whether the problem is discarded.
- **A case records where its expected output came from.** Beyond the largest
  input the reference finishes at generation time, only the canonical can
  compute an expected output, and such a case is evidence about the cap rather
  than about the verdict. Two cases in a set are not equally strong, and only
  the `expected_from` field says which is which.
- **A case names the call that proposed its arguments.** That call is not the
  problem's own wherever a mutation round or the speedup search won the case.
  Three sites write cases at three configurations, and a reader taking the
  problem's provenance would attribute a round's case to the generator.
- **A case names the round that won it, zero for the set the first round was run
  against.** Replaying the discrimination site needs that set as it stood,
  because the set decides which mutants survive and the set goes into the
  prompt. A loop shown a case a round already won reaches other survivors and
  sends another prompt hash, so the verdict the generation run recorded is paid
  for a second time.
- **Zero covers two writers, and provenance separates them.** The statement's
  own cases name the generator's call. A fuzz case names the call that wrote
  the input generator. Each kind was in the set before any round ran, and that
  is all zero says. No field repeats what the call already names.
- **The separating case names no round.** The separating case is appended
  after the loop, so it was never in the set the survivors were decided
  against. Zero would put the separating case in the set a replay rebuilds. An
  absent round keeps the case out without inventing a round nothing ran.
- **Cases that separate nothing are worse than none**, because they license the
  word `verified` on a canonical that is wrong. A set that does not discriminate
  is a defect in the problem, and a problem carrying such a set does not land.
- **The cases define the problem, and the statement can disagree with them.**
  A finite set of arguments and returns describes some function. The statement
  is prose, so a mistake lands in the statement rather than in the cases.
- **A case set a deterministic canonical passes is already consistent.** Two
  cases with the same arguments and different returns fit no function, so no
  canonical can pass both. No separate check for consistency runs.
- **Cases are appended, never revised.** An edge case, or a case that forces a
  timeout, is added. An addition leaves behind a canonical needing
  re-verification, and never a record that is now wrong.
- **A case carries its arguments literally, and weighs at most 64 KiB.** The
  ceiling covers the arguments and the expected value together. A separating
  input is the largest a case ever holds, and separating a quadratic solution
  from a linear one takes a few thousand elements. A seed and a size would
  store less. Such a case would name how its input is built rather than what
  the input holds, and a run would build the input before judging it.
- **The ceiling is reached at a few thousand elements**, since an integer drawn
  at full magnitude costs eleven bytes. Four of the first twenty searches
  crossed the ceiling before the naive solution exceeded the cap, so a
  quadratic separation may not fit.
- **The separating case is chosen against the sitting's cap**, and never
  against generation's. The separating size is the size at which a submission
  that did not use the form fails, so the cap a sitting judges under decides
  that size.
- **A separation at the smallest legal input is a whole verdict.** Eight of the
  first fifteen searches separated at one or two. The naive solution scans a
  range taken from the values the input carries, and a legal input carries
  values large enough at any size. The naive solution exceeds the cap on
  inputs smaller than the statement admits, so every legal input teaches the
  form.
- **A size is comparable only within one naive solution's cost.** A form whose
  naive solution is exponential in the size separates in the tens. A form
  whose naive cost the values drive separates at the smallest legal input,
  against the same bound of a hundred thousand. Two sizes drawn from two naive
  solutions say nothing about each other.
- **A separating input over the ceiling stores no case.** The draft stops at
  the search, and the run reports what the walk found.
- **A search stores no case for one of two reasons, and the draft names the two
  apart.** The two reasons assert opposite things. A search that reached a
  separating size and could not store the case has established the speedup. It
  reports the size and both timings. A search whose walk crossed the ceiling
  before the naive solution ever exceeded the cap has established nothing: a
  separation may sit at a size the walk could not look at.

- **A search that stored no case is not a defect either way.** A run folding
  those two answers together with a naive solution that finished at the
  largest legal input could not tell a defect from an unknown.
- **The naive solution finishing at the largest legal input is a defect in the
  run, not in the problem.** The naive solution is prompted as the approach the
  form replaces and told which form to avoid, so finishing means the prompt did
  not take.
- **Three faults produce that answer, and the run cannot separate them.** The
  naive solution reached the form. The input generator built a shape the form
  does not beat. Or the template claims a speedup its form does not have.
- **A problem whose template claims a speedup lands with the case that
  separates it, or it does not land.** A rung teaches the claimed speedup. A
  corpus carrying problems that do not demonstrate the speedup teaches the
  form on problems the naive solution also solves.
- **The same holds where no search ran.** A call that wrote no input generator,
  or one that wrote no naive solution, leaves the claim undemonstrated as an
  empty search does. The draft stops at the step before the search.
- **The problem is held as a draft rather than discarded.** The statement, the
  cases and every solution passed every gate that judges them. Discarding here
  would keep only the problems one model happened to be slow at. The draft is
  resumed where it stopped, so nothing the calls bought is thrown away.
- **A held draft leaves by one of four exits**, and each names a different
  thing the run got wrong. A resumed search separates the draft. A second
  naive solution is drawn, and the second one is slow. The template's
  `speedup` is corrected, and the next resume skips the search. Or the draft
  is rejected: the claim holds, and this problem does not exercise the form.
- **A resume watches the template's `speedup` beside the prompt hash.** A flag
  edit moves neither a configuration nor a prompt, so a resume reading only
  those two would leave the draft where the search stopped it.
- **A resume asks the naive site again where the naive solution finished at
  every size the input generator reached**, though its configuration and its
  prompt hash both stand. The naive site is sampled, so a second call is a
  second draw. The skip that spares every other site would spend the exit that
  costs one call.
- **The draft carries why the search stored no case**, since the exits differ by
  that reason. A crashed input generator is the inputs site's to repair, and a
  second naive draw there buys a call the search still cannot use.
- **The reference is not asked again for this.** The reference is immutable,
  the search no longer measures against the reference, and a second blind
  reading answers a question no exit asks.
- **Rejection is the exit left when the draws run out.** A model prompted to be
  slow and told the form to avoid, writing the form anyway, is the strongest
  evidence the run can produce that the problem does not exercise the form.
- **A speedup whose separating size is a million elements goes unenforced.**
  That separation is a log factor rather than the quadratic a card teaches.
  The bar is that some input separates the two solutions, not that the
  separation is worth the card.
- **Consistent is not the same as statable.** A set fitting only "compute f,
  except return 7 on this input" is a function nobody can write a statement
  for. Such a problem does not land, and the discrimination bar catches it.
- **How discrimination is established is in `flows.md`.** A blind reference
  disagreeing on any case discards the problem, and a surviving mutant of the
  canonical names a case that has to exist.
- **The mutation loop stops after two rounds**, at one call each. A survivor
  two rounds did not kill is usually equivalent to the canonical, and no case
  kills an equivalent mutant. A round that kills nothing stops the loop
  early, since the next round asks the same question of the same survivors.
  The bound of two was set before a corpus existed, and how much the second
  round still kills revises it.
- **A round's proposal lands only where it killed.** The round is paid for by
  the call rather than by the cases it returns, so a proposal no mutant fails
  is a case every later verification runs for nothing. `flows.md` gives how
  the kill is attributed.
- **The fuzz pass runs before the first round, and costs no call.** The input
  generator builds at several sizes and seeds, and the mutants still standing
  are run against those inputs. Only the mutants that survive the fuzz pass
  reach a round.
- **The canonical is the oracle for killing, and the reference still settles
  the case.** A mutant is killed by answering a built input differently from
  the solution it is a copy of, which needs no expected value. The stored case
  carries the reference's answer, as every other case does.
- **Only an input that killed is kept.** An input that killed nothing catches
  nothing, and every later verification would run it. The reference is run on
  the kept inputs alone, so the rest cost one execution each.
- **The first input that kills a mutant is the input kept.** The pass builds
  smallest first, so the kept case is the smallest that separates. A second
  input killing the same mutant adds a case that decides nothing new.
- **A kept input is shrunk before it is stored.** A kept input is as large as
  the size it was built at, and the mistake it catches usually needs a few
  elements. The shrink is paid once, and every verification that runs the case
  saves the difference.
- **The shrink is checked against the mutants that input killed**, not against
  the whole set. A smaller input killing fewer of those mutants would lose a
  kill the pass already counted, and nothing else would catch it.
- **Only lists shrink.** A shorter list is the same question asked of less. A
  smaller number is a different question, and nothing says the smaller number
  is still legal under the statement.
- **The shrunk input carries its own answer.** The canonical is run again on
  the shrunk input. A case keeping the answer to the input it was shrunk from
  would fail the solution it was written from.
- **The ceiling is checked after the shrink.** An input over the ceiling is
  storable once it is only as large as the kill needs. Checking before the
  shrink would discard the kill with the size.
- **The shrink runs on a budget of candidate inputs.** Each candidate costs a
  run of the canonical and one run per mutant it must keep killing, so an
  input nothing shrinks would otherwise spend the pass's whole runtime.
- **A built input the canonical cannot answer drops the case**, as a proposed
  input does. No check runs a built input against the constraints the
  statement gives, so a crash there is as likely to be an input the problem
  excludes as a defect in the canonical.
- **A kept input the canonical and the reference answer differently discards
  the problem**, as a round's proposal does. The pass reaches boundaries the
  first set never did, and the pass exists to find a canonical wrong at one of
  those boundaries.

## Solutions

A solution the engine wrote for a problem, in one of three roles.

- **The canonical displays the template's form**, and a rung teaches the
  canonical. It is exemplary rather than merely correct.
- **The reference is written from the statement alone**, and it computes the
  expected outputs. Independence is its whole purpose, so a solution
  displaying the form could not serve as a reference.
- **The speedup search times the naive solution.** The naive solution is the
  approach the card's form replaces, and the search measures the canonical
  against it. The reference once held both jobs, and the jobs conflict. The
  reference job needs a blind reading, and the naive job needs a solution that
  does not reach the form.
- **The naive solution may not narrow its candidates the way the canonical
  does.** A naive solution trying only the values the input carries has used
  the insight the form is built on. The two solutions then run the same way,
  and the search separates nothing.
- **The naive solution may not be slower than the approach it stands for
  either.** A naive solution trying every subset where the statement describes
  a scan is separated at a few dozen elements, and a submission of the wrong
  complexity passes every input that small.
- **The prompt states both ends.** Two edits to the prompt have each fixed one
  end and caused the other, so a prompt naming one end alone has been written
  twice.
- **The naive solution may be told which form to avoid**, where the reference
  may not. The naive solution settles no case, discards no problem and is
  scored against nothing, so nothing it is shown can reach a verdict.
- **The naive site is sampled, for the reason the generator is.** It produces
  an artifact rather than a verdict, so asking again is a second draw rather
  than the answer already stored.
- **The naive solution is verified, and a failure is its own.** A wrong naive
  solution measures nothing, so one that answers a case wrongly is not stored
  and the draft is held. The failure never discards the problem: being wrong
  says nothing about the statement.
- **A case the naive solution does not finish is not a failure.** Being slow
  is the naive solution's purpose, and only a computed answer can be wrong.
  The cases written with the statement are small, so a case the naive solution
  cannot answer there is the same evidence the search looks for at size.
- **The naive solution is written only where the template claims a speedup**,
  as the search runs only there. A form that is its own optimum has nothing to
  be measured against.
- **The naive solution is excluded from what a canonical answers for**, as the
  reference is: no technique reading, no template match, no rung. It is the
  approach the card exists to replace.
- **The naive solution is stored at landing, as the reference is.** A replay
  re-runs the search over the stored problem, and re-deriving the naive
  solution would re-pay the call that wrote it.
- **The role is stored, because all three roles are verified against the same
  cases.** Passing says nothing about which role a solution holds, and a
  reader taking a reference for a canonical would teach the approach the card
  exists to replace.
- **A template match is keyed to a solution.** A form is displayed by code, so
  which form is a question about the solution, and a statement only implies
  one. The matcher reads the canonical beside the statement, and the verdict
  is about the canonical.
- **A problem may carry several canonicals, and together they say what it
  teaches.** Two
  approaches to one problem is the ordinary case, and two canonicals let one
  rung cover a core template and an optional one. A problem carrying one
  canonical can teach one form.
- **A template is the origin of a problem, and never the origin of its later
  solutions.** The later canonicals are enumerated: a call over a landed
  problem proposes the approaches that solve it, and each proposal is
  generated as its own canonical. Asking for a solution by template would
  reach only forms someone authored, where enumeration reaches the techniques
  no card covers.
- **A later canonical carries less assurance than the first.** The case set
  was built to kill mutants of the first canonical, so a second approach
  passing those cases was never tested on its own failure modes. The later
  canonical is stored and it teaches. Re-running the mutation loop over the
  later canonical would close the gap.
- **A solution is never counted as an attempt**: no user and no sitting. A
  solution answers no board row and earns no progress, and a user who reads
  one has not solved the problem.
- **A canonical is sampled, not greedy, which is the exception `machine.md`
  names.** Generation produces the artifact rather than a verdict about one,
  so no verdict needs protecting from variance. Variance stops one model's
  habits becoming the whole corpus. The cost is a canonical that is
  re-runnable and never reproducible, which is also why nothing re-derives it.
- **A solution is immutable once written.** Whether a solution passes is a
  fact about a run, so nothing about how it ran is stored on the solution.

## Technique readings

A technique reading names which techniques a solution used. It is
product-owned and global, as the solution is.

- **A reading is its own record, not a technique claim.** A claim is testimony
  about the user's own attempt, and is private. A reading is a verdict about
  code the engine wrote, and ships with the corpus. One record type for both
  would also make the fallback a fold over records of the type it falls back
  for.
- **The candidates are the whole vocabulary**, where an attempt is classified
  against the problem's own techniques. A problem's techniques are derived
  from these readings, so constraining a reading by them is circular.
- **One reader writes two records.** The prompt, the transport and the
  staleness rule are shared with the attempt classifier. Two prompts asking
  one question would drift, and neither score would compare with the other.
- **A reading is a machine record like any other**: provenance whole,
  staleness keyed on the prompt hash of what was sent, and re-derivable at any
  time. A claim carries one problem's criteria, and a reading carries the
  whole vocabulary's, so any criteria edit re-reads every canonical.
- **Two writers, and the user's stands first**, as a claim resolves. A hand
  reading adjudicates rather than testifies: nobody sat for a canonical, so
  the user's reading is of code they did not produce. The hand reading stands
  all the same, and it is the reference a configuration is scored against.
- **A problem's techniques are folded from its readings.** The union over the
  standing readings of its canonicals, with the reference excluded.

## Verification runs

A verification run is one execution of a solution against a problem's cases.

- **A verification is its own record, because the outcome is a fact about the
  run.** The cap and the machine decide a timeout, and a crash can come from
  the runner rather than the solution. A result stored on the solution would
  claim a permanence it does not have.
- **Re-running is legal and expected**, as re-deriving a reading is. Two runs
  of one solution are two records, and neither run supersedes the other.
- **The cap is stored beside the results.** The cap decided any timeout, and
  two runs under different caps are not comparable. No other field would show
  that the caps differ.
- **The runner and the interpreter are named, as one opaque string.** A local
  subprocess and a container under a CPU limit decide a timeout differently,
  and nothing else separates two runs that disagree. Full environment
  provenance is deferred, and subsumes this field rather than replacing it.
- **The verification result is per case, and names how each case went**:
  passed, wrong, timed out or crashed. A share cannot say which input timed
  out, and the set of cases that passed cannot say why the rest did not. A
  failure mode is read from which case failed and how. Phase 8 stores the same
  result for an attempt.
- **A run covers the whole case set**, including the cases it answered
  before. A run answering only the cases added since the last run would fold
  to their outcome alone and say nothing about the rest. Executing code is
  cheap where a model call is not.
- **The outcome over the run is folded, never stored**, and it uses the four
  outcomes a case uses. A timeout is a fact about the run that surfaces at one
  case, so the level it is read at does not change what it means.
- **The most severe failure stands in that fold.** A solution that only ran
  slowly is otherwise correct, which is a different remedy from one returning
  a wrong answer. An empty set folds to nothing rather than to passed, or the
  fold would claim a verification that never ran.

## Execution

How a solution is run. The runner is a component and can be replaced. A
`Verification` is append-only and cannot. So the meaning of a stored result is
fixed here rather than by whatever executed it.

- **The cap is wall clock around the `solve` call, measured in the child.**
  Interpreter start is excluded, since it moves with the machine's load. Two
  runs storing one number would otherwise not be comparable.
- **A case is decided by JSON equality on the returned value**, encoded with
  sorted keys. A tuple and a list are one answer under that rule, and `True`
  and `1` are two.
- **A problem admitting several correct returns does not land.** The
  alternative is a checker per problem, and every stored verdict would then
  depend on code the record does not name. The statement says how ties are
  broken, and a canonical and a reference disagreeing catches a statement
  that does not. The rule excludes a problem asking for any valid answer of
  many, and that cost is accepted until a core template needs one.
- **A return that JSON cannot encode is `CRASHED`.** The fault is the
  solution's rather than the case's. `WRONG` would file it beside an answer
  that was computed and is merely incorrect. The child does the encoding, so
  every runner uses the encoder `as_json` uses, or the same return would be
  decided differently by where it ran.
- **A solution defining no module-level `solve` fails every case as
  `CRASHED`.** Code that does not parse is rejected the same way. It is a
  verdict rather than an error, because Phase 8 reads this path for an
  attempt, and a submission with a syntax error is the ordinary case.
- **No case observes another.** A solution memoising in a module global would
  otherwise answer one case from a cache built for a different one, and a wrong
  key would pass. Which mechanism gives that isolation is the runner's to
  choose.
- **A runner fault is raised, never recorded.** A subprocess that fails to
  start says nothing about the solution, and a stored `CRASHED` would discard a
  sound problem over the runner's own defect.
- **A run is comparable only within one runner.** A CPU limit changes what a
  timing bar measures, so the smallest input separating a naive solution from a
  canonical is a fact about the runner that found it.
- **Comparison stays outside the runner.** A runner is handed code, the
  arguments and a cap, and returns what each call produced. The runner is
  never told what a case expects, so the rule deciding a case cannot vary by
  where the code ran.
- **A case yielding no value is read by the solution's role.** A canonical that
  crashed or timed out discards the problem, since nothing establishes what the
  case returns. A reference that crashed or timed out is the ordinary path
  beyond its reach, and the case takes the canonical's answer, with
  `expected_from` naming the canonical.
- **A reference that computed no case discards the problem.** Every expected
  output would then be the canonical's own, and `verified` would mean only that
  the solution agrees with itself. Some cases beyond the reference's reach is
  the ordinary path. All of them beyond it is no independent reading at all.
- **The stored cap is the child's**, since that is the number the case was
  judged by. The parent runs a slack timer of its own, which the runner owns.
- **A child reporting nothing is read from how it died.** The parent's timer
  firing is `TIMEOUT`. A signal is `CRASHED`, and a segfault and a kill under
  memory pressure both land there. Anything else is the runner's own fault and
  is raised, since it says nothing about the solution.
- **A case result carries what the child measured.** The separating input a
  speedup search looks for is found from those numbers, and a result holding
  only the outcome would make every later search re-run the whole set.
