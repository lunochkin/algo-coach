import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { View } from 'react-native';
import { Button, Snackbar, Text, TouchableRipple, useTheme } from 'react-native-paper';

import {
  CONTINUE,
  continueOffered,
  continueCounts,
  continueLine,
  continuePlan,
  emptyContinue,
  EXAM_LINK,
  NEW_STEP,
  queueStart,
  waitingOutside,
  continueAct,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { BottomBar, startQueue, styles, Press } from '@/ui/common';
import { radius, space } from '@/ui/tokens';

/**
 * The knowledge study's next step, the same on Practice and on Knowledge:
 * the queue Continue would open, its counts, and the press starting it, or
 * the notice saying why nothing is ready with the one act that changes that.
 */
export function useContinue() {
  const st = useStore();
  const { board, focus, newLimit, now } = st;
  const cont = useMemo(() => continuePlan(board, focus, null, newLimit), [board, focus, newLimit]);
  const counts = useMemo(() => (cont ? continueCounts(cont, focus, now) : null), [cont, focus, now]);
  const [notice, setNotice] = useState('');
  const [action, setAction] = useState<{ label: string; run: () => void } | null>(null);

  const start = () => {
    if (!cont || !counts) return;
    if (counts.empty) {
      const empty = emptyContinue({ blocked: counts.blocked, newLimit, focus });
      setNotice(empty.notice);
      const act = empty.action;
      const run = () => {
        if (!act) return;
        const step = continueAct(act.kind);
        if (step.raise) {
          void st.raiseNew();
          cont.queue.raise(NEW_STEP);
        }
        if (step.clearFocus) void st.setFocus(null);
        if (step.open === 'queue') startQueue(st, 'next', cont.queue, cont.course, cont.include);
        else if (step.open === 'certs') router.push('/certs');
      };
      setAction(act && { label: act.label, run });
      return;
    }
    startQueue(st, 'next', cont.queue, cont.course, cont.include);
  };

  /** The reviews waiting outside a strict focus: a plain review queue over every served module. */
  const reviewOutside = () => {
    const review = queueStart('review', null, st);
    if (review) startQueue(st, 'review', review.queue, review.course, review.include);
  };

  const clear = () => {
    setNotice('');
    setAction(null);
  };
  return { cont, counts, focus, start, reviewOutside, notice, action, clear, ready: continueOffered(counts) };
}

export type Next = ReturnType<typeof useContinue>;

/**
 * Continue in the bar at the bottom, with its counts above it, as the
 * knowledge home holds it. The home adds Exam beside it, at a lower weight: `pages.md`, A page's areas.
 */
export function ContinueBar({ next, exam = false }: { next: Next; exam?: boolean }) {
  return (
    <BottomBar bottom={0} row above={<CountsLine next={next} />}>
      {exam ? (
        <Press
          mode="contained-tonal"
          icon="clipboard-check-outline"
          disabled={!next.ready}
          onPress={() => router.push('/exam')}
        >
          {EXAM_LINK}
        </Press>
      ) : null}
      <Press icon="play" style={{ flex: 1 }} disabled={!next.ready} onPress={next.start}>
        {CONTINUE}
      </Press>
    </BottomBar>
  );
}

/** What Continue serves, with the press serving the reviews a strict focus leaves out. */
// `bare` drops the counts the focus card already reads, and keeps the press
// serving the reviews a strict focus leaves out
function CountsLine({ next, bare = false, start = false }: { next: Next; bare?: boolean; start?: boolean }) {
  const theme = useTheme();
  const { counts, focus } = next;
  if (!counts || (bare && counts.outside === 0)) return null;
  return (
    <View style={[styles.row, { justifyContent: start ? 'flex-start' : 'center', flexWrap: 'wrap', minHeight: 24 }]}>
      {bare ? null : (
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {continueLine(counts, !!focus?.strict)}
        </Text>
      )}
      {counts.outside > 0 ? (
        <TouchableRipple
          onPress={next.reviewOutside}
          borderless
          accessibilityRole="link"
          accessibilityLabel={waitingOutside(counts.outside)}
          style={{
            minHeight: 48,
            justifyContent: 'center',
            paddingHorizontal: space[1],
            borderRadius: radius(theme).lg,
          }}
        >
          <Text variant="bodySmall" style={{ color: theme.colors.primary, textDecorationLine: 'underline' }}>
            {bare ? waitingOutside(counts.outside) : ` · ${waitingOutside(counts.outside)}`}
          </Text>
        </TouchableRipple>
      ) : null}
    </View>
  );
}

/**
 * Continue inside the focus's panel, as the board holds it: the board names
 * several studies, so its bottom bar holds no press. `pages.md`, Sections.
 */
export function ContinueInPanel({ next, inFocus = false }: { next: Next; inFocus?: boolean }) {
  return (
    <View style={{ gap: space[1] }}>
      {/* a panel press reads at a lower weight than a page's act */}
      <Button
        mode="contained-tonal"
        icon="play"
        style={{ alignSelf: 'flex-start' }}
        disabled={!next.ready}
        onPress={next.start}
      >
        {CONTINUE}
      </Button>
      <CountsLine next={next} bare={inFocus} start />
    </View>
  );
}

/** Why Continue found nothing ready, above the bar, with its one act. */
export function ContinueNotice({ next }: { next: Next }) {
  return (
    <Snackbar
      visible={!!next.notice}
      onDismiss={next.clear}
      duration={next.action ? 6000 : 2500}
      action={next.action ? { label: next.action.label, onPress: next.action.run } : undefined}
      wrapperStyle={{ bottom: 160 }}
    >
      {next.notice}
    </Snackbar>
  );
}
