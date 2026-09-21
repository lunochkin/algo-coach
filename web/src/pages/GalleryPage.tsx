import { type ReactNode, useState } from 'react'

import type { Submitted, Template } from '@/api/client'
import { AccountMenu } from '@/components/AccountMenu'
import { CodeEditor } from '@/components/CodeEditor'
import { ElapsedClock } from '@/components/ElapsedClock'
import { Loaded } from '@/components/Loaded'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import { Panel, Stat, Stats } from '@/components/Panel'
import { PickList, PickRow } from '@/components/PickRow'
import { SectionBar } from '@/components/SectionBar'
import { TemplatePanel } from '@/components/TemplatePanel'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Verdict } from '@/components/Verdict'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

const SURFACES = [
  'background',
  'foreground',
  'card',
  'popover',
  'primary',
  'secondary',
  'muted',
  'accent',
  'destructive',
  'border',
]
const VERDICTS = ['verdict-passed', 'verdict-wrong', 'verdict-timeout', 'verdict-crashed']
const CODE = ['code-keyword', 'code-name', 'code-string', 'code-number', 'code-comment']
const ROLES = [
  ['title', 'text-title'],
  ['heading', 'text-heading'],
  ['body', 'text-body'],
  ['meta', 'text-meta'],
  ['code', 'text-code font-mono'],
]
const STEPS = ['gutter', 'section', 'stack']
const WIDTHS = ['reading', 'wide', 'form']

// a record shaped like a submission's, so the verdict renders every outcome
// without a sitting behind it
const SUBMITTED: Submitted = {
  attempt: {
    id: 'a-gallery',
    user_id: 'u-4f9c2a',
    problem_id: 'p-gallery',
    finished_at: '2026-09-18T09:00:00Z',
    solved: false,
  },
  verification: {
    id: 'v-gallery',
    attempt_id: 'a-gallery',
    created_at: '2026-09-18T09:00:00Z',
    cap_ms: 2000,
    runner: 'container/cpython-3.14',
    results: [
      { case_id: 'c1', outcome: 'passed', elapsed_ms: 3 },
      { case_id: 'c2', outcome: 'passed', elapsed_ms: 4 },
      { case_id: 'c3', outcome: 'wrong', elapsed_ms: 5 },
      { case_id: 'c4', outcome: 'timeout' },
      { case_id: 'c5', outcome: 'crashed', error: "TypeError: 'int' object is not iterable" },
    ],
  },
  failure: {
    case_id: 'c3',
    outcome: 'wrong',
    args: [[1, 4, 1, 1], 8],
    expected: 3,
    returned: 4,
    error: null,
  },
}

const NOTHING = { retry: () => {} }

// a template shaped like a card's, so the panel hides and reveals a real form
const TEMPLATE: Template = {
  id: 't-gallery',
  slug: 'lower-bound',
  title: 'Lower bound',
  trigger: 'The first index whose value is **not less** than a target.',
  notes: 'The half-open interval is what keeps the two ends comparable.',
  optional: false,
  speedup: true,
  kind: 'code',
  code:
    'def solve(xs: list[int], target: int) -> int:\n' +
    '    lo, hi = 0, len(xs)\n' +
    '    while lo < hi:\n' +
    '        mid = (lo + hi) // 2\n' +
    '        if xs[mid] < target:\n' +
    '            lo = mid + 1\n' +
    '        else:\n' +
    '            hi = mid\n' +
    '    return lo\n',
  unordered: false,
  cases: [],
}

const SECTIONS = [
  { id: 'gallery-brief', label: 'The brief' },
  { id: 'gallery-templates', label: 'The templates' },
  { id: 'gallery-ladder', label: 'The ladder' },
]

