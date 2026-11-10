import { router, useLocalSearchParams } from 'expo-router';
import { Fragment, useMemo, useRef, type ReactNode } from 'react';
import { ScrollView, View, type ScrollViewInstance, type TextStyle } from 'react-native';
import { useMarkdown } from 'react-native-marked';
import { Appbar, Button, Chip, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  lessonsAround,
  minutesOf,
  sections,
  type Course,
  type Lesson,
  lessonNote,
  LESSON_MARK_READ,
  LESSON_MARK_UNREAD,
  LESSON_MISSING,
  LESSON_NEXT,
  LESSON_NO_TEXT,
  LESSON_RELATED,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { BottomBar, styles } from '@/ui/common';
import { CodeRenderer, markdownOptions } from '@/ui/markdown';

/** `lesson:` links stay in the app. */
class LessonRenderer extends CodeRenderer {
  constructor(
    private readonly onLesson: (ref: string) => void,
    private readonly linkColor: string,
  ) {
    super();
  }

  link(children: string | ReactNode[], href: string, style?: TextStyle, title?: string): ReactNode {
    if (!href.startsWith('lesson:')) return super.link(children, href, style, title);
    return (
      <Text
        accessibilityRole="link"
        onPress={() => this.onLesson(href.slice('lesson:'.length))}
        style={[style, { color: this.linkColor, textDecorationLine: 'underline' }]}
      >
        {children}
      </Text>
    );
  }
}

/** One section of a lesson, rendered without a list so the outer ScrollView can jump to it. */
function Section(props: { text: string; renderer: LessonRenderer; onY: (y: number) => void }) {
  const theme = useTheme();
  const elements = useMarkdown(props.text, markdownOptions(theme, props.renderer));
  return (
    <View onLayout={(e) => props.onY(e.nativeEvent.layout.y)}>
      {elements.map((el, i) => (
        <Fragment key={i}>{el}</Fragment>
      ))}
    </View>
  );
}

export default function LessonScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { course, slug, anchor } = useLocalSearchParams<{ course: string; slug: string; anchor?: string }>();
  const c = st.catalog?.courses.find((x) => x.slug === course);
  const lesson = c?.graph?.lesson(slug ?? '');
  const done = !!st.catalog?.lessonsDone?.has(`${course}:${slug}`);
  const body = c?.lessonBodies[slug ?? ''] ?? '';
  const parts = useMemo(() => sections(body), [body]);

  const scroll = useRef<ScrollViewInstance>(null);
  const ys = useRef(new Map<string, number>());
  const jumped = useRef(false);

  const renderer = useMemo(() => {
    const jump = (to: string) => {
      const y = ys.current.get(to);
      if (y !== undefined) scroll.current?.scrollTo({ y: Math.max(0, y - 8), animated: true });
    };
    return new LessonRenderer((ref) => {
      const [target, frag] = ref.split('#');
      if (target === slug && frag) jump(frag);
      else router.push({ pathname: '/lesson', params: { course: course ?? '', slug: target, anchor: frag ?? '' } });
    }, theme.colors.primary);
  }, [course, slug, theme.colors.primary]);

  const mark = async (status: 'done' | 'undone') => {
    if (!course || !slug) return;
    await st.setLessonState(course, slug, status);
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={lesson?.title ?? 'Lesson'} />
      </Appbar.Header>
      {lesson && c ? (
        <Text
          variant="labelMedium"
          style={{ color: theme.colors.onSurfaceVariant, paddingHorizontal: 16, paddingBottom: 8 }}
        >
          {lessonNote(c.title, body ? minutesOf(lesson, body) : null, done)}
        </Text>
      ) : null}
      {!lesson || !c ? (
        <Text style={{ padding: 16 }}>{LESSON_MISSING}</Text>
      ) : body ? (
        <ScrollView ref={scroll} contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 128 }}>
          {parts.map((p, i) => (
            <Section
              key={i}
              text={p.text}
              renderer={renderer}
              onY={(y) => {
                if (!p.anchor) return;
                ys.current.set(p.anchor, y);
                // Opened at an anchor: scroll once that section has been laid out.
                if (anchor && p.anchor === anchor && !jumped.current) {
                  jumped.current = true;
                  setTimeout(() => scroll.current?.scrollTo({ y: Math.max(0, y - 8), animated: false }), 50);
                }
              }}
            />
          ))}
          <Footer c={c} slug={slug ?? ''} />
        </ScrollView>
      ) : (
        <Text style={{ padding: 16, color: theme.colors.onSurfaceVariant }}>{LESSON_NO_TEXT}</Text>
      )}
      {lesson ? (
        <BottomBar bottom={insets.bottom}>
          <Button
            mode={done ? 'outlined' : 'contained'}
            icon={done ? 'book-remove-outline' : 'book-check-outline'}
            onPress={() => void mark(done ? 'undone' : 'done')}
            contentStyle={{ paddingVertical: 8 }}
          >
            {done ? LESSON_MARK_UNREAD : LESSON_MARK_READ}
          </Button>
        </BottomBar>
      ) : null}
    </View>
  );
}

/** "Next": lessons that need this one. "Related": other lessons teaching the same subtopic. */
function Footer({ c, slug }: { c: Course; slug: string }) {
  const theme = useTheme();
  const { next, related } = lessonsAround(c, slug);
  const row = (title: string, items: Lesson[]) =>
    items.length ? (
      <View style={{ gap: 6, marginTop: 16 }}>
        <Text variant="labelLarge" style={{ color: theme.colors.primary }}>
          {title}
        </Text>
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          {items.map((x) => (
            <Chip
              key={x.slug}
              icon="book-open-variant"
              onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug: x.slug } })}
            >
              {x.title}
            </Chip>
          ))}
        </View>
      </View>
    ) : null;
  return (
    <>
      {row(LESSON_NEXT, next)}
      {row(LESSON_RELATED, related)}
    </>
  );
}
