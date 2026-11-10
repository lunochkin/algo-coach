import { pieces } from '@/lib/python'

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
