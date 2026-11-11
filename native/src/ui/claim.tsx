import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { Button, Checkbox, RadioButton, Text, useTheme } from 'react-native-paper';

import {
  attemptLine,
  CLAIM_CONFIDENCE,
  CLAIM_DECLINE,
  CLAIM_NOTE,
  CLAIM_QUESTION,
  CLAIM_TITLE,
  claimDefault,
  claimReady,
  claimRefused,
  claimToggled,
  type Confidence,
  CONFIDENCES,
  described,
  LABEL_OPTIONAL,
  LABEL_QUESTION,
  MODE_GLOSS,
  saveLabel,
  type components,
  OF,
} from '@algo-coach/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { ErrorLine, Loaded } from '@/ui/common';
import { Sheet } from '@/ui/sheet';
import { Toggle, Toggles } from '@/ui/toggle';
import { Heading } from '@/ui/rows';

type Asked = components['schemas']['Asked'];
type FailureMode = components['schemas']['FailureMode'];

/**
 * The claim a sitting ends on, as a bottom sheet: each attempt the sitting
 * minted, in the order it was submitted. Closing the sheet leaves the rest
 * to the problem's own techniques, as on the web.
 */
export function ClaimSheet({
  sittingId,
  drilled,
  visible,
  onDone,
}: {
  sittingId: string;
  drilled: string | null;
  visible: boolean;
  onDone: () => void;
}) {
  const loaded = useEngine(visible ? '/api/sittings/{sitting_id}/unclaimed' : null, { sitting_id: sittingId });
  const [answered, setAnswered] = useState(0);
  const attempts = loaded.data?.attempts ?? [];
  const finished = loaded.data !== null && answered >= attempts.length;

  useEffect(() => {
    if (visible && finished) onDone();
  }, [visible, finished, onDone]);

  const asked = attempts[answered];
  return (
    <Sheet visible={visible && !finished} onDismiss={onDone} title={CLAIM_TITLE} note={CLAIM_NOTE}>
      {!loaded.data || !asked ? (
        <Loaded of={OF.claim} state={{ ...loaded, data: null }}>
          {() => null}
        </Loaded>
      ) : (
        <ClaimForm
          // a fresh form per attempt, so no answer carries over to the next
          key={asked.attempt.id}
          asked={asked}
          position={attemptLine(answered, attempts.length, asked.attempt)}
          techniques={loaded.data.techniques}
          drilled={drilled}
          onClaimed={() => setAnswered(answered + 1)}
        />
      )}
    </Sheet>
  );
}

function ClaimForm({
  asked,
  position,
  techniques,
  drilled,
  onClaimed,
}: {
  asked: Asked;
  position: string;
  techniques: string[];
  drilled: string | null;
  onClaimed: () => void;
}) {
  const theme = useTheme();
  const { origin } = useStore().settings;
  const [chosen, setChosen] = useState<string[]>(() => claimDefault(drilled, techniques));
  const [declined, setDeclined] = useState(false);
  const [confidence, setConfidence] = useState<Confidence | null>(null);
  const [mode, setMode] = useState<FailureMode | null>(null);
  const [sending, setSending] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const id = asked.attempt.id;

  // the claim first, since naming the techniques is what the label then asks
  // about. A mode nobody picked sends no second request
  async function send() {
    if (!confidence) return;
    setSending(true);
    setRefused(null);
    try {
      const client = engine(origin, await getToken());
      const claimed = await client.POST('/api/attempts/{attempt_id}/claims', {
        params: { path: { attempt_id: id } },
        body: { techniques: chosen, declined, confidence },
      });
      if (!claimed.data) return setRefused(described(claimed.error));
      if (mode) {
        const labelled = await client.POST('/api/attempts/{attempt_id}/labels', {
          params: { path: { attempt_id: id } },
          body: { mode },
        });
        if (!labelled.data) return setRefused(described(labelled.error));
      }
      onClaimed();
    } catch (reason) {
      setRefused(String(reason));
    } finally {
      setSending(false);
    }
  }

  return (
    <View style={{ gap: 12 }}>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {position}
      </Text>
      <Heading sub title={CLAIM_QUESTION} />
      <View>
        {techniques.map((technique) => (
          <Checkbox.Item
            key={technique}
            label={technique}
            mode="android"
            position="leading"
            labelStyle={{ textAlign: 'left' }}
            disabled={declined}
            status={chosen.includes(technique) ? 'checked' : 'unchecked'}
            onPress={() => setChosen(claimToggled(chosen, technique))}
          />
        ))}
        <Checkbox.Item
          label={CLAIM_DECLINE}
          mode="android"
          position="leading"
          labelStyle={{ textAlign: 'left' }}
          status={declined ? 'checked' : 'unchecked'}
          onPress={() => {
            // a decline clears the ticks rather than hiding them, so undoing
            // it starts from nothing
            setDeclined(!declined);
            if (!declined) setChosen([]);
          }}
        />
      </View>
      <Heading sub title={CLAIM_CONFIDENCE} />
      <Toggles>
        {CONFIDENCES.map((one) => (
          <Toggle key={one} on={confidence === one} onPress={() => setConfidence(one)}>
            {one}
          </Toggle>
        ))}
      </Toggles>
      {asked.modes.length > 0 ? (
        <>
          <Heading sub title={LABEL_QUESTION} />
          <RadioButton.Group value={mode ?? ''} onValueChange={(value) => setMode(value as FailureMode)}>
            {asked.modes.map((one) => (
              <RadioButton.Item
                key={one}
                value={one}
                mode="android"
                position="leading"
                label={`${one} · ${MODE_GLOSS[one]}`}
                labelStyle={{ textAlign: 'left' }}
              />
            ))}
          </RadioButton.Group>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {LABEL_OPTIONAL}
          </Text>
        </>
      ) : null}
      {refused ? <ErrorLine>{claimRefused(refused)}</ErrorLine> : null}
      <Button
        mode="contained"
        onPress={() => void send()}
        disabled={!claimReady(chosen, declined, confidence) || sending}
      >
        {saveLabel(sending)}
      </Button>
    </View>
  );
}
