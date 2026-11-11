import { ScrollView, View } from 'react-native';
import { Appbar, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { cardBlocks, inProgress, notInProgress, type components } from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { CardPanel } from '@/ui/cards';
import { Heading } from '@/ui/rows';
import { Loaded, styles } from '@/ui/common';

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
        <Loaded of="the cards" state={cards} blank="No card is seeded yet.">
          {(data) => <Listing cards={data} />}
        </Loaded>
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
