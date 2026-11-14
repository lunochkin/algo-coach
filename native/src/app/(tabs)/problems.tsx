import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Button, Text, useTheme } from 'react-native-paper';

import {
  clearFilters,
  listingHeading,
  listingView,
  NO_FILTER,
  PAGE_NEXT,
  PAGE_PREVIOUS,
  pageOf,
  PROBLEMS_NONE,
  PROBLEMS_NONE_MATCH,
  PROBLEMS_NOTE,
  PROBLEMS_TITLE,
  techniqueStats,
  toggled,
  type ListingFilter,
  OF,
  techniquesLine,
} from '@climb/core';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { Loaded, styles, ScreenHeader } from '@/ui/common';
import { Heading, PickPanel, PickRow } from '@/ui/rows';
import { Toggle } from '@/ui/toggle';
import { usePullSync } from '@/ui/pull';
import { space } from '@/ui/tokens';

/**
 * Every served problem, filtered by technique and difficulty, as the web's
 * listing: `pages.md`, Sections. A row opens the Problem screen.
 */
export default function ProblemsScreen() {
  const theme = useTheme();
  const listed = useEngine('/api/problems');
  const pull = usePullSync(listed.reload);
  const [filter, setFilter] = useState<ListingFilter>(NO_FILTER);
  const [now] = useState(() => Date.now());
  const muted = { color: theme.colors.onSurfaceVariant };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={PROBLEMS_TITLE} back={null} aside={<AccountMenu />} />
      <ScrollView refreshControl={pull} contentContainerStyle={[styles.page, { paddingBottom: space[6] }]}>
        <Text variant="bodyMedium" style={muted}>
          {PROBLEMS_NOTE}
        </Text>
        <Loaded of={OF.problems} state={listed} blank={PROBLEMS_NONE}>
          {(data) => {
            const view = listingView(data, filter);
            return (
              <>
                {(
                  [
                    ['difficulties', view.difficulties],
                    ['techniques', view.tags],
                  ] as const
                ).map(([kind, chips]) => (
                  <View key={kind} style={[styles.row, { flexWrap: 'wrap' }]}>
                    {chips.map((chip) => (
                      <Toggle key={chip.name} on={chip.on} onPress={() => setFilter(toggled(filter, kind, chip.name))}>
                        {`${chip.name} ${chip.count}`}
                      </Toggle>
                    ))}
                  </View>
                ))}
                <Heading
                  title={listingHeading(view.filtered)}
                  count={view.shown}
                  aside={
                    view.filtered ? (
                      <Button compact onPress={() => setFilter(NO_FILTER)}>
                        {clearFilters(filter)}
                      </Button>
                    ) : null
                  }
                />
                {view.shown === 0 ? (
                  <Text variant="bodyMedium" style={muted}>
                    {PROBLEMS_NONE_MATCH}
                  </Text>
                ) : (
                  <PickPanel>
                    {view.rows.map((row) => (
                      <PickRow
                        key={row.problem_id}
                        title={row.title}
                        badge={row.difficulty}
                        stats={techniqueStats(row, now)}
                        note={techniquesLine(row.techniques)}
                        mono
                        // the one tag the listing is filtered to is the technique drilled
                        onPress={() =>
                          router.push({
                            pathname: '/problem',
                            // `from` names the listing, so the sitting's way back names it
                            params: view.drilled
                              ? { problem: row.problem_id, technique: view.drilled, from: 'problems' }
                              : { problem: row.problem_id, from: 'problems' },
                          })
                        }
                      />
                    ))}
                  </PickPanel>
                )}
                {view.pages > 1 ? (
                  <View style={[styles.row, { justifyContent: 'center' }]}>
                    <Button
                      mode="outlined"
                      compact
                      disabled={view.page === 1}
                      onPress={() => setFilter({ ...filter, page: view.page - 1 })}
                    >
                      {PAGE_PREVIOUS}
                    </Button>
                    <Text variant="bodySmall" style={muted}>
                      {pageOf(view.page, view.pages)}
                    </Text>
                    <Button
                      mode="outlined"
                      compact
                      disabled={view.page === view.pages}
                      onPress={() => setFilter({ ...filter, page: view.page + 1 })}
                    >
                      {PAGE_NEXT}
                    </Button>
                  </View>
                ) : null}
              </>
            );
          }}
        </Loaded>
      </ScrollView>
    </View>
  );
}
