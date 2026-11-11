import { router } from 'expo-router';
import { Fragment, useState } from 'react';
import { Divider, ProgressBar, Text, useTheme } from 'react-native-paper';

import { cardRow, type components, type RecallMark, cardsCounted, RECALL_MARKS, RUNGS_SOLVED } from '@algo-coach/core';
import { tones } from '@/ui/common';
import { Panel, PanelStrip, PickRow } from '@/ui/rows';

type ListedCard = components['schemas']['ListedCard'];

// one card reads as one row wherever it is listed: `pages.md`, A page's areas

/** A panel of card rows, headed by the family several of them teach, which the strip opens. */
export function CardPanel({ technique, cards }: { technique: string | null; cards: ListedCard[] }) {
  const theme = useTheme();
  const [now] = useState(() => Date.now());
  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <Panel>
      {technique ? (
        <PanelStrip onPress={() => router.push({ pathname: '/technique', params: { technique } })}>
          <Text variant="titleSmall" style={{ fontFamily: 'monospace', flex: 1 }}>
            {technique}
          </Text>
          <Text variant="bodySmall" style={muted}>
            {cardsCounted(cards.length)}
          </Text>
        </PanelStrip>
      ) : null}
      {cards.map((card, i) => {
        const row = cardRow(card, technique, now);
        return (
          <Fragment key={card.slug}>
            {i > 0 ? <Divider /> : null}
            <PickRow
              title={row.title}
              stats={[...(row.technique ? [{ label: '', value: row.technique }] : []), { label: '', value: row.aside }]}
              note={row.state ?? undefined}
              onPress={() => router.push({ pathname: '/card', params: { slug: card.slug } })}
            >
              {row.progress ? (
                <ProgressBar
                  progress={row.progress.rungs === 0 ? 0 : row.progress.solved / row.progress.rungs}
                  accessibilityLabel={`${RUNGS_SOLVED}: ${row.progress.solved} / ${row.progress.rungs}`}
                  style={{ maxWidth: 240, borderRadius: 2 }}
                />
              ) : null}
              {row.trigger !== null ? (
                <Text variant="bodySmall" numberOfLines={2} style={muted}>
                  {row.trigger}
                </Text>
              ) : null}
              <Marks marks={row.recall} />
            </PickRow>
          </Fragment>
        );
      })}
    </Panel>
  );
}

function Marks({ marks }: { marks: RecallMark[] }) {
  const theme = useTheme();
  const tone = (one: RecallMark) =>
    one.tone === 'passed'
      ? tones(theme.dark).done
      : one.tone === 'wrong'
        ? theme.colors.error
        : theme.colors.onSurfaceVariant;
  return (
    <Text
      variant="bodySmall"
      style={{ color: theme.colors.onSurfaceVariant }}
      accessibilityLabel={`${RECALL_MARKS}: ${marks.map((one) => `${one.title}, ${one.reading}`).join('; ')}`}
    >
      {RECALL_MARKS}
      {marks.map((one) => (
        <Text key={one.templateId}>
          {' '}
          <Text style={{ fontFamily: 'monospace', color: tone(one) }}>{one.mark}</Text>
        </Text>
      ))}
    </Text>
  );
}
