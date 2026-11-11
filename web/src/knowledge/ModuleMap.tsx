import { Maximize, Minus, Plus } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

import {
  certPips,
  certToOpen,
  certStates,
  cut,
  edgePaths,
  entryMark,
  layoutClusters,
  lessonNode,
  lessonPanelSub,
  lessonSlug,
  lessonView,
  levelDots,
  MAP_DIMS,
  MAP_FIT,
  MAP_LEGEND,
  MAP_LESSONS,
  MAP_READ,
  MODULE_START,
  mapLit,
  mapTitles,
  nodeView,
  subTitle,
  type Board,
  type CellState,
  type CertState,
  type Course,
  type Focus,
  type PlacedNode,
} from '@algo-coach/core'

import { Link } from 'react-router'

import { Panel } from '@/components/Panel'
import { Button } from '@/components/ui/button'
import { Toggle } from '@/components/ui/toggle'
import { CertDialog } from '@/knowledge/CertDialog'
import { lessonPath } from '@/knowledge/paths'
import type { Scope } from '@/knowledge/StartSheet'
import { cn } from '@/lib/utils'

const W = MAP_DIMS.nodeW
const H = MAP_DIMS.nodeH
const ZOOMS = [0.5, 0.75, 1, 1.25]

// progress reads in the flame, as the groups table reads it; what cannot serve
// reads muted
const DOT: Record<CellState, string> = {
  covered: 'fill-brand stroke-brand',
  open: 'fill-foreground stroke-foreground',
  locked: 'fill-muted-foreground/30 stroke-muted-foreground/50',
  empty: 'fill-none stroke-border',
}
const PIP: Record<CertState, string> = {
  earned: 'fill-brand stroke-brand',
  needs_refresh: 'fill-brand-wash stroke-brand',
  ready: 'fill-brand-deep stroke-brand-deep',
  in_progress: 'fill-foreground/60 stroke-foreground',
  locked: 'fill-muted stroke-muted-foreground/50',
  empty: 'fill-none stroke-border',
  not_certified: 'fill-none stroke-muted-foreground',
  insufficient_pool: 'fill-brand-wash stroke-brand',
}

type Props = {
  c: Course
  b: Board
  focus: Focus | null
  certExams: Parameters<typeof certStates>[2]
  onStart: (s: Scope) => void
  onAim: (topic: string, sub: string) => void
}

