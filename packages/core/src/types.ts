import type { Certs, RawCerts } from './certs';
import type { Graph, RawGraph } from './graph';

export type Format = 'choice' | 'short' | 'card';
export type Status = 'unseen' | 'weak' | 'due' | 'learning' | 'mastered';
export type Grade = 'k' | 'p' | 'n';

export interface TopicDef {
  slug: string;
  tier: number;
  title: string;
  subs: string[];
  sub_titles?: Record<string, string>; // a subtopic's title, where the module gives one
}

export interface CourseDef {
  title: string;
  order?: number;
  pass_ratio: number;
  kinds: string[];
  code_kinds?: string[];
  code_lang?: string;
  topic: TopicDef[];
}

export interface RawQuestion {
  id: string;
  topic: string;
  sub: string;
  level?: number;
  kind: string;
  prompt: string;
  format?: Format;
  code?: string;
  choices?: string[];
  answer?: string[] | string;
  accept?: string[];
  case?: boolean;
  key?: string[] | string; // a legacy string is read as one point
  traps?: string[];
  explain?: string;
  why?: string[];
  detail?: string | RawDetail; // a plain string is legacy, read as mechanism
  key_detail?: string[];
  traps_detail?: string[];
  lesson?: string; // "slug" or "slug#anchor"
}

export interface RawDetail {
  mechanism?: string;
  example?: string;
  pitfalls?: string[];
  versions?: string;
  diagram?: string;
}

export interface Detail {
  mechanism: string;
  example: string; // monospace, verbatim
  pitfalls: string[];
  versions: string;
  diagram: string; // monospace, never reflowed
}

export interface FsrsRules {
  version: number;
  desired_retention: number;
  maximum_interval: number; // days
  learning_steps_minutes: number[];
  relearning_steps_minutes: number[];
  enable_fuzzing: boolean; // always false: replays must agree
  parameters: number[];
  mastered_stability_days: number;
}

export interface Rules {
  fsrs: FsrsRules;
  levels: Record<string, string>;
}

export interface Snapshot {
  format: number;
  rules?: { fsrs?: FsrsRules; levels?: Record<string, string> };
  courses: {
    slug: string;
    definition: CourseDef;
    questions: RawQuestion[];
    graph?: RawGraph;
    lesson_bodies?: Record<string, string>; // format 5
    certs?: RawCerts; // format 6
  }[];
}

export interface Topic {
  slug: string;
  tier: number;
  title: string;
  subs: string[];
  subTitles: Record<string, string>;
}

export interface Course {
  slug: string;
  title: string;
  order: number;
  paused: boolean; // learner state from status records, not course content
  archived: boolean; // paused and hidden everywhere; see visibleCatalog
  graph: Graph | null; // prerequisites; null when absent or invalid
  graphErrors: string[]; // why a published graph is ignored
  lessonBodies: Record<string, string>; // Markdown by lesson slug; empty before format 5
  certs: Certs | null; // certifications; null when absent or invalid
  certsErrors: string[];
  passRatio: number;
  kinds: string[];
  codeLang: string;
  topics: Topic[];
}

export interface Question {
  course: string;
  id: string;
  topic: string;
  sub: string;
  level: number;
  kind: string;
  prompt: string;
  format: Format;
  code: string;
  choices: string[];
  answer: number[]; // indexes into choices, ascending
  accept: string[];
  caseSensitive: boolean;
  key: string[]; // card: points of the model answer
  traps: string[]; // card: known wrong claims
  explain: string;
  why: string[];
  detail: Detail | null;
  lesson: string; // "slug" or "slug#anchor": where this is taught; "" when unset
  keyDetail: string[]; // card: one explanation per point
  trapsDetail: string[]; // card: why each trap is wrong
}

export interface Group {
  course: string;
  topic: string;
  sub: string;
  level: number;
}

export interface AttemptRecord {
  t: string;
  course: string;
  id: string;
  ok: boolean;
  guess?: true;
  grade?: Grade;
  missed?: number[]; // card: 0-based points not recalled
  traps?: number[]; // card: 0-based traps fallen into
  wrong?: true; // card: something else said wrong
}

export type CourseStatus = 'active' | 'paused' | 'archived';

export interface StatusRecord {
  t: string;
  course: string;
  status: CourseStatus;
}

/** A raise of today's limit: the day's raises add up across devices. */
export interface RaiseRecord {
  t: string;
  n: number;
}

export interface LessonRecord {
  t: string;
  course: string;
  lesson: string;
  status: 'done' | 'undone';
}

export interface SessionRecord {
  t: string;
  mode: string;
  score: number;
  n: number;
}

export interface Attempt {
  t: number; // epoch ms
  rating: number; // FSRS: 1 Again, 2 Hard, 3 Good; a pass is Good
}
