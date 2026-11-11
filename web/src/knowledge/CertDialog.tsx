import { Target, Trophy } from 'lucide-react'
import { Link } from 'react-router'

import {
  CERT_START,
  CERT_TAKE_EXAM,
  CERT_TARGET,
  CERT_TO_COVER,
  CERT_UNTARGET,
  certConditions,
  certFocus,
  type Board,
  type CertStatus,
  type Course,
  newRecord,
} from '@algo-coach/core'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { EXAM } from '@/knowledge/paths'
import type { Scope } from '@/knowledge/StartSheet'

export type OpenCert = { c: Course; b: Board; states: Map<string, CertStatus>; id: string }

// a certification's conditions, its exam and its focus press, opened from
// the certifications' grid and from the map: `pages.md`, The two clients
export function CertDialog({
  open,
  onClose,
  onStart,
}: {
  open: OpenCert | null
  onClose: () => void
  onStart: (s: Scope) => void
}) {
  const k = useKnowledge()
  const { focus } = useLearner()
  const v = open ? certConditions(open.b, open.c, open.id, open.states, focus) : null
  return (
    <Dialog open={!!v} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        {v && open && (
          <>
            <DialogHeader>
              <DialogTitle>{v.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-stack text-meta">
              <p className="font-medium text-foreground">{v.label}</p>
              {v.note && <p>{v.note}</p>}
              {v.progressNote && <p className="text-muted-foreground">{v.progressNote}</p>}
              <ul className="space-y-1">
                {v.checks.map((x) => (
                  <li key={x.text}>
                    <span className={x.ok ? 'text-verdict-passed' : 'text-verdict-wrong'}>
                      {x.ok ? '✓' : '✗'}{' '}
                    </span>
                    {x.text}
                  </li>
                ))}
              </ul>
              {v.short.length > 0 && (
                <div className="space-y-1">
                  <p className="font-medium">{CERT_TO_COVER}</p>
                  {v.short.map((g) => (
                    <div key={g.sub} className="flex items-center gap-stack">
                      <span className="flex-1">{g.line}</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const level = open.c.certs?.get(open.id)?.level ?? null
                          onClose()
                          onStart({ course: open.c.slug, topic: g.topic, sub: g.sub, level })
                        }}
                      >
                        {CERT_START}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-muted-foreground">{v.scope}</p>
            </div>
            <DialogFooter>
              {v.offersExam && (
                <Button asChild>
                  <Link to={`${EXAM}?${new URLSearchParams({ cert: open.id })}`}>
                    <Trophy />
                    {CERT_TAKE_EXAM}
                  </Link>
                </Button>
              )}
              {v.offersTarget &&
                (v.targeted ? (
                  <Button
                    variant="outline"
                    onClick={() => void k.add('focus', newRecord.focus(null))}
                  >
                    {CERT_UNTARGET}
                  </Button>
                ) : (
                  <Button
                    variant={v.offersExam ? 'outline' : 'default'}
                    onClick={() => {
                      const f = certFocus(open.c, open.id, !!focus?.strict)
                      if (f) void k.add('focus', newRecord.focus(f))
                      onClose()
                    }}
                  >
                    <Target />
                    {CERT_TARGET}
                  </Button>
                ))}
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
