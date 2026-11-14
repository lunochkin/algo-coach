// the privacy policy, one text both clients render: the web at `/privacy`,
// which the providers' consent screens name, and the phone's Privacy screen
const POLICY = `# Privacy policy

Last updated: 11 November 2026

Climbance is an app for practising algorithmic problem solving, used in a
browser and as an app on your phone, and access is by invitation. This page
says what Climbance stores about you, why it stores it, and who can read it.

Climbance is run by Maksim Lunochkin. Write to
[maksim@lunochkin.com](mailto:maksim@lunochkin.com) with any request about this
policy.

## Signing in

You sign in through Google or GitHub, and Climbance never sees a password.

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
- The database also holds when the session was last used and which browser
  opened it, as the browser names itself. That name tells two of your
  browsers apart in the list of signed-in devices.
- A session lasts 30 days. Signing out ends the session on the server and
  clears the cookie.

The phone app signs in through the same provider, in a browser sheet, and
receives a random token in place of a cookie.

- The phone keeps the token in its secure storage: the Keystore on Android,
  the Keychain on iOS.
- The database holds a hash of the token rather than the token, with the name
  you gave the device, when it signed in and when it was last used.
- A token lapses after 90 days unused, and each use extends it. Signing out in
  the app ends it on the server.

The list of signed-in devices names every browser and phone signed in to your
account, and ends any one of them.
- The app runs no analytics and no advertising, and loads nothing from another
  site.

## Your practice

The app stores what you do in it, so that it can show your progress:

- each sitting: the problem, when the sitting started and ended, and every
  pause;
- each submission: your code, how long it took, and how it did on each of the
  problem's test cases;
- your answers after a submission: which techniques you used, and why the
  submission went the way it did;
- each card you start studying, when you started, and the problems drawn for
  it;
- each form you write from memory: your code, how it did on the form's test
  cases, and which hints you took;
- each answer to a knowledge question, each round of questions, and your
  study choices: the focus, each module's status and order, the lessons you
  marked read, certification exams, your daily limit and its raises, and the
  exam size. Each of these names the device it was made on.

This record is private to you, and no other user can see it. Maksim Lunochkin
can read it through the database.

## On your device

- The browser and the phone each keep a copy of the knowledge questions and of
  your record, so questions work without a connection. A record not yet sent
  waits in that copy and is sent at the next connection.
- Signing out sends what waits, then deletes the copy. Where something cannot
  be sent, the app names it and asks before deleting it.
- The browser also keeps the code you typed and did not submit, your choice of
  starting the clock by itself, and the colour scheme. These stay in that
  browser and are never sent.
- The phone can remind you when questions are due for review, at an hour you
  choose. The phone schedules the reminder itself, and it says only how many
  reviews are due. The phone asks for permission before the first one.

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

Everything above that is not kept on your device is stored in one database, on
a server rented from a hosting provider in the European Union. Backups of the database are kept away from that
server for 30 days.

## Your rights

Write to the address above to ask for any of these:

- a copy of your whole record, as JSON;
- correction of what the app stores about you;
- erasure of your whole record, which cannot be undone;
- a restriction of how your data is used, or an objection to a use.

Erasure removes your record from the database at once, and from the backups
once they expire, within 30 days. Your email, your sign-in and your signed-in
devices are kept, so you can still sign in, and a new record starts. A copy on
a device is deleted when that device signs out.

You can also complain to the data protection authority of the country where you
live.

## Changes

This page changes when what the app stores changes, and the date at the top
says when it last changed.
`;

export interface PrivacyPolicy {
  title: string;
  updated: string | null;
  // the prose, with the title and the date taken off: both read in the header
  body: string;
}

export function privacyPolicy(text: string = POLICY): PrivacyPolicy {
  return {
    title: /^#\s+(.+)$/m.exec(text)?.[1] ?? 'Privacy policy',
    updated: /^Last updated:\s*(.+)$/m.exec(text)?.[1] ?? null,
    body: text
      .replace(/^#\s+.+$/m, '')
      .replace(/^Last updated:.*$/m, '')
      .trimStart(),
  };
}

export const privacyUpdated = (updated: string) => `Last updated ${updated}`;
