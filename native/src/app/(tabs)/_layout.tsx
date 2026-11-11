import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Tabs } from 'expo-router/js-tabs';

import { SECTION_PRACTICE, SECTION_PROBLEMS, SECTION_CARDS, SECTION_KNOWLEDGE } from '@algo-coach/core';
import { Frozen } from '@/ui/frozen';

// the sections the phone holds, as bottom tabs: `pages.md`, The structure. A
// tab shows once the phone holds a page under its section, and a bar of one
// tab names nothing, so it shows from the second section on
const SECTIONS = [
  { name: 'index', title: SECTION_PRACTICE, icon: 'target' },
  { name: 'problems', title: SECTION_PROBLEMS, icon: 'format-list-bulleted' },
  { name: 'cards', title: SECTION_CARDS, icon: 'cards-outline' },
  { name: 'knowledge', title: SECTION_KNOWLEDGE, icon: 'brain' },
] as const;

// Practice opens first, as the board does on the web, and back from another tab
// returns there. It holds the redirect to the login, and its knowledge part
// serves offline from the device's copy: `pages.md`, The two clients
export const unstable_settings = { anchor: 'index' };

export default function TabsLayout() {
  return (
    <Tabs
      backBehavior="initialRoute"
      screenLayout={({ children }) => <Frozen>{children}</Frozen>}
      screenOptions={{
        headerShown: false,
        tabBarStyle: SECTIONS.length > 1 ? undefined : { display: 'none' },
      }}
    >
      {SECTIONS.map((s) => (
        <Tabs.Screen
          key={s.name}
          name={s.name}
          options={{
            title: s.title,
            tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name={s.icon} color={String(color)} size={size} />,
          }}
        />
      ))}
    </Tabs>
  );
}
