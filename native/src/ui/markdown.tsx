import { cloneElement, Fragment, isValidElement, useMemo, type ReactElement, type ReactNode } from 'react';
import { View, type TextStyle, type ViewStyle } from 'react-native';
import { Renderer, useMarkdown, type MarkedStyles } from 'react-native-marked';
import { Text, useTheme, type MD3Theme } from 'react-native-paper';

import { withMath } from '@/lib/math';
import { CodeBlock } from '@/ui/common';
import { font, space, textSize } from '@/ui/tokens';

const CODE_SCALE = 0.85;

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

/** Code blocks in the app's monospace block, never wrapped. */
export class CodeRenderer extends Renderer {
  code(text: string, _language?: string, _container?: ViewStyle, _style?: TextStyle): ReactNode {
    return <CodeBlock code={text} verbatim />;
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
    h1: { ...theme.fonts.headlineSmall, color: theme.colors.onSurface, marginVertical: space[2] },
    h2: { ...theme.fonts.titleLarge, color: theme.colors.onSurface, marginVertical: space[1.5] },
    h3: { ...theme.fonts.titleMedium, color: theme.colors.onSurface, marginVertical: space[1] },
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
    <View>
      {elements.map((el, i) => (
        <Fragment key={i}>{el}</Fragment>
      ))}
    </View>
  );
}
