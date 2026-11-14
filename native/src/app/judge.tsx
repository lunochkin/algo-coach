import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  JUDGE_CLEAN,
  JUDGE_FLAWED,
  JUDGE_NEXT,
  JUDGE_NONE,
  JUDGE_SUBMIT,
  JUDGE_TAP,
  JUDGE_TITLE,
  VERDICTS,
  type components,
  judge,
  judgeDepth,
  judgeCorrection,
  judgeExample,
  nextJudged,
  separatingLines,
  verdictPassed,
} from '@algo-coach/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { BottomBar, ErrorLine, Press, ScreenHeader, styles, tones } from '@/ui/common';
import { font, space } from '@/ui/tokens';

type JudgedItem = components['schemas']['JudgedItem'];
type JudgeDecided = components['schemas']['JudgeDecided'];

/** Judging a solution, as the web's page: `pages.md`, Judging a solution. */
export default function JudgeScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const st = useStore();
  const { card } = useLocalSearchParams<{ card?: string }>();
  const [item, setItem] = useState<JudgedItem | null | undefined>(undefined);
  const [tapping, setTapping] = useState(false);
  const [tapped, setTapped] = useState<number | null>(null);
  const [decided, setDecided] = useState<JudgeDecided | null>(null);
  const [refused, setRefused] = useState<string | null>(null);
  const [round, setRound] = useState(0);

  useEffect(() => {
    let live = true;
    void (async () => {
      const next = await nextJudged(engine(st.settings.origin, await getToken()), card ?? null);
      if (!live) return;
      if (next.ok) setItem(next.value);
      else setRefused(next.refused);
    })();
    return () => {
      live = false;
    };
  }, [card, round, st.settings.origin]);

  const send = async (line: number | null) => {
    if (!item) return;
    const answered = await judge(engine(st.settings.origin, await getToken()), item.item_id, line);
    if (answered.ok) setDecided(answered.value);
    else setRefused(answered.refused);
  };

  // Next clears the answer in the press itself, and the effect fetches
  const another = () => {
    setTapping(false);
    setTapped(null);
    setDecided(null);
    setRefused(null);
    setRound((one) => one + 1);
  };

  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader
        title={item ? item.template_title : JUDGE_TITLE}
        note={[item ? `${item.card_title} · ${judgeDepth(item.depth)}` : null]}
      />
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 160 }]}>
        {refused ? <ErrorLine>{refused}</ErrorLine> : null}
        {item === null ? <Text style={muted}>{JUDGE_NONE}</Text> : null}
        {item ? (
          <>
            <Text style={muted}>{item.asks}</Text>
            <Text style={{ fontFamily: font.mono }}>{judgeExample(item.example)}</Text>
            <View style={{ borderRadius: 12, overflow: 'hidden', backgroundColor: theme.colors.surfaceVariant }}>
              {item.lines.map((line, index) => {
                const number = index + 1;
                const flawed = decided?.line === number;
                return (
                  <Pressable
                    key={number}
                    disabled={!tapping || decided !== null}
                    onPress={() => setTapped(number)}
                    accessibilityRole="button"
                    accessibilityLabel={`line ${number}: ${line}`}
                    style={{
                      flexDirection: 'row',
                      gap: space[2],
                      paddingVertical: 3,
                      paddingHorizontal: space[2],
                      backgroundColor: tapped === number ? theme.colors.secondaryContainer : undefined,
                      borderLeftWidth: flawed ? 4 : 0,
                      borderLeftColor: theme.colors.error,
                    }}
                  >
                    <Text style={[{ fontFamily: font.mono, width: 22, textAlign: 'right' }, muted]}>{number}</Text>
                    <Text style={{ fontFamily: font.mono, flex: 1 }}>{line || ' '}</Text>
                  </Pressable>
                );
              })}
            </View>
            {decided ? (
              <View style={{ gap: space[1] }}>
                <Text
                  variant="titleSmall"
                  style={{ color: verdictPassed(decided.verdict) ? tones(theme.dark).done : theme.colors.error }}
                >
                  {VERDICTS[decided.verdict]}
                </Text>
                {judgeCorrection(decided) ? (
                  <>
                    <Text style={muted}>{judgeCorrection(decided)?.label}</Text>
                    <Text style={{ fontFamily: font.mono }}>{judgeCorrection(decided)?.code.trim()}</Text>
                  </>
                ) : null}
                {separatingLines(decided).map((line) => (
                  <Text key={line} style={{ fontFamily: font.mono }}>
                    {line}
                  </Text>
                ))}
              </View>
            ) : null}
          </>
        ) : null}
      </ScrollView>
      {item ? (
        <BottomBar
          bottom={insets.bottom}
          row={!decided && !tapping}
          above={tapping && !decided ? <Text style={muted}>{JUDGE_TAP}</Text> : null}
        >
          {decided ? (
            <Press onPress={another}>{JUDGE_NEXT}</Press>
          ) : tapping ? (
            <Press disabled={tapped === null} onPress={() => void send(tapped)}>
              {JUDGE_SUBMIT}
            </Press>
          ) : (
            <>
              <Press style={{ flex: 1 }} onPress={() => void send(null)}>
                {JUDGE_CLEAN}
              </Press>
              <Press style={{ flex: 1 }} mode="outlined" onPress={() => setTapping(true)}>
                {JUDGE_FLAWED}
              </Press>
            </>
          )}
        </BottomBar>
      ) : null}
    </View>
  );
}
