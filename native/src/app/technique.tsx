import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { readFailure, techniqueCards, techniqueStats, loadingLine } from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { CardPanel } from '@/ui/cards';
import { Failed, styles } from '@/ui/common';
import { Heading, PickPanel, PickRow } from '@/ui/rows';

/**
 * A technique's problems and the cards teaching it or a narrower one:
 * `pages.md`, The two clients. A problem's row opens the Problem screen.
 */
export default function TechniqueScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { technique = '' } = useLocalSearchParams<{ technique: string }>();
  const problems = useEngine('/api/techniques/{technique}/candidates', { technique });
  // the technique's cards, read as the cards list reads them
  const taught = useEngine('/api/techniques/{technique}/cards', { technique });
  const listed = useEngine('/api/cards');
  const error = problems.error ?? taught.error ?? listed.error;
  const [now] = useState(() => Date.now());

  const cards = techniqueCards(listed.data ?? [], taught.data ?? []);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={technique} />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        {error ? (
          <Failed
            message={readFailure('the technique', error)}
            onRetry={() => {
              problems.reload();
              taught.reload();
              listed.reload();
            }}
          />
        ) : problems.data === null || taught.data === null || listed.data === null ? (
          <Text variant="bodyMedium">{loadingLine('the technique')}</Text>
        ) : (
          <>
            {cards.length > 0 ? (
              <>
                <Heading title="Cards" count={cards.length} />
                <CardPanel technique={null} cards={cards} />
              </>
            ) : null}
            <Heading title="Problems" count={problems.data.length} />
            {problems.data.length === 0 ? (
              <Text variant="bodyMedium">No served problem carries this technique.</Text>
            ) : (
              <PickPanel>
                {problems.data.map((row) => (
                  <PickRow
                    key={row.problem_id}
                    title={row.title}
                    badge={row.difficulty}
                    stats={techniqueStats(row, now)}
                    onPress={() =>
                      router.push({ pathname: '/problem', params: { problem: row.problem_id, technique } })
                    }
                  />
                ))}
              </PickPanel>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}
