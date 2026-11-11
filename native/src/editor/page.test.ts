import { describe, expect, it } from 'vitest';

import { sourceHash } from '../../editor/build.mjs';
import { SOURCE_HASH } from './page';

describe('the editor page the app ships', () => {
  it('was bundled from the sources as they stand: run `just editor-page`', () => {
    expect(SOURCE_HASH).toBe(sourceHash());
  });
});