// a module's prerequisite graph, laid out by the core as the phone lays it out:
// `pages.md`, The structure
export function ModuleMap({ c, b, focus, certExams, onStart, onAim }: Props) {
  const [withLessons, setWithLessons] = useState(false)
  const [zoom, setZoom] = useState(2)
  const [picked, setPicked] = useState<string | null>(null)
  const box = useRef<HTMLDivElement>(null)
  const layout = useMemo(() => layoutClusters(c, c.graph!, MAP_DIMS, withLessons), [c, withLessons])
  const at = useMemo(() => new Map(layout.nodes.map((n) => [n.sub, n])), [layout])
  const states = useMemo(
    () => (c.certs ? certStates(b, c, certExams) : new Map()),
    [b, c, certExams],
  )
  const dots = useMemo(() => levelDots(b, c, layout.nodes), [b, c, layout])
  const pips = useMemo(() => certPips(c, states, layout.nodes), [c, states, layout])
  const lit = useMemo(() => mapLit(c, layout, picked, focus), [c, layout, picked, focus])
  const titles = useMemo(() => mapTitles(c), [c])
  const paths = useMemo(() => edgePaths(layout), [layout])
  const scale = ZOOMS[zoom]

  // opens on the first group with new work, as the phone's map does
  useEffect(() => {
    const first = b.frontier(c)[0]
    const n = first ? at.get(first.sub) : undefined
    const el = box.current
    if (!n || !el) return
    el.scrollLeft = (n.x + W / 2) * scale - el.clientWidth / 2
    el.scrollTop = (n.y + H / 2) * scale - el.clientHeight / 3
    // the first frame alone: a later zoom keeps the reader's place
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const on = (k: string) => !lit || lit.has(k)
  const sel = picked ? at.get(picked) : undefined

  return (
    <div className="space-y-stack">
      <div className="flex flex-wrap items-center gap-stack text-meta">
        <Legend tone={DOT.covered} label={MAP_LEGEND.covered} />
        <Legend tone={DOT.open} label={MAP_LEGEND.open} />
        <Legend tone={DOT.locked} label={MAP_LEGEND.locked} />
        <Legend tone={DOT.empty} label={MAP_LEGEND.empty} />
        <span className="flex-1" />
        {(c.graph?.lessons.length ?? 0) > 0 && (
          <Toggle
            size="sm"
            variant="outline"
            pressed={withLessons}
            onPressedChange={setWithLessons}
          >
            {MAP_LESSONS}
          </Toggle>
        )}
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Zoom out"
          disabled={zoom === 0}
          onClick={() => setZoom(zoom - 1)}
        >
          <Minus />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Zoom in"
          disabled={zoom === ZOOMS.length - 1}
          onClick={() => setZoom(zoom + 1)}
        >
          <Plus />
        </Button>
        <Button variant="ghost" size="icon-sm" aria-label={MAP_FIT} onClick={() => setZoom(0)}>
          <Maximize />
        </Button>
      </div>

      <div ref={box} className="h-[60vh] overflow-auto rounded-xl border bg-background">
        <svg
          width={layout.width * scale}
          height={layout.height * scale}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          onClick={() => setPicked(null)}
          role="img"
          aria-label={`The prerequisite map of ${c.title}`}
        >
          {layout.clusters.map((k) => (
            <g key={k.topic} opacity={on(`cluster:${k.topic}`) ? 1 : 0.35}>
              <rect
                x={k.x}
                y={k.y}
                width={k.w}
                height={k.h}
                rx={18}
                className="fill-card stroke-border"
              />
              <text x={k.x + 16} y={k.y + 22} className="fill-brand-deep text-[14px]">
                {titles.get(k.topic) ?? k.topic}
              </text>
            </g>
          ))}
          {paths.map(({ edge: e, d, dash }) => {
            const shown = on(e.from) && on(e.to)
            return (
              <path
                key={`${e.from}>${e.to}`}
                d={d}
                fill="none"
                strokeDasharray={dash?.join(' ')}
                strokeWidth={shown && lit ? 2 : 1.2}
                opacity={shown ? 0.9 : 0.12}
                className={
                  shown && lit
                    ? 'stroke-brand-deep'
                    : e.kind === 'teaches'
                      ? 'stroke-brand'
                      : 'stroke-muted-foreground'
                }
              />
            )
          })}
          {layout.nodes.map((n) => (
            <Node
              key={n.sub}
              n={n}
              c={c}
              b={b}
              title={n.kind === 'cert' ? (titles.get(n.topic) ?? n.topic) : subTitle(c, n.sub)}
              dots={dots.get(n.sub) ?? []}
              pips={pips.get(n.sub) ?? []}
              entry={layout.outside.has(n.sub)}
              picked={n.sub === picked}
              dim={!on(n.sub)}
              onPick={() => setPicked(n.sub === picked ? null : n.sub)}
            />
          ))}
        </svg>
      </div>

      {sel?.kind === 'cert' ? (
        // a certificate node opens the next certification of its scope to earn, as the phone's map does
        <CertDialog
          open={(() => {
            const id = certToOpen(c, states, sel.topic)
            return id ? { c, b, states, id } : null
          })()}
          onClose={() => setPicked(null)}
          onStart={onStart}
        />
      ) : (
        sel && <Picked n={sel} c={c} b={b} focus={focus} onStart={onStart} onAim={onAim} />
      )}
    </div>
  )
}

function Legend({ tone, label }: { tone: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <svg width={10} height={10} aria-hidden>
        <circle cx={5} cy={5} r={4} className={tone} strokeWidth={1.2} />
      </svg>
      {label}
    </span>
  )
}

function Node(props: {
  n: PlacedNode
  c: Course
  b: Board
  title: string
  dots: (CellState | null)[]
  pips: { letter: string; state: CertState; filled: boolean }[]
  entry: boolean
  picked: boolean
  dim: boolean
  onPick: () => void
}) {
  const { n, picked } = props
  const ring = picked ? 'stroke-brand-deep' : 'stroke-border'
  const select = (event: React.MouseEvent) => {
    event.stopPropagation()
    props.onPick()
  }
  const slug = lessonSlug(n.sub)
  const lesson = slug ? props.c.graph?.lesson(slug) : undefined
  return (
    <g
      opacity={props.dim ? 0.2 : 1}
      onClick={select}
      className="cursor-pointer"
      role="button"
      aria-label={n.kind === 'lesson' ? `Lesson: ${lesson?.title ?? n.sub}` : props.title}
    >
      {n.kind === 'cert' ? (
        <>
          <rect
            x={n.x}
            y={n.y}
            width={W}
            height={H}
            rx={H / 2}
            className={cn('fill-brand-wash/50', ring)}
            strokeWidth={picked ? 2.5 : 1.5}
          />
          <text x={n.x + 18} y={n.y + 22} className="fill-foreground text-[13px]">
            {cut(props.title, 20)}
          </text>
          {props.pips.map((p, i) => (
            <g key={p.letter}>
              <circle
                cx={n.x + 26 + i * 26}
                cy={n.y + H - 15}
                r={9}
                className={PIP[p.state]}
                strokeWidth={1.2}
                opacity={p.filled ? 1 : 0.6}
              />
              <text
                x={n.x + 22.5 + i * 26}
                y={n.y + H - 11}
                className="fill-foreground text-[10px]"
              >
                {p.letter}
              </text>
            </g>
          ))}
        </>
      ) : n.kind === 'lesson' ? (
        <>
          <rect
            x={n.x}
            y={n.y}
            width={W}
            height={H}
            rx={4}
            className={cn('fill-brand-wash', ring)}
            strokeWidth={picked ? 2.5 : 2}
          />
          <text x={n.x + 20} y={n.y + 22} className="fill-muted-foreground text-[12px]">
            {lesson ? lessonNode(props.b.lessonState(props.c, lesson)) : 'lesson'}
          </text>
          <text x={n.x + 20} y={n.y + 40} className="fill-foreground text-[13px]">
            {cut(lesson?.title ?? n.sub, 19)}
          </text>
        </>
      ) : (
        <>
          <rect
            x={n.x}
            y={n.y}
            width={W}
            height={H}
            rx={12}
            className={cn(picked ? 'fill-brand-wash' : 'fill-muted', ring)}
            strokeWidth={picked ? 2 : 1}
          />
          <text x={n.x + 12} y={n.y + 22} className="fill-foreground text-[13px]">
            {cut(props.title, 21)}
          </text>
          {/* the subtopic also needs subtopics of other topics, through its cluster's edge */}
          {props.entry && (
            <path
              d={entryMark(n)}
              fill="none"
              strokeWidth={2}
              className="stroke-muted-foreground"
            />
          )}
          {props.dots.map((state, i) => (
            <circle
              key={i}
              cx={n.x + 18 + i * 16}
              cy={n.y + H - 14}
              r={5}
              strokeWidth={1.2}
              className={DOT[state ?? 'empty']}
            />
          ))}
        </>
      )}
    </g>
  )
}

// what the picked node offers, as the phone's node card does
function Picked(props: {
  n: PlacedNode
  c: Course
  b: Board
  focus: Focus | null
  onStart: (s: Scope) => void
  onAim: (topic: string, sub: string) => void
}) {
  const { n, c, b } = props
  const slug = lessonSlug(n.sub)
  if (slug) {
    const v = lessonView(b, c, slug)
    if (!v) return null
    return (
      <Panel>
        <p className="font-medium">{v.title}</p>
        <p className="text-meta text-muted-foreground">{lessonPanelSub(v.state)}</p>
        <p className="text-meta">{v.teaches}</p>
        {v.needs && <p className="text-meta">{v.needs}</p>}
        {v.pretest && <p className="text-meta text-muted-foreground">{v.pretest}</p>}
        <div>
          <Button asChild size="sm">
            <Link to={lessonPath(c.slug, slug)}>{MAP_READ}</Link>
          </Button>
        </div>
      </Panel>
    )
  }
  const v = nodeView(b, c, n, props.focus)
  return (
    <Panel>
      <div>
        <p className="font-medium">{v.title}</p>
        <p className="text-meta text-muted-foreground">{v.topic}</p>
      </div>
      <div className="space-y-0.5 text-meta">
        {v.levels.map((x) => (
          <p key={x.line}>{x.line}</p>
        ))}
        {v.alsoNeeds && <p className="text-muted-foreground">{v.alsoNeeds}</p>}
        {v.unlocks && <p className="text-muted-foreground">{v.unlocks}</p>}
      </div>
      <div className="flex gap-stack">
        <Button size="sm" onClick={() => props.onStart(v.scope)}>
          {MODULE_START}
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={v.aimed}
          onClick={() => props.onAim(n.topic, n.sub)}
        >
          {v.aimLabel}
        </Button>
      </div>
    </Panel>
  )
}
