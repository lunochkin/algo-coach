import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  techniqueCards,
  techniqueStats,
  OF,
  TECHNIQUE_CARDS,
  TECHNIQUE_PROBLEMS,
  TECHNIQUE_NONE,
} from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { CardPanel } from '@/ui/cards';
import { Blank, Loaded, styles } from '@/ui/common';
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
        <Loaded
          of={OF.technique}
          state={{
            data: problems.data && taught.data && listed.data ? problems.data : null,
            error,
            reload: () => {
              problems.reload();
              taught.reload();
              listed.reload();
            },
          }}
        >
          {(rows) => (
            <>
              {cards.length > 0 ? (
                <>
                  <Heading title={TECHNIQUE_CARDS} count={cards.length} />
                  <CardPanel technique={null} cards={cards} />
                </>
              ) : null}
              <Heading title={TECHNIQUE_PROBLEMS} count={rows.length} />
              {rows.length === 0 ? (
                <Blank>{TECHNIQUE_NONE}</Blank>
              ) : (
                <PickPanel>
                  {rows.map((row) => (
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
        </Loaded>
      </ScrollView>
    </View>
  );
}
