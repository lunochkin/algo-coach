import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Card, Chip, Text, TouchableRipple, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  readFailure,
  RECALL_THIS,
  RECALL_TITLE,
  recallLine,
  revealLabel,
  type components,
  loadingLine,
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
import { CodeBlock, Failed, styles } from '@/ui/common';
import { Markdown } from '@/ui/markdown';
import { Badge, PickPanel, PickRow } from '@/ui/rows';

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

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={card?.title ?? slug} subtitle={card?.technique} />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        {studied.error ? (
          <Failed message={readFailure('the card', studied.error)} onRetry={studied.reload} />
        ) : !card ? (
          <Text variant="bodyMedium">{loadingLine('the card')}</Text>
        ) : (
          <>
            <Text variant="titleMedium">When to reach for it</Text>
            <Markdown>{card.trigger}</Markdown>
            <Text variant="titleMedium">The brief</Text>
            <Markdown>{card.brief}</Markdown>
            <Ladder studied={studied.data!} />
            {studied.data!.run ? null : <RunStart slug={slug} onStarted={studied.reload} />}
            {studied.data!.probes.length > 0 ? <Probes studied={studied.data!} /> : null}
            <Text variant="titleMedium">
              Templates <Text style={{ color: theme.colors.onSurfaceVariant }}>{card.templates.length}</Text>
            </Text>
            {/* a drawn recall is offered beside a run's progress, as on the web */}
            {studied.data!.run && card.templates.some((one) => (one.cases ?? []).length > 0) ? (
              <Button
                mode="outlined"
                icon="pencil-outline"
                style={{ alignSelf: 'flex-start' }}
                onPress={() => router.push({ pathname: '/recall', params: { slug } })}
              >
                {RECALL_TITLE}
              </Button>
            ) : null}
            {card.templates.map((template) => (
              <TemplateCard
                key={template.slug}
                card={slug}
                template={template}
                recalled={recall.get(template.id)}
                now={now}
              />
            ))}
          </>
        )}
      </ScrollView>
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

function Ladder({ studied }: { studied: Studied }) {
  const theme = useTheme();
  const view = ladderView(studied);
  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <>
      <Text variant="titleMedium">
        {LADDER_TITLE} <Text style={muted}>{view.aside}</Text>
      </Text>
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
    </>
  );
}

function Probes({ studied }: { studied: Studied }) {
  const theme = useTheme();
  return (
    <>
      <Text variant="titleMedium">
        {PROBES_TITLE} <Text style={{ color: theme.colors.onSurfaceVariant }}>{PROBES_ASIDE}</Text>
      </Text>
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
    </>
  );
}

// the press opening a run, below the ladder it measures from. Starting draws
// the probes; the sittings the run counts are still sat on the web
function RunStart({ slug, onStarted }: { slug: string; onStarted: () => void }) {
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
    <View style={{ gap: 8 }}>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {RUN_START_NOTE}
      </Text>
      <Button mode="contained" onPress={() => void start()} disabled={starting} style={{ alignSelf: 'flex-start' }}>
        {runStartLabel(starting)}
      </Button>
      {refused ? (
        <Text variant="bodySmall" style={{ color: theme.colors.error }}>
          {runStartRefused(refused)}
        </Text>
      ) : null}
    </View>
  );
}
