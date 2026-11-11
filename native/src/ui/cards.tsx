import { router } from 'expo-router';
import { Fragment, useState } from 'react';
import { View } from 'react-native';
import { Card, Divider, ProgressBar, Text, TouchableRipple, useTheme } from 'react-native-paper';

import { cardRow, type components, type RecallMark, cardsCounted, RECALL_MARKS } from '@algo-coach/core';
import { styles, tones } from '@/ui/common';

type ListedCard = components['schemas']['ListedCard'];

// one card reads as one row wherever it is listed: `pages.md`, A page's areas

/** A panel of card rows, headed by the family several of them teach. */
export function CardPanel({ technique, cards }: { technique: string | null; cards: ListedCard[] }) {
  const theme = useTheme();
  const [now] = useState(() => Date.now());
  return (
    // one View: Card hands each direct child an `index`, which a Fragment refuses
    <Card mode="outlined">
      <View>
        {technique ? (
          <>
            <View style={[styles.row, { paddingHorizontal: 16, paddingVertical: 12 }]}>
              <Text variant="titleSmall" style={{ fontFamily: 'monospace', flex: 1 }}>
                {technique}
              </Text>
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {cardsCounted(cards.length)}
              </Text>
            </View>
            <Divider />
          </>
        ) : null}
        {cards.map((card, i) => {
          const row = cardRow(card, technique, now);
          return (
            <Fragment key={card.slug}>
              {i > 0 ? <Divider /> : null}
              <TouchableRipple
                onPress={() => router.push({ pathname: '/card', params: { slug: card.slug } })}
                accessibilityRole="link"
                accessibilityLabel={row.title}
              >
                <View style={{ paddingHorizontal: 16, paddingVertical: 12, gap: 4 }}>
                  {/* the title alone on its line: a phone is too narrow for the aside beside it */}
                  <Text variant="titleMedium">{row.title}</Text>
                  <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                    {row.technique ? <Text style={{ fontFamily: 'monospace' }}>{row.technique} · </Text> : null}
                    {row.aside}
                  </Text>
                  {row.state !== null ? (
                    <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                      {row.state}
                    </Text>
                  ) : null}
                  {row.progress ? (
                    <ProgressBar
                      progress={row.progress.rungs === 0 ? 0 : row.progress.solved / row.progress.rungs}
                      accessibilityLabel={`Rungs solved: ${row.progress.solved} of ${row.progress.rungs}`}
                      style={{ maxWidth: 240, borderRadius: 2 }}
                    />
                  ) : null}
                  {row.trigger !== null ? (
                    <Text variant="bodySmall" numberOfLines={2} style={{ color: theme.colors.onSurfaceVariant }}>
                      {row.trigger}
                    </Text>
                  ) : null}
                  <Marks marks={row.recall} />
                </View>
              </TouchableRipple>
            </Fragment>
          );
        })}
      </View>
    </Card>
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
