# Roadmap

Each phase ships one capability and a write-up. Ship thin.

A phase exits on one act a reader can check: a pass through the flow the phase
ships, for a phase the user runs, or the next phase using the capability, for
one that builds a capability. A phase can also close as superseded: it was
built, and something later answered it, so its exit no longer applies.

`docs/architecture/` owns the concepts, boundaries, and invariants.
This file owns only sequencing. On any difference, the architecture wins.

A phase section is short: what ships, what it exits on, and for a closed one
what it measured. Reasons are in `docs/architecture/` and in the commits, and
are not repeated here. `docs/TODO.md` drops a phase when it closes.

## Phase 1 — Push API, techniques, drill board — done

- Push API: `Problem` and `Attempt` ingested per record from the practice
  client.
- Techniques: the product-owned vocabulary, shipped as code.
- Drill board: per-technique progress derived from the log.

Measured:

- 485 problems in the backlog: 61 reached no technique, 183 one, 241 two or
  more. That share made a classifier worth building.
- 1785 attempts over 117 practice days, 159 of them in the last 30.
- The board renders 25 technique rows, and 101 attempts reach none.

## Phase 2 — Drill loop on a pushed problem — superseded

Board, then a technique, then a problem, solved on the platform. Superseded by
Phase 8: a loop that waits on a push can verify no submission and time no
sitting. The claim and self-label prompt survives unchanged.

## Phase 3 — Technique attribution — done

- User claims over the backlog: the eval set, adjudicated against a frontier
  model.
- A classifier constrained to the problem's own candidates, scored per
  technique by set equality.
- The call log beneath it: one transport, one record per request.
- Provenance settled: model, effort, pin, temperature, prompt hash.

Measured:

- Twelve configurations over a 10x price range scored within two attempts of
  each other and failed in the same cells. Changing the model was never the fix.
- A configuration against itself, three `--fresh` passes: 1 of 31 attempts
  flips for opus, 3 for haiku and sonnet. 0.5-2.2% of decisions, and the
  ceiling any score is read against.
- Set equality compounds a per-candidate error: 95% of calls reads as 87% over
  three candidates.
- Keying reuse on the prompt hash rather than on a version: editing one
  criteria entry re-derived 7 of 31 attempts.
- 100 attempts claimed blind, carrying 138 claims, so 38 revisions. 62 of them
  were read by a frontier configuration to adjudicate the set.
- Requiring `effort` and `prompt_hash` deleted the 25 machine claims already
  written, rather than re-deriving them.

## Phase 4 — Cards and template matching — done

- Card content as product data, authored by a skill into `content/` and seeded
  into the store.
- Template matches: one record per template and problem, negatives included.
- The matcher and its hand pass.

Measured:

- Nine cards ported, each authored blind and then compared against the
  hand-written one. The diffs became the skill's rules.
- `statement` tightened to required and non-blank at 485 of 485, and held at
  ~4k problems across an eight-fold push.

## Phase 5 — Pivot to generated problems — done

One origin end to end. The ingest path removed before generation was written.

- The architecture doc first, then the code it settled.
- The push command, payloads, external-id resolution, tag mapping and
  push-driven drill loop deleted.
- The pushed corpus moved to `data/old/` as a calibration corpus: 1785
  attempts and 3962 problems, with the claims and the call log.
- The live store emptied, then `origin`, `source_status`, `external_id` and
  the platform fields removed.
- The eval set did not survive: 138 user claims key to pushed attempts.

## Phase 6 — Problem generation — done

The engine writes problems: a statement, the test cases that decide it, a
canonical solution and a reference solution. Everything that makes a generated
problem sound.

- Five call sites, each at its own configuration: the generator, the blind
  reference, the input generator, the naive solution, the discrimination round.
- A blind reference settles every expected value, and a disagreement rejects
  the draft.
- Mutants of the canonical, killed by the statement's cases, then by built
  inputs, then by at most two rounds of proposed cases. A proposal lands only
  where it killed.
- A separating case where the template claims a speedup: the smallest input
  the naive solution exceeds the drill cap on, under a 64 KiB case ceiling.
- The statement ends on its `solve` signature, checked against the canonical.
- Site outcomes: what each site's gates said, per attempt, beside the call log.
- Drafts as states, held where a step failed, resumed by `generate --resume`,
  listed by `--drafts`.
