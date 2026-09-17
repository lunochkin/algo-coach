import { useState } from 'react'
import { useParams } from 'react-router'

import { api, type Template } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function CardPage() {
  const { slug = '' } = useParams()
  const card = useLoaded(
    (signal) => api.GET('/api/cards/{slug}', { params: { path: { slug } }, signal }),
    `card:${slug}`,
  )

  return (
    <article className="space-y-section">
      <PageHeader
        back={{ to: '/cards', label: 'Cards' }}
        title={card.data?.title ?? slug}
        note={card.data?.technique}
      />
      <Loaded of="the card" state={card}>
        {(card) => (
          <div className="space-y-section">
            <section className="space-y-1">
              <h2 className="text-heading font-medium">When to reach for it</h2>
              <p>{card.trigger}</p>
            </section>
            <section>
              <Markdown>{card.brief}</Markdown>
            </section>
            <section className="space-y-stack">
              <h2 className="text-heading font-medium">Templates</h2>
              {card.templates.map((template) => (
                <TemplateView key={template.slug} template={template} />
              ))}
            </section>
          </div>
        )}
      </Loaded>
    </article>
  )
}

// the code and the notes stay hidden until asked for: `content.md` gives why a
// form is worth deriving before it is read
function TemplateView({ template }: { template: Template }) {
  const [revealed, setRevealed] = useState(false)

  return (
    <div className="space-y-stack rounded-lg border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium">{template.title}</h3>
        {template.optional && <Badge variant="secondary">optional</Badge>}
        {template.kind === 'procedure' && <Badge variant="outline">procedure</Badge>}
      </div>
      <p>{template.trigger}</p>
      {revealed ? (
        <>
          <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-code">
            {template.code}
          </pre>
          {template.notes && <Markdown>{template.notes}</Markdown>}
          <Button variant="ghost" size="sm" onClick={() => setRevealed(false)}>
            Hide
          </Button>
        </>
      ) : (
        <div className="relative">
          <pre
            aria-hidden="true"
            className="pointer-events-none max-h-40 overflow-hidden rounded-md bg-muted p-3 font-mono text-code blur-md select-none"
          >
            {template.code}
          </pre>
          <div className="absolute inset-0 flex items-center justify-center">
            <Button variant="secondary" onClick={() => setRevealed(true)}>
              Reveal the form
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
