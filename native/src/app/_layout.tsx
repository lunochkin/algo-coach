import { useMaterial3Theme } from '@pchmn/expo-material3-theme';
import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useMemo } from 'react';
import { useColorScheme, View } from 'react-native';
import { MD3DarkTheme, MD3LightTheme, PaperProvider, useTheme } from 'react-native-paper';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { KeyboardProvider } from 'react-native-keyboard-controller';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';

import { StoreProvider } from '@/lib/store';

export default function RootLayout() {
  const dark = useColorScheme() === 'dark';
  const { theme: m3 } = useMaterial3Theme();
  const paper = useMemo(
    () => (dark ? { ...MD3DarkTheme, colors: m3.dark } : { ...MD3LightTheme, colors: m3.light }),
    [dark, m3],
  );
  const nav = useMemo(() => {
    const base = dark ? DarkTheme : DefaultTheme;
    const c = paper.colors;
    return {
      ...base,
      colors: {
        ...base.colors,
        primary: c.primary,
        background: c.background,
        card: c.surface,
        text: c.onSurface,
        border: c.outlineVariant,
        notification: c.error,
      },
    };
  }, [dark, paper]);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <KeyboardProvider>
          <PaperProvider theme={paper}>
            <ThemeProvider value={nav}>
              <StoreProvider>
                <StatusBar style="auto" />
                <Stack screenOptions={{ headerShown: false }} />
                <NavigationScrim />
              </StoreProvider>
            </ThemeProvider>
          </PaperProvider>
        </KeyboardProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

// the app draws edge to edge, and a three-button bar shows no ground of its
// own: a page scrolling under it would read through the buttons. Paper's
// dialogs and sheets portal above this
function NavigationScrim() {
  const { bottom } = useSafeAreaInsets();
  const theme = useTheme();
  if (bottom === 0) return null;
  return (
    <View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        height: bottom,
        backgroundColor: theme.colors.background,
      }}
    />
  );
}
