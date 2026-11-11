import { ScrollView, View } from 'react-native';
import { Appbar, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { cardBlocks, inProgress, notInProgress, readFailure, type components, loadingLine } from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { CardPanel, Heading } from '@/ui/cards';
import { Failed, styles } from '@/ui/common';

type ListedCard = components['schemas']['ListedCard'];

/** The cards, grouped by family as the web's list groups them: `pages.md`, A page's areas. */
export default function CardsScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const cards = useEngine('/api/cards');

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
          <Text variant="bodyMedium">{loadingLine('the cards')}</Text>
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
  const rest = notInProgress(cards);
  return (
    <>
      {studying.length > 0 ? (
        <>
          <Heading title="Studying" count={studying.length} />
          <CardPanel technique={null} cards={studying} />
        </>
      ) : null}
      {rest.length > 0 && studying.length > 0 ? <Heading title="Not started" count={rest.length} /> : null}
      {cardBlocks(rest).map((block) => (
        <CardPanel key={block.technique ?? block.cards[0].slug} technique={block.technique} cards={block.cards} />
      ))}
    </>
  );
}
