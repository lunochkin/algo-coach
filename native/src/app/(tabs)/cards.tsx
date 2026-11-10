import { router } from 'expo-router';
import { Fragment, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Card, Divider, ProgressBar, Text, TouchableRipple, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { cardBlocks, cardRow, inProgress, readFailure, type components, type RecallMark } from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { Failed, styles, tones } from '@/ui/common';

type ListedCard = components['schemas']['ListedCard'];

/** The cards, grouped by family as the web's list groups them: `pages.md`, A page's areas. */
export default function CardsScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const cards = useEngine<ListedCard[]>('/cards');

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Content title="Cards" />
        <AccountMenu />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          One card teaches one technique: when to reach for it, and the forms to reproduce from memory.
        </Text>
        {cards.error ? (
          <Failed message={readFailure('the cards', cards.error)} onRetry={cards.reload} />
        ) : cards.data === null ? (
          <Text variant="bodyMedium">Reading the cards…</Text>
        ) : cards.data.length === 0 ? (
          <Text variant="bodyMedium">No card is seeded yet.</Text>
        ) : (
          <Listing cards={cards.data} />
        )}
      </ScrollView>
    </View>
  );
}

function Listing({ cards }: { cards: ListedCard[] }) {
  const studying = inProgress(cards);
  const rest = cards.filter((card) => !card.status.started_at);
  return (
    <>
      {studying.length > 0 ? (
        <>
          <Heading title="Studying" count={studying.length} />
          <Panel technique={null} cards={studying} />
        </>
      ) : null}
      {rest.length > 0 && studying.length > 0 ? <Heading title="Not started" count={rest.length} /> : null}
      {cardBlocks(rest).map((block) => (
        <Panel key={block.technique ?? block.cards[0].slug} technique={block.technique} cards={block.cards} />
      ))}
    </>
  );
}

function Heading({ title, count }: { title: string; count: number }) {
  const theme = useTheme();
  return (
    <Text variant="titleMedium" style={{ marginTop: 8 }}>
      {title} <Text style={{ color: theme.colors.onSurfaceVariant }}>{count}</Text>
    </Text>
  );
}

function Panel({ technique, cards }: { technique: string | null; cards: ListedCard[] }) {
  const theme = useTheme();
  const [now] = useState(() => Date.now());
  return (
    <Card mode="outlined">
      {technique ? (
        <>
          <View style={[styles.row, { paddingHorizontal: 16, paddingVertical: 12 }]}>
            <Text variant="titleSmall" style={{ fontFamily: 'monospace', flex: 1 }}>
              {technique}
            </Text>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {cards.length} cards
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
              accessibilityLabel={row.title}>
              <View style={{ paddingHorizontal: 16, paddingVertical: 12, gap: 4 }}>
                <View style={styles.row}>
                  <Text variant="titleMedium" style={{ flexShrink: 1 }}>
                    {row.title}
                  </Text>
                  {row.technique ? (
                    <Text variant="bodySmall" style={{ fontFamily: 'monospace', color: theme.colors.onSurfaceVariant }}>
                      {row.technique}
                    </Text>
                  ) : null}
                  <Text variant="bodySmall" style={{ marginLeft: 'auto', color: theme.colors.onSurfaceVariant }}>
                    {row.aside}
                  </Text>
                </View>
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
    </Card>
  );
}

function Marks({ marks }: { marks: RecallMark[] }) {
  const theme = useTheme();
  const tone = (one: RecallMark) =>
    one.tone === 'passed' ? tones(theme.dark).done : one.tone === 'wrong' ? theme.colors.error : theme.colors.onSurfaceVariant;
  return (
    <Text
      variant="bodySmall"
      style={{ color: theme.colors.onSurfaceVariant }}
      accessibilityLabel={`recall: ${marks.map((one) => `${one.title}, ${one.reading}`).join('; ')}`}>
      recall{' '}
      {marks.map((one) => (
        <Text key={one.templateId} style={{ fontFamily: 'monospace', color: tone(one) }}>
          {one.mark}{' '}
        </Text>
      ))}
    </Text>
  );
}
