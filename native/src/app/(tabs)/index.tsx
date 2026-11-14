import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Text, TouchableRipple, useTheme } from 'react-native-paper';
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
  BOARD_NEXT,
  JUDGE_NOTE,
  JUDGE_TITLE,
  boardMoreCards,
  nextCards,
  BOARD_UNTOUCHED,
  BOARD_PRACTISED,
  BOARD_NOTE,
  MODULES_HEADING,
  focusLabel,
  orderedModuleRows,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { AccountMenu } from '@/ui/account';
import { CardPanel } from '@/ui/cards';
import { Loaded, styles, ScreenHeader } from '@/ui/common';
import { ContinueInPanel, ContinueNotice, useContinue } from '@/ui/continue';
import { FocusCard } from '@/ui/focuscard';
import { ModuleRow } from '@/ui/modules';
import { Heading, Panel, PickPanel, PickRow } from '@/ui/rows';
import { usePullSync } from '@/ui/pull';
import { radius } from '@/ui/tokens';

type Board = components['schemas']['Board'];
type ListedCard = components['schemas']['ListedCard'];

const open = (technique: string) => router.push({ pathname: '/technique', params: { technique } });

/** The board, as the web's: the cards in progress, then the techniques by staleness. */
export default function PracticeScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const st = useStore();
  const next = useContinue();
  // the knowledge modules, from the device's copy: the board is the overview
  // of every study, `pages.md`, Sections
  const { board: learner, courseOrder, now } = st;
  const all = useMemo(() => learner(null), [learner]);
  const modules = useMemo(() => (all ? orderedModuleRows(all, courseOrder, now) : []), [all, now, courseOrder]);
  useEffect(() => {
    // the app opens on Login until it holds a token, and returns there on sign-out
    if (st.ready && !st.hasToken) router.replace('/login');
  }, [st.ready, st.hasToken]);

  const board = useEngine('/api/board');
  const cards = useEngine('/api/cards');
  const pull = usePullSync(board.reload, cards.reload);
  // the cards in progress only add to the board, so a failed list reads as none, as on the web
  const error = board.error;
  const cardsIn = cards.data !== null || cards.error !== null;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={BOARD_TITLE} back={null} aside={<AccountMenu />} />
      <ScrollView refreshControl={pull} contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 32 }]}>
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
            style={{ borderRadius: radius(theme).xl }}
          >
            <FocusCard
              label={focusLabel(next.focus, st.catalog)}
              focus={next.focus}
              b={next.cont.b}
              queue={next.cont.queue}
              exams={st.catalog?.certExams ?? []}
              footer={<ContinueInPanel next={next} inFocus />}
            />
          </TouchableRipple>
        ) : modules.length > 0 ? (
          <Panel padded>
            <ContinueInPanel next={next} />
          </Panel>
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
            data: board.data && cardsIn ? { board: board.data, cards: cards.data ?? [] } : null,
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
      <ContinueNotice next={next} />
    </View>
  );
}

function BoardBody({ board, cards }: { board: Board; cards: ListedCard[] }) {
  const theme = useTheme();
  const [now] = useState(() => Date.now());
  const { untouched, practised, foot } = boardView(board);
  const studying = inProgress(cards);
  const next = nextCards(cards);
  return (
    <>
      {studying.length > 0 ? (
        <>
          <Heading title={BOARD_STUDYING} count={studying.length} />
          <CardPanel technique={null} cards={studying} />
        </>
      ) : null}
      {/* the short exercise, across every card: `pages.md`, Judging */}
      <Panel>
        <PickRow title={JUDGE_TITLE} note={JUDGE_NOTE} stats={[]} onPress={() => router.push('/judge')} />
      </Panel>
      {next.cards.length > 0 ? (
        <>
          <Heading title={BOARD_NEXT} count={next.cards.length + next.more} />
          <CardPanel technique={null} cards={next.cards} />
          {next.more > 0 ? (
            <Text
              variant="bodySmall"
              accessibilityRole="link"
              onPress={() => router.navigate('/cards')}
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              {boardMoreCards(next.more)}
            </Text>
          ) : null}
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
