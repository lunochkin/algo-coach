import { ArchiveRestore, LogOut, RefreshCw, Smartphone } from 'lucide-react'
import { useState } from 'react'

import {
  ACCOUNT,
  ARCHIVED_MODULES,
  meLine,
  named,
  RESTORE,
  SAVE,
  SAVED,
  setting,
  SETTING_LABEL,
  settingRange,
  SETTINGS,
  SIGN_OUT,
  SIGNED_IN_DEVICES,
  STUDY as STUDY_HEADING,
  STUDY_SETTINGS,
  studyForm,
  SYNC_NOW,
  syncErrorSummary,
  syncLine,
  type SettingName,
  type SettingRecord,
  waitingToSend,
  newRecord,
} from '@algo-coach/core'

import { api } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { PageHeader } from '@/components/PageHeader'
import { SectionHeading } from '@/components/SectionHeading'
import { Panel } from '@/components/Panel'
import { SignedInDevices } from '@/components/SignedInDevices'
import { SignOut } from '@/components/SignOut'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { linesOf, loadedFrom, useKnowledge } from '@/knowledge/context'
import { useLearner } from '@/knowledge/learner'
import { cn } from '@/lib/utils'

const STUDY = STUDY_SETTINGS.map((name) => ({ name, label: SETTING_LABEL[name] }))

type Values = Record<SettingName, number>

export function SettingsPage() {
  const k = useKnowledge()
  const records = linesOf<SettingRecord>(k.records, 'setting')
  const values = Object.fromEntries(
    STUDY.map(({ name }) => [name, setting(records, name)]),
  ) as Values
  // held here: a save remounts the fields, and the line saying so outlives them
  const [said, setSaid] = useState<string | null>(null)

  return (
    <section className="space-y-section">
      <PageHeader title={SETTINGS} note="The study settings hold on every device you sign in on." />
      <Account />
      <Loaded of="the settings" state={loadedFrom(k, values)}>
        {/* a value another device set reaches the fields at its sync */}
        {(values) => (
          <Study key={JSON.stringify(values)} stored={values} said={said} onSaid={setSaid} />
        )}
      </Loaded>
      <Sync />
      <Archived />
    </section>
  )
}

// the sync's state and a press to sync now, as the phone's Settings holds them
function Sync() {
  const k = useKnowledge()
  const { now } = useLearner()
  return (
    <section className="space-y-stack">
      <SectionHeading title="Sync" />
      <Panel>
        <div className="flex flex-wrap items-center gap-stack">
          <div className="flex-1 space-y-0.5">
            <p>{syncLine(k.sync, now)}</p>
            {k.outbox > 0 && (
              <p className="text-meta text-muted-foreground">{waitingToSend(k.outbox)}</p>
            )}
            {k.sync.error && !k.sync.running && (
              <p className="text-meta text-verdict-wrong" title={k.sync.error}>
                {syncErrorSummary(k.sync.error)}
              </p>
            )}
          </div>
          <Button variant="outline" disabled={k.sync.running} onClick={() => void k.resync()}>
            <RefreshCw />
            {SYNC_NOW}
          </Button>
        </div>
      </Panel>
    </section>
  )
}

// an archived module leaves every page but this one, and restoring it loses nothing
function Archived() {
  const k = useKnowledge()
  const { archived } = useLearner()
  if (!archived.length) return null
  return (
    <section className="space-y-stack">
      <SectionHeading title={ARCHIVED_MODULES} count={archived.length} />
      <ul className="divide-y rounded-xl border bg-card">
        {archived.map((c) => (
          <li key={c.slug} className="flex items-center gap-stack px-4 py-3">
            <span className="flex-1">{c.title}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void k.add('status', newRecord.status(c.slug, 'active'))}
            >
              <ArchiveRestore />
              {RESTORE}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  )
}

function Account() {
  const me = useLoaded((signal) => api.GET('/api/me', { signal }), 'me')
  const [apps, setApps] = useState(false)

  return (
    <section className="space-y-stack">
      <SectionHeading title={ACCOUNT} />
      <Panel>
        <div className="flex flex-wrap items-center gap-stack">
          <div className="flex-1">
            <p className="font-medium">{named(me.data)}</p>
            <p className={cn('text-meta text-muted-foreground', me.data?.email && 'font-mono')}>
              {meLine(me.data)}
            </p>
          </div>
          <Button variant="outline" onClick={() => setApps(true)}>
            <Smartphone />
            {SIGNED_IN_DEVICES}
          </Button>
          <SignOut>
            {(start) => (
              <Button variant="outline" onClick={start}>
                <LogOut />
                {SIGN_OUT}
              </Button>
            )}
          </SignOut>
        </div>
      </Panel>
      <SignedInDevices open={apps} onOpenChange={setApps} />
    </section>
  )
}

type StudyProps = {
  stored: Values
  said: string | null
  onSaid: (said: string | null) => void
}

function Study({ stored, said, onSaid: setSaid }: StudyProps) {
  const { add } = useKnowledge()
  const [typed, setTyped] = useState(() => texts(stored))

  const { values, ok, valid, changed } = studyForm(typed, stored)

  async function save() {
    for (const name of changed) await add('setting', { name, n: values[name] })
    setSaid(SAVED)
  }

  return (
    <section className="space-y-stack">
      <SectionHeading title={STUDY_HEADING} />
      <Panel>
        {STUDY.map(({ name, label }) => (
          <div key={name} className="flex flex-wrap items-center gap-stack">
            <Label htmlFor={name} className="flex-1">
              {label}
            </Label>
            <Input
              id={name}
              inputMode="numeric"
              className="w-24 tabular-nums"
              value={typed[name]}
              aria-invalid={!ok[name]}
              aria-describedby={`${name}-range`}
              onChange={(event) => {
                setTyped({ ...typed, [name]: event.target.value })
                setSaid(null)
              }}
            />
            <span id={`${name}-range`} className="w-20 text-meta text-muted-foreground">
              {settingRange(name)}
            </span>
          </div>
        ))}
        <div className="flex items-center gap-stack">
          <Button disabled={!valid || changed.length === 0} onClick={() => void save()}>
            {SAVE}
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
