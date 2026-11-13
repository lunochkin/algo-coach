import { router } from 'expo-router';
import { Fragment, useState } from 'react';
import { Divider, Text, useTheme } from 'react-native-paper';

import {
  cardNeeds,
  cardRow,
  type components,
  type RecallMark,
  cardsCounted,
  RECALL_MARKS,
  RUNGS_SOLVED,
  recallMarkLabel,
} from '@algo-coach/core';
import { tones } from '@/ui/common';
import { Panel, PanelStrip, PickRow } from '@/ui/rows';
import { font } from '@/ui/tokens';

type ListedCard = components['schemas']['ListedCard'];

// one card reads as one row wherever it is listed: `pages.md`, A page's areas

/**
 * A panel of card rows, headed by the family several of them teach, which the
 * strip opens. Given `graph`, each row names the cards it requires: the web
 * draws those edges, and the phone's column has no room for them.
 */
export function CardPanel({
  technique,
  cards,
  graph,
}: {
  technique: string | null;
  cards: ListedCard[];
  graph?: ListedCard[];
}) {
  const theme = useTheme();
  const [now] = useState(() => Date.now());
  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <Panel>
      {technique ? (
        <PanelStrip onPress={() => router.push({ pathname: '/technique', params: { technique } })}>
          <Text variant="titleSmall" style={{ fontFamily: font.mono, flex: 1 }}>
            {technique}
          </Text>
          <Text variant="bodySmall" style={muted}>
            {cardsCounted(cards.length)}
          </Text>
        </PanelStrip>
      ) : null}
      {cards.map((card, i) => {
        const row = cardRow(card, technique, now);
        const needs = graph ? cardNeeds(card, graph) : row.waits;
        return (
          <Fragment key={card.slug}>
            {i > 0 ? <Divider /> : null}
            <PickRow
              title={row.title}
              stats={[...(row.technique ? [{ label: '', value: row.technique }] : []), { label: '', value: row.aside }]}
              note={row.state ?? undefined}
              dim={row.waits !== null}
              onPress={() => router.push({ pathname: '/card', params: { slug: card.slug } })}
              progress={row.progress && { value: row.progress.solved, total: row.progress.rungs, label: RUNGS_SOLVED }}
            >
              {needs !== null ? (
                <Text variant="bodySmall" style={muted}>
                  {needs}
                </Text>
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
      accessibilityLabel={`${RECALL_MARKS}: ${marks.map(recallMarkLabel).join('; ')}`}
    >
      {RECALL_MARKS}
      {marks.map((one) => (
        <Text key={one.templateId}>
          {' '}
          <Text style={{ fontFamily: font.mono, color: tone(one) }}>{one.mark}</Text>
        </Text>
      ))}
    </Text>
  );
}
