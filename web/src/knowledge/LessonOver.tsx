import { lessonPage } from '@algo-coach/core'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useLearner } from '@/knowledge/learner'
import { LessonBody } from '@/pages/LessonPage'

export type Reading = { course: string; slug: string } | null

// a lesson read over a running queue, as the phone reads it, so reading ends
// nothing: `pages.md`, The knowledge pages. A linked lesson opens in place
export function LessonOver(props: { reading: Reading; onRead: (r: Reading) => void }) {
  const { reading, onRead } = props
  const { catalog } = useLearner()
  const { c, x, body, read, note } = lessonPage(catalog, reading?.course ?? '', reading?.slug ?? '')
  return (
    <Dialog open={reading !== null} onOpenChange={(open) => open || onRead(null)}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-3xl">
        {c && x ? (
          <>
            <DialogHeader>
              <DialogTitle>{x.title}</DialogTitle>
              <DialogDescription>{note}</DialogDescription>
            </DialogHeader>
            <LessonBody
              c={c}
              x={x}
              body={body}
              read={read}
              onLesson={(slug) => onRead({ course: c.slug, slug })}
            />
          </>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
