import { type ReactNode, useCallback, useRef, useState } from 'react';
import {
  type HostInstance,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  ScrollView,
  type ScrollViewInstance,
  View,
} from 'react-native';
import { useTheme } from 'react-native-paper';

import { sectionOpened, sectionToggled } from '@algo-coach/core';
import { Heading, Panel } from '@/ui/rows';
import { Toggle } from '@/ui/toggle';

export interface Item {
  id: string;
  label: string;
}

/**
 * A long screen's sections, as the web's `useSections` holds them: which the
 * reader closed, the one they are in, and a jump that opens a section before
 * scrolling to it. Positions are measured against the scroll view, so a
 * section nested in other views reads the same. `register` names any view a
 * jump can reach, a lesson's `###` anchors included.
 */
export function useSections(items: Item[]) {
  const scroll = useRef<ScrollViewInstance>(null);
  const views = useRef(new Map<string, HostInstance>());
  const offset = useRef(0);
  const last = useRef(0);
  const trailing = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [closed, setClosed] = useState<string[]>([]);
  const [current, setCurrent] = useState<string | null>(null);

  const at = useCallback(
    (id: string) =>
      new Promise<number | null>((resolve) => {
        const view = views.current.get(id);
        const host = scroll.current;
        if (!view || !host) return resolve(null);
        view.measureLayout(
          host as never,
          (_x: number, y: number) => resolve(y),
          () => resolve(null),
        );
      }),
    [],
  );

  const ids = items.map((item) => item.id).join(',');
  const mark = useCallback(async () => {
    const named = ids ? ids.split(',') : [];
    const ys = await Promise.all(named.map(at));
    // the section whose heading sits above the top fifth of the screen
    let found: string | null = named[0] ?? null;
    ys.forEach((y, i) => {
      if (y !== null && y <= offset.current + 120) found = named[i];
    });
    setCurrent(found);
  }, [ids, at]);

  const onScroll = useCallback(
    (e: NativeSyntheticEvent<NativeScrollEvent>) => {
      offset.current = e.nativeEvent.contentOffset.y;
      // throttled, with a trailing mark so the last position always reads
      if (trailing.current) clearTimeout(trailing.current);
      trailing.current = setTimeout(() => void mark(), 150);
      const now = Date.now();
      if (now - last.current < 120) return;
      last.current = now;
      void mark();
    },
    [mark],
  );

  const jump = useCallback(
    (id: string, animated = true) => {
      setClosed((was) => sectionOpened(was, id));
      if (ids.split(',').includes(id)) setCurrent(id);
      // a closed section lays out its body on the next frame
      requestAnimationFrame(
        () =>
          void at(id).then((y) => {
            if (y !== null) scroll.current?.scrollTo({ y: Math.max(0, y - 8), animated });
          }),
      );
    },
    [at, ids],
  );

  const register = useCallback(
    (id: string) => (view: HostInstance | null) => {
      if (view) views.current.set(id, view);
      else views.current.delete(id);
    },
    [],
  );

  return {
    items,
    current,
    scroll,
    onScroll,
    jump,
    register,
    closed: (id: string) => closed.includes(id),
    toggle: (id: string) => setClosed((was) => sectionToggled(was, id)),
  };
}

export type Sections = ReturnType<typeof useSections>;

/**
 * The sections of a long screen in one row under its header, which stays in
 * place as the screen scrolls. One section has nothing to jump between.
 */
export function SectionBar({ sections }: { sections: Pick<Sections, 'items' | 'current' | 'jump'> }) {
  const theme = useTheme();
  if (sections.items.length < 2) return null;
  return (
    <View style={{ borderBottomWidth: 1, borderColor: theme.colors.outlineVariant }}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 6, paddingHorizontal: 16, paddingVertical: 8 }}
      >
        {sections.items.map((item) => (
          <Toggle key={item.id} on={sections.current === item.id} onPress={() => sections.jump(item.id)}>
            {item.label}
          </Toggle>
        ))}
      </ScrollView>
    </View>
  );
}

/**
 * One section of a long screen: its heading closes it, and its body sits in
 * a bordered panel where it is prose, or bare where it brings panels of its own.
 */
export function PageSection(props: {
  of: Sections;
  id: string;
  title: string;
  count?: number;
  aside?: ReactNode;
  body?: 'prose' | 'bare';
  children: ReactNode;
}) {
  const closed = props.of.closed(props.id);
  return (
    <View ref={props.of.register(props.id)} collapsable={false} style={{ gap: 8 }}>
      <Heading
        title={props.title}
        count={props.count}
        aside={props.aside}
        closed={closed}
        onToggle={() => props.of.toggle(props.id)}
      />
      {closed ? null : props.body === 'bare' ? (
        props.children
      ) : (
        <Panel style={{ paddingHorizontal: 12, paddingVertical: 4 }}>{props.children}</Panel>
      )}
    </View>
  );
}
