import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, ProgressBar, Text, useTheme } from 'react-native-paper';
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
  OF,
  CARD_TRIGGER,
  CARD_BRIEF,
  CARD_TEMPLATES,
  HIDE_FORM,
  cardNote,
  cardProgress,
  CARD_OPTIONAL,
  PROCEDURE,
  FORM_NO_CASES,
  RUNGS_SOLVED,
  FORMS_RECALLED,
  PROBES_DRAWN,
  nextRung,
} from '@algo-coach/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { BottomBar, CodeBlock, HeaderNote, Loaded, styles } from '@/ui/common';
import { Markdown } from '@/ui/markdown';
import { Badge, Panel, PickPanel, PickRow } from '@/ui/rows';
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
          { id: 'trigger', label: CARD_TRIGGER },
          { id: 'brief', label: CARD_BRIEF },
          { id: 'ladder', label: LADDER_TITLE },
          ...(studied.data.probes.length ? [{ id: 'probes', label: PROBES_TITLE }] : []),
          { id: 'templates', label: CARD_TEMPLATES },
        ]
      : [],
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={card?.title ?? slug} />
      </Appbar.Header>
      <HeaderNote lines={[studied.data ? cardNote(studied.data, now) : card?.technique]} />
      <SectionBar sections={sections} />
      <ScrollView
        ref={sections.scroll}
        onScroll={sections.onScroll}
        scrollEventThrottle={32}
        // room under the last template for the run's press over it
        contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + (studied.data ? 140 : 24) }]}
      >
        <Loaded of={OF.card} state={studied}>
          {(data) => (
            <>
              {data.run ? <RunProgress studied={data} /> : null}
              <PageSection of={sections} id="trigger" title={CARD_TRIGGER}>
                <Markdown>{data.card.trigger}</Markdown>
              </PageSection>
              <PageSection of={sections} id="brief" title={CARD_BRIEF}>
                <Markdown>{data.card.brief}</Markdown>
              </PageSection>
              <Ladder studied={data} of={sections} />
              {data.probes.length > 0 ? <Probes studied={data} of={sections} /> : null}
              <PageSection
                of={sections}
                id="templates"
                title={CARD_TEMPLATES}
                count={data.card.templates.length}
                body="bare"
              >
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
      {studied.data?.run ? (
        <NextRung studied={studied.data} bottom={insets.bottom} />
      ) : studied.data ? (
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
    <Panel padded>
      <View style={[styles.row, { flexWrap: 'wrap' }]}>
        <Text variant="titleMedium" style={{ flexShrink: 1 }}>
          {template.title}
        </Text>
        {template.optional ? <Badge label={CARD_OPTIONAL} /> : null}
        {template.kind === 'procedure' ? <Badge label={PROCEDURE} /> : null}
      </View>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {recallable ? recallLine(recalled, now) : FORM_NO_CASES}
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
            {HIDE_FORM}
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
    </Panel>
  );
}

type Studied = components['schemas']['Studied'];

// a rung and a probe each open the problem, with the card's technique drilled,
// and the card the sitting returns to
const openProblem = (problem: string, technique: string, card: string) =>
  router.push({ pathname: '/problem', params: { problem, technique, card } });

// what a run has reached, as the web's card reads it: the rungs solved, the
// forms recalled and the probes drawn, with the recall offered where a form
// carries cases to check it
function RunProgress({ studied }: { studied: Studied }) {
  const theme = useTheme();
  const p = cardProgress(studied);
  return (
    <Panel padded>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {[
          `${p.solved}/${p.rungs} ${RUNGS_SOLVED}`,
          `${p.recalled}/${p.forms} ${FORMS_RECALLED}`,
          `${p.probes} ${PROBES_DRAWN}`,
        ].join(' · ')}
      </Text>
      <ProgressBar
        progress={p.rungs === 0 ? 0 : p.solved / p.rungs}
        accessibilityLabel={`${RUNGS_SOLVED}: ${p.solved} / ${p.rungs}`}
        style={{ borderRadius: 2 }}
      />
      {p.recallable ? (
        <Button
          mode="outlined"
          icon="pencil-outline"
          style={{ alignSelf: 'flex-start' }}
          onPress={() => router.push({ pathname: '/recall', params: { slug: studied.card.slug } })}
        >
          {RECALL_TITLE}
        </Button>
      ) : null}
    </Panel>
  );
}

// the card's act once a run is open: the rung next, in the bar at the bottom
function NextRung({ studied, bottom }: { studied: Studied; bottom: number }) {
  const { next } = cardProgress(studied);
  if (!next) return null;
  return (
    <BottomBar bottom={bottom}>
      <Button
        mode="contained"
        icon="play"
        contentStyle={{ paddingVertical: 8 }}
        onPress={() => openProblem(next.problemId, studied.card.technique, studied.card.slug)}
      >
        {nextRung(next.title)}
      </Button>
    </BottomBar>
  );
}

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
              <PickRow
                key={rung.problemId}
                // solved since the run began: a reading, not a control
                lead={
                  rung.solved !== null ? (
                    <MaterialCommunityIcons
                      name={rung.solved ? 'checkbox-marked' : 'checkbox-blank-outline'}
                      size={18}
                      color={theme.colors.onSurfaceVariant}
                    />
                  ) : undefined
                }
                title={rung.title}
                badge={rung.difficulty}
                stats={[{ label: '', value: rung.need }]}
                note={rung.covers ?? undefined}
                onPress={() => openProblem(rung.problemId, studied.card.technique, studied.card.slug)}
              />
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
