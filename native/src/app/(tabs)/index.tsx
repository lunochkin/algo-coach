import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Text, TouchableRipple, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  boardView,
  inProgress,
  techniqueStats,
  type components,
  BOARD_TITLE,
  OF,
  BOARD_NONE,
  BOARD_STUDYING,
  BOARD_UNTOUCHED,
  BOARD_PRACTISED,
  BOARD_NOTE,
  bySavedOrder,
  moduleRows,
  MODULES_HEADING,
  focusLabel,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { CardPanel } from '@/ui/cards';
import { Loaded, styles } from '@/ui/common';
import { ContinueBar, ContinueNotice, useContinue } from '@/ui/continue';
import { FocusCard } from '@/ui/focuscard';
import { ModuleRow } from '@/ui/modules';
import { Heading, Panel, PickPanel, PickRow } from '@/ui/rows';

type Board = components['schemas']['Board'];
type ListedCard = components['schemas']['ListedCard'];

const open = (technique: string) => router.push({ pathname: '/technique', params: { technique } });

/** The board, as the web's: the cards in progress, then the techniques by staleness. */
export default function PracticeScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const st = useStore();
  const [now] = useState(() => Date.now());
  const next = useContinue();
  // the knowledge modules, from the device's copy: the board is the overview
  // of every study, `pages.md`, Sections
  const { board: learner, courseOrder } = st;
  const all = useMemo(() => learner(null), [learner]);
  const modules = useMemo(
    () => (all ? bySavedOrder(moduleRows(all, now), (row) => row.c.slug, courseOrder) : []),
    [all, now, courseOrder],
  );
  useEffect(() => {
    // the app opens on Login until it holds a token, and returns there on sign-out
    if (st.ready && !st.hasToken) router.replace('/login');
  }, [st.ready, st.hasToken]);

  const board = useEngine('/api/board');
  const cards = useEngine('/api/cards');
  const error = board.error ?? cards.error;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.Content title={BOARD_TITLE} />
        <AccountMenu />
      </Appbar.Header>
      {/* room under the last row for the bar over it */}
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 160 }]}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {BOARD_NOTE}
        </Text>
        {/* the knowledge study first, from the device's copy, so it reads
            before and without the engine's answer: `pages.md`, Sections */}
        {next.focus && next.cont ? (
          <TouchableRipple
            onPress={() => router.navigate('/knowledge')}
            accessibilityRole="link"
            borderless
            style={{ borderRadius: theme.roundness * 3 }}
          >
            <FocusCard
              label={focusLabel(next.focus, st.catalog)}
              focus={next.focus}
              b={next.cont.b}
              queue={next.cont.queue}
              exams={st.catalog?.certExams ?? []}
            />
          </TouchableRipple>
        ) : null}
        {modules.length > 0 ? (
          <>
            <Heading title={MODULES_HEADING} count={modules.length} />
            <PickPanel>
              {modules.map((row) => (
                <ModuleRow key={row.c.slug} row={row} />
              ))}
            </PickPanel>
          </>
        ) : null}

        <Loaded
          of={OF.board}
          state={{
            data: board.data && cards.data ? { board: board.data, cards: cards.data } : null,
            error,
            reload: () => {
              board.reload();
              cards.reload();
            },
          }}
          blank={BOARD_NONE}
          blankWhen={(x) => x.board.rows.length === 0}
        >
          {(x) => <BoardBody board={x.board} cards={x.cards} />}
        </Loaded>
      </ScrollView>
      <ContinueBar next={next} />
      <ContinueNotice next={next} />
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
          <Heading title={BOARD_STUDYING} count={studying.length} />
          <CardPanel technique={null} cards={studying} />
        </>
      ) : null}
      {untouched.length > 0 ? (
        <>
          <Heading title={BOARD_UNTOUCHED} count={untouched.length} />
          <Panel padded style={{ flexDirection: 'row', flexWrap: 'wrap', columnGap: 20, rowGap: 8 }}>
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
          </Panel>
        </>
      ) : null}
      {practised.length > 0 ? (
        <>
          <Heading title={BOARD_PRACTISED} count={practised.length} />
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
