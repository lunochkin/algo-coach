import { useIsFocused } from 'expo-router';
import type { ReactNode } from 'react';
import { Freeze } from 'react-freeze';

// a tab out of view skips the store's every change until it is back in view;
// Expo Router turns the navigators' own `freezeOnBlur` off
export function Frozen({ children }: { children: ReactNode }) {
  return <Freeze freeze={!useIsFocused()}>{children}</Freeze>;
}
