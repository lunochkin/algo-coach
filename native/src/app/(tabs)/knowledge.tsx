import { router } from 'expo-router';
import { useMemo } from 'react';
import { Pressable, View } from 'react-native';
import { Button, IconButton, TouchableRipple, useTheme } from 'react-native-paper';
import ReorderableList, { useReorderableDrag, type ReorderableListReorderEvent } from 'react-native-reorderable-list';

import {
  focusOpens,
  CERTIFICATIONS_LINK,
  type ModuleRow as ModuleRowView,
  focusLabel,
  LESSONS_LINK,
  MODULES_HEADING,
  MODULES_OF,
  NO_MODULES,
  KNOWLEDGE_NOTE,
  SYNC_NOW,
  reorderLabel,
  SECTION_KNOWLEDGE,
  moved,
  knowledgeHome,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { fromCopy, Loaded, styles, SyncBanner, SyncLine, ScreenHeader } from '@/ui/common';
import { ContinueBar, ContinueNotice, useContinue } from '@/ui/continue';
import { FocusCard } from '@/ui/focuscard';
import { AccountMenu } from '@/ui/account';
import { ModuleRow } from '@/ui/modules';
import { Heading, PanelItem, PickPanel, PickRow } from '@/ui/rows';
import { usePullSync } from '@/ui/pull';
import { radius, space } from '@/ui/tokens';

export default function Home() {
  const st = useStore();
  const pull = usePullSync();
  const theme = useTheme();
  const next = useContinue();
  const { cont, focus: focused } = next;

  const { board } = st;
  const b = useMemo(() => board(null), [board]);
  const { now, courseOrder: order } = st;
  const certExams = st.catalog?.certExams;
  const home = useMemo(() => (b ? knowledgeHome(b, order, certExams ?? [], now) : null), [b, order, certExams, now]);
  const rows = home?.rows ?? [];
  const { toRead = null, toTake: certToTake = null } = home ?? {};
  const onReorder = ({ from, to }: ReorderableListReorderEvent) => {
    void st.setCourseOrder(
      moved(
        rows.map((r) => r.c.slug),
        from,
        to,
      ),
    );
  };

  // a snapshot holding no module reads as empty, as on the web; the banner
  // above names a failed sync
  const body =
    !st.catalog || rows.length === 0 ? (
      <Loaded of={MODULES_OF} state={fromCopy(st, st.ready ? [] : null)} blank={NO_MODULES}>
        {() => null}
      </Loaded>
    ) : null;
  const header = (
    <View style={{ gap: space[3], marginBottom: space[3] }}>
      <SyncBanner sync={st.sync} />
      {/* the lessons and the certifications are steps down from the home: `pages.md`, The structure */}
      <View style={styles.row}>
        <Button compact icon="book-open-variant" onPress={() => router.push('/lessons')}>
          {LESSONS_LINK}
        </Button>
        <Button compact icon="trophy-outline" onPress={() => router.push('/certs')}>
          {CERTIFICATIONS_LINK}
        </Button>
      </View>
      {/* one scroll, in the web's order: the next steps and the focus, the acts,
          then the modules. A bar pinned over the list left the modules a sliver */}
      <View style={{ gap: space[2] }}>
        {/* the next steps the rules would take, as rows, since each opens a page */}
        {certToTake || toRead ? (
          <PickPanel>
            {certToTake ? (
              <PickRow
                title={certToTake.line}
                stats={[]}
                onPress={() => router.push({ pathname: '/certs', params: { open: certToTake.id } })}
              />
            ) : null}
            {toRead ? (
              <PickRow
                title={toRead.line}
                stats={[]}
                onPress={() =>
                  router.push({ pathname: '/lesson', params: { course: toRead.c.slug, slug: toRead.lesson.slug } })
                }
              />
            ) : null}
          </PickPanel>
        ) : null}
        {focused && cont ? (
          // the focus opens what it covers: `pages.md`, The knowledge pages
          <TouchableRipple
            onPress={() => {
              const to = focusOpens(focused);
              if ('cert' in to) router.push({ pathname: '/certs', params: { open: to.cert } });
              else router.push({ pathname: '/module', params: { course: to.module, tab: 'map' } });
            }}
            accessibilityRole="link"
            borderless
            style={{ borderRadius: radius(theme).xl }}
          >
            <FocusCard
              label={focusLabel(focused, st.catalog)}
              focus={focused}
              b={cont.b}
              queue={cont.queue}
              exams={st.catalog?.certExams ?? []}
              onClear={() => void st.setFocus(null)}
              onStrict={() => void st.setFocus({ ...focused, strict: !focused.strict })}
              onMoreNew={() => void st.raiseNew()}
            />
          </TouchableRipple>
        ) : null}
      </View>
      {body}
      {rows.length ? <Heading title={MODULES_HEADING} count={rows.length} /> : null}
    </View>
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={SECTION_KNOWLEDGE} back={null} aside={<AccountMenu />} note={[KNOWLEDGE_NOTE]} />
      <ReorderableList
        refreshControl={pull}
        data={rows}
        keyExtractor={(r) => r.c.slug}
        onReorder={onReorder}
        ListHeaderComponent={header}
        ListFooterComponent={
          <Pressable onPress={() => st.requestSync(0)} accessibilityLabel={SYNC_NOW} style={{ marginTop: space[3] }}>
            <SyncLine sync={st.sync} showError={false} />
          </Pressable>
        }
        // room under the last row for the bar over it
        contentContainerStyle={{ padding: space[4], paddingBottom: 160 }}
        renderItem={({ item, index }) => (
          <PanelItem first={index === 0} last={index === rows.length - 1}>
            <DraggedModule row={item} />
          </PanelItem>
        )}
      />
      {/* the home's act, Continue, with Exam beside it at a lower weight */}
      <ContinueBar next={next} exam />
      <ContinueNotice next={next} />
    </View>
  );
}

/** A module's row, which a long press or the handle drags to reorder. */
function DraggedModule({ row }: { row: ModuleRowView }) {
  const drag = useReorderableDrag();
  return (
    <ModuleRow
      row={row}
      onLongPress={drag}
      aside={<IconButton icon="drag" onPressIn={drag} accessibilityLabel={reorderLabel(row.c.title)} />}
    />
  );
}
