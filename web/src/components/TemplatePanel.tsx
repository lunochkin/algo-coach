import { useState } from 'react'

import { Link } from 'react-router'

import type { Recalled, Template } from '@/api/client'
import { Markdown } from '@/components/Markdown'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { lastAt } from '@/lib/format'
import { pieces } from '@/lib/python'

// the form stays hidden until it is asked for: `content.md` gives why a form
// is worth deriving before it is read. The trigger reads either way, since it
// says when to reach for the form rather than how the form is written
export function TemplatePanel({
  template,
  card,
  recalled,
}: {
  template: Template
  // the card the form is taught by, which its recall is started from
  card: string
  recalled: Recalled | undefined
}) {
  const [revealed, setRevealed] = useState(false)
  const lines = template.code.trimEnd().split('\n').length
  // `content.md`: a template no case checks is read on the card and never
  // recalled
  const recallable = (template.cases ?? []).length > 0

  return (
    <div className="overflow-hidden rounded-xl border">
      {/* what the form is, and how its recall has gone: the header carries the
          identity, and the body carries the form and the acts on it */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b bg-card px-4 py-3">
        <h3 className="font-medium">{template.title}</h3>
        {template.optional && <Badge variant="secondary">optional</Badge>}
        {template.kind === 'procedure' && <Badge variant="outline">procedure</Badge>}
        <span className="ml-auto text-meta text-muted-foreground">
          {recallable ? reads(recalled) : 'No case checks this form'}
        </span>
      </div>

      <div className="space-y-stack px-4 py-3">
        <Markdown>{template.trigger}</Markdown>

        {revealed ? (
          <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
            <code>
              {pieces(template.code).map((piece, index) => (
                <span key={index} className={piece.token}>
                  {piece.text}
                </span>
              ))}
            </code>
          </pre>
        ) : (
          // the press is the cover: it names the length and nothing of the
          // form, and a reader decides from that whether to try recalling it
          <button
            type="button"
            onClick={() => setRevealed(true)}
            className="w-full rounded-md border border-dashed px-3 py-2 text-left text-meta text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            Reveal the form · {lines === 1 ? '1 line' : `${lines} lines`}
          </button>
        )}

        {revealed && template.notes && <Markdown>{template.notes}</Markdown>}

        <div className="flex flex-wrap items-center gap-2">
          {recallable ? (
            <Button variant="outline" size="sm" asChild>
              <Link
                to={`/cards/${encodeURIComponent(card)}/recall/${encodeURIComponent(template.slug)}`}
              >
                Recall this form
              </Link>
            </Button>
          ) : (
            <span className="text-meta text-muted-foreground">
              Read here and never recalled, since no case checks it.
            </span>
          )}
          {revealed && (
            <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setRevealed(false)}>
              Hide the form
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

// a hinted pass is not a pass, so the hints read beside the moment
function reads(one: Recalled | undefined): string {
  if (one === undefined || one.last_at === null) return 'Never recalled'
  const hints = one.hints.length === 0 ? 'no hint taken' : `${one.hints.length} hints`
  return `Recalled ${lastAt(one.last_at)} · ${one.verified ? 'passed' : 'failed'} · ${hints}`
}
