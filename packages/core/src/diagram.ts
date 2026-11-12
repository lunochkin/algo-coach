/** One Mermaid source as the seed drew it, in each scheme: `knowledge.md`, Diagrams. */
export interface Drawing {
  light: string;
  dark: string;
}

const WHOLE = /^\s*```mermaid\n([\s\S]*?)^```\s*$/m;

/**
 * A question's diagram as a Mermaid source, where one fence is all it holds,
 * without the newline ending its last line, as the seed keys the drawing.
 */
export function mermaidSource(diagram: string): string | null {
  const m = WHOLE.exec(diagram);
  if (!m || m.index !== 0 || m[0].length !== diagram.length) return null;
  return m[1].replace(/\n+$/, '');
}

/** The size a drawing asks for, from its viewBox, in CSS pixels. */
export function drawingSize(svg: string): { width: number; height: number } | null {
  const box = /viewBox="([^"]+)"/.exec(svg)?.[1].trim().split(/[\s,]+/).map(Number);
  if (!box || box.length !== 4 || !(box[2] > 0 && box[3] > 0)) return null;
  return { width: box[2], height: box[3] };
}
