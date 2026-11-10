import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Button, Card, Chip, Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { readFailure, recallLine, revealLabel, type components } from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { CodeBlock, Failed, styles } from '@/ui/common';
import { Markdown } from '@/ui/markdown';

type Studied = components['schemas']['Studied'];
type Template = components['schemas']['Template'];
type Recalled = components['schemas']['Recalled'];

/**
 * A card's trigger, brief and templates, each form hidden until revealed:
 * `content.md`, Cards. The ladder, the probes and the recall stay on the web,
 * since each opens a sitting or the trainer.
 */
export default function CardScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { slug = '' } = useLocalSearchParams<{ slug: string }>();
  const studied = useEngine<Studied>(`/cards/${encodeURIComponent(slug)}`);
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
          <Text variant="bodyMedium">Reading the card…</Text>
        ) : (
          <>
            <Text variant="titleMedium">When to reach for it</Text>
            <Markdown>{card.trigger}</Markdown>
            <Text variant="titleMedium">The brief</Text>
            <Markdown>{card.brief}</Markdown>
            <Text variant="titleMedium">
              Templates <Text style={{ color: theme.colors.onSurfaceVariant }}>{card.templates.length}</Text>
            </Text>
            {card.templates.map((template) => (
              <TemplateCard key={template.slug} template={template} recalled={recall.get(template.id)} now={now} />
            ))}
          </>
        )}
      </ScrollView>
    </View>
  );
}

function TemplateCard({ template, recalled, now }: { template: Template; recalled: Recalled | undefined; now: number }) {
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
          {template.kind === 'procedure' ? <Chip compact mode="outlined">procedure</Chip> : null}
        </View>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
          {recallable ? recallLine(recalled, now) : 'No case checks this form'}
        </Text>
        <Markdown>{template.trigger}</Markdown>
        {revealed ? (
          <>
            <CodeBlock code={template.code} verbatim />
            {template.notes ? <Markdown>{template.notes}</Markdown> : null}
            <Button mode="text" onPress={() => setRevealed(false)} style={{ alignSelf: 'flex-end' }}>
              Hide the form
            </Button>
          </>
        ) : (
          <Button mode="outlined" icon="eye-outline" onPress={() => setRevealed(true)} style={{ alignSelf: 'flex-start' }}>
            {revealLabel(template.code)}
          </Button>
        )}
      </Card.Content>
    </Card>
  );
}
