# Machine records

What a record written by a model carries, and the call log underneath it.
Part of the architecture; `README.md` is the map.

## Machine records

Claims, template matches, technique readings, canonical solutions and the
arguments of a test case are written by a model. What each carries to stay
comparable is the same, and is stated here once.

- **Provenance is the configuration**: model, effort, the endpoint it was
  pinned to, temperature, the digest of what that record was sent, and the call
  that sent it. All of them or none, since a record whose configuration is
  partly unknown compares with nothing. A model asked for no effort, or one
  that rejects the parameter, records the level it ran at rather than an empty
  field.
- **A configuration is per call site, not per run.** Writing a problem takes
  five calls, and they ask for different things: a statement and a solution, an
  independent reading of that statement, the inputs that catch a wrong
  solution, code that builds an input of a given size, and the slowest correct
  solution a timing bar measures against. One configuration over all five makes
  the cheapest of them pay the price of the hardest.
- **A run mixing models stays readable, because each record copies its own
  call's configuration.** The problem names the call that wrote it, its
  reference names the call written blind, and a case won by a round names the
  call that proposed it. Nothing reads a run-wide configuration, so there is
  none to be wrong.
- **A pin is part of the reading, not a note about routing.** A model id
  resolves to as many builds as there are endpoints serving it, and
  quantization changes the weights. Unpinned, the router chooses per request,
  so the records under one key are a mixture no later run can separate.
- **Who served it is recorded and never compared.** The router reports a
  company rather than an endpoint, and one company serves several builds. It
  confirms a pin held without identifying the build, and it is unknown when a
  reader asks what it has already read.
- **A reading is greedy, and says so.** Sampling turns a verdict the model
  holds at 0.9 into one it gives four times in five. An eval absorbs that by
  being repeated; a sweep writes into an append-only log the board reads
  forever. Temperature identifies a record for the same reason the pin does:
  one says which weights answered, the other how they were sampled. A
  temperature nobody set is the provider's own default — recorded absent, and
  equal only to itself, which keeps records taken before the parameter existed
  scorable rather than discarded.
- **The generator and the naive site are sampled**, for the reason `corpus.md`
  gives: each produces an artifact rather than a verdict about one. The
  generator's variance buys diversity across a corpus of statements, and the
  naive site's buys a second draw where the first one wrote the form.
- **The other three are greedy**, which is what makes two configurations of one
  site comparable over the same item. They answer about a statement that
  already exists, and each answer decides something.
- **Whether a site can be greedy is the endpoint's answer.** A request naming
  a parameter its endpoint does not advertise is refused rather than served, so
  a temperature sent where none is offered fails the call instead of running
  greedy. Some endpoints serving a model at an effort advertise no temperature
  and others carry both, so pinning a site to `0` costs the effort in one place
  and nothing in another.
- **What a reading cost is recorded and never compared.** A price says when a
  reading was taken rather than which reader took it, so two readings compare
  whether or not either carries one. It sits outside the all-or-none rule with
  the temperature: a reading stored before the field existed carries none, and
  so does one a provider priced at nothing.
- **Staleness keys on the digest of what was sent**, never on a version over
  the rulebook. A criterion travels with its candidate, so editing one entry
  re-derives what that entry reached and leaves the rest. An author can forget
  to bump a version while the text moves; a digest cannot. It costs a reflowed
  sentence re-deriving what it reaches, and a rulebook that is cited as a
  digest rather than as "prompt 3".
- **The record's own copy of the configuration cannot drift**, because a call
  is append-only and the copy is made in the same write. It is there so the log
  reads alone: loading the calls to learn which model produced a record would
  put a megabyte-scale read on every command.
- **The precedence is a reader, not a write path.** Preferring the user's
  record on read makes overwriting the evidence unrepresentable, where a write
  path that skips what the user answered depends on every writer remembering
  to.
- **Each configuration is scored over what it read**, and the denominator is
  printed rather than assumed. Scoring over the intersection alone charges
  every column for the records one of them failed on. A share prints as
  `92/98`, so two columns over different samples cannot be read as one rate.
  The reader still supplies the judgement that the harder sample reads as the
  worse reader.

## Site outcomes

What one generation call site left on one attempt at writing a problem. A
model wrote no part of it. It records what the run's gates said about the answer
a call returned, which is why it sits beside the call log.

- **What a site left is stored rather than only printed.** A run's stage lines
  end with the process. The gate that rejected an answer, the configuration
  behind it and the digest it was sent are readable nowhere else.
- **One record per site and per attempt.** The five sites can run at five
  configurations, and one record over the attempt could not say which of them a
  gate rejected.
- **A kill is filed under the site whose output did it**, as a gate is filed
  under the site whose answer made it decidable. The mutants the statement's own
  cases caught are the generator's, the ones built inputs caught are the inputs
  site's, and a round's are the discrimination site's.
- **That attribution is what makes the split complete.** Each site's record
  exists exactly where its own count can be other than zero: the generator
  always answered, the fuzz pass ran only where a generator was written, and a
  round killed only where one was asked. Held on the discrimination record
  alone, the three sources would go unrecorded on every attempt the fuzz pass
  finished — which is the attempt that says a round was not needed.
- **The mutants a canonical yielded sit on the site that wrote it.** The count
  is a fact about that solution, so it is readable on an attempt no round
  reached, and two generator configurations compare on it.
