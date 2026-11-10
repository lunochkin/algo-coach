import { LogOut, Smartphone } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import {
  setting,
  SETTING_RANGE,
  validSetting,
  type SettingName,
  type SettingRecord,
} from '@algo-coach/core/settings'

import { api } from '@/api/client'
import { linesOf, readLog, sendLines, type Cursor } from '@/api/log'
import { useLoaded } from '@/api/useLoaded'
import { named, signOut } from '@/api/account'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { SignedInApps } from '@/components/SignedInApps'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

// the phone's Study settings, read in the phone's order: `pages.md`, Sections
const STUDY: { name: SettingName; label: string }[] = [
  { name: 'new_per_day', label: 'New questions per day' },
  { name: 'exam_size', label: 'Exam size' },
]

type Values = Record<SettingName, number>

async function load(signal: AbortSignal) {
  const log = await readLog(signal)
  if (log.data === undefined) return { error: log.error }
  const records = linesOf<SettingRecord>(log.data.records, 'setting')
  const values = Object.fromEntries(STUDY.map(({ name }) => [name, setting(records, name)])) as Values
  return { data: { values, cursor: log.data.cursor } }
}

export function SettingsPage() {
  const loaded = useLoaded(load, 'settings')

  return (
    <section className="space-y-section">
      <PageHeader title="Settings" note="The study settings hold on every device you sign in on." />
      <Account />
      <Loaded of="the settings" state={loaded}>
        {({ values, cursor }) => <Study saved={values} cursor={cursor} />}
      </Loaded>
    </section>
  )
}

function Heading({ children }: { children: ReactNode }) {
  return <h2 className="text-heading font-medium">{children}</h2>
}

function Account() {
  const me = useLoaded((signal) => api.GET('/api/me', { signal }), 'me')
  const [apps, setApps] = useState(false)

  return (
    <section className="space-y-stack">
      <Heading>Account</Heading>
      <Panel>
        <div className="flex flex-wrap items-center gap-stack">
          <div className="flex-1">
            <p className="font-medium">{named(me.data)}</p>
            {me.data?.email && (
              <p className="font-mono text-meta text-muted-foreground">{me.data.user_id}</p>
            )}
          </div>
          <Button variant="outline" onClick={() => setApps(true)}>
            <Smartphone />
            Signed-in apps
          </Button>
          <Button variant="outline" onClick={() => void signOut()}>
            <LogOut />
            Sign out
          </Button>
        </div>
      </Panel>
      <SignedInApps open={apps} onOpenChange={setApps} />
    </section>
  )
}

function Study({ saved, cursor }: { saved: Values; cursor: Cursor }) {
  const [stored, setStored] = useState(saved)
  const [typed, setTyped] = useState(() => texts(saved))
  // the reply then carries only what was written since the page loaded
  const [since, setSince] = useState(cursor)
  const [said, setSaid] = useState<string | null>(null)

  const values = Object.fromEntries(STUDY.map(({ name }) => [name, Number(typed[name])])) as Values
  const valid = STUDY.every(({ name }) => validSetting(name, values[name]))
  const changed = STUDY.filter(({ name }) => values[name] !== stored[name])

  async function save() {
    const lines = changed.map(({ name }) => ({ kind: 'setting', name, n: values[name] }))
    const next = await sendLines(lines, since)
    if (next === null) return setSaid('Not saved: the engine did not answer.')
    setSince(next)
    setStored(values)
    setSaid('Saved.')
  }

  return (
    <section className="space-y-stack">
      <Heading>Study</Heading>
      <Panel>
        {STUDY.map(({ name, label }) => {
          const [low, high] = SETTING_RANGE[name]
          const ok = validSetting(name, values[name])
          return (
            <div key={name} className="flex flex-wrap items-center gap-stack">
              <Label htmlFor={name} className="flex-1">
                {label}
              </Label>
              <Input
                id={name}
                inputMode="numeric"
                className="w-24 tabular-nums"
                value={typed[name]}
                aria-invalid={!ok}
                aria-describedby={`${name}-range`}
                onChange={(event) => {
                  setTyped({ ...typed, [name]: event.target.value })
                  setSaid(null)
                }}
              />
              <span id={`${name}-range`} className="w-20 text-meta text-muted-foreground">
                {low} to {high}
              </span>
            </div>
          )
        })}
        <div className="flex items-center gap-stack">
          <Button disabled={!valid || changed.length === 0} onClick={() => void save()}>
            Save
          </Button>
          {said && <span className="text-meta text-muted-foreground">{said}</span>}
        </div>
      </Panel>
    </section>
  )
}

function texts(values: Values): Record<SettingName, string> {
  return Object.fromEntries(STUDY.map(({ name }) => [name, String(values[name])])) as Record<
    SettingName,
    string
  >
}
