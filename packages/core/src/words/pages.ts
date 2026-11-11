// what the practice pages, the navigation and the shared presses say, for
// every platform: a platform changes the look alone, and reads each sentence
// from here

// the sections the navigation names: `pages.md`, Sections
export const SECTION_PRACTICE = 'Practice';
export const SECTION_PROBLEMS = 'Problems';
export const SECTION_CARDS = 'Cards';
export const SECTION_KNOWLEDGE = 'Knowledge';

// the way back, named by the page it returns to
export const BACK_BOARD = 'Board';
export const BACK_PROBLEMS = 'Problems';
export const BACK_CARDS = 'Cards';
export const BACK_KNOWLEDGE = 'Knowledge';
export const BACK_LESSONS = 'Lessons';
export const BACK_CERTIFICATIONS = 'Certifications';
export const BACK_SIGN_IN = 'Sign in';

// what a page loads, as its loading and failed readings name it
export const OF = {
  board: 'the board',
  cards: 'the cards',
  card: 'the card',
  candidates: 'the candidates',
  technique: 'the technique',
  problems: 'the problems',
  problem: 'the problem',
  recall: 'the form to recall',
  claim: 'the claim',
  devices: 'the signed-in devices',
  settings: 'the settings',
  signIn: 'the sign-in',
  module: 'the module',
  lesson: 'the lesson',
  lessons: 'the lessons',
  certifications: 'the certifications',
  exam: 'the exam',
  queue: 'the queue',
} as const;

// the presses a sheet or a dialog closes on
export const CANCEL = 'Cancel';
export const CLOSE = 'Close';
export const COPY = 'Copy';

// the board
export const BOARD_TITLE = 'Practice';
export const BOARD_NOTE = 'Continue a card or a module, or pick a technique, stalest first.';
export const BOARD_NONE = 'No served problem carries a technique yet.';
export const BOARD_STUDYING = 'Cards in progress';
export const BOARD_UNTOUCHED = 'Techniques not practised yet';
export const BOARD_PRACTISED = 'Techniques practised';

// a technique's page
export const TECHNIQUE_CARDS = 'Cards';
export const TECHNIQUE_PROBLEMS = 'Problems';
export const TECHNIQUE_NONE = 'No served problem carries this technique.';

// the cards, and a card
export const CARDS_TITLE = 'Cards';
export const CARDS_NOTE =
  'One card teaches one technique: when to reach for it, and the forms to reproduce from memory.';
export const CARDS_NONE = 'No card is seeded yet.';
export const CARDS_STUDYING = 'Studying';
export const CARDS_NOT_STARTED = 'Not started';
export const cardsCounted = (n: number) => (n === 1 ? '1 card' : `${n} cards`);
export const CARD_TRIGGER = 'When to reach for it';
export const CARD_BRIEF = 'The brief';
export const CARD_TEMPLATES = 'Templates';
export const CARD_OPTIONAL = 'optional';
export const RUNGS_SOLVED = 'rungs solved';
export const QUESTIONS_PASSED = 'questions passed';
export const FORMS_RECALLED = 'forms recalled';
export const PROBES_DRAWN = 'probes drawn';
export const HIDE_FORM = 'Hide the form';
export const FORM_UNCHECKED = 'Read here and never recalled, since no case checks it.';

// a problem's page and its sitting
export const PROBLEM_FALLBACK = 'The problem';
export const PROBLEM_OPENING = 'Opening the problem…';
export const PROBLEM_RETIRED =
  'This problem was retired: its statement asked for something its cases do not decide. It is served to nobody, and your attempts on it stay in your log.';
export const SITTING_STATEMENT = 'Statement';
export const SITTING_CODE = 'Code';
export const ELAPSED_TIME = 'Elapsed time';
export const CASES_IN_ORDER = 'Cases, in order';