- A template match keyed to a solution. The generating canonical asserts its
  own pair.
- Solution claims over canonicals, and problem techniques derived from them
  wherever a command loads problems.
- The gap report, and `generate --gaps` aimed at what it lists.
- Exit: every landed problem carries techniques derived from its canonicals
  and a case set measured against the mutation bound, and the gap report names
  the templates the next run is aimed at.

Measured:

- One problem: Opus 5 at high $0.41 over 6 calls and 190 s of model time, 70 s
  of it the round. Gemini 3.7 Flash at medium $0.031 over 4 calls and 28 s.
  Reasoning is the output: 5,263 of the round's 5,573 tokens. Ten attempts on
  one template cost $0.47 to $0.55 over 36 to 49 calls, $0.095 per landed
  problem.
- Mutants: 53 and 22 on the first two canonicals, 46 and 17 killed by the
  statement's own cases. Round one killed nothing on either, and the survivors
  were equivalent by inspection. `ROUNDS` stays at two. Later landings killed
  4 of 4, 7 of 7 and 11 of 13, the round proposing nothing.
- The runner spent 76.3 s on 22 mutants, 70 s of it seven timeout kills at the
  generation cap. Process start is not the cost, so no fork server.
- Ten attempts on `answer-space`: 5 landed, 4 rejected as `misdeclared`, 1 held.
  Two rejections checked by hand had the canonical right and the declared value
  wrong, so the gate became a count. Re-run: 8 landed, 1 `untested` on an
  argument order the prose left open, 1 held on `input_too_large`.
- Separating sizes: the first two searches gave `input_too_large`, because the
  blind reference had written the form. The naive solution is its own site for
  that reason. Five then separated at 1, 2, 6, 13 and 21 against a legal 100000,
  the naive solution prompted too slow. Fifteen over the corpus: eight at one or
  two where the naive solution scans the values, six at 13 to 27 where it is
  exponential, four over the ceiling. The input generator's bound is not a
  denominator.
- Of ten statements on one template, 1 reused a domain the trigger names and 2
  asked a question a listed statement already asked, both with the twin in the
  list. Held drafts are not listed.
- 28 canonicals read at two cents, none undecided. Every problem derives
  `binary-search`: 12 that alone, 7 one code more, 5 two more.
- `generate --gaps --count 1` aimed at 35 of 37 core templates. Seven reached
  before a stop by hand: 4 landed, 2 held on `input_too_large`, 1 cut.
  `--count` is per template.

## Phase 7 — Finishing the sweep — done

The corpus the drill loop needs, before the loop. Split from Phase 6 on
2026-09-02. The matcher measurement moved behind the beta on 2026-09-09, since
the loop needs problems and not a score.

- `generate --gaps` reports no gap: 74 problems over 9 cards, and every core
  template but the framing procedure carries a solution. 760 cases, 10.3 to a
  problem.
- 19 drafts were rejected and none is held: 10 `misdeclared`, 5 `unexercised`
  by hand, 3 `disagreed`, 1 `untested`.
- The case ceiling went from 64 KiB to 1 MiB over two raises, each paid for by
  a naive solution that crossed the cap between the two sizes.
- 57 separating sizes recorded, from 1 to 30,232. Twelve at 1, where the values
  the input carries drive the naive solution's cost. 31 under 100, where the
  naive solution is exponential. 18 over 1,000, where it is quadratic.
- A sublinear form separates by repeating one case's call: rotated-array at
  94,839 elements over 2,000 calls, count-based-kth at 43,690 over 8,000. The
  canonical has to finish within a tenth of the cap at that point.
- Four prompt faults were found by the holds and fixed: random inputs the naive
  solution is fast on, a statement whose constraints leave the search no room,
  a naive solution reaching the technique through a form no template names, and
  a return value no two solutions compare equal on.
- Exit met: every held draft landed or was rejected.

## Phase 8 — The engine serves — done

The first attempts the engine produces itself. It serves a generated problem,
times the sitting, runs the submission against the problem's own cases, and
records the verdict. The interface is a web app served locally: Phase 9 hosts
the same pages for invited users, so a terminal interface here would be written
twice.

- A JSON API under `/api` as the second adapter beside the CLI, and a React
  frontend built to static files on the API's origin: the board, the cards, a
  technique's candidates, and the sitting's page with its editor, verdict,
  clock and claim.