// every token and every component the pages read, on one page: a token edited
// in `index.css` reaches eight pages, and this page shows each use at once
export function GalleryPage() {
  return (
    <div className="space-y-section">
      <PageHeader
        title="The gallery"
        note="Served in development alone. pages.md gives the design system this page shows."
      />

      <Section title="Colour">
        <Swatches names={SURFACES} />
        <Swatches names={VERDICTS} />
        <Swatches names={CODE} />
      </Section>

      <Section title="Type">
        {ROLES.map(([role, size]) => (
          <p key={role} className={size}>
            <span className="text-meta text-muted-foreground">{role} </span>
            The canonical displays the template&rsquo;s form.
          </p>
        ))}
      </Section>

      <Section title="Spacing">
        {STEPS.map((step) => (
          <div key={step} className="flex items-center gap-2">
            <span className="w-20 text-meta text-muted-foreground">{step}</span>
            <div className="h-4 bg-accent" style={{ width: `var(--spacing-${step})` }} />
          </div>
        ))}
      </Section>

      <Section title="Width">
        {WIDTHS.map((width) => (
          <div key={width} className="flex items-center gap-2">
            <span className="w-20 text-meta text-muted-foreground">{width}</span>
            <div
              className="h-2 bg-accent"
              style={{ width: `min(100%, var(--container-${width}))` }}
            />
          </div>
        ))}
      </Section>

      <Section title="Press">
        <div className="flex flex-wrap items-center gap-2">
          <Button>Start the sitting</Button>
          <Button variant="secondary">Reveal the form</Button>
          <Button variant="outline">Pause</Button>
          <Button variant="ghost">Hide</Button>
          <Button variant="link">binary-search</Button>
          <Button size="sm" variant="outline">
            Retry
          </Button>
          <Button disabled>Running…</Button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">optional</Badge>
          <Badge variant="outline">procedure</Badge>
        </div>
      </Section>

      <Section title="Answer">
        <div className="flex items-center gap-2">
          <Checkbox id="gallery-claim" />
          <Label htmlFor="gallery-claim">binary-search</Label>
        </div>
        <ToggleGroup type="single" variant="outline">
          <ToggleGroupItem value="guess">guess</ToggleGroupItem>
          <ToggleGroupItem value="leaning">leaning</ToggleGroupItem>
          <ToggleGroupItem value="sure">sure</ToggleGroupItem>
        </ToggleGroup>
        <RadioGroup>
          <div className="flex items-center gap-2">
            <RadioGroupItem id="gallery-mode-gap" value="gap" />
            <Label htmlFor="gallery-mode-gap" className="gap-2">
              <span className="font-mono">gap</span>
              <span className="text-muted-foreground">I did not hold the form</span>
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem id="gallery-mode-rust" value="rust" />
            <Label htmlFor="gallery-mode-rust" className="gap-2">
              <span className="font-mono">rust</span>
              <span className="text-muted-foreground">I held the form and did not reach it</span>
            </Label>
          </div>
        </RadioGroup>
      </Section>

      <Section title="The navigation's right">
        {/* the two the shell ends on. The menu reads `/api/me`, so it names
            the signed-in user rather than a sample */}
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <AccountMenu />
        </div>
      </Section>

      <Section title="A list of picks">
        <PickList>
          <PickRow
            to="/gallery"
            title="Smallest feasible speed"
            badge={<Badge variant="outline">medium</Badge>}
            stats={[
              { label: 'attempts', value: 2 },
              { label: 'solved', value: '1/2' },
              { label: 'last', value: '6d ago' },
            ]}
          />
          <PickRow
            to="/gallery"
            title="Monotonic stack"
            stats={[{ label: 'attempts', value: 0 }]}
          />
        </PickList>
      </Section>

      <Section title="A panel of counts">
        <Panel>
          <Stats>
            <Stat value={48} label="problems" />
            <Stat value={14} label="techniques" />
            <Stat value="1/2" label="solved" />
          </Stats>
        </Panel>
      </Section>

      <Section title="A long page's sections">
        <JumpBar />
      </Section>

      <Section title="A template">
        <TemplatePanel template={TEMPLATE} />
      </Section>

      <Section title="The three readings">
        <Loaded of="the board" state={NOTHING}>
          {() => null}
        </Loaded>
        <Loaded of="the board" state={{ ...NOTHING, error: '503 from the API' }}>
          {() => null}
        </Loaded>
        <Loaded
          of="the board"
          state={{ ...NOTHING, data: [] }}
          blank="No served problem carries a technique yet."
        >
          {() => null}
        </Loaded>
      </Section>

      <Section title="The verdict">
        <Verdict submitted={SUBMITTED} />
      </Section>

      <Section title="The clock">
        {/* frozen, so the reading needs no moment to count on from */}
        <ElapsedClock elapsedSec={724} receivedAt={0} running={false} />
      </Section>

      <Section title="Prose">
        <Markdown>
          {'Return the **smallest** speed `k` such that every pile is eaten within `h` hours.'}
        </Markdown>
      </Section>

      <Section title="The editor">
        <div className="h-64">
          <CodeEditor
            initial={'def solve(piles: list[int], h: int) -> int:\n    # the form\n    return 0\n'}
            onChange={() => {}}
            onSubmit={() => {}}
          />
        </div>
      </Section>
    </div>
  )
}

// the bar is stateful on a card page, and the state is the reading it shows
function JumpBar() {
  const [current, setCurrent] = useState<string | null>(SECTIONS[0].id)

  return <SectionBar items={SECTIONS} current={current} onJump={setCurrent} />
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-stack border-t pt-4">
      <h2 className="text-heading font-medium">{title}</h2>
      {children}
    </section>
  )
}

function Swatches({ names }: { names: string[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {names.map((name) => (
        <div key={name} className="w-32 space-y-1">
          <div
            className="h-10 rounded-md border"
            // the raw variable, not `--color-*`: `@theme inline` resolves a
            // token into the utility and emits no custom property for it
            style={{ background: `var(--${name})` }}
          />
          <span className="text-meta text-muted-foreground">{name}</span>
        </div>
      ))}
    </div>
  )
}
