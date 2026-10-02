import { Link } from 'react-router'

import { api, type ListedCard } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { lastAt, plain } from '@/lib/format'

export function CardsPage() {
  const cards = useLoaded((signal) => api.GET('/api/cards', { signal }), 'cards')

  return (
    <section className="space-y-section">
      <PageHeader
        title="Cards"
        note="One card teaches one technique: when to reach for it, and the forms to reproduce from memory."
      />
      <Loaded of="the cards" state={cards} blank="No card is seeded yet.">
        {(cards) => {
          // the cards with a run open read first, the most recently active
          // first: they are the ones the user is working through
          const studying = cards
            .filter((card) => card.status.started_at)
            .sort((a, b) => (b.status.last_at ?? '').localeCompare(a.status.last_at ?? ''))
          const rest = cards.filter((card) => !card.status.started_at)
          return (
            <div className="space-y-section">
              {studying.length > 0 && (
                <section className="space-y-stack">
                  <h2 className="text-heading font-medium">Studying</h2>
                  <Panel technique={null} cards={studying} />
                </section>
              )}
              {rest.length > 0 && (
                <section className="space-y-stack">
                  {studying.length > 0 && <h2 className="text-heading font-medium">Not started</h2>}
                  {blocks(rest).map((block) => (
                    <Panel
                      key={'technique' in block ? block.technique : block.cards[0].slug}
                      technique={'technique' in block ? block.technique : null}
                      cards={block.cards}
                    />
                  ))}
                </section>
              )}
            </div>
          )
        }}
      </Loaded>
    </section>
  )
}

// every block is the same panel: a family several cards teach carries a
// header naming it, and the cards that teach a family of their own carry the
// name on the row instead
function Panel({ technique, cards }: { technique: string | null; cards: ListedCard[] }) {
  return (
    <section className="overflow-hidden rounded-xl border">
      {technique && (
        <div className="flex items-baseline gap-3 border-b bg-card px-4 py-3">
          <h2 className="font-mono text-heading font-medium">{technique}</h2>
          <span className="ml-auto text-meta text-muted-foreground">{cards.length} cards</span>
        </div>
      )}
      <div className="divide-y divide-border">
        {cards.map((card) => (
          <CardRow key={card.slug} card={card} named={card.technique !== technique} />
        ))}
      </div>
    </section>
  )
}

// `named` carries the technique on the row wherever no heading names it: a
// card that stands alone, or a narrower technique under its family's heading
function CardRow({ card, named = false }: { card: ListedCard; named?: boolean }) {
  const optional = card.templates.filter((one) => one.optional).length
  const { status } = card

  return (
    <Link
      to={`/cards/${encodeURIComponent(card.slug)}`}
      className="group block px-4 py-3 transition-colors hover:bg-accent"
    >
      <div className="flex items-baseline gap-3">
        <span className="font-medium underline-offset-4 group-hover:underline">{card.title}</span>
        {named && <span className="font-mono text-meta text-muted-foreground">{card.technique}</span>}
        <span className="ml-auto shrink-0 text-meta text-muted-foreground tabular-nums">
          {status.started_at ? lastAt(status.last_at) : templates(card.templates.length, optional)}
        </span>
      </div>
      {status.started_at ? (
        // a started card was already chosen, so its progress replaces the
        // trigger it was chosen by
        <p className="mt-1 text-meta text-muted-foreground tabular-nums">
          started {new Date(status.started_at).toLocaleDateString()} · ladder {status.solved}/
          {status.rungs}, required {status.required_solved}/{status.required}
          {status.gaps > 0 && ` · ${status.gaps} ${status.gaps === 1 ? 'form' : 'forms'} uncovered`}
        </p>
      ) : (
        // the trigger says when to reach for the technique, which is what a
        // reader picks a card by
        <p className="mt-1 line-clamp-2 text-meta text-muted-foreground">{plain(card.trigger)}</p>
      )}
      <RecallMarks card={card} />
    </Link>
  )
}

// one mark per template in the card's order: the last recall of each form
function RecallMarks({ card }: { card: ListedCard }) {
  const recalled = new Map(card.status.recall.map((one) => [one.template_id, one]))
  return (
    <p className="mt-1 flex items-center gap-1.5 text-meta text-muted-foreground">
      recall
      {card.templates.map((template) => {
        const [mark, reading] = recallMark(template.cases?.length ?? 0, recalled.get(template.id))
        return (
          <span key={template.id} title={`${template.title}: ${reading}`} className="font-mono">
            {mark}
          </span>
        )
      })}
    </p>
  )
}

function recallMark(
  cases: number,
  last: ListedCard['status']['recall'][number] | undefined,
): [string, string] {
  // a template no case checks is read on the card and never recalled
  if (cases === 0) return ['-', 'read, not recalled']
  if (!last?.last_at) return ['·', 'never recalled']
  if (!last.verified) return ['✗', 'failed']
  return last.hints.length > 0 ? ['◐', 'passed with hints'] : ['✓', 'recalled clean']
}

function templates(count: number, optional: number): string {
  const all = count === 1 ? '1 template' : `${count} templates`
  return optional === 0 ? all : `${all}, ${optional} optional`
}

type Block = { technique: string; cards: ListedCard[] } | { cards: ListedCard[] }

// the API orders the cards by family, the technique a narrower one is a kind
// of. A family with one card is a row like any other, since a heading over a
// single row names what the row says
function blocks(cards: ListedCard[]): Block[] {
  const out: Block[] = []
  for (const card of cards) {
    const last = out.at(-1)
    const taught = cards.filter((one) => one.family === card.family)
    if (taught.length > 1) {
      if (last && 'technique' in last && last.technique === card.family) last.cards.push(card)
      else out.push({ technique: card.family, cards: [card] })
    } else if (last && !('technique' in last)) last.cards.push(card)
    else out.push({ cards: [card] })
  }
  return out
}
