import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { expect, it } from 'vitest';

import { Board, loadSnapshot, nextQueue, type Snapshot } from './index';

// Smoke test over a snapshot saved from the engine, where one is present. git ignores content/.
const REAL = resolve(__dirname, '../../../content/snapshot.json');

it.skipIf(!existsSync(REAL))('loads the real courses.json and picks a session', () => {
  const cat = loadSnapshot(JSON.parse(readFileSync(REAL, 'utf8')) as Snapshot);
  expect(cat.questions.length).toBeGreaterThan(0);
  const b = Board.build(cat, []);
  const q = nextQueue(b, 10).pick(b, Date.now());
  expect(q).not.toBeNull();
  for (const q of cat.questions) {
    if (q.format === 'choice') expect(q.answer.every((i) => i >= 0 && i < q.choices.length)).toBe(true);
  }
});