- A sitting is stored and kept after it ends, its pauses as intervals, and an
  attempt carries the sitting's elapsed time with every pause excluded.
- An attempt's verification is its own record. A failing submission shows its
  first failing case whole, and a crashed case carries what raised it.
- A defective problem is retired by hand in the terminal, and the board stops
  counting that problem's attempts in either direction.
- The claim is asked of each attempt when the sitting ends. The self-label
  waits for the failure-mode block, which settles `speed`, `rust` and `gap`
  before anything writes a label under them.
- 26 of the 74 problems the sweep landed carried no `def solve(...)` line,
  written before a statement had to end on one, and were retired `defective`.
  The board offers 14 techniques on the 48 left.
- Exit met: sittings completed by hand from the board to the claim, over three
  attempts: a wrong answer, a timeout on a separating case, and a pass, each
  claimed and one declined.

## Phase 9 — The engine hosted — done

The same loop, for people who are not the author. The stores moved to Postgres,
each person signs in to a log of their own, and their code runs in a sandbox.

- Storage is one Postgres database behind the store interfaces the domain
  already called, a column per field, with the append-only rule held by
  triggers.
- Sign-in is through Google and GitHub, and a session lives in Postgres for 30
  days as a hashed token. Access is by invitation, checked at the callback
  before any record is stored.
- One user's log is exported and erased whole, and the dev login answers a
  loopback request alone.
- The pages and the API are deployed on one origin behind Caddy, from an image
  carrying the compose file it deploys with, on a push to main. Postgres
  listens on the server's loopback, and a command run off the server reaches it
  through an SSH tunnel.
- A submission runs in a container under gVisor: no network, a read-only root,
  a non-root user, dropped capabilities, and limits on memory, processes and
  output. The image is pinned by digest.
- The broker holds the container runtime's socket, admits one run at a time,
  refuses a wait past a bound, kills a run past its deadline by name, and
  removes what a dead broker left. The API holds no socket and reaches the
  broker on a network only the two join.
- `runner.run` calls the broker where `ALGO_COACH_BROKER` names one, and the
  local subprocess everywhere else. The comparison against `expected` stays
  above that boundary.
- A user's submissions are capped at ten a minute. A sitting nothing has
  touched for 45 minutes ends at its last activity, where it is next read.
- A privacy policy page opens without a session, which Google's consent screen
  asks for.
- Measured: the 50 served problems' canonicals ran through the broker under
  gVisor at the drill cap, over all 506 of their cases, and none took over a
  tenth of the cap. The separating sizes found on the local subprocess stand
  under the clock a verdict is now read from.
- Measured: gVisor holds a case's own address-space limit, where the
  container's memory limit alone has the host kill the container. A container
  process limit of 64 ended the sandbox itself, since gVisor backs each process
  a case starts with a host process of its own. `/tmp` is writable inside the
  container whatever the root filesystem allows.
- The corpus moved to the hosted store as product data: 76 problems, 779 cases,
  223 solutions, 9 cards, and the 574 calls those records name. No log record
  was copied.
- Left to the deployment repo, and open there: the scheduled backup with a
  restore tried, the rebuild rehearsal, and the retention statement the privacy
  policy already promises.
- Exit met: a sitting on the deployed engine, signed in through a provider,
  from the board to the claim. Its attempt was judged under
  `container/cpython-3.14` at the drill cap. The self-label the loop is
  specified to ask for is unbuilt, and the failure-mode block settles its
  failure modes.

## Phase 10 — The pages designed — done

The pages given one design, before Phase 11 adds its own.

- A design system in the theme: a type scale named by the role a page reads a
  size in, the spacing steps, the layout widths, one mono family, a token per
  verdict outcome, and the editor's five syntax colours.
- The dark set applies from the browser's colour-scheme preference, and no
  switch stores one.
- `/gallery`, built in development alone, shows every token and every component
  the pages read.
- `pages.md` and `wireframes.md`: the two sections, the pages under each, a
  page's areas, the design system, and thirteen views drawn at low fidelity.
- One shell: the navigation naming Practice and Cards, and one header carrying
  the way back, the title and the line identifying what the title names.
- Every page rebuilt on it: the board, a technique's candidates, the picked
  problem, the cards, one card, the sitting, the login, the policy and the
  missing page.
