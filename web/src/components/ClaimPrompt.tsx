import { useEffect, useState } from 'react'

import { api, type Attempt, type FailureMode } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { duration } from '@/lib/format'

type Confidence = 'guess' | 'leaning' | 'sure'

// each mode is offered as its own word beside a gloss: the word alone does not
// separate `rust` from `gap`. Which of them an attempt leaves open is the
// route's answer, since the verdict decides it
const GLOSS: Record<FailureMode, string> = {
  speed: 'I got there, slower than I should have',
  none: 'Nothing went wrong',
  gap: 'I did not hold the form',
  rust: 'I held the form and did not reach it',
  syntax: 'I slipped writing code I know',
}

type Props = {
  sittingId: string
  // the technique the problem was picked by: the default answer, since
  // selection chose the problem for it
  drilled: string | null
  onDone: () => void
}

// the claim and the label, asked of every attempt the sitting minted, in the
// order they were submitted: the attempts a claim skips are left to the
// problem's own techniques, and a skipped label leaves the attempt unlabelled
export function ClaimPrompt({ sittingId, drilled, onDone }: Props) {
  const loaded = useLoaded(
    (signal) =>
      api.GET('/api/sittings/{sitting_id}/unclaimed', {
        params: { path: { sitting_id: sittingId } },
        signal,
      }),
    `unclaimed:${sittingId}`,
  )
  const [answered, setAnswered] = useState(0)
  const data = loaded.data
  const attempts = data?.attempts ?? []
  const finished = data !== undefined && answered >= attempts.length

  useEffect(() => {
    if (finished) onDone()
  }, [finished, onDone])

  if (data === undefined || finished)
    return <Loaded of="the claim" state={loaded}>{() => null}</Loaded>

  const asked = attempts[answered]
  return (
    <ClaimForm
      // a fresh form per attempt, so no answer carries over to the next
      key={asked.attempt.id}
      attempt={asked.attempt}
      modes={asked.modes}
      position={`Attempt ${answered + 1} of ${attempts.length}`}
      techniques={data.techniques}
      drilled={drilled}
      onClaimed={() => setAnswered(answered + 1)}
    />
  )
}

type FormProps = {
  attempt: Attempt
  // the modes this attempt's verdict leaves open; none where the record
  // already answers why it went that way
  modes: FailureMode[]
  position: string
  techniques: string[]
  drilled: string | null
  onClaimed: () => void
}

function ClaimForm({ attempt, modes, position, techniques, drilled, onClaimed }: FormProps) {
  const [chosen, setChosen] = useState<string[]>(
    drilled && techniques.includes(drilled) ? [drilled] : [],
  )
  const [declined, setDeclined] = useState(false)
  const [confidence, setConfidence] = useState<Confidence | null>(null)
  const [mode, setMode] = useState<FailureMode | null>(null)
  const [sending, setSending] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)
  const answers = declined || chosen.length > 0

  // the claim first, since naming the techniques is what the label then asks
  // about. A mode nobody picked sends no second request
  async function send() {
    if (!confidence) return
    setSending(true)
    setRefused(null)
    try {
      const claimed = await api.POST('/api/attempts/{attempt_id}/claims', {
        params: { path: { attempt_id: attempt.id } },
        body: { techniques: chosen, declined, confidence },
      })
      if (!claimed.data) return setRefused(described(claimed.error))
      if (mode) {
        const labelled = await api.POST('/api/attempts/{attempt_id}/labels', {
          params: { path: { attempt_id: attempt.id } },
          body: { mode },
        })
        if (!labelled.data) return setRefused(described(labelled.error))
      }
      onClaimed()
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-5">
      <p className="text-meta text-muted-foreground">
        {position} · {attempt.solved ? 'solved' : 'not solved'}
        {attempt.time_to_solve_sec != null && ` · ${duration(attempt.time_to_solve_sec)}`}
      </p>

      <fieldset className="space-y-2">
        <legend className="mb-2 font-medium">Which techniques did this code use?</legend>
        {techniques.map((technique) => (
          <div key={technique} className="flex items-center gap-2">
            <Checkbox
              id={`claim-${technique}`}
              checked={chosen.includes(technique)}
              disabled={declined}
              onCheckedChange={(checked) =>
                setChosen(
                  checked === true
                    ? [...chosen, technique]
                    : chosen.filter((one) => one !== technique),
                )
              }
            />
            <Label htmlFor={`claim-${technique}`}>{technique}</Label>
          </div>
        ))}
        <div className="flex items-center gap-2 pt-1">
          <Checkbox
            id="claim-declined"
            checked={declined}
            onCheckedChange={(checked) => {
              // a decline clears the ticks rather than hiding them, so undoing
              // it starts from nothing instead of bringing back an earlier choice
              setDeclined(checked === true)
              if (checked === true) setChosen([])
            }}
          />
          <Label htmlFor="claim-declined">None of these</Label>
        </div>
      </fieldset>

      <div className="space-y-2">
        <p className="font-medium">How sure are you?</p>
        <ToggleGroup
          type="single"
          variant="outline"
          value={confidence ?? ''}
          onValueChange={(value) => setConfidence(value ? (value as Confidence) : null)}
        >
          <ToggleGroupItem value="guess">guess</ToggleGroupItem>
          <ToggleGroupItem value="leaning">leaning</ToggleGroupItem>
          <ToggleGroupItem value="sure">sure</ToggleGroupItem>
        </ToggleGroup>
      </div>

      {modes.length > 0 && (
        <fieldset className="space-y-2">
          <legend className="mb-2 font-medium">Why did it go that way?</legend>
          <RadioGroup value={mode ?? ''} onValueChange={(value) => setMode(value as FailureMode)}>
            {modes.map((one) => (
              <div key={one} className="flex items-center gap-2">
                <RadioGroupItem id={`label-${one}`} value={one} />
                <Label htmlFor={`label-${one}`} className="gap-2">
                  <span className="font-mono">{one}</span>
                  <span className="text-muted-foreground">{GLOSS[one]}</span>
                </Label>
              </div>
            ))}
          </RadioGroup>
          <p className="text-meta text-muted-foreground">
            Answering is optional, and a skipped label leaves the attempt unlabelled.
          </p>
        </fieldset>
      )}

      {refused && <p className="text-destructive">The answer was refused: {refused}</p>}
      <Button onClick={send} disabled={!answers || !confidence || sending}>
        {sending ? 'Saving…' : 'Save'}
      </Button>
    </div>
  )
}
