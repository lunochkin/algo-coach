import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { Appbar, Chip, Text, TouchableRipple, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { problemCards, problemTried, readFailure, type components } from '@algo-coach/core';
import { useEngine } from '@/lib/useEngine';
import { CodeBlock, Failed, styles } from '@/ui/common';
import { Markdown } from '@/ui/markdown';

type Picked = components['schemas']['Picked'];
type Served = components['schemas']['Served'];
type ListedCard = components['schemas']['ListedCard'];

/**
 * A problem's record and its statement, with no editor and no clock: the
 * sitting stays on the web. Reading the statement mints nothing, as
 * `log.md` gives.
 */
export default function ProblemScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { problem = '', technique } = useLocalSearchParams<{ problem: string; technique?: string }>();
  const path = `/problems/${encodeURIComponent(problem)}`;
  const picked = useEngine<Picked>(path);
  // a retired problem is refused its statement, and reads as its record alone
  const served = useEngine<Served>(picked.data && !picked.data.retired ? `${path}/statement` : null);
  const listed = useEngine<ListedCard[]>('/cards');
  const error = picked.error ?? served.error ?? listed.error;
  const [now] = useState(() => Date.now());
  const record = picked.data;
  const cards = record ? problemCards(listed.data ?? [], record.techniques, technique ?? null) : [];
  const muted = { color: theme.colors.onSurfaceVariant };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={record?.title ?? 'The problem'} />
      </Appbar.Header>
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        {error ? (
          <Failed
            message={readFailure('the problem', error)}
            onRetry={() => {
              picked.reload();
              served.reload();
              listed.reload();
            }}
          />
        ) : !record || listed.data === null || (!record.retired && served.data === null) ? (
          <Text variant="bodyMedium">Reading the problem…</Text>
        ) : (
          <>
            <View style={[styles.row, { flexWrap: 'wrap' }]}>
              {record.difficulty ? (
                <Chip compact mode="outlined">
                  {record.difficulty}
                </Chip>
              ) : null}
              <Text variant="bodySmall" style={muted}>
                {record.techniques.join(' · ')}
              </Text>
              <Text variant="bodySmall" style={muted}>
                {problemTried(record, now)}
              </Text>
            </View>
            {cards.length > 0 ? (
              <View style={[styles.row, { flexWrap: 'wrap' }]}>
                <Text variant="bodySmall" style={muted}>
                  {cards.length === 1 ? 'Card:' : 'Cards:'}
                </Text>
                {cards.map((card) => (
                  <TouchableRipple
                    key={card.slug}
                    accessibilityRole="link"
                    onPress={() => router.push({ pathname: '/card', params: { slug: card.slug } })}>
                    <Text variant="bodySmall" style={{ color: theme.colors.primary }}>
                      {card.title}
                    </Text>
                  </TouchableRipple>
                ))}
              </View>
            ) : null}
            {record.retired ? (
              <Text variant="bodyMedium">
                This problem was retired: its statement asked for something its cases do not decide. It is served to
                nobody, and your attempts on it stay in your log.
              </Text>
            ) : served.data ? (
              <>
                <Markdown>{served.data.statement}</Markdown>
                {served.data.signature ? <CodeBlock code={served.data.signature} verbatim /> : null}
                <Text variant="bodySmall" style={muted}>
                  The problem is solved on the web, where the editor and the clock are.
                </Text>
              </>
            ) : null}
          </>
        )}
      </ScrollView>
    </View>
  );
}
