import { Fragment } from 'react';
import { ScrollView, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { depthSections, type components, CARDS_TITLE, OF, CARDS_NONE, CARDS_NOTE } from '@climb/core';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { CardPanel } from '@/ui/cards';
import { Heading } from '@/ui/rows';
import { Loaded, styles, ScreenHeader } from '@/ui/common';
import { usePullSync } from '@/ui/pull';

type ListedCard = components['schemas']['ListedCard'];

/** The cards by depth in the card graph, as the web's list reads them: `pages.md`, A page's areas. */
export default function CardsScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const cards = useEngine('/api/cards');
  const pull = usePullSync(cards.reload);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={CARDS_TITLE} back={null} aside={<AccountMenu />} />
      <ScrollView refreshControl={pull} contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {CARDS_NOTE}
        </Text>
        <Loaded of={OF.cards} state={cards} blank={CARDS_NONE}>
          {(data) => <Listing cards={data} />}
        </Loaded>
      </ScrollView>
    </View>
  );
}

// the card graph by depth, the roots first, as the web's list reads it; each
// row names the cards it requires where the web draws edges
function Listing({ cards }: { cards: ListedCard[] }) {
  return (
    <>
      {depthSections(cards).map((section) => (
        <Fragment key={section.depth}>
          <Heading title={section.title} count={section.cards.length} />
          <CardPanel technique={null} cards={section.cards} graph={cards} />
        </Fragment>
      ))}
    </>
  );
}
