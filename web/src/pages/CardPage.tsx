import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { api, type Template } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function CardPage() {
  const { slug = '' } = useParams()
  const card = useLoaded(
    (signal) => api.GET('/api/cards/{slug}', { params: { path: { slug } }, signal }),
    `card:${slug}`,
  )

  return (
    <article className="space-y-6">
      <Button variant="outline" asChild>
        <Link to="/cards">Back to the cards</Link>
      </Button>
      <Loaded of="the card" state={card}>
        {(card) => (
          <div className="space-y-6">
            <header className="space-y-1">
              <p className="text-meta text-muted-foreground">{card.technique}</p>
              <h1 className="text-2xl font-semibold">{card.title}</h1>
            </header>
            <section className="space-y-1">
              <h2 className="text-lg font-medium">When to reach for it</h2>
              <p>{card.trigger}</p>
            </section>
            <section>
              <Markdown>{card.brief}</Markdown>
            </section>
            <section className="space-y-4">
              <h2 className="text-lg font-medium">Templates</h2>
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
    <div className="space-y-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium">{template.title}</h3>
        {template.optional && <Badge variant="secondary">optional</Badge>}
        {template.kind === 'procedure' && <Badge variant="outline">procedure</Badge>}
      </div>
      <p className="text-sm">{template.trigger}</p>
      {revealed ? (
        <>
          <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-sm">
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
            className="pointer-events-none max-h-40 overflow-hidden rounded-md bg-muted p-3 font-mono text-sm blur-md select-none"
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
