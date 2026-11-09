import { useMaterial3Theme } from '@pchmn/expo-material3-theme';
import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useMemo } from 'react';
import { useColorScheme } from 'react-native';
import { MD3DarkTheme, MD3LightTheme, PaperProvider } from 'react-native-paper';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { KeyboardProvider } from 'react-native-keyboard-controller';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { StoreProvider } from '@/lib/store';

export default function RootLayout() {
  const dark = useColorScheme() === 'dark';
  const { theme: m3 } = useMaterial3Theme();
  const paper = useMemo(
    () =>
      dark ? { ...MD3DarkTheme, colors: m3.dark } : { ...MD3LightTheme, colors: m3.light },
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
          </StoreProvider>
        </ThemeProvider>
      </PaperProvider>
      </KeyboardProvider>
    </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
