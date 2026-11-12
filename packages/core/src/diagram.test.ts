import { describe, expect, it } from 'vitest';

import { drawingSize, mermaidSource } from './diagram';

describe('a Mermaid source', () => {
  it('is a question diagram that one fence is all of, without its last newline', () => {
    expect(mermaidSource('```mermaid\nflowchart TB\n  a --> b\n```\n')).toBe('flowchart TB\n  a --> b');
  });

  it('is no source where prose sits beside the fence', () => {
    expect(mermaidSource('As drawn:\n```mermaid\nflowchart TB\n```')).toBeNull();
    expect(mermaidSource('```mermaid\nflowchart TB\n```\nafter')).toBeNull();
  });

  it('is no source in a drawing made of characters', () => {
    expect(mermaidSource('┌──┐\n│a │\n└──┘')).toBeNull();
  });
});

describe('a drawing', () => {
  it('asks for the size its viewBox gives', () => {
    expect(drawingSize('<svg viewBox="4 4 365.5 351" fill="#333">')).toEqual({ width: 365.5, height: 351 });
  });

  it('asks for none without a viewBox', () => {
    expect(drawingSize('<svg width="10">')).toBeNull();
  });
});
