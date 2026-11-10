import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Chip, SegmentedButtons, Text, TextInput, useTheme } from 'react-native-paper';
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Catalog,
  examFailed,
  examOpening,
  examPool,
  levelExam,
  levelExamLabel,
  levelName,
  levels,
  validSetting,
  EXAM_ALL,
  EXAM_LEVEL,
  EXAM_LOADING,
  EXAM_MODULE,
  EXAM_NOTE,
  EXAM_SIZE,
  EXAM_TITLE,
  examModuleChoice,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { useSavedSize } from '@/lib/useSavedSize';
import { BottomBar, Failed, startExam, styles } from '@/ui/common';

// the choices wait for the copy, so the size and the focus they open on are the stored ones
export default function Exam() {
  const st = useStore();
  const theme = useTheme();
  const catalog = st.ready ? st.catalog : null;
  if (catalog) return <Choices catalog={catalog} />;
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Header />
      <View style={styles.page}>
        {st.sync.error && !st.sync.running ? (
          <Failed message={examFailed(st.sync.error)} onRetry={() => st.requestSync(0)} />
        ) : (
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
            {EXAM_LOADING}
          </Text>
        )}
      </View>
    </View>
  );
}

function Header() {
  return (
    <Appbar.Header>
      <Appbar.BackAction onPress={() => router.back()} />
      <Appbar.Content title={EXAM_TITLE} />
    </Appbar.Header>
  );
}

function Choices({ catalog }: { catalog: Catalog }) {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const courses = catalog.courses;
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
  const lv = levels(catalog.rules);

  const start = () => {
    if (!b || !count) return;
    startExam(st, levelExam(b, level, n));
  };

  return (
    <KeyboardAvoidingView behavior="padding" style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Header />
      <ScrollView
        contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 96 }]}
        keyboardShouldPersistTaps="handled"
      >
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {EXAM_NOTE}
        </Text>
        <Text variant="titleSmall">{EXAM_MODULE}</Text>
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          <Chip selected={course === null} showSelectedCheck onPress={() => setCourse(null)}>
            {EXAM_ALL}
          </Chip>
          {courses.map((c) => (
            <Chip key={c.slug} selected={course === c.slug} showSelectedCheck onPress={() => setCourse(c.slug)}>
              {examModuleChoice(c)}
            </Chip>
          ))}
        </View>
        <Text variant="titleSmall">{EXAM_LEVEL}</Text>
        <SegmentedButtons
          value={String(level)}
          onValueChange={(v) => setLevel(Number(v))}
          buttons={lv.map((l) => ({
            value: String(l),
            label: levelName(catalog.rules, l, true),
          }))}
        />
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {catalog.rules.levels[level] ?? ''}
        </Text>
        <TextInput mode="outlined" label={EXAM_SIZE} value={size} onChangeText={setSize} keyboardType="number-pad" />
      </ScrollView>
      <BottomBar bottom={insets.bottom}>
        <Button mode="contained" icon="play" disabled={!count} onPress={start} contentStyle={{ paddingVertical: 8 }}>
          {levelExamLabel(catalog.rules, level, pool.length, count)}
        </Button>
      </BottomBar>
    </KeyboardAvoidingView>
  );
}
