import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { ScrollView, type ScrollViewInstance, View } from 'react-native';
import { Button, IconButton, Menu, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  BACK_TO_CARD,
  hintTaken,
  HINT_NAMES,
  HINTS,
  nextHint,
  RECALL_ANOTHER,
  RECALL_FORM,
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
  recallMenu,
  requestHint,
  revealForm,
  runRecall,
} from '@climb/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { BottomBar, CodeBlock, ErrorLine, Loaded, styles, tones, Press, ScreenHeader } from '@/ui/common';
import { Heading } from '@/ui/rows';
import { CodeEditor, type EditorHandle } from '@/ui/editor';
import type { Key } from '@/lib/keys';
import { KeyPad } from '@/ui/keys';
import { Markdown } from '@/ui/markdown';
import { space } from '@/ui/tokens';

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
      <ScreenHeader title={drawn ? RECALL_TITLE : (data?.title ?? RECALL_TITLE)} />
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

  // one hint per request, so the screen holds nothing it was not given
  async function hint() {
    if (next === null) return;
    const got = await requestHint(engine(origin, await getToken()), slug, prompt.template_slug, next);
    if (got.ok) setTaken([...taken, got.value]);
    else setRefused(got.refused);
  }

  async function run() {
    setRunning(true);
    setRefused(null);
    const out = await runRecall(
      engine(origin, await getToken()),
      slug,
      prompt.template_slug,
      code.current,
      taken.map((one) => one.hint),
    );
    if (out.ok) setRan(out.value);
    else setRefused(out.refused);
    setRunning(false);
  }

  if (ran) return <Ran ran={ran} slug={slug} templateSlug={prompt.template_slug} bottom={bottom} />;

  return (
    <View style={{ flex: 1, paddingBottom: bottom + 8 }}>
      {/* what the recall asks, above the editor: short enough that the
          editor keeps most of the screen */}
      <ScrollView
        ref={top}
        style={{ flexGrow: 0, maxHeight: 200 }}
        contentContainerStyle={{ padding: space[4], gap: space[2] }}
        // a hint taken lands below the trigger, where the panel scrolls to it
        onContentSizeChange={() => taken.length > 0 && top.current?.scrollToEnd()}
      >
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {recallNote(drawn)}
        </Text>
        {drawn ? null : <Templates slug={slug} prompt={prompt} />}
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {RECALL_TRIGGER}
        </Text>
        <Markdown>{prompt.trigger}</Markdown>
        {taken.map((one) => (
          <View key={one.hint} style={{ gap: space[1] }}>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {hintTaken(one.hint)}
            </Text>
            {one.hint === 'form' ? <CodeBlock code={one.text} verbatim wrap /> : <Markdown>{one.text}</Markdown>}
          </View>
        ))}
      </ScrollView>
      <CodeEditor ref={editor} onNames={setNames} initial={code.current} onChange={(typed) => (code.current = typed)} />
      {/* the ladder, as on the web, so the reader sees what a hint costs
          before taking it: each one answers more of the question than the last */}
      <View style={[styles.row, { paddingHorizontal: space[2], paddingTop: space[1.5], gap: space[2] }]}>
        {HINTS.map((one) => (
          <Text
            key={one}
            variant="bodySmall"
            style={{
              color: theme.colors.onSurfaceVariant,
              textDecorationLine: taken.some((each) => each.hint === one) ? 'line-through' : 'none',
            }}
          >
            {HINT_NAMES[one]}
          </Text>
        ))}
      </View>
      <View style={[styles.row, { paddingHorizontal: space[2], paddingVertical: space[1.5], gap: space[2] }]}>
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
        <View style={{ paddingHorizontal: space[2] }}>
          <ErrorLine>{recallRefused(refused)}</ErrorLine>
        </View>
      ) : null}
      {keys ? (
        <View style={{ paddingHorizontal: space[2] }}>
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
  // which form is recalled, and each one the menu offers, as core names them
  const menu = recallMenu(prompt);
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
            {menu.here}
          </Button>
        }
      >
        {menu.items.map((one) => (
          <Menu.Item
            key={one.slug}
            title={[one.title, one.note].filter(Boolean).join(' · ')}
            leadingIcon={one.current ? 'check' : undefined}
            disabled={!one.enabled}
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
    setForm(await revealForm(engine(origin, await getToken()), slug, templateSlug));
  }

  return (
    <>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: bottom + 120 }]}>
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
          // the cover over the form, drawn as a card's template draws its own
          <Button mode="outlined" icon="eye-outline" onPress={reveal} style={{ alignSelf: 'flex-start' }}>
            {REVEAL_FORM}
          </Button>
        ) : (
          <CodeBlock code={form} verbatim wrap />
        )}
      </ScrollView>
      {/* the result's act, another recall, with the way back to the card beside it */}
      <BottomBar bottom={bottom} row>
        <Press mode="outlined" onPress={() => router.back()}>
          {BACK_TO_CARD}
        </Press>
        <Press style={{ flex: 1 }} onPress={() => router.replace({ pathname: '/recall', params: { slug } })}>
          {RECALL_ANOTHER}
        </Press>
      </BottomBar>
    </>
  );
}
