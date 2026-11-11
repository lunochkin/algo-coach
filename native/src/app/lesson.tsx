import { router, useLocalSearchParams } from 'expo-router';
import { Fragment, useEffect, useMemo, type ReactNode } from 'react';
import { type HostInstance, ScrollView, View, type TextStyle } from 'react-native';
import { useMarkdown } from 'react-native-marked';
import { Appbar, Button, Chip, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  lessonParts,
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
  LESSON_FALLBACK,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { BottomBar, styles } from '@/ui/common';
import { CodeRenderer, markdownOptions } from '@/ui/markdown';
import { PageSection, type Sections, SectionBar, useSections } from '@/ui/sections';

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

/** A stretch of a lesson, rendered without a list so the outer ScrollView can jump to it. */
function Chunk(props: { text: string; renderer: LessonRenderer; at: (view: HostInstance | null) => void }) {
  const theme = useTheme();
  const elements = useMarkdown(props.text, markdownOptions(theme, props.renderer));
  return (
    <View ref={props.at} collapsable={false}>
      {elements.map((el, i) => (
        <Fragment key={i}>{el}</Fragment>
      ))}
    </View>
  );
}

/** Text cut at its `###` headings, each a view a link's anchor can reach. */
function Chunks(props: { text: string; renderer: LessonRenderer; of: Sections }) {
  const chunks = useMemo(() => sections(props.text), [props.text]);
  return (
    <>
      {chunks.map((chunk, i) => (
        <Chunk
          key={i}
          text={chunk.text}
          renderer={props.renderer}
          at={chunk.anchor ? props.of.register(chunk.anchor) : () => {}}
        />
      ))}
    </>
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
  // the parts read as a long screen's sections: `pages.md`, A page's areas
  const parts = useMemo(() => lessonParts(body), [body]);
  const titled = parts.filter((part) => part.title !== null);
  const sections = useSections(titled.map((part) => ({ id: part.anchor!, label: part.title! })));
  const { jump } = sections;

  // opened at an anchor: scroll there once the text has been laid out
  useEffect(() => {
    if (!anchor) return;
    const t = setTimeout(() => jump(anchor, false), 150);
    return () => clearTimeout(t);
  }, [anchor, body, jump]);

  const renderer = useMemo(
    () =>
      new LessonRenderer((ref) => {
        const [target, frag] = ref.split('#');
        if (target === slug && frag) jump(frag);
        else router.push({ pathname: '/lesson', params: { course: course ?? '', slug: target, anchor: frag ?? '' } });
      }, theme.colors.primary),
    [course, slug, theme.colors.primary, jump],
  );

  const mark = async (status: 'done' | 'undone') => {
    if (!course || !slug) return;
    await st.setLessonState(course, slug, status);
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={lesson?.title ?? LESSON_FALLBACK} />
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
        <>
          <SectionBar sections={sections} />
          <ScrollView
            ref={sections.scroll}
            onScroll={sections.onScroll}
            scrollEventThrottle={32}
            contentContainerStyle={{ padding: 16, gap: 12, paddingBottom: insets.bottom + 128 }}
          >
            {parts.map((part, i) =>
              part.title === null ? (
                <Chunks key={i} text={part.text} renderer={renderer} of={sections} />
              ) : (
                <PageSection key={i} of={sections} id={part.anchor!} title={part.title}>
                  <Chunks text={part.text} renderer={renderer} of={sections} />
                </PageSection>
              ),
            )}
            <Footer c={c} slug={slug ?? ''} />
          </ScrollView>
        </>
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
