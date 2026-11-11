import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Chip, Text, useTheme } from 'react-native-paper';

import {
  clearFilters,
  listingHeading,
  listingView,
  loadingLine,
  NO_FILTER,
  PAGE_NEXT,
  PAGE_PREVIOUS,
  pageOf,
  PROBLEMS_NONE,
  PROBLEMS_NONE_MATCH,
  PROBLEMS_NOTE,
  PROBLEMS_TITLE,
  readFailure,
  techniqueStats,
  toggled,
  type ListingFilter,
} from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { Failed, styles } from '@/ui/common';
import { Heading, PickPanel, PickRow } from '@/ui/rows';

/**
 * Every served problem, filtered by technique and difficulty, as the web's
 * listing: `pages.md`, Sections. A row opens the Problem screen.
 */
export default function ProblemsScreen() {
  const theme = useTheme();
  const listed = useEngine('/api/problems');
  const [filter, setFilter] = useState<ListingFilter>(NO_FILTER);
  const [now] = useState(() => Date.now());
  const muted = { color: theme.colors.onSurfaceVariant };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Content title={PROBLEMS_TITLE} />
        <AccountMenu />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: 24 }]}>
        <Text variant="bodyMedium" style={muted}>
          {PROBLEMS_NOTE}
        </Text>
        {listed.error ? (
          <Failed message={readFailure('the problems', listed.error)} onRetry={listed.reload} />
        ) : listed.data === null ? (
          <Text variant="bodyMedium">{loadingLine('the problems')}</Text>
        ) : listed.data.length === 0 ? (
          <Text variant="bodyMedium">{PROBLEMS_NONE}</Text>
        ) : (
          (() => {
            const view = listingView(listed.data, filter);
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
                      <Chip
                        key={chip.name}
                        compact
                        selected={chip.on}
                        showSelectedCheck={false}
                        mode={chip.on ? 'flat' : 'outlined'}
                        onPress={() => setFilter(toggled(filter, kind, chip.name))}
                      >
                        {`${chip.name} ${chip.count}`}
                      </Chip>
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
                        note={row.techniques.join(' · ')}
                        mono
                        // the one tag the listing is filtered to is the technique drilled
                        onPress={() =>
                          router.push({
                            pathname: '/problem',
                            params: view.drilled
                              ? { problem: row.problem_id, technique: view.drilled }
                              : { problem: row.problem_id },
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
          })()
        )}
      </ScrollView>
    </View>
  );
}
