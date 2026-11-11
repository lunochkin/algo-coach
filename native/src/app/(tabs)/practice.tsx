import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Card, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { boardView, inProgress, techniqueStats, type components } from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { CardPanel } from '@/ui/cards';
import { Loaded, styles } from '@/ui/common';
import { Heading, PickPanel, PickRow } from '@/ui/rows';

type Board = components['schemas']['Board'];
type ListedCard = components['schemas']['ListedCard'];

const open = (technique: string) => router.push({ pathname: '/technique', params: { technique } });

/** The board, as the web's: the cards in progress, then the techniques by staleness. */
export default function PracticeScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const board = useEngine('/api/board');
  const cards = useEngine('/api/cards');
  const error = board.error ?? cards.error;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Content title="Practice" />
        <AccountMenu />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          Continue a card in progress, or pick a technique, stalest first.
        </Text>
        <Loaded
          of="the board"
          state={{
            data: board.data && cards.data ? { board: board.data, cards: cards.data } : null,
            error,
            reload: () => {
              board.reload();
              cards.reload();
            },
          }}
          blank="No served problem carries a technique yet."
          blankWhen={(x) => x.board.rows.length === 0}
        >
          {(x) => <BoardBody board={x.board} cards={x.cards} />}
        </Loaded>
      </ScrollView>
    </View>
  );
}

function BoardBody({ board, cards }: { board: Board; cards: ListedCard[] }) {
  const theme = useTheme();
  const [now] = useState(() => Date.now());
  const { untouched, practised, foot } = boardView(board);
  const studying = inProgress(cards);
  return (
    <>
      {studying.length > 0 ? (
        <>
          <Heading title="Cards in progress" count={studying.length} />
          <CardPanel technique={null} cards={studying} />
        </>
      ) : null}
      {untouched.length > 0 ? (
        <>
          <Heading title="Techniques not practised yet" count={untouched.length} />
          <Card mode="outlined">
            <Card.Content style={{ flexDirection: 'row', flexWrap: 'wrap', columnGap: 20, rowGap: 8 }}>
              {untouched.map((row) => (
                <Text
                  key={row.technique}
                  variant="bodyLarge"
                  accessibilityRole="link"
                  onPress={() => open(row.technique)}
                  style={{ color: theme.colors.primary }}
                >
                  {row.technique}
                </Text>
              ))}
            </Card.Content>
          </Card>
        </>
      ) : null}
      {practised.length > 0 ? (
        <>
          <Heading title="Techniques practised" count={practised.length} />
          <PickPanel>
            {practised.map((row) => (
              <PickRow
                key={row.technique}
                title={row.technique}
                stats={techniqueStats(row, now)}
                onPress={() => open(row.technique)}
              />
            ))}
          </PickPanel>
        </>
      ) : null}
      {foot ? (
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {foot}
        </Text>
      ) : null}
    </>
  );
}
