import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { useColorScheme } from 'react-native';

import type { SchemeChoice } from '@algo-coach/core';
import { getMeta, setMeta } from './db';

// about this phone rather than the account, so it stays on the device, as the
// web's scheme stays in the browser: `pages.md`, The design system
const KEY = 'scheme';

interface Scheme {
  choice: SchemeChoice;
  dark: boolean;
  choose: (choice: SchemeChoice) => void;
}

const Context = createContext<Scheme | null>(null);

export function SchemeProvider({ children }: { children: ReactNode }) {
  const system = useColorScheme();
  const [choice, setChoice] = useState<SchemeChoice>('system');
  useEffect(() => {
    void getMeta(KEY).then((v) => {
      if (v === 'light' || v === 'dark') setChoice(v);
    });
  }, []);
  const choose = useCallback((next: SchemeChoice) => {
    setChoice(next);
    void setMeta(KEY, next);
  }, []);
  const dark = choice === 'system' ? system === 'dark' : choice === 'dark';
  return <Context.Provider value={{ choice, dark, choose }}>{children}</Context.Provider>;
}

export function useScheme(): Scheme {
  const s = useContext(Context);
  if (!s) throw new Error('useScheme outside SchemeProvider');
  return s;
}
