import { router, useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Text, TextInput, useTheme } from 'react-native-paper';
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  type Catalog,
  certById,
  certExam,
  examChoice,
  certExamRule,
  CERT_EXAM_MISSING,
  CERT_EXAM_START,
  examOpening,
  levelExam,
  levelName,
  levels,
  EXAM_ALL,
  EXAM_LEVEL,
  EXAM_MODULE,
  EXAM_NOTE,
  EXAM_SIZE,
  EXAM_TITLE,
  examModuleChoice,
  OF,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { useSavedSize } from '@/lib/useSavedSize';
import { BottomBar, fromCopy, Loaded, startExam, styles } from '@/ui/common';
import { Toggle, Toggles } from '@/ui/toggle';
import { Heading } from '@/ui/rows';

// the choices wait for the copy, so the size and the focus they open on are the stored ones
export default function Exam() {
  const st = useStore();
  const theme = useTheme();
  const { cert } = useLocalSearchParams<{ cert?: string }>();
  const catalog = st.ready ? st.catalog : null;
  if (catalog && cert) return <CertChoice id={cert} catalog={catalog} />;
  if (catalog) return <Choices catalog={catalog} />;
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Header />
      <View style={styles.page}>
        <Loaded of={OF.exam} state={fromCopy(st, null)}>
          {() => null}
        </Loaded>
      </View>
    </View>
  );
}

function Header({ title = EXAM_TITLE }: { title?: string }) {
  return (
    <Appbar.Header>
      <Appbar.BackAction onPress={() => router.back()} />
      <Appbar.Content title={title} />
    </Appbar.Header>
  );
}

// a certification exam's choices are its rule alone, read before the sample is drawn
function CertChoice({ id, catalog }: { id: string; catalog: Catalog }) {
  const st = useStore();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const found = certById(catalog, id);
  const b = found ? st.board(found.c.slug) : null;
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Header title={found?.x.title ?? EXAM_TITLE} />
      <View style={styles.page}>
        {found && b ? (
          <>
            <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
              {EXAM_NOTE}
            </Text>
            <Text variant="bodyLarge">{certExamRule(found.x.rule.size, found.x.rule.passShare)}</Text>
          </>
        ) : (
          <Text variant="bodyMedium">{CERT_EXAM_MISSING}</Text>
        )}
      </View>
      {found && b ? (
        <BottomBar bottom={insets.bottom}>
          <Button
            mode="contained"
            icon="play"
            contentStyle={{ paddingVertical: 8 }}
            onPress={() => {
              const plan = certExam(b, found.c, id);
              if (plan) startExam(st, plan);
            }}
          >
            {CERT_EXAM_START}
          </Button>
        </BottomBar>
      ) : null}
    </View>
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
  const choice = useMemo(() => examChoice(b, catalog.rules, level, size), [b, catalog, level, size]);
  const lv = levels(catalog.rules);

  const start = () => {
    if (!b || !choice.count) return;
    startExam(st, levelExam(b, level, choice.n));
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
        <Heading sub title={EXAM_MODULE} />
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          <Toggle on={course === null} onPress={() => setCourse(null)}>
            {EXAM_ALL}
          </Toggle>
          {courses.map((c) => (
            <Toggle key={c.slug} on={course === c.slug} onPress={() => setCourse(c.slug)}>
              {examModuleChoice(c)}
            </Toggle>
          ))}
        </View>
        <Heading sub title={EXAM_LEVEL} />
        <Toggles>
          {lv.map((l) => (
            <Toggle key={l} on={level === l} onPress={() => setLevel(l)}>
              {levelName(catalog.rules, l, true)}
            </Toggle>
          ))}
        </Toggles>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {catalog.rules.levels[level] ?? ''}
        </Text>
        <TextInput mode="outlined" label={EXAM_SIZE} value={size} onChangeText={setSize} keyboardType="number-pad" />
      </ScrollView>
      <BottomBar bottom={insets.bottom}>
        <Button
          mode="contained"
          icon="play"
          disabled={!choice.count}
          onPress={start}
          contentStyle={{ paddingVertical: 8 }}
        >
          {choice.label}
        </Button>
      </BottomBar>
    </KeyboardAvoidingView>
  );
}
