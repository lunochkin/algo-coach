import { RECALL_THIS, HIDE_FORM } from '@climb/core'
import { useState } from 'react'

import { Link } from 'react-router'

import type { Recalled, Template } from '@/api/client'
import { PanelFrame, PanelStrip } from '@/components/Panel'
import { Markdown } from '@/components/Markdown'
import { PythonCode, RevealPress } from '@/components/PythonCode'
import { Tag } from '@/components/Tag'
import { Button } from '@/components/ui/button'
import { templateView } from '@/lib/format'

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
  const view = templateView(template, recalled)

  return (
    <PanelFrame>
      {/* what the form is, and how its recall has gone: the header carries the
          identity, and the body carries the form and the acts on it */}
      <PanelStrip>
        <h3 className="font-medium">{template.title}</h3>
        {view.badges.map((badge) => (
          <Tag key={badge}>{badge}</Tag>
        ))}
        <span className="ml-auto text-meta text-muted-foreground">{view.status}</span>
      </PanelStrip>

      <div className="space-y-stack px-4 py-3">
        <Markdown>{template.trigger}</Markdown>

        {revealed ? (
          <PythonCode code={template.code} />
        ) : (
          // the press is the cover: it names the length and nothing of the
          // form, and a reader decides from that whether to try recalling it
          <RevealPress label={view.reveal} onReveal={() => setRevealed(true)} />
        )}

        {revealed && template.notes && <Markdown>{template.notes}</Markdown>}

        <div className="flex flex-wrap items-center gap-stack">
          {view.recallable ? (
            <Button variant="outline" size="sm" asChild>
              <Link
                to={`/cards/${encodeURIComponent(card)}/recall/${encodeURIComponent(template.slug)}`}
              >
                {RECALL_THIS}
              </Link>
            </Button>
          ) : (
            <span className="text-meta text-muted-foreground">{view.unchecked}</span>
          )}
          {revealed && (
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto"
              onClick={() => setRevealed(false)}
            >
              {HIDE_FORM}
            </Button>
          )}
        </div>
      </div>
    </PanelFrame>
  )
}
