# Privacy policy

Last updated: 15 September 2026

algo-coach is an app for practising algorithmic problem solving, and access is
by invitation. This page says what the app stores about you, why it stores it,
and who can read it.

algo-coach is run by Maksim Lunochkin. Write to
[maksim@lunochkin.com](mailto:maksim@lunochkin.com) with any request about this
policy.

## Signing in

You sign in through Google or GitHub, and algo-coach never sees a password.

- The app asks the provider for your account's id and your verified email
  address, and nothing else.
- The app stores that id, that email, and when you first signed in. It stores
  no name and no profile picture.
- Your email is checked against the list of invited emails. A sign-in whose
  email has no invitation is refused before anything about it is stored.

## Your session

- While you sign in, a cookie carries the sign-in's own checks between the
  app and the provider. It expires after 10 minutes.
- Signing in then sets a cookie holding a random token. The page's scripts
  cannot read either cookie.
- The database holds a hash of the token rather than the token, with when the
  session began and when it expires.
- A session lasts 30 days. Signing out ends the session on the server and
  clears the cookie.
- The app runs no analytics and no advertising, and loads nothing from another
  site.

## Your practice

The app stores what you do in it, so that it can show your progress:

- each sitting: the problem, when the sitting started and ended, and every
  pause;
- each submission: your code, how long it took, and how it did on each of the
  problem's test cases;
- your answers after a submission: which techniques you used, and why the
  submission went the way it did.

This record is private to you, and no other user can see it. Maksim Lunochkin
can read it through the database.

## Language models

Your submitted code may be sent to a language model, to name the techniques it
used. The request goes through OpenRouter, which passes it to the company
serving that model. The request and the answer are stored with your record.

OpenRouter is based in the United States, and so are most of the companies
serving the models. Your code can therefore be processed outside the European
Union. OpenRouter covers such transfers by the European Commission's adequacy
decisions and its standard contractual clauses (GDPR Art. 45 and 46).

## Why the app uses your data

- Your email, your sign-in and your practice record are used to provide the
  app you signed in to: letting you in, and showing your progress. The legal
  basis is the performance of that service for you (GDPR Art. 6(1)(b)).
- Sending your code to a language model serves the operator's legitimate
  interest in naming the techniques you used, so that your progress is shown
  per technique (GDPR Art. 6(1)(f)). You can object to it by writing to the
  address above, and your code is then not sent.

## Where it is stored

Everything above is stored in one database, on a server rented from a hosting
provider in the European Union. Backups of the database are kept away from that
server for 30 days.

## Your rights

Write to the address above to ask for any of these:

- a copy of your whole record, as JSON;
- correction of what the app stores about you;
- erasure of your whole record, which cannot be undone;
- a restriction of how your data is used, or an objection to a use.

Erasure removes your record from the database at once, and from the backups
once they expire, within 30 days. Your email and your sign-in are kept, so you
can still sign in, and a new record starts.

You can also complain to the data protection authority of the country where you
live.

## Changes

This page changes when what the app stores changes, and the date at the top
says when it last changed.
