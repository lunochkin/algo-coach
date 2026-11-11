import { pieces } from '@algo-coach/editor'

// Python read on a page, coloured by the one mapping the editor uses:
// `pages.md`, The design system
export function PythonCode({ code }: { code: string }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
      <code>
        {pieces(code).map((piece, index) => (
          <span key={index} className={piece.token}>
            {piece.text}
          </span>
        ))}
      </code>
    </pre>
  )
}

// the cover over a hidden form: a dashed press naming the form's length and
// nothing of it, so a reader decides from that whether to try recalling it
export function RevealPress({ label, onReveal }: { label: string; onReveal: () => void }) {
  return (
    <button
      type="button"
      onClick={onReveal}
      className="w-full rounded-md border border-dashed px-3 py-2 text-left text-meta text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      {label}
    </button>
  )
}

// a value read back, such as a failing case's arguments or a question's code:
// the code block's shape without Python's colours
export function PlainCode({ children, wrap = false }: { children: string; wrap?: boolean }) {
  return (
    <pre
      className={
        wrap
          ? 'max-h-64 overflow-auto rounded-md bg-muted p-3 font-mono text-code break-words whitespace-pre-wrap'
          : 'overflow-x-auto rounded-md bg-muted p-3 font-mono text-code'
      }
    >
      {children}
    </pre>
  )
}
