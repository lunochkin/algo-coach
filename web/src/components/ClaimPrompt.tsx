import { useEffect, useState } from 'react'

import { api, type Attempt } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { duration } from '@/lib/format'

type Confidence = 'guess' | 'leaning' | 'sure'

type Props = {
  sittingId: string
  // the technique the problem was picked by: the default answer, since
  // selection chose the problem for it
  drilled: string | null
  onDone: () => void
}

// asked of every attempt the sitting minted, in the order they were submitted:
// the attempts a claim skips are left to the problem's own techniques
export function ClaimPrompt({ sittingId, drilled, onDone }: Props) {
  const { data, error } = useLoaded(
    (signal) =>
      api.GET('/api/sittings/{sitting_id}/unclaimed', {
        params: { path: { sitting_id: sittingId } },
        signal,
      }),
    `unclaimed:${sittingId}`,
  )
  const [answered, setAnswered] = useState(0)
  const attempts = data?.attempts ?? []
  const finished = data !== undefined && answered >= attempts.length

  useEffect(() => {
    if (finished) onDone()
  }, [finished, onDone])

  if (error) return <p className="text-destructive">The claim did not load: {error}</p>
  if (!data || finished) return <p className="text-muted-foreground">Loading the claim…</p>

  const attempt = attempts[answered]
  return (
    <ClaimForm
      // a fresh form per attempt, so no answer carries over to the next
      key={attempt.id}
      attempt={attempt}
      position={`Attempt ${answered + 1} of ${attempts.length}`}
      techniques={data.techniques}
      drilled={drilled}
      onClaimed={() => setAnswered(answered + 1)}
    />
  )
}

type FormProps = {
  attempt: Attempt
  position: string
  techniques: string[]
  drilled: string | null
  onClaimed: () => void
}

function ClaimForm({ attempt, position, techniques, drilled, onClaimed }: FormProps) {
  const [chosen, setChosen] = useState<string[]>(
    drilled && techniques.includes(drilled) ? [drilled] : [],
  )
  const [declined, setDeclined] = useState(false)
  const [confidence, setConfidence] = useState<Confidence | null>(null)
  const [sending, setSending] = useState(false)
  const [refused, setRefused] = useState<string | null>(null)
  const answers = declined || chosen.length > 0

  async function send() {
    if (!confidence) return
    setSending(true)
    setRefused(null)
    try {
      const { data, error } = await api.POST('/api/attempts/{attempt_id}/claims', {
        params: { path: { attempt_id: attempt.id } },
        body: { techniques: declined ? [] : chosen, declined, confidence },
      })
      if (data) onClaimed()
      else setRefused(described(error))
    } catch (reason) {
      setRefused(String(reason))
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">
        {position} · {attempt.solved ? 'solved' : 'not solved'}
        {attempt.time_to_solve_sec != null && ` · ${duration(attempt.time_to_solve_sec)}`}
      </p>

      <fieldset className="space-y-2">
        <legend className="mb-2 font-medium">Which techniques did this code use?</legend>
        {techniques.map((technique) => (
          <div key={technique} className="flex items-center gap-2">
            <Checkbox
              id={`claim-${technique}`}
              checked={!declined && chosen.includes(technique)}
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
            onCheckedChange={(checked) => setDeclined(checked === true)}
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

      {refused && <p className="text-destructive">The claim was refused: {refused}</p>}
      <Button onClick={send} disabled={!answers || !confidence || sending}>
        {sending ? 'Saving…' : 'Save the claim'}
      </Button>
    </div>
  )
}
