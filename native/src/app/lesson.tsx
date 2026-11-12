import { router, useLocalSearchParams } from 'expo-router';
import { cloneElement, Fragment, isValidElement, useEffect, useMemo, type ReactElement, type ReactNode } from 'react';
import { type HostInstance, ScrollView, View, type TextStyle } from 'react-native';
import { useMarkdown } from 'react-native-marked';
import { Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  lessonParts,
  lessonsAround,
  sections,
  type Course,
  type Lesson,
  LESSON_MARK_READ,
  LESSON_MARK_UNREAD,
  LESSON_MISSING,
  LESSON_NEXT,
  LESSON_NO_TEXT,
  LESSON_RELATED,
  OF,
  lessonPage,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { Blank, BottomBar, fromCopy, Loaded, styles, Press, ScreenHeader } from '@/ui/common';
import { BLOCK_GAP, CodeRenderer, InlineCode, type InlineCodeProps, markdownOptions } from '@/ui/markdown';
import { Heading } from '@/ui/rows';
import { PageSection, type Sections, SectionBar, useSections } from '@/ui/sections';
import { space } from '@/ui/tokens';

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
    const linked: TextStyle = { color: this.linkColor, textDecorationLine: 'underline' };
    // inline code carries its own style, so it would not read as part of the link
    const parts = Array.isArray(children)
      ? children.map((x) =>
          isValidElement(x) && x.type === InlineCode
            ? cloneElement(x as ReactElement<InlineCodeProps>, {
                style: { ...(x as ReactElement<InlineCodeProps>).props.style, ...linked },
              })
            : x,
        )
      : children;
    return (
      <Text
        key={this.getKey()}
        accessibilityRole="link"
        onPress={() => this.onLesson(href.slice('lesson:'.length))}
        style={[style, linked]}
      >
        {parts}
      </Text>
    );
  }
}

/** A stretch of a lesson, rendered without a list so the outer ScrollView can jump to it. */
function Chunk(props: { text: string; renderer: LessonRenderer; at: (view: HostInstance | null) => void }) {
  const theme = useTheme();
  const elements = useMarkdown(props.text, markdownOptions(theme, props.renderer));
  return (
    <View ref={props.at} collapsable={false} style={{ gap: BLOCK_GAP }}>
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
    <View style={{ gap: BLOCK_GAP }}>
      {chunks.map((chunk, i) => (
        <Chunk
          key={i}
          text={chunk.text}
          renderer={props.renderer}
          at={chunk.anchor ? props.of.register(chunk.anchor) : () => {}}
        />
      ))}
    </View>
  );
}

export default function LessonScreen() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { course, slug, anchor } = useLocalSearchParams<{ course: string; slug: string; anchor?: string }>();
  const { c, x: lesson, body, read: done, title, note } = lessonPage(st.catalog, course ?? '', slug ?? '');
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
    // Mark read returns where the lesson was opened from: `pages.md`
    if (status === 'done') {
      if (router.canGoBack()) router.back();
      else router.replace('/lessons');
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={title} note={[note]} />
      {!lesson || !c ? (
        <View style={styles.page}>
          <Loaded
            of={OF.lesson}
            state={fromCopy(st, st.catalog ? { lesson } : null)}
            blank={LESSON_MISSING}
            blankWhen={(x) => !x.lesson}
          >
            {() => null}
          </Loaded>
        </View>
      ) : body ? (
        <>
          <SectionBar sections={sections} />
          <ScrollView
            ref={sections.scroll}
            onScroll={sections.onScroll}
            onScrollBeginDrag={sections.onScrollBeginDrag}
            scrollEventThrottle={32}
            contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 128 }]}
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
        // a lesson with no text yet still names the lessons around it, as the web does
        <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 128 }]}>
          <Blank>{LESSON_NO_TEXT}</Blank>
          <Footer c={c} slug={slug ?? ''} />
        </ScrollView>
      )}
      {lesson ? (
        <BottomBar bottom={insets.bottom}>
          <Press
            mode={done ? 'outlined' : 'contained'}
            icon={done ? 'book-remove-outline' : 'book-check-outline'}
            onPress={() => void mark(done ? 'undone' : 'done')}
          >
            {done ? LESSON_MARK_UNREAD : LESSON_MARK_READ}
          </Press>
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
      <View style={{ gap: space[1.5], marginTop: space[4] }}>
        <Heading sub title={title} />
        {/* destinations, so links rather than chips: a chip is a control */}
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', columnGap: 16, rowGap: 6 }}>
          {items.map((x) => (
            <Text
              key={x.slug}
              variant="bodyMedium"
              accessibilityRole="link"
              onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug: x.slug } })}
              style={{ color: theme.colors.primary }}
            >
              {x.title}
            </Text>
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
