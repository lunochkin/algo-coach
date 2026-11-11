import {
  attemptLine,
  CLAIM_CONFIDENCE,
  CLAIM_DECLINE,
  CLAIM_QUESTION,
  claimDefault,
  claimReady,
  claimRefused,
  claimToggled,
  type Confidence,
  CONFIDENCES,
  LABEL_OPTIONAL,
  LABEL_QUESTION,
  MODE_GLOSS,
  saveLabel,
  OF,
} from '@algo-coach/core'
import { useEffect, useState } from 'react'

import { api, type Attempt, type FailureMode } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Loaded } from '@/components/Loaded'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

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
    return (
      <Loaded of={OF.claim} state={loaded}>
        {() => null}
      </Loaded>
    )

  const asked = attempts[answered]
  return (
    <ClaimForm
      // a fresh form per attempt, so no answer carries over to the next
      key={asked.attempt.id}
      attempt={asked.attempt}
      modes={asked.modes}
      position={attemptLine(answered, attempts.length, asked.attempt)}
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
  const [chosen, setChosen] = useState<string[]>(() => claimDefault(drilled, techniques))
  const [declined, setDeclined] = useState(false)
  const [confidence, setConfidence] = useState<Confidence | null>(null)
  const [mode, setMode] = useState<FailureMode | null>(null)
  const [sending, setSending] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)

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
      <p className="text-meta text-muted-foreground">{position}</p>

      <fieldset className="space-y-2">
        <legend className="mb-2 font-medium">{CLAIM_QUESTION}</legend>
        {techniques.map((technique) => (
          <div key={technique} className="flex items-center gap-2">
            <Checkbox
              id={`claim-${technique}`}
              checked={chosen.includes(technique)}
              disabled={declined}
              onCheckedChange={() => setChosen(claimToggled(chosen, technique))}
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
          <Label htmlFor="claim-declined">{CLAIM_DECLINE}</Label>
        </div>
      </fieldset>

      <div className="space-y-2">
        <p className="font-medium">{CLAIM_CONFIDENCE}</p>
        <ToggleGroup
          type="single"
          variant="outline"
          value={confidence ?? ''}
          onValueChange={(value) => setConfidence(value ? (value as Confidence) : null)}
        >
          {CONFIDENCES.map((one) => (
            <ToggleGroupItem key={one} value={one}>
              {one}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      {modes.length > 0 && (
        <fieldset className="space-y-2">
          <legend className="mb-2 font-medium">{LABEL_QUESTION}</legend>
          <RadioGroup value={mode ?? ''} onValueChange={(value) => setMode(value as FailureMode)}>
            {modes.map((one) => (
              <div key={one} className="flex items-center gap-2">
                <RadioGroupItem id={`label-${one}`} value={one} />
                <Label htmlFor={`label-${one}`} className="gap-2">
                  <span className="font-mono">{one}</span>
                  <span className="text-muted-foreground">{MODE_GLOSS[one]}</span>
                </Label>
              </div>
            ))}
          </RadioGroup>
          <p className="text-meta text-muted-foreground">{LABEL_OPTIONAL}</p>
        </fieldset>
      )}

      {refused && <p className="text-destructive">{claimRefused(refused)}</p>}
      <Button onClick={send} disabled={!claimReady(chosen, declined, confidence) || sending}>
        {saveLabel(sending)}
      </Button>
    </div>
  )
}