// the rest
export const NOT_FOUND = 'No page here';
export const SIGN_IN_TITLE = 'Sign in';
export const LESSON_FALLBACK = 'Lesson';
export const KNOWLEDGE_NOTE = 'Answer the questions due, then the new ones.';
export const SETTINGS_NOTE = 'The study settings hold on every device you sign in on.';
export const SYNC_HEADING = 'Sync';
export const SUBTOPIC_COLUMN = 'Subtopic';
export const SCOPE_COLUMN = 'Scope';
export const ZOOM_IN = 'Zoom in';
export const ZOOM_OUT = 'Zoom out';
export const moveUp = (title: string) => `Move ${title} up`;
export const moveDown = (title: string) => `Move ${title} down`;

// the phone's keyboard, each key named for a screen reader
export const KEY_NAMES = {
  back: 'Backspace',
  dedent: 'Dedent',
  indent: 'Indent',
  block: 'Select the block',
  lineUp: 'Move the line up',
  lineDown: 'Move the line down',
  duplicate: 'Duplicate the line',
  shift: 'Shift',
  left: 'Cursor left',
  right: 'Cursor right',
  space: 'Space',
  enter: 'Enter',
  letters: 'Letters',
  symbols: 'More symbols',
  keywords: 'Keywords',
} as const;
export const nameKey = (name: string) => `Name ${name}`;
export const KEY_SPACE = 'space';
export const MAP_FIT_PRESS = 'Fit';
export const cardsOffered = (n: number) => (n === 1 ? 'Card:' : 'Cards:');
export const NO_DIFFICULTY = 'no difficulty';

// the phone's own settings and sign-in: `pages.md`, The two clients
export const ENGINE_ADDRESS = 'Engine address';
export const ADDRESS_HINT = 'An address such as https://example.invalid';
export const DEVICE_NAME = 'Device name';
export const DEVICE_NAME_RULE = 'Letters, digits, - and _ only';
export const REMINDER_HOUR = 'Reminder hour (0–23)';
export const REMINDER_HOUR_RULE = '0–23';
export const NO_SESSION = 'No session';
export const FINISH = 'Finish';
export const keyboardToggle = (shown: boolean) => (shown ? 'Hide the keyboard' : 'Show the keyboard');
export const mapLessonsToggle = (shown: boolean) => (shown ? 'Hide lessons' : 'Show lessons');
export const NOT_SIGNED_IN = 'Not signed in.';
export const RECALL_MARKS = 'recall';

// the rest the pages typed inline
export const studyingSince = (when: string) => `studying since ${when}`;
export const nextRung = (title: string) => `Next rung: ${title}`;
export const A_FORM = 'a form';
export const SUBMIT_KEYS = '⌘/Ctrl + Enter';
export const SUBMIT_HINT = `${SUBMIT_KEYS} · judged against the problem's own test cases`;
export const CUT_VALUE = 'Cut';
export const showAllKb = (bytes: number) => `Show all ${(bytes / 1024).toFixed(0)} KB`;
export const PROCEDURE = 'procedure';
export const FORM_NO_CASES = 'No case checks this form';
export const LOADING = 'Loading…';
export const mapOf = (title: string) => `The prerequisite map of ${title}`;

// what a screen reader reads for a press that names its record
export const restoreLabel = (title: string) => `Restore ${title}`;
export const revokeLabel = (name: string) => `Revoke ${name}`;
export const reorderLabel = (title: string) => `Reorder ${title}`;
export const startLabel = (title: string) => `Start ${title}`;
export const gradeLabel = (grade: string) => `Grade: ${grade}`;
export const raiseLabel = (step: number) => `Allow ${step} more new questions`;
export const caseLabel = (index: number, outcome: string, elapsedMs?: number | null) =>
  `case ${index + 1}: ${outcome}${elapsedMs == null ? '' : `, ${elapsedMs} ms`}`;
/** A problem's techniques in one line, as its row and its page read them. */
export const techniquesLine = (techniques: readonly string[]) => techniques.join(' · ');
export const syncErrorLabel = (summary: string) => `Sync error: ${summary}. Tap for details.`;
