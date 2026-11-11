import { ScrollView, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { privacyPolicy, privacyUpdated } from '@algo-coach/core';
import { styles, ScreenHeader } from '@/ui/common';
import { Markdown } from '@/ui/markdown';

const POLICY = privacyPolicy();

/** The privacy policy, the text the web serves at `/privacy`, held in the app so it reads offline. */
export default function PrivacyScreen() {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScreenHeader title={POLICY.title} />
      <ScrollView contentContainerStyle={[styles.page, { paddingBottom: insets.bottom + 24 }]}>
        {POLICY.updated ? (
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {privacyUpdated(POLICY.updated)}
          </Text>
        ) : null}
        <Markdown>{POLICY.body}</Markdown>
      </ScrollView>
    </View>
  );
}
