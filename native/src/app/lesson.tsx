import { router, useLocalSearchParams } from 'expo-router';
import { cloneElement, Fragment, isValidElement, useMemo, useRef, useState, type ReactElement, type ReactNode } from 'react';
import { ScrollView, View, type ScrollViewInstance, type TextStyle, type ViewStyle } from 'react-native';
import { Renderer, useMarkdown, type MarkedStyles } from 'react-native-marked';
import { Appbar, Button, Chip, Menu, Text, useTheme, type MD3Theme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { minutesOf, sections, type Course } from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { BottomBar, CodeBlock, styles } from '@/ui/common';

const CODE_SCALE = 0.85;

interface InlineCodeProps {
  text: string;
  style: TextStyle;
  size: number;
}

function InlineCode({ text, style, size }: InlineCodeProps) {
  return (
    <Text selectable style={[style, { fontSize: size }]}>
      {text}
    </Text>
  );
}

/** Code blocks in the app's monospace block (no wrapping); `lesson:` links stay in the app. */
class LessonRenderer extends Renderer {
  constructor(
    private readonly onLesson: (ref: string) => void,
    private readonly linkColor: string,
  ) {
    super();
  }

  code(text: string, _language?: string, _container?: ViewStyle, _style?: TextStyle): ReactNode {
    return <CodeBlock code={text} verbatim />;
  }

  // Monospace looks larger than body text at the same size: scale it to the surrounding text.
  codespan(text: string, style?: TextStyle): ReactNode {
    const { fontSize: _fs, lineHeight: _lh, ...rest } = style ?? {};
    return <InlineCode key={this.getKey()} text={text} style={rest} size={CODE_SCALE * 16} />;
  }

  heading(children: string | ReactNode[], style?: TextStyle): ReactNode {
    const size = CODE_SCALE * (style?.fontSize ?? 16);
    const scaled = Array.isArray(children)
      ? children.map((x) => (isValidElement(x) && x.type === InlineCode ? cloneElement(x as ReactElement<InlineCodeProps>, { size }) : x))
      : children;
    return super.heading(scaled, style);
  }

  link(children: string | ReactNode[], href: string, style?: TextStyle, title?: string): ReactNode {
    if (!href.startsWith('lesson:')) return super.link(children, href, style, title);
    return (
      <Text
        accessibilityRole="link"
        onPress={() => this.onLesson(href.slice('lesson:'.length))}
        style={[style, { color: this.linkColor, textDecorationLine: 'underline' }]}>
        {children}
      </Text>
    );
  }
}

function markdownStyles(theme: MD3Theme): MarkedStyles {
  return {
    h1: { ...theme.fonts.headlineSmall, color: theme.colors.onSurface, marginVertical: 8 },
    h2: { ...theme.fonts.titleLarge, color: theme.colors.onSurface, marginVertical: 6 },
    h3: { ...theme.fonts.titleMedium, color: theme.colors.onSurface, marginVertical: 4 },
    text: { ...theme.fonts.bodyLarge, color: theme.colors.onSurface },
    li: { ...theme.fonts.bodyLarge, color: theme.colors.onSurface },
    codespan: { fontFamily: 'monospace', fontStyle: 'normal', backgroundColor: theme.colors.surfaceVariant },
  };
}

/** One section of a lesson, rendered without a list so the outer ScrollView can jump to it. */
function Section(props: { text: string; renderer: LessonRenderer; onY: (y: number) => void }) {
  const theme = useTheme();
  const elements = useMarkdown(props.text, {
    renderer: props.renderer,
    styles: markdownStyles(theme),
    theme: {
      colors: {
        text: theme.colors.onSurface,
        link: theme.colors.primary,
        code: theme.colors.surfaceVariant,
        border: theme.colors.outlineVariant,
      },
    },
  });
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
  const [menu, setMenu] = useState(false);
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
    if (status === 'done') router.back();
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={lesson?.title ?? 'Lesson'} />
        {lesson && body ? (
          <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant, marginRight: 8 }}>
            {`~${minutesOf(lesson, body)} min`}
          </Text>
        ) : null}
        {done ? (
          <Menu
            visible={menu}
            onDismiss={() => setMenu(false)}
            anchor={<Appbar.Action icon="dots-vertical" onPress={() => setMenu(true)} accessibilityLabel="More" />}>
            <Menu.Item
              leadingIcon="book-refresh-outline"
              title="Mark as unread"
              onPress={() => {
                setMenu(false);
                void mark('undone');
              }}
            />
          </Menu>
        ) : null}
      </Appbar.Header>
      {!lesson || !c ? (
        <Text style={{ padding: 16 }}>This lesson is not in the current courses.</Text>
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
        <Text style={{ padding: 16, color: theme.colors.onSurfaceVariant }}>
          This lesson's text is not in the course snapshot yet; sync after the laptop publishes it.
        </Text>
      )}
      {lesson ? (
        <BottomBar bottom={insets.bottom}>
          <Button
            mode="contained"
            icon={done ? 'check' : 'book-check-outline'}
            disabled={done}
            onPress={() => void mark('done')}
            contentStyle={{ paddingVertical: 8 }}>
            {done ? 'Done' : 'Done reading'}
          </Button>
        </BottomBar>
      ) : null}
    </View>
  );
}

/** "Next": lessons that need this one. "Related": other lessons teaching the same subtopic. */
function Footer({ c, slug }: { c: Course; slug: string }) {
  const theme = useTheme();
  const all = c.graph?.lessons ?? [];
  const me = all.find((x) => x.slug === slug);
  if (!me) return null;
  const next = all.filter((x) => x.needs.includes(`lesson:${slug}`));
  const subs = new Set(me.teaches.map(([s]) => s));
  const related = all.filter((x) => x.slug !== slug && !next.includes(x) && x.teaches.some(([s]) => subs.has(s)));
  const row = (title: string, items: typeof all) =>
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
              onPress={() => router.push({ pathname: '/lesson', params: { course: c.slug, slug: x.slug } })}>
              {x.title}
            </Chip>
          ))}
        </View>
      </View>
    ) : null;
  return (
    <>
      {row('Next', next)}
      {row('Related', related)}
    </>
  );
}
