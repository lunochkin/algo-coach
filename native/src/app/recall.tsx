import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { ScrollView, type ScrollViewInstance, View } from 'react-native';
import { Appbar, Button, IconButton, Menu, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  BACK_TO_CARD,
  described,
  FORM_HIDDEN,
  hintTaken,
  nextHint,
  RECALL_ANOTHER,
  RECALL_FORM,
  RECALL_NO_CASES,
  RECALL_OPTIONAL,
  RECALL_TITLE,
  RECALL_TRIGGER,
  recallBlank,
  RECALLING,
  recallNote,
  recallOptional,
  recallRefused,
  recallView,
  REVEAL_FORM,
  runLabel,
  takeHint,
  type components,
  OF,
  keyboardToggle,
} from '@algo-coach/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { CodeBlock, Loaded, styles, tones } from '@/ui/common';
import { Heading } from '@/ui/rows';
import { CodeEditor, type EditorHandle } from '@/ui/editor';
import type { Key } from '@/lib/keys';
import { KeyPad } from '@/ui/keys';
import { Markdown } from '@/ui/markdown';

type Prompted = components['schemas']['Prompted'];
type Hint = components['schemas']['Hint'];
type RecallAttempt = components['schemas']['RecallAttempt'];

/**
 * One template reproduced from memory: `flows.md`, Recalling a template. A
 * screen opened without a template recalls the one the trainer draws, and
 * withholds its title.
 */
export default function RecallScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { slug = '', template } = useLocalSearchParams<{ slug: string; template?: string }>();
  const drawn = !template;
  const named = useEngine(template ? '/api/cards/{slug}/recall/{template_slug}' : null, {
    slug,
    template_slug: template ?? '',
  });
  const drew = useEngine(template ? null : '/api/cards/{slug}/recall', { slug });
  const prompt = template ? named : drew;
  const data = prompt.data;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={drawn ? RECALL_TITLE : (data?.title ?? RECALL_TITLE)} />
      </Appbar.Header>
      {data ? (
        <Trainer key={data.template_slug} slug={slug} prompt={data} drawn={drawn} bottom={insets.bottom} />
      ) : (
        <View style={styles.page}>
          <Loaded of={OF.recall} state={prompt}>
            {() => null}
          </Loaded>
        </View>
      )}
    </View>
  );
}

function Trainer({ slug, prompt, drawn, bottom }: { slug: string; prompt: Prompted; drawn: boolean; bottom: number }) {
  const theme = useTheme();
  const { origin } = useStore().settings;
  const editor = useRef<EditorHandle>(null);
  const onKey = useCallback((key: Key) => editor.current?.press(key), []);
  const [names, setNames] = useState<string[]>([]);
  const top = useRef<ScrollViewInstance>(null);
  const code = useRef(recallBlank(prompt.signature));
  const [taken, setTaken] = useState<{ hint: Hint; text: string }[]>([]);
  const [running, setRunning] = useState(false);
  const [ran, setRan] = useState<RecallAttempt | null>(null);
  const [refused, setRefused] = useState<string | null>(null);
  // hidden on a press, so the editor takes the pad's height: a median
  // canonical is eighteen lines, and the pad leaves room for about eight
  const [keys, setKeys] = useState(true);
  const next = nextHint(taken.map((one) => one.hint));
  const path = { slug, template_slug: prompt.template_slug };

  // one hint per request, so the screen holds nothing it was not given
  async function hint() {
    if (next === null) return;
    try {
      const { data, error } = await engine(origin, await getToken()).GET(
        '/api/cards/{slug}/recall/{template_slug}/hints/{hint}',
        { params: { path: { ...path, hint: next } } },
      );
      if (data) setTaken([...taken, { hint: data.hint, text: data.text }]);
      else setRefused(described(error));
    } catch (reason) {
      setRefused(String(reason));
    }
  }

  async function run() {
    setRunning(true);
    setRefused(null);
    try {
      const { data, error } = await engine(origin, await getToken()).POST('/api/cards/{slug}/recall/{template_slug}', {
        params: { path },
        body: { code: code.current, hints: taken.map((one) => one.hint) },
      });
      if (data) setRan(data);
      else setRefused(described(error));
    } catch (reason) {
      setRefused(String(reason));
    } finally {
      setRunning(false);
    }
  }

  if (ran) return <Ran ran={ran} slug={slug} templateSlug={prompt.template_slug} bottom={bottom} />;

  return (
    <View style={{ flex: 1, paddingBottom: bottom + 8 }}>
      {/* what the recall asks, above the editor: short enough that the
          editor keeps most of the screen */}
      <ScrollView
        ref={top}
        style={{ flexGrow: 0, maxHeight: 200 }}
        contentContainerStyle={{ padding: 16, gap: 8 }}
        // a hint taken lands below the trigger, where the panel scrolls to it
        onContentSizeChange={() => taken.length > 0 && top.current?.scrollToEnd()}
      >
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {recallNote(drawn)}
        </Text>
        {drawn ? null : <Templates slug={slug} prompt={prompt} />}
        <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {RECALL_TRIGGER}
        </Text>
        <Markdown>{prompt.trigger}</Markdown>
        {taken.map((one) => (
          <View key={one.hint} style={{ gap: 4 }}>
            <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant }}>
              {hintTaken(one.hint)}
            </Text>
            {one.hint === 'form' ? <CodeBlock code={one.text} verbatim /> : <Markdown>{one.text}</Markdown>}
          </View>
        ))}
      </ScrollView>
      <CodeEditor ref={editor} onNames={setNames} initial={code.current} onChange={(typed) => (code.current = typed)} />
      <View style={[styles.row, { paddingHorizontal: 8, paddingVertical: 6, gap: 8 }]}>
        <Button mode="contained" onPress={run} disabled={running}>
          {runLabel(running)}
        </Button>
        {next !== null ? (
          <Button mode="outlined" onPress={hint}>
            {takeHint(next)}
          </Button>
        ) : null}
        <IconButton
          icon={keys ? 'keyboard-close' : 'keyboard'}
          accessibilityLabel={keyboardToggle(keys)}
          style={{ marginLeft: 'auto' }}
          onPress={() => {
            setKeys(!keys);
            // once the screen has laid out at the new height
            setTimeout(() => editor.current?.measure(), 100);
          }}
        />
      </View>
      {refused ? (
        <Text variant="bodySmall" style={{ color: theme.colors.error, paddingHorizontal: 8 }}>
          {recallRefused(refused)}
        </Text>
      ) : null}
      {keys ? (
        <View style={{ paddingHorizontal: 8 }}>
          <KeyPad lines names={names} onKey={onKey} />
        </View>
      ) : null}
    </View>
  );
}

