import { useState } from 'react';
import { Pressable, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

import { FORECAST_HEADING, FORECAST_NOTE, forecastBarLabel, type ForecastView } from '@climb/core';

import { Heading, Panel } from './rows';
import { space, textSize } from './tokens';

const HEIGHT = 64;

/** The reviews ahead, a column per learning day; a press on a day names it above, as hover does on the web. */
export function ReviewForecast({ view }: { view: ForecastView }) {
  const theme = useTheme();
  const muted = theme.colors.onSurfaceVariant;
  const [picked, setPicked] = useState<number | null>(null);
  const shown = picked === null ? null : view.bars[picked];
  const micro = { fontSize: textSize.micro, color: muted, fontVariant: ['tabular-nums' as const] };
  return (
    <View style={{ gap: space[2], marginTop: space[3] }}>
      <Heading title={FORECAST_HEADING} />
      <Panel padded>
        <Text variant="bodySmall" style={{ color: muted }} accessibilityLiveRegion="polite">
          {shown ? forecastBarLabel(shown.day, shown.reviews) : view.summary}
        </Text>
        <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: space[0.5], height: HEIGHT + 16 }}>
          {view.bars.map((bar, i) => (
            <Pressable
              key={i}
              onPress={() => setPicked(picked === i ? null : i)}
              accessibilityLabel={forecastBarLabel(bar.day, bar.reviews)}
              style={{ flex: 1, height: '100%', alignItems: 'center', justifyContent: 'flex-end' }}
            >
              <Text style={micro}>{bar.labelled ? String(bar.reviews) : ' '}</Text>
              <View
                style={{
                  width: '100%',
                  maxWidth: 24,
                  borderTopLeftRadius: 4,
                  borderTopRightRadius: 4,
                  backgroundColor: bar.today ? theme.colors.onSurface : muted,
                  opacity: picked !== null && picked !== i ? 0.5 : 1,
                  height: view.max ? Math.max(bar.reviews ? 2 : 0, (bar.reviews / view.max) * HEIGHT) : 0,
                }}
              />
            </Pressable>
          ))}
        </View>
        <View
          style={{
            flexDirection: 'row',
            justifyContent: 'space-between',
            borderTopWidth: 1,
            borderColor: theme.colors.outlineVariant,
            paddingTop: space[1],
          }}
        >
          <Text style={micro}>{view.first}</Text>
          <Text style={micro}>{view.last}</Text>
        </View>
        <Text variant="bodySmall" style={{ color: muted }}>
          {FORECAST_NOTE}
        </Text>
      </Panel>
    </View>
  );
}
