import { cloneElement, Fragment, isValidElement, useMemo, type ReactElement, type ReactNode } from 'react';
import { Linking, View, type TextStyle, type ViewStyle } from 'react-native';
import { Renderer, useMarkdown, type MarkedStyles } from 'react-native-marked';
import { Text, useTheme, type MD3Theme } from 'react-native-paper';

import { codeWraps, EXTERNAL_HINT, EXTERNAL_MARK, isExternal } from '@algo-coach/core';

import { withMath } from '@/lib/math';
import { CodeBlock } from '@/ui/common';
import { ProseTable } from '@/ui/table';
import { font, space, textSize } from '@/ui/tokens';

const CODE_SCALE = 0.85;

// the space between two blocks of authored prose
export const BLOCK_GAP = space[4];

export interface InlineCodeProps {
  text: string;
  style: TextStyle;
  size: number;
}

export function InlineCode({ text, style, size }: InlineCodeProps) {
  return (
    <Text selectable style={[style, { fontSize: size }]}>
      {text}
    </Text>
  );
}

const soft = (text: string | ReactNode[]) => (typeof text === 'string' ? text.replace(/\n/g, ' ') : text);

/** Code blocks in the app's monospace block, wrapped by the language the fence names. */
export class CodeRenderer extends Renderer {
  code(text: string, language?: string, _container?: ViewStyle, _style?: TextStyle): ReactNode {
    return <CodeBlock key={this.getKey()} code={text} verbatim wrap={codeWraps(language)} flush />;
  }

  // a grid where the columns fit, a block per row otherwise, never scrolled sideways
  table(header: ReactNode[][], rows: ReactNode[][][]): ReactNode {
    return <ProseTable key={this.getKey()} header={header} rows={rows} />;
  }

  // the library returns a list's items as a fragment, which the gap between
  // blocks would space apart: the list is one block
  list(ordered: boolean, li: ReactNode[], listStyle?: ViewStyle, textStyle?: TextStyle, startIndex?: number): ReactNode {
    return <View key={this.getKey()}>{super.list(ordered, li, listStyle, textStyle, startIndex)}</View>;
  }

  // monospace reads larger than body text at the same size
  codespan(text: string, style?: TextStyle): ReactNode {
    const { fontSize: _fs, lineHeight: _lh, ...rest } = style ?? {};
    return <InlineCode key={this.getKey()} text={text} style={rest} size={CODE_SCALE * textSize.body} />;
  }

  // a newline inside a paragraph is a soft break, which markdown reads as a
  // space: a hard break reaches `br` instead
  text(text: string | ReactNode[], style?: TextStyle): ReactNode {
    return super.text(soft(text), style);
  }

  // emphasis whose only child is text reaches here unparsed, newline and all
  em(children: string | ReactNode[], style?: TextStyle): ReactNode {
    return super.em(soft(children), style);
  }

  strong(children: string | ReactNode[], style?: TextStyle): ReactNode {
    return super.strong(soft(children), style);
  }

  // the library labels every link "Link", which hides its text from a screen reader
  link(children: string | ReactNode[], href: string, style?: TextStyle, _title?: string): ReactNode {
    const external = isExternal(href);
    return (
      <Text
        key={this.getKey()}
        accessibilityRole="link"
        accessibilityHint={external ? EXTERNAL_HINT : undefined}
        onPress={() => void Linking.openURL(href)}
        style={style}
      >
        {children}
        {external ? EXTERNAL_MARK : null}
      </Text>
    );
  }

  heading(children: string | ReactNode[], style?: TextStyle): ReactNode {
    const size = CODE_SCALE * (style?.fontSize ?? textSize.body);
    const scaled = Array.isArray(children)
      ? children.map((x) =>
          isValidElement(x) && x.type === InlineCode ? cloneElement(x as ReactElement<InlineCodeProps>, { size }) : x,
        )
      : children;
    return super.heading(scaled, style);
  }
}

function markdownStyles(theme: MD3Theme): MarkedStyles {
  return {
    // a block carries no spacing of its own: the gap between blocks spaces them,
    // so a section's first block sits as far under the heading as any other
    paragraph: { paddingVertical: 0 },
    h1: { ...theme.fonts.headlineSmall, color: theme.colors.onSurface, marginVertical: 0, marginTop: space[2] },
    h2: { ...theme.fonts.titleLarge, color: theme.colors.onSurface, marginVertical: 0, marginTop: space[1.5] },
    h3: { ...theme.fonts.titleMedium, color: theme.colors.onSurface, marginVertical: 0, marginTop: space[1] },
    text: { ...theme.fonts.bodyLarge, color: theme.colors.onSurface },
    li: { ...theme.fonts.bodyLarge, color: theme.colors.onSurface },
    codespan: { fontFamily: font.mono, fontStyle: 'normal', backgroundColor: theme.colors.surfaceVariant },
  };
}

export function markdownOptions(theme: MD3Theme, renderer: Renderer) {
  return {
    renderer,
    styles: markdownStyles(theme),
    theme: {
      colors: {
        text: theme.colors.onSurface,
        link: theme.colors.primary,
        code: theme.colors.surfaceVariant,
        border: theme.colors.outlineVariant,
      },
    },
  };
}

/** Authored markdown, rendered in place rather than as a list. */
export function Markdown({ children }: { children: string }) {
  const theme = useTheme();
  const renderer = useMemo(() => new CodeRenderer(), []);
  const elements = useMarkdown(withMath(children), markdownOptions(theme, renderer));
  return (
    <View style={{ gap: BLOCK_GAP }}>
      {elements.map((el, i) => (
        <Fragment key={i}>{el}</Fragment>
      ))}
    </View>
  );
}
