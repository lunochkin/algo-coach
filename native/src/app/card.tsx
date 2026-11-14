import { MaterialCommunityIcons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Button, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  judgeFrom,
  RECALL_THIS,
  RECALL_TITLE,
  type components,
  ladderView,
  LADDER_GAP,
  LADDER_TITLE,
  PROBES_ASIDE,
  PROBES_TITLE,
  probeState,
  RUN_START_NOTE,
  runLock,
  runStartLabel,
  runStartRefused,
  OF,
  CARD_TRIGGER,
  briefParts,
  CARD_TEMPLATES,
  HIDE_FORM,
  cardNote,
  cardProgress,
  RUNGS_SOLVED,
  FORMS_RECALLED,
  PROBES_DRAWN,
  nextRung,
  templateView,
  cardSections,
  startCardRun,
} from '@climb/core';
import { engine } from '@/lib/engine';
import { getToken } from '@/lib/settings';
import { useStore } from '@/lib/store';
import { useEngine } from '@/lib/useEngine';
import { BottomBar, CodeBlock, Loaded, styles, Press, ScreenHeader } from '@/ui/common';
import { Markdown } from '@/ui/markdown';
import { Badge, Panel, PickPanel, PickRow, Progress, Stat, Stats } from '@/ui/rows';
import { PageSection, type Sections, SectionBar, useSections } from '@/ui/sections';
import { usePullSync } from '@/ui/pull';
import { space } from '@/ui/tokens';

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
  const pull = usePullSync(studied.reload);
  const [now] = useState(() => Date.now());
  const card = studied.data?.card;
  const recall = new Map((studied.data?.recall ?? []).map((one) => [one.template_id, one]));

  const sections = useSections(cardSections(studied.data));

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={card?.title ?? slug} note={[studied.data ? cardNote(studied.data, now) : card?.technique]} />
      <SectionBar sections={sections} />
      <ScrollView
        refreshControl={pull}
        ref={sections.scroll}
        onScroll={sections.onScroll}
        onScrollBeginDrag={sections.onScrollBeginDrag}
        scrollEventThrottle={32}
        // room under the last template for the run's press over it
        contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + (studied.data ? 140 : 24) }]}
      >
        <Loaded of={OF.card} state={studied}>
          {(data) => (
            <>
              {data.run ? <RunProgress studied={data} /> : null}
              <Text
                variant="bodyMedium"
                accessibilityRole="link"
                onPress={() => router.push({ pathname: '/judge', params: { card: data.card.slug } })}
                style={{ color: theme.colors.primary }}
              >
                {judgeFrom(data.card.title)}
              </Text>
              <PageSection of={sections} id="trigger" title={CARD_TRIGGER}>
                <Markdown>{data.card.trigger}</Markdown>
              </PageSection>
              {briefParts(data.card.brief).map((part) => (
                <PageSection key={part.id} of={sections} id={part.id} title={part.title}>
                  <Markdown>{part.text}</Markdown>
                </PageSection>
              ))}
              <Ladder studied={data} of={sections} />
              {data.probes.length > 0 ? <Probes studied={data} of={sections} /> : null}
              <PageSection of={sections} id="templates" title={CARD_TEMPLATES} count={data.card.templates.length}>
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
        <RunStart slug={slug} lock={runLock(studied.data.waiting)} bottom={insets.bottom} onStarted={studied.reload} />
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
  const view = templateView(template, recalled, now);

  return (
    <Panel padded>
      <View style={[styles.row, { flexWrap: 'wrap' }]}>
        <Text variant="titleMedium" style={{ flexShrink: 1 }}>
          {template.title}
        </Text>
        {view.badges.map((badge) => (
          <Badge key={badge} label={badge} />
        ))}
      </View>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {view.status}
      </Text>
      <Markdown>{template.trigger}</Markdown>
      {view.recallable ? (
        <Button
          mode="contained-tonal"
          icon="pencil-outline"
          style={{ alignSelf: 'flex-start' }}
          onPress={() => router.push({ pathname: '/recall', params: { slug: card, template: template.slug } })}
        >
          {RECALL_THIS}
        </Button>
      ) : (
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {view.unchecked}
        </Text>
      )}
      {revealed ? (
        <>
          <CodeBlock code={template.code} verbatim wrap />
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
          {view.reveal}
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
  const p = cardProgress(studied);
  return (
    <Panel padded>
      <Stats>
        <Stat value={`${p.solved}/${p.rungs}`} label={RUNGS_SOLVED} />
        <Stat value={`${p.recalled}/${p.forms}`} label={FORMS_RECALLED} />
        <Stat value={p.probes} label={PROBES_DRAWN} />
      </Stats>
      <Progress value={p.solved} total={p.rungs} label={RUNGS_SOLVED} />
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
      <Press icon="play" onPress={() => openProblem(next.problemId, studied.card.technique, studied.card.slug)}>
        {nextRung(next.title)}
      </Press>
    </BottomBar>
  );
}

function Ladder({ studied, of }: { studied: Studied; of: Sections }) {
  const theme = useTheme();
  const view = ladderView(studied);
  const muted = { color: theme.colors.onSurfaceVariant };
  return (
    <PageSection of={of} id="ladder" title={LADDER_TITLE} count={view.count} aside={view.aside}>
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
              <View key={gap} style={[styles.row, { paddingHorizontal: space[4], paddingVertical: space[3] }]}>
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
    <PageSection of={of} id="probes" title={PROBES_TITLE} count={studied.probes.length} aside={PROBES_ASIDE}>
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
// bottom with the note on what it measures. Starting draws the probes. A locked
// card names what it waits on there instead, and its press stays disabled
function RunStart({
  slug,
  lock,
  bottom,
  onStarted,
}: {
  slug: string;
  lock: string | null;
  bottom: number;
  onStarted: () => void;
}) {
  const theme = useTheme();
  const st = useStore();
  const [starting, setStarting] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const start = async () => {
    setStarting(true);
    setRefused(null);
    // a refusal is named on the bar, never read as a run that started
    const started = await startCardRun(engine(st.settings.origin, await getToken()), slug);
    setStarting(false);
    if (started.ok) onStarted();
    else setRefused(started.refused);
  };
  return (
    <BottomBar
      bottom={bottom}
      above={
        <Text variant="bodySmall" style={{ color: refused ? theme.colors.error : theme.colors.onSurfaceVariant }}>
          {refused ? runStartRefused(refused) : (lock ?? RUN_START_NOTE)}
        </Text>
      }
    >
      <Press onPress={() => void start()} disabled={starting || lock !== null}>
        {runStartLabel(starting, lock !== null)}
      </Press>
    </BottomBar>
  );
}
