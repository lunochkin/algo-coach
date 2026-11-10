import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Chip, SegmentedButtons, Text, TextInput, useTheme } from 'react-native-paper';
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  examOpening,
  examPool,
  levelExam,
  levelExamLabel,
  levelName,
  levels,
  validSetting,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { useSavedSize } from '@/lib/useSavedSize';
import { BottomBar, startExam, styles } from '@/ui/common';

export default function Exam() {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const courses = st.catalog?.courses ?? [];
  // opens on the focus, which the phone and the web share: `knowledge.md`, Queues
  const [opening] = useState(() => examOpening(st.focus));
  const [course, setCourse] = useState<string | null>(opening.course);
  const [level, setLevel] = useState(opening.level);
  const [size, setSize] = useSavedSize();
  const { board } = st;
  const b = useMemo(() => board(course), [board, course]);
  const pool = useMemo(() => (b ? examPool(b, level) : []), [b, level]);
  const n = Number(size);
  const count = validSetting('exam_size', n) ? Math.min(n, pool.length) : 0;
  const lv = st.catalog ? levels(st.catalog.rules) : [0, 1, 2, 3];

  const start = () => {
    if (!b || !count) return;
    startExam(st, levelExam(b, level, n));
  };

  return (
    <KeyboardAvoidingView behavior="padding" style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Exam" />
      </Appbar.Header>
      <ScrollView
        contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 96 }]}
        keyboardShouldPersistTaps="handled">
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          Unlocked questions at one level, no cards. No feedback until the end; then the score per
          topic and a review of what you missed.
        </Text>
        <Text variant="titleSmall">Course</Text>
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          <Chip selected={course === null} showSelectedCheck onPress={() => setCourse(null)}>
            All
          </Chip>
          {courses.map((c) => (
            <Chip
              key={c.slug}
              selected={course === c.slug}
              showSelectedCheck
              onPress={() => setCourse(c.slug)}>
              {c.paused ? `${c.title} (paused)` : c.title}
            </Chip>
          ))}
        </View>
        <Text variant="titleSmall">Level</Text>
        <SegmentedButtons
          value={String(level)}
          onValueChange={(v) => setLevel(Number(v))}
          buttons={lv.map((l) => ({
            value: String(l),
            label: st.catalog ? levelName(st.catalog.rules, l, true) : `L${l}`,
          }))}
        />
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {st.catalog?.rules.levels[level] ?? ''}
        </Text>
        <TextInput
          mode="outlined"
          label="Questions"
          value={size}
          onChangeText={setSize}
          keyboardType="number-pad"
        />
      </ScrollView>
      <BottomBar bottom={insets.bottom}>
        <Button
          mode="contained"
          icon="play"
          disabled={!count}
          onPress={start}
          contentStyle={{ paddingVertical: 8 }}>
          {st.catalog ? levelExamLabel(st.catalog.rules, level, pool.length, count) : ''}
        </Button>
      </BottomBar>
    </KeyboardAvoidingView>
  );
}