- **A gate is filed under the site whose answer made it decidable.** A canonical
  contradicting the cases its own call declared is the generator's. A
  disagreement is the blind site's, since nothing disagrees before a second
  reading of the statement exists.
- **The search's verdict is filed under every site it judged.** It times the
  clock against the canonical on an input the builder made, so neither answer
  alone makes it decidable. A resume that re-asked one of the two writes that
  record and no other, and the size would otherwise be lost with the site it
  reused.
- **The builder's bound is on the record, not only on the draft.** A landed
  problem clears its draft, so the largest input the statement admits is
  readable nowhere else. A separating size read without it says nothing about
  how far the search had left to look.
- **Two of a problem's records can carry different verdicts.** The builder's
  answers for the search that judged it when it was written, and a later
  clock's for the search that judged the redraw. Each says what one answer was
  worth at one configuration, which is what a record is for.
- **The exception is the gate no answer was rejected by.** A held draft is
  rejected where the problem does not exercise the form its template claims,
  and every site answered. It is read from the draft, which is the record that
  outlives the run.
- **The attempt carries an id the run mints.** A discarded draft has no problem
  to key to, and it is the attempt whose cost nothing else records.
- **The problem is named where one landed.** Its id exists only once the problem
  is stored, so the records are written at that point rather than as each site
  answers.
- **A site that made no call writes no record.** Provenance is all or none, and
  a record carrying none compares with nothing. Absence on a site means it was
  never asked, which is where the first case set already killed every mutant.
- **The discrimination record cites the last round's call.** A loop pays for up
  to two rounds, and the counters the record carries are what the last one left.
- **A round records what it proposed beside what landed.** A proposal that
  killed nothing is not stored, so the set alone cannot say what the call was
  paid for. The difference is what the round bought nothing with.
- **What each round killed is a list, in order.** A field per round would fix
  the bound in the schema, where `ROUNDS` is what a corpus revises. It is the
  one ordered counter, and a report reads position rather than a key.
- **The records are written at one point, once the loop has run.** A site
  answers before its counters are known, so writing as each answers would need
  a record amended later. What this costs is holding the first case set's
  verdict, since a gate raised after it belongs to another site.
- **The verdicts are named fields rather than a mapping.** A report groups by
  gate and averages the counters, and a mapping makes every key a field nothing
  enforces.
- **A site skips an item it has answered at the current digest**, as the
  classifier skips a claim. So a second configuration is paid for only where it
  has not read, and the run that wrote the problem answers for the bench it was
  written with.
- **The item is the problem, and the generator has none.** It writes a problem
  rather than answering one, and asking it again is a new problem by design.
  The other three sites are re-asked about a statement the store already
  holds.

## Calls

One request to a model and what came back. A layer below the claims. A claim
cites a call and reads its own meaning into the response, and the call record
holds nothing about what the answer was for.

- **Domain-free on purpose.** No attempt, no techniques, no vocabulary — only
  what was asked, of whom, and what returned. That is what lets a second domain
  reuse the log without being taught anything, and what keeps the run loop's
  decisions in the domain where they belong.
- **The prompt is stored whole, beside its digest.** The record therefore
  digests to its own key, and a renderer that changes later cannot make an old
  one unreadable. It is inline rather than deduplicated into a store of its
  own: one append cannot half-succeed, where a file plus a log line can leave a
  call naming a prompt that is not there.
- **It holds what a claim structurally cannot**: the tokens a run cost, the
  reasoning behind a verdict, and the calls that produced no claim at all. A
  decline names no candidate and a failure names nothing, so neither reaches a
  claim at all. Without this record both are counters that print once.
- **One transport, one shape.** Every model is reached as chat completions
  through a router, so adding a model is a string and adding a provider is a
  base URL. Two provider shapes maintained by hand would create pressure to
  adopt a library that reconciles them, and such a library can downgrade a
  schema into a prompt where the record cannot show it happened.
- **Every request names one endpoint.** A provider that cannot honour the
  response schema is never chosen, and a request fails rather than falling back
  to a backend the record would not name.
- **Reasoning is what the reading produced, not what was asked for.** A model
  that decides a question needs no thought returns none, and the empty field is
  a fact about the reading rather than a gap in the record.
- **A call is timed at two levels**: what the caller waited and how many
  requests that took, beside what the last request took alone. Their difference
  is the endpoint's backoff, and without it a run held behind a per-minute cap
  reads as a slow model.
- **A rate cap and a gateway failure are absorbed here, never reported
  upward.** Both are facts about the endpoint rather than about the
  configuration, and a run's abort exists to catch a broken configuration. The
  waits cover a minute between them, since that is the window a per-minute cap
  is stated in. The endpoint's own reset time is not read: where it is carried
  varies by provider, and a wrong parse would sleep for hours.
- **A 404 naming no endpoints is asked once more, at the shortest wait.** The
  router's list of endpoints serving a model moves under a pinned request, so
  the answer is state rather than a rejected request. What the retry decides is
  whether the list moved, not whether a cap window passed.
- **A model id that does not exist answers the same way**, and pays one extra
  request before it fails. Nothing in the message separates it from a list that
  moved, and one request is cheaper than a wrong pin failing a whole backlog.
- **Every other failure is raised on the first request.** A rejected schema and
  an unset key are answered the same way twice, so retrying them spends the
  abort count slowly instead of at once.
- **Nothing on the run path reads it back.** Whether to ask again is decided
  from the claims, which carry the configuration already. The file is written
  by every run and loaded only to analyse one.

