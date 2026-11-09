import type { Item } from '@/lib/sections'
import { cn } from '@/lib/utils'

// the sections of a long page, in one row that stays at the top as the page
// scrolls: a card's brief runs past a screen, and the ladder under it is
// otherwise reached by scrolling through the whole of it
export function SectionBar({
  items,
  current,
  onJump,
}: {
  items: Item[]
  current: string | null
  onJump: (id: string) => void
}) {
  return (
    <nav className="sticky top-0 z-10 -mx-gutter border-b bg-background px-gutter">
      <div className="flex gap-1 overflow-x-auto py-2">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onJump(item.id)}
            aria-current={current === item.id ? 'true' : undefined}
            className={cn(
              'rounded-lg px-2.5 py-1 text-meta whitespace-nowrap transition-colors',
              current === item.id
                ? 'bg-secondary text-secondary-foreground'
                : 'text-muted-foreground hover:bg-accent',
            )}
          >
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
