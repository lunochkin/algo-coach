import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import {
  levelName,
  levels,
  START_ALL,
  START_KIND,
  START_LEVEL,
  START_NOTHING,
  START_ONLY_REVIEWS,
  startPreview,
  startTitle,
  type DrillScope,
} from '@algo-coach/core'

import { Choice } from '@/components/Choice'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { filteredQuery } from '@/knowledge/filtered'
import { useLearner } from '@/knowledge/learner'

/** Where a filtered queue starts: the module, a topic, a subtopic or one group. */
export type Scope = Pick<DrillScope, 'course' | 'topic' | 'sub' | 'level'>

// the sheet's choices narrow this one queue, and starting it moves no focus:
// `knowledge.md`, Queues
export function StartSheet({ scope, onClose }: { scope: Scope | null; onClose: () => void }) {
  return (
    <Dialog open={scope !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        {scope && <Choices key={JSON.stringify(scope)} scope={scope} />}
      </DialogContent>
    </Dialog>
  )
}

const ALL = 'all'

function Choices({ scope }: { scope: Scope }) {
  const { catalog, board, newLimit, now } = useLearner()
  const navigate = useNavigate()
  const [level, setLevel] = useState<number | null>(scope.level ?? null)
  const [kind, setKind] = useState<string | null>(null)
  const [due, setDue] = useState(false)
  const c = catalog?.courses.find((x) => x.slug === scope.course)
  // named explicitly, so a paused module serves too
  const b = useMemo(() => board(scope.course), [board, scope.course])
  const choices: DrillScope = { ...scope, level, kind, due }
  const preview = b ? startPreview(b, choices, newLimit, now) : null
  if (!c || !catalog) return null

  const title = startTitle(c, scope)
  return (
    <>
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
      </DialogHeader>
      <div className="space-y-stack">
        <Choice label={START_LEVEL}>
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            className="w-auto flex-wrap"
            value={level === null ? ALL : String(level)}
            onValueChange={(v) => v && setLevel(v === ALL ? null : Number(v))}
          >
            <ToggleGroupItem value={ALL}>{START_ALL}</ToggleGroupItem>
            {levels(catalog.rules).map((l) => (
              <ToggleGroupItem key={l} value={String(l)}>
                {levelName(catalog.rules, l)}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </Choice>
        {c.kinds.length > 1 && (
          <Choice label={START_KIND}>
            <ToggleGroup
              type="single"
              variant="outline"
              size="sm"
              className="w-auto flex-wrap"
              value={kind ?? ALL}
              onValueChange={(v) => v && setKind(v === ALL ? null : v)}
            >
              <ToggleGroupItem value={ALL}>{START_ALL}</ToggleGroupItem>
              {c.kinds.map((k) => (
                <ToggleGroupItem key={k} value={k}>
                  {k}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </Choice>
        )}
        <div className="flex items-center gap-2">
          <Checkbox id="only-reviews" checked={due} onCheckedChange={(on) => setDue(on === true)} />
          <Label htmlFor="only-reviews">{START_ONLY_REVIEWS}</Label>
        </div>
      </div>
      <DialogFooter>
        <Button
          disabled={!preview || preview.empty}
          onClick={() => navigate(filteredQuery(choices))}
        >
          {preview?.label ?? START_NOTHING}
        </Button>
      </DialogFooter>
    </>
  )
}
