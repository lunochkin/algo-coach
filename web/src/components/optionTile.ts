import { cn } from '@/lib/utils'

// one option tile, as a choice is drawn wherever one is offered or read back:
// picked reads bordered and tinted, and an open choice tints on hover. A
// button, a label and a list item each carry it, so it is a class
export const optionTile = (picked: boolean, open = true) =>
  cn(
    'flex gap-3 rounded-xl border px-4 py-2.5 text-left',
    picked ? 'border-foreground bg-muted' : open && 'hover:bg-muted/50',
  )
