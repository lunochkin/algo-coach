import { LogOut, Smartphone } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import {
  setting,
  SETTING_RANGE,
  validSetting,
  type SettingName,
  type SettingRecord,
} from '@algo-coach/core'

import { named } from '@/api/account'
import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { Panel } from '@/components/Panel'
import { SignedInApps } from '@/components/SignedInApps'
import { SignOut } from '@/components/SignOut'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { linesOf, loadedFrom, useKnowledge } from '@/knowledge/context'

// the phone's Study settings, read in the phone's order: `pages.md`, Sections
const STUDY: { name: SettingName; label: string }[] = [
  { name: 'new_per_day', label: 'New questions per day' },
  { name: 'exam_size', label: 'Exam size' },
]

type Values = Record<SettingName, number>

export function SettingsPage() {
  const k = useKnowledge()
  const records = linesOf<SettingRecord>(k.records, 'setting')
  const values = Object.fromEntries(STUDY.map(({ name }) => [name, setting(records, name)])) as Values
  // held here: a save remounts the fields, and the line saying so outlives them
  const [said, setSaid] = useState<string | null>(null)

  return (
    <section className="space-y-section">
      <PageHeader title="Settings" note="The study settings hold on every device you sign in on." />
      <Account />
      <Loaded of="the settings" state={loadedFrom(k, values)}>
        {/* a value another device set reaches the fields at its sync */}
        {(values) => <Study key={JSON.stringify(values)} stored={values} said={said} onSaid={setSaid} />}
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
          <SignOut>
            {(start) => (
              <Button variant="outline" onClick={start}>
                <LogOut />
                Sign out
              </Button>
            )}
          </SignOut>
        </div>
      </Panel>
      <SignedInApps open={apps} onOpenChange={setApps} />
    </section>
  )
}

type StudyProps = { stored: Values; said: string | null; onSaid: (said: string | null) => void }

function Study({ stored, said, onSaid: setSaid }: StudyProps) {
  const { add } = useKnowledge()
  const [typed, setTyped] = useState(() => texts(stored))

  const values = Object.fromEntries(STUDY.map(({ name }) => [name, Number(typed[name])])) as Values
  const valid = STUDY.every(({ name }) => validSetting(name, values[name]))
  const changed = STUDY.filter(({ name }) => values[name] !== stored[name])

  async function save() {
    for (const { name } of changed) await add('setting', { name, n: values[name] })
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
