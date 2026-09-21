import { useState } from 'react'

import type { Template } from '@/api/client'
import { Markdown } from '@/components/Markdown'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { pieces } from '@/lib/python'

// the form stays hidden until it is asked for: `content.md` gives why a form
// is worth deriving before it is read. The trigger reads either way, since it
// says when to reach for the form rather than how the form is written
export function TemplatePanel({ template }: { template: Template }) {
  const [revealed, setRevealed] = useState(false)
  const lines = template.code.trimEnd().split('\n').length

  return (
    <div className="overflow-hidden rounded-xl border">
      <div className="flex flex-wrap items-center gap-2 border-b bg-card px-4 py-3">
        <h3 className="font-medium">{template.title}</h3>
        {template.optional && <Badge variant="secondary">optional</Badge>}
        {template.kind === 'procedure' && <Badge variant="outline">procedure</Badge>}
        <Button
          variant={revealed ? 'ghost' : 'secondary'}
          size="sm"
          className="ml-auto"
          onClick={() => setRevealed(!revealed)}
        >
          {revealed ? 'Hide the form' : 'Reveal the form'}
        </Button>
      </div>

      <div className="space-y-stack px-4 py-3">
        <Markdown>{template.trigger}</Markdown>
        {revealed ? (
          <>
            <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
              <code>
                {pieces(template.code).map((piece, index) => (
                  <span key={index} className={piece.token}>
                    {piece.text}
                  </span>
                ))}
              </code>
            </pre>
            {template.notes && <Markdown>{template.notes}</Markdown>}
          </>
        ) : (
          // the length, and nothing of the form: a reader decides whether to
          // try recalling it from how long it is
          <p className="rounded-md border border-dashed px-3 py-2 text-meta text-muted-foreground">
            The form is hidden · {lines === 1 ? '1 line' : `${lines} lines`}
          </p>
        )}
      </div>
    </div>
  )
}
