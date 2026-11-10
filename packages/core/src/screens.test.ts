import { describe, expect, it } from 'vitest';

import {
  Board,
  continueLine,
  counted,
  DEFAULT_RULES,
  emptyContinue,
  groupLabel,
  loadSnapshot,
  nextUpView,
  offersRaise,
  questionHead,
  queueLine,
  queueSummary,
  queueTitle,
} from './index';

const mk = (id: string, sub: string) => ({
  id, topic: 't', sub, level: 0, kind: 'concept', prompt: id, format: 'choice' as const,
  choices: ['a', 'b', 'c'], answer: ['A'],
});
const course = (extra: object = {}) =>
  loadSnapshot({
    format: 6,
    courses: [
      {
        slug: 'c',
        definition: {
          title: 'C', pass_ratio: 1, kinds: ['concept'],
          topic: [{ slug: 't', tier: 1, title: 'Types', subs: ['s1', 's2'], sub_titles: { s1: 'Ints' } }],
        },
        questions: [mk('a', 's1'), mk('b', 's2')],
        ...extra,
      },
    ],
  } as never);
const T = new Date(Date.UTC(2026, 10, 10, 12)).toISOString();

describe('group label', () => {
  it('names the topic, the subtopic by its title and the level', () => {
    const [c] = course().courses;
    expect(groupLabel(c, DEFAULT_RULES, { topic: 't', sub: 's1', level: 1 })).toBe('Types › Ints · Associate');
  });

  it('drops the topic where the view names it already', () => {
    const [c] = course().courses;
    expect(groupLabel(c, DEFAULT_RULES, { topic: 't', sub: 's2', level: 0 }, false)).toBe('s2 · Foundation');
  });
});

describe('question head', () => {
  const cat = course();
  const [c] = cat.courses;
  const q = cat.questions.find((x) => x.id === 'a')!;

  it('ends on the queue tag', () => {
    expect(questionHead(c, DEFAULT_RULES, q, 'new')).toBe('Types › Ints · Foundation · concept · new');
  });

  it('marks a question served before its learning step is due', () => {
    expect(questionHead(c, DEFAULT_RULES, q, 'weak', true)).toBe(
      'Types › Ints · Foundation · concept · weak · learning step, early',
    );
  });
});

describe('next up', () => {
  it('names the group, its progress and the other open groups', () => {
    const b = Board.build(course(), []);
    const v = nextUpView(b, b.courses[0]);
    expect(v.title).toBe('Next up: Ints · Foundation');
    expect(v.detail).toBe('Types · 0/1 passed · 1 more open');
    expect(v.accessibilityLabel).toBe('Next up: practise Ints Foundation');
  });

  it('names the lesson every open group waits for', () => {
    const lesson = { title: 'Names', file: 'lessons/names.md', teaches: ['s1@0', 's2@0'], needs: [], pretest: 0 };
    const b = Board.build(course({ graph: { format: 2, lesson: { names: lesson } }, lesson_bodies: { names: '# Names' } }), []);
    expect(nextUpView(b, b.courses[0]).title).toBe('Next up: read “Names”');
  });

  it('says so once every open group is done', () => {
    const b = Board.build(course(), [
      { t: T, course: 'c', id: 'a', ok: true },
      { t: T, course: 'c', id: 'b', ok: true },
    ]);
    expect(nextUpView(b, b.courses[0])).toMatchObject({ title: 'All unlocked groups done', next: null });
  });
});

describe('count lines', () => {
  it('leaves the learning count out where nothing is in a step', () => {
    expect(continueLine({ reviews: 3, learning: 0, newLeft: 7 })).toBe('3 reviews · 7 new left today');
    expect(queueLine({ reviews: 3, learning: 2, newLeft: 0 })).toBe('3 due · 2 learning · 0 new left today');
  });

  it('names a strict focus', () => {
    expect(continueLine({ reviews: 1, learning: 1, newLeft: 2 }, true)).toBe(
      'Strict focus · 1 review · 1 learning · 2 new left',
    );
  });
});

describe('the raise', () => {
  it('is offered only where the limit holds unseen questions back', () => {
    expect(offersRaise('next', 0, true)).toBe(true);
    expect(offersRaise('next', 1, true)).toBe(false);
    expect(offersRaise('next', 0, false)).toBe(false);
    expect(offersRaise('review', 0, true)).toBe(false);
  });
});

describe('empty Continue', () => {
  const focus = { course: 'c', topic: null, sub: null };

  it('offers the raise where the day limit emptied the queue, focus or not', () => {
    expect(emptyContinue({ blocked: true, newLimit: 10, focus })).toEqual({
      notice: "Today's 10 new questions are done, and more are unlocked.",
      action: { kind: 'raise', label: '+5 new today' },
    });
  });

  it('sends a certificate focus to the certificates', () => {
    expect(emptyContinue({ blocked: false, newLimit: 10, focus: { ...focus, cert: 'all@0' } }).action?.kind).toBe('certs');
  });

  it('offers to clear any other focus', () => {
    expect(emptyContinue({ blocked: false, newLimit: 10, focus }).action?.kind).toBe('clear-focus');
  });

  it('offers nothing without a focus', () => {
    expect(emptyContinue({ blocked: false, newLimit: 10, focus: null }).action).toBeNull();
  });
});

describe('a stopped queue', () => {
  it('names why it stopped, and how it went', () => {
    expect(queueSummary({ answered: 4, correct: 3, introduced: 2, stopped: true })).toEqual({
      title: 'Stopped',
      line: 'Accuracy 75% · 2 new introduced',
    });
  });

  it('reads an empty queue as nothing more ready', () => {
    expect(queueSummary({ answered: 0, correct: 0, introduced: 0, stopped: false }).title).toBe('Nothing more ready');
  });

  it('titles the filtered queue by its own name, not the board section', () => {
    expect(queueTitle('drill')).toBe('Filtered');
  });
});

describe('a count', () => {
  it('names one in the singular, and any other number in the plural', () => {
    expect(counted(1, 'review')).toBe('1 review');
    expect(counted(0, 'review')).toBe('0 reviews');
    expect(counted(2, 'subtopic')).toBe('2 subtopics');
  });

  it('reads one review in the singular under Continue', () => {
    expect(continueLine({ reviews: 1, learning: 0, newLeft: 3 })).toBe('1 review · 3 new left today');
  });
});