- Loading, the failure with its retry, and the blank answer render through one
  component.
- The picked problem moved to `/problems/:problem_id`, served by a route of its
  own, so a rung of a ladder reaches the same page.
- A refused sign-in returns to the login page as a code, which names no address.
- A hidden page pauses the sitting, and the page returning resumes the pause
  hiding started.
- Exit met: every existing page is built on the design system.

Measured:

- Every verdict and code colour clears a contrast of 4.5 against its own
  background: 4.55 to 6.99 in the light scheme, 6.12 to 11.15 in the dark one.
  Two light values were under the bar as first chosen, and were darkened.
- The gallery leaves the production bundle. The build folds the guard on the
  route, and `dist/` names neither the page nor its examples.

Left open:

- No page was read by eye. The browser extension was not connected and the
  frontend carries no test framework, so every page stands on the typecheck,
  the lint and the build alone.

## Phase 11 — Ladder, recall and card runs — done

The pieces a card needs once there are problems to fill it.

- The three flows written and drawn first: starting a card run, solving a rung,
  and recalling a template, each a sequence with a low-fidelity wireframe.
- A template carries the cases a reproduction of its form is checked against,
  and `unordered` says its answer is a set, compared with its top level sorted.
- The ladder resolved from the template matches, one rung per core template and
  the selector filling out to `size`. A rung's requiredness is derived from what
  it covers, and a core template nothing displays is reported as a gap.
- Ladder progress is a fold over the attempts made since the run began, so a
  re-derived ladder keeps what was solved and a retired problem leaves it.
- `CardRun` and `RecallAttempt`, both append-only, with the probes and the case
  results as child rows and the erasure reaching all four tables.
- Starting a card mints the run and draws its probes in one act: the technique's
  problems, unseen first, then least recently attempted, never a rung.
- A recall runs the typed file through the runner a submission uses, at the same
  cap and under the same per-minute bound.
- The trainer withholds the title and the form. The API sends the trigger and
  the signature alone, and each hint is its own request.
- The card page on its two wireframes, the trainer, `?card=` on a problem, and
  the sitting returning to the card it came from.
- Exit met: a card run gone through by hand, from the start to a rung solved, a
  template recalled cold, and a probe offered.

## Phase 12 — The matcher, measured (current)

The worth of a generated corpus, measured.

- The hand pass, which writes the matcher's reference and is the only reading
  of a generated problem no model produced.
- User matches over pairs of a template and a solution, from the templates
  alone.
- The matcher scored per pair and grouped per template, positive verdicts in
  both directions.
- A configuration pinned before any number is quoted.
- Exit: the matcher carries a per-template score in both directions.

## Phase 13 — Mastery and scheduling

Per-technique skill state derived from the log, and a scheduler that picks what
the user practises next.

- Mastery per technique, derived from attempts, their claims and their
  verdicts, and never stored.
- A scheduler picking the next sitting from that state. The board still offers
  every technique beside the pick.
- Exit: a sitting started from the scheduler's pick on the board, and
  completed to the claim.

## Further developments

Blocks of work not ready for a phase, unnumbered and unordered. A block becomes
a planned phase once it is clear enough to plan, and `docs/TODO.md` holds the
items of each block, the smaller ones included.

- **Failure mode.** Why an attempt failed: the self-label written once `speed`,
  `rust` and `gap` are settled, a diagnosis call narrowed to what the record
  supports, and a scheduler that targets the diagnosed cause.
- **Alternative solutions.** Every other way to solve a stored problem,
  enumerated over the corpus, each approach its own canonical judged by the
  problem's cases.
- **The corpus gated.** Whether a generated statement gives its form away,
  measured against the rate over `data/old/`, the corpus no generator wrote.
- **Program-analysis-grounded diagnosis.** A diagnosis grounded in AST diffs
  against the canonicals, execution traces and measured complexity.
- **Retrieval.** Similar problems, patterns and briefs retrieved from the corpus
  and the user's own attempts.
- **MCP and autonomy.** The corpus and tools exposed as an MCP server, and a
  scheduled agent running the practice loop.
- **Multi-agent**, only once a real pipeline needs one.
- **Soundness-checked synthesis.** Generation upgraded with formal constraint
  specs, property-based cases and adversarial validation.
