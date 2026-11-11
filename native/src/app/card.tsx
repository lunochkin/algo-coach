import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Card, Chip, Text, TouchableRipple, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  RECALL_THIS,
  RECALL_TITLE,
  recallLine,
  revealLabel,
  type components,
  ladderView,
  LADDER_GAP,
  LADDER_TITLE,
  PROBES_ASIDE,
  PROBES_TITLE,
  probeState,
  described,
  RUN_START_NOTE,
  runStartLabel,
  runStartRefused,
} from '@algo-coach/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { BottomBar, CodeBlock, Loaded, styles } from '@/ui/common';
import { Markdown } from '@/ui/markdown';
import { Badge, PickPanel, PickRow } from '@/ui/rows';
import { PageSection, type Sections, SectionBar, useSections } from '@/ui/sections';

type Template = components['schemas']['Template'];
type Recalled = components['schemas']['Recalled'];

/**
 * A card's trigger, brief, ladder, probes and templates, each form hidden
 * until revealed: `content.md`, Cards. A rung and a probe open the Problem
 * screen, where the sitting stays on the web, and a template opens its recall.
 */
export default function CardScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { slug = '' } = useLocalSearchParams<{ slug: string }>();
  const studied = useEngine('/api/cards/{slug}', { slug });
  const [now] = useState(() => Date.now());
  const card = studied.data?.card;
  const recall = new Map((studied.data?.recall ?? []).map((one) => [one.template_id, one]));

  const sections = useSections(
    studied.data
      ? [
          { id: 'trigger', label: 'When to reach for it' },
          { id: 'brief', label: 'The brief' },
          { id: 'ladder', label: LADDER_TITLE },
          ...(studied.data.probes.length ? [{ id: 'probes', label: PROBES_TITLE }] : []),
          { id: 'templates', label: 'Templates' },
        ]
      : [],
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={card?.title ?? slug} subtitle={card?.technique} />
      </Appbar.Header>
      <SectionBar sections={sections} />
      <ScrollView
        ref={sections.scroll}
        onScroll={sections.onScroll}
        scrollEventThrottle={32}
        // room under the last template for the run's press over it
        contentContainerStyle={[
          styles.page,
          { paddingBottom: insets.bottom + (studied.data && !studied.data.run ? 140 : 24) },
        ]}
      >
        <Loaded of="the card" state={studied}>
          {(data) => (
            <>
              <PageSection of={sections} id="trigger" title="When to reach for it">
                <Markdown>{data.card.trigger}</Markdown>
              </PageSection>
              <PageSection of={sections} id="brief" title="The brief">
                <Markdown>{data.card.brief}</Markdown>
              </PageSection>
              <Ladder studied={data} of={sections} />
              {data.probes.length > 0 ? <Probes studied={data} of={sections} /> : null}
              <PageSection
                of={sections}
                id="templates"
                title="Templates"
                count={data.card.templates.length}
                body="bare"
              >
                {/* a drawn recall is offered beside a run's progress, as on the web */}
                {data.run && data.card.templates.some((one) => (one.cases ?? []).length > 0) ? (
                  <Button
                    mode="outlined"
                    icon="pencil-outline"
                    style={{ alignSelf: 'flex-start' }}
                    onPress={() => router.push({ pathname: '/recall', params: { slug } })}
                  >
                    {RECALL_TITLE}
                  </Button>
                ) : null}
                {data.card.templates.map((template) => (
                  <TemplateCard
                    key={template.slug}
                    card={slug}
                    template={template}
                    recalled={recall.get(template.id)}
                    now={now}
                  />
                ))}
              </PageSection>
            </>
          )}
        </Loaded>
      </ScrollView>
      {studied.data && !studied.data.run ? (
        <RunStart slug={slug} bottom={insets.bottom} onStarted={studied.reload} />
      ) : null}
    </View>
  );
}

function TemplateCard({
  card,
  template,
  recalled,
  now,
}: {
  card: string;
  template: Template;
  recalled: Recalled | undefined;
  now: number;
}) {
  const theme = useTheme();
  const [revealed, setRevealed] = useState(false);
  // a template no case checks is read on the card and never recalled
  const recallable = (template.cases ?? []).length > 0;

  return (
    <Card mode="outlined">
      <Card.Content style={{ gap: 8 }}>
        <View style={[styles.row, { flexWrap: 'wrap' }]}>
          <Text variant="titleMedium" style={{ flexShrink: 1 }}>
            {template.title}
          </Text>
          {template.optional ? <Chip compact>optional</Chip> : null}
          {template.kind === 'procedure' ? (
            <Chip compact mode="outlined">
              procedure
            </Chip>
          ) : null}
        </View>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {recallable ? recallLine(recalled, now) : 'No case checks this form'}
        </Text>
        <Markdown>{template.trigger}</Markdown>
        {recallable ? (
          <Button
            mode="contained-tonal"
            icon="pencil-outline"
            style={{ alignSelf: 'flex-start' }}
            onPress={() => router.push({ pathname: '/recall', params: { slug: card, template: template.slug } })}
          >
            {RECALL_THIS}
          </Button>
        ) : null}
        {revealed ? (
          <>
            <CodeBlock code={template.code} verbatim />
            {template.notes ? <Markdown>{template.notes}</Markdown> : null}
            <Button mode="text" onPress={() => setRevealed(false)} style={{ alignSelf: 'flex-end' }}>
              Hide the form
            </Button>
          </>
        ) : (
          <Button
            mode="outlined"
            icon="eye-outline"
            onPress={() => setRevealed(true)}
            style={{ alignSelf: 'flex-start' }}
          >
            {revealLabel(template.code)}
          </Button>
        )}
      </Card.Content>
    </Card>
  );
}

