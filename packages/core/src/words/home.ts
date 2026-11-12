// what the knowledge screens say about the home, for every platform: a
// platform changes the look alone, and reads each sentence from here
import { NEW_STEP } from '../queue';
import type { Stat } from '../practice';
import { SETTING_RANGE, type SettingName } from '../settings';

// the platform a device names itself by, where a sentence says "this browser"
export type ThisDevice = 'browser' | 'phone';

// the home
export const MODULES_OF = 'the modules';
export const NO_MODULES = 'No module is seeded yet.';
export const LESSONS_LINK = 'Lessons';
export const CERTIFICATIONS_LINK = 'Certifications';
export const CONTINUE = 'Continue';
export const EXAM_LINK = 'Exam';
export const PAUSED = 'paused';
export const MODULES_HEADING = 'Modules';

export const waitingOutside = (n: number) => `${n} waiting outside`;

/** A module row's counts: what it owes now, then how much it holds. */
export const moduleStats = (due: number, total: number): Stat[] => [
  { value: due, label: 'due' },
  { value: total, label: total === 1 ? 'question' : 'questions' },
];

// the focus panel
export const FOCUS_PREFIX = 'Focus:';
export const focusTitle = (label: string) => `${FOCUS_PREFIX} ${label}`;
export const STRICT = 'Strict';
export const strictLabel = (strict: boolean) =>
  strict ? 'Strict: reviews from the focus alone' : 'Relaxed: reviews from everywhere';
export const CLEAR_FOCUS = 'Clear';
// clearing asks first, since aiming a focus takes several presses on a module's page
export const clearFocusTitle = (label: string) => `Clear the focus on ${label}?`;
export const CLEAR_FOCUS_BODY =
  'Continue then serves every active module again. A focus is aimed again from a module\'s page or a certification.';
export const CLEAR_FOCUS_KEEP = 'Keep it';
export const DUE_NOW = 'to review now';
export const LEARNING = 'learning';
export const NEW_LEFT = 'new left today';
export const RAISE_TODAY = `${NEW_STEP} more new today`;
export const FOCUS_NEXT = 'Next:';
export const FOCUS_CERT = 'Certification:';

// the account menu
export const YOUR_ACCOUNT = 'Your account';
export const SETTINGS = 'Settings';
export const SIGNED_IN_DEVICES = 'Signed-in devices';
export const SIGN_OUT = 'Sign out';
// the address the provider verified, and the engine's own id where no provider linked one
export const named = (me: { email: string | null; user_id: string } | undefined) =>
  me === undefined ? 'Signed in' : (me.email ?? me.user_id);
export const READING_SESSION = 'Reading the session…';
export const NO_PROVIDER_LINKED = 'Signed in with no provider linked';
// the line under the name: the engine's own id under a verified address, or why there is no address
export function meLine(me: { email: string | null; user_id: string } | undefined): string {
  if (me === undefined) return READING_SESSION;
  return me.email ? me.user_id : NO_PROVIDER_LINKED;
}

// the settings
export const ACCOUNT = 'Account';
export const STUDY = 'Study';
export const SETTING_LABEL: Record<SettingName, string> = {
  new_per_day: 'New questions per day',
  exam_size: 'Exam size',
};
export function settingRange(name: SettingName): string {
  const [low, high] = SETTING_RANGE[name];
  return `${low} to ${high}`;
}
export const SAVE = 'Save';
export const SAVED = 'Saved.';
export const SYNC_NOW = 'Sync now';
export const waitingToSend = (n: number) => `${n} ${n === 1 ? 'record waits' : 'records wait'} to be sent`;
export const ARCHIVED_MODULES = 'Archived modules';
export const RESTORE = 'Restore';

// the sign-out
export const SIGN_OUT_TITLE = 'Sign out and lose unsent records?';
export function signOutWarning(n: number, here: ThisDevice): string {
  const one = n === 1;
  return `${one ? 'One record' : `${n} records`} did not reach the engine. Signing out now deletes ${one ? 'it' : 'them'} from this ${here}.`;
}
export const STAY_SIGNED_IN = 'Stay signed in';

// the signed-in devices
export const REVOKED_NOTE = 'A revoked device is signed out at its next request.';
export const thisDevice = (here: ThisDevice) => `this ${here}`;
export const REVOKE = 'Revoke';

// the login
export const LOGIN_INTRO = 'Deliberate practice of algorithmic problem-solving. Access is by invitation.';
const PROVIDER_NAMES = { google: 'Google', github: 'GitHub' } as const;
export const continueWith = (provider: keyof typeof PROVIDER_NAMES) => `Continue with ${PROVIDER_NAMES[provider]}`;
export const devLoginAs = (user: string) => `Dev login as ${user}`;
export const SIGN_IN_LOADING = 'Reading the sign-in…';
export const NO_SIGN_IN = 'No sign-in is configured.';
export const NO_DEV_LOGIN = 'The engine offers no dev login, which the dev app signs in through.';
export function signInUnread(error: string): string {
  if (/network request failed|failed to fetch|timed? ?out|offline/i.test(error)) {
    return 'No connection. The sign-in is read from the engine.';
  }
  return `The sign-in did not load: ${error}`;
}

// the codes `Refusal` in `api/signin.py` sends back. The code carries no
// address, so a refusal names none
const REFUSALS: Record<string, string> = {
  incomplete: 'That sign-in did not complete. Try again.',
  'no-email': 'That account has no verified email address, which signs nobody in.',
  uninvited: 'That address has no invitation.',
};
export const refusal = (code: string) => REFUSALS[code] ?? REFUSALS.incomplete;

// the privacy policy, linked from both clients' login
export const PRIVACY_NOTE = 'The app stores what you attempt and what a model says about it.';
export const PRIVACY_LINK = 'Privacy policy';
