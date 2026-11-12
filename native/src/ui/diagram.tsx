import { useState } from 'react';
import { View } from 'react-native';
import { useTheme } from 'react-native-paper';
import { SvgXml } from 'react-native-svg';

import { drawingSize } from '@algo-coach/core';

import { useStore } from '@/lib/store';
import { CodeBlock } from '@/ui/common';

/**
 * A Mermaid source as the seed drew it, in the app's scheme, scaled to the
 * reading width and never wider than drawn: `knowledge.md`, Diagrams. A
 * source with no drawing reads as its text.
 */
export function Diagram({ source }: { source: string }) {
  const theme = useTheme();
  const drawn = useStore().catalog?.diagrams[source];
  const [width, setWidth] = useState(0);
  const svg = drawn && (theme.dark ? drawn.dark : drawn.light);
  const size = svg ? drawingSize(svg) : null;
  if (!svg || !size) return <CodeBlock code={source} verbatim wrap={false} flush />;
  const shown = Math.min(width, size.width);
  return (
    <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)} accessible accessibilityLabel={source}>
      {shown > 0 ? <SvgXml xml={svg} width={shown} height={(shown * size.height) / size.width} /> : null}
    </View>
  );
}
