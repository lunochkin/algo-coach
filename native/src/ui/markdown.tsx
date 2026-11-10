import { cloneElement, Fragment, isValidElement, useMemo, type ReactElement, type ReactNode } from 'react';
import { View, type TextStyle, type ViewStyle } from 'react-native';
import { Renderer, useMarkdown, type MarkedStyles } from 'react-native-marked';
import { Text, useTheme, type MD3Theme } from 'react-native-paper';

import { CodeBlock } from '@/ui/common';

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

/** Code blocks in the app's monospace block, never wrapped. */
export class CodeRenderer extends Renderer {
  code(text: string, _language?: string, _container?: ViewStyle, _style?: TextStyle): ReactNode {
    return <CodeBlock code={text} verbatim />;
  }

  // monospace reads larger than body text at the same size
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
  const elements = useMarkdown(children, markdownOptions(theme, renderer));
  return (
    <View>
      {elements.map((el, i) => (
        <Fragment key={i}>{el}</Fragment>
      ))}
    </View>
  );
}