type Studied = components['schemas']['Studied'];

// a rung and a probe each open the problem, with the card's technique drilled,
// and the card the sitting returns to
const openProblem = (problem: string, technique: string, card: string) =>
  router.push({ pathname: '/problem', params: { problem, technique, card } });

function Ladder({ studied, of }: { studied: Studied; of: Sections }) {
  const theme = useTheme();
  const view = ladderView(studied);
  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <PageSection of={of} id="ladder" title={LADDER_TITLE} count={view.count} aside={view.aside} body="bare">
      {view.rows.length > 0 || view.gaps.length > 0 ? (
        <PickPanel>
          {[
            ...view.rows.map((rung) => (
              <TouchableRipple
                key={rung.problemId}
                accessibilityRole="link"
                accessibilityLabel={rung.title}
                onPress={() => openProblem(rung.problemId, studied.card.technique, studied.card.slug)}
              >
                <View style={{ paddingHorizontal: 16, paddingVertical: 12, gap: 6 }}>
                  <View style={[styles.row, { flexWrap: 'wrap' }]}>
                    {/* solved since the run began: a reading, not a control */}
                    {rung.solved !== null ? (
                      <MaterialCommunityIcons
                        name={rung.solved ? 'checkbox-marked' : 'checkbox-blank-outline'}
                        size={18}
                        color={theme.colors.onSurfaceVariant}
                      />
                    ) : null}
                    <Text variant="titleMedium" style={{ flexShrink: 1 }}>
                      {rung.title}
                    </Text>
                  </View>
                  <View style={[styles.row, { flexWrap: 'wrap' }]}>
                    {rung.difficulty ? <Badge label={rung.difficulty} /> : null}
                    <Text variant="bodySmall" style={muted}>
                      {rung.need}
                    </Text>
                  </View>
                  {rung.covers ? (
                    <Text variant="bodySmall" style={muted}>
                      {rung.covers}
                    </Text>
                  ) : null}
                </View>
              </TouchableRipple>
            )),
            ...view.gaps.map((gap) => (
              <View key={gap} style={[styles.row, { paddingHorizontal: 16, paddingVertical: 12 }]}>
                <Text variant="bodySmall" style={[muted, { flex: 1 }]}>
                  {gap}
                </Text>
                <Badge label={LADDER_GAP} />
              </View>
            )),
          ]}
        </PickPanel>
      ) : null}
    </PageSection>
  );
}

function Probes({ studied, of }: { studied: Studied; of: Sections }) {
  return (
    <PageSection
      of={of}
      id="probes"
      title={PROBES_TITLE}
      count={studied.probes.length}
      aside={PROBES_ASIDE}
      body="bare"
    >
      <PickPanel>
        {studied.probes.map((one) => (
          <PickRow
            key={one.problem.id}
            title={one.problem.title}
            badge={one.problem.difficulty ?? null}
            stats={[{ label: '', value: probeState(one.attempted) }]}
            onPress={() => openProblem(one.problem.id, studied.card.technique, studied.card.slug)}
          />
        ))}
      </PickPanel>
    </PageSection>
  );
}

// the card's act before a run: the press opening one, in the bar at the
// bottom with the note on what it measures. Starting draws the probes
function RunStart({ slug, bottom, onStarted }: { slug: string; bottom: number; onStarted: () => void }) {
  const theme = useTheme();
  const st = useStore();
  const [starting, setStarting] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const start = async () => {
    setStarting(true);
    setRefused(null);
    try {
      await engine(st.settings.origin, await getToken()).POST('/api/cards/{slug}/runs', {
        params: { path: { slug } },
      });
      onStarted();
    } catch (e) {
      setRefused(described(e));
    } finally {
      setStarting(false);
    }
  };
  return (
    <BottomBar
      bottom={bottom}
      above={
        <Text variant="bodySmall" style={{ color: refused ? theme.colors.error : theme.colors.onSurfaceVariant }}>
          {refused ? runStartRefused(refused) : RUN_START_NOTE}
        </Text>
      }
    >
      <Button mode="contained" onPress={() => void start()} disabled={starting} contentStyle={{ paddingVertical: 8 }}>
        {runStartLabel(starting)}
      </Button>
    </BottomBar>
  );
}