// every form the card teaches, so the user switches without reading the card
// again. A template no case checks is named and never opened
function Templates({ slug, prompt }: { slug: string; prompt: Prompted }) {
  const [open, setOpen] = useState(false);
  const here = prompt.templates.find((one) => one.slug === prompt.template_slug);
  return (
    <View style={[styles.row, { flexWrap: 'wrap' }]}>
      <Text variant="bodySmall">{RECALLING}</Text>
      <Menu
        visible={open}
        onDismiss={() => setOpen(false)}
        anchor={
          <Button
            mode="outlined"
            compact
            icon="chevron-down"
            contentStyle={{ flexDirection: 'row-reverse' }}
            onPress={() => setOpen(true)}
          >
            {here?.title ?? RECALL_TITLE}
          </Button>
        }
      >
        {prompt.templates.map((one) => (
          <Menu.Item
            key={one.slug}
            title={[one.title, one.optional && RECALL_OPTIONAL, !one.recallable && RECALL_NO_CASES]
              .filter(Boolean)
              .join(' · ')}
            leadingIcon={one.slug === prompt.template_slug ? 'check' : undefined}
            disabled={!one.recallable}
            onPress={() => {
              setOpen(false);
              router.setParams({ slug, template: one.slug });
            }}
          />
        ))}
      </Menu>
      {recallOptional(prompt) ? <Text variant="bodySmall">{RECALL_OPTIONAL}</Text> : null}
    </View>
  );
}

// the verdict, and the form on a press: a user who failed to recall a form
// learns which form it was and decides whether to read it
function Ran({
  ran,
  slug,
  templateSlug,
  bottom,
}: {
  ran: RecallAttempt;
  slug: string;
  templateSlug: string;
  bottom: number;
}) {
  const theme = useTheme();
  const { origin } = useStore().settings;
  const [form, setForm] = useState<string | null>(null);
  const view = recallView(ran);

  async function reveal() {
    const { data } = await engine(origin, await getToken()).GET(
      '/api/cards/{slug}/recall/{template_slug}/hints/{hint}',
      { params: { path: { slug, template_slug: templateSlug, hint: 'form' } } },
    );
    if (data) setForm(data.text);
  }

  return (
    <ScrollView contentContainerStyle={[styles.page, { paddingBottom: bottom + 24 }]}>
      <Text variant="titleMedium" style={{ color: view.recalled ? tones(theme.dark).done : theme.colors.error }}>
        {view.verdict}
      </Text>
      {view.failures ? (
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {view.failures}
        </Text>
      ) : null}
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {view.hints}
      </Text>
      <Heading title={RECALL_FORM} />
      {form === null ? (
        <>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {FORM_HIDDEN}
          </Text>
          <Button mode="outlined" icon="eye-outline" onPress={reveal} style={{ alignSelf: 'flex-start' }}>
            {REVEAL_FORM}
          </Button>
        </>
      ) : (
        <CodeBlock code={form} verbatim />
      )}
      <View style={[styles.row, { flexWrap: 'wrap', gap: 8 }]}>
        <Button mode="contained" onPress={() => router.replace({ pathname: '/recall', params: { slug } })}>
          {RECALL_ANOTHER}
        </Button>
        <Button mode="outlined" onPress={() => router.back()}>
          {BACK_TO_CARD}
        </Button>
      </View>
    </ScrollView>
  );
}
