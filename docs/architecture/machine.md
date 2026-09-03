# Machine records

What a record written by a model carries, and the call log underneath it.
Part of the architecture; `README.md` is the map.

## Machine records

Claims, template matches, technique readings and canonical solutions are
written by a model. What each carries to stay comparable is the same, and is
stated here once.

- **Provenance is the configuration**: model, effort, the endpoint it was
  pinned to, temperature, the digest of what that record was sent, and the call
  that sent it. All of them or none, since a record whose configuration is
  partly unknown compares with nothing. A model asked for no effort, or one
  that rejects the parameter, records the level it ran at rather than an empty
  field.
- **A configuration is per call site, not per run.** Writing a problem takes
  four calls, and they ask for different things: a statement and a solution, an
  independent reading of that statement, the inputs that catch a wrong
  solution, and code that builds an input of a given size. One configuration
  over all four makes the cheapest of them pay the price of the hardest.
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
  scorable rather than discarded. Generation is the exception, and
  `corpus.md` gives the reason.
- **The generator alone is sampled**, where the exception is stated over
  generation as a whole. What sampling buys is diversity across a corpus of
  statements, and the other three sites write against a statement that already
  exists. They are greedy, which is what makes two configurations of one site
  comparable over the same item.
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
- **The user's record stands over the machine's answer to the same question**,
  whichever was written later. The machine's is stored and scored, never
  promoted. A reader that prefers the user's makes overwriting the evidence
  unrepresentable, where a write path that skips what the user answered depends
  on every writer remembering to.
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
- **One record per site and per attempt.** The four sites can run at four
  configurations, and one record over the attempt could not say which of them a
  gate rejected.
- **A gate is filed under the site whose answer made it decidable.** A canonical
  contradicting the cases its own call declared is the generator's. A
  disagreement is the blind site's, since nothing disagrees before a second
  reading of the statement exists.
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
- **The verdicts are named fields rather than a mapping.** A report groups by
  gate and averages the counters, and a mapping makes every key a field nothing
  enforces.

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
- **Every request names one endpoint, and records who answered.** A provider
  that cannot honour the response schema is never chosen, and a request fails
  rather than falling back to a backend the record would not name. The pin says
  which build was asked for and is what a re-run needs; the server says whether
  anything answered at all. What it was sampled at is recorded beside them, and
  a claim's copy is taken from here.
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
- **Every other failure is raised on the first request.** A rejected schema, an
  unset key and a model that does not exist are answered the same way twice, so
  retrying them spends the abort count slowly instead of at once.
- **Nothing on the run path reads it back.** Whether to ask again is decided
  from the claims, which carry the configuration already. The file is written
  by every run and loaded only to analyse one.

