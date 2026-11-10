import { useMemo, useState, type ReactNode } from 'react';
import { ScrollView, View } from 'react-native';
import { Button, Chip, Dialog, Portal, Switch, Text } from 'react-native-paper';

import {
  levelName,
  levels,
  START_ALL,
  START_KIND,
  START_LEVEL,
  START_NOTHING,
  START_ONLY_REVIEWS,
  startPreview,
  startTitle,
} from '@algo-coach/core';
import { useStore } from '@/lib/store';
import { startQueue, styles } from '@/ui/common';

/** Where a filtered queue starts: a module, narrowed to a topic, a subtopic or one group. */
export interface Scope {
  course: string;
  topic: string | null;
  sub: string | null;
  level: number | null;
}

/** The sheet that starts a filtered queue, opened from a press on the module's screens. */
export function useStartSheet(): { open: (s: Scope) => void; sheet: ReactNode } {
  const [scope, setScope] = useState<Scope | null>(null);
  const sheet = scope ? <StartSheet key={JSON.stringify(scope)} scope={scope} onClose={() => setScope(null)} /> : null;
  return { open: setScope, sheet };
}

// the choices narrow this one queue, and starting it moves no focus: `knowledge.md`, Queues
function StartSheet({ scope, onClose }: { scope: Scope; onClose: () => void }) {
  const st = useStore();
  const [level, setLevel] = useState(scope.level);
  const [kind, setKind] = useState<string | null>(null);
  const [due, setDue] = useState(false);
  const { board } = st;
  // named explicitly, so a paused module serves too, as on the web
  const b = useMemo(() => board(scope.course), [board, scope.course]);
  const c = st.catalog?.courses.find((x) => x.slug === scope.course);
  const limit = st.newLimit;
  const preview = useMemo(
    () => (b ? startPreview(b, { ...scope, level, kind, due }, limit, Date.now()) : null),
    [b, scope, level, kind, due, limit],
  );
  if (!c) return null;

  const title = startTitle(c, scope);
  const start = () => {
    if (!preview || preview.empty) return;
    onClose();
    startQueue(st, 'drill', preview.queue, scope.course);
  };

  return (
    <Portal>
      <Dialog visible onDismiss={onClose} style={{ maxHeight: '85%' }}>
        <Dialog.Title>{title}</Dialog.Title>
        <Dialog.ScrollArea style={{ paddingHorizontal: 24 }}>
          <ScrollView contentContainerStyle={{ gap: 8, paddingVertical: 8 }}>
            <Text variant="titleSmall">{START_LEVEL}</Text>
            <View style={[styles.row, { flexWrap: 'wrap' }]}>
              <Chip selected={level === null} onPress={() => setLevel(null)}>
                {START_ALL}
              </Chip>
              {levels(st.catalog!.rules).map((l) => (
                <Chip key={l} selected={level === l} onPress={() => setLevel(level === l ? null : l)}>
                  {levelName(st.catalog!.rules, l)}
                </Chip>
              ))}
            </View>
            {c.kinds.length > 1 ? (
              <>
                <Text variant="titleSmall">{START_KIND}</Text>
                <View style={[styles.row, { flexWrap: 'wrap' }]}>
                  <Chip selected={kind === null} onPress={() => setKind(null)}>
                    {START_ALL}
                  </Chip>
                  {c.kinds.map((k) => (
                    <Chip key={k} selected={kind === k} onPress={() => setKind(kind === k ? null : k)}>
                      {k}
                    </Chip>
                  ))}
                </View>
              </>
            ) : null}
            <View style={styles.row}>
              <Switch value={due} onValueChange={setDue} />
              <Text variant="bodyMedium" onPress={() => setDue(!due)}>
                {START_ONLY_REVIEWS}
              </Text>
            </View>
          </ScrollView>
        </Dialog.ScrollArea>
        <Dialog.Actions>
          <Button onPress={onClose}>Cancel</Button>
          <Button mode="contained" icon="play" disabled={!preview || preview.empty} onPress={start}>
            {preview?.label ?? START_NOTHING}
          </Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
}
