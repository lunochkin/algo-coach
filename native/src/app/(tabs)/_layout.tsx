import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Tabs } from 'expo-router/js-tabs';

// the sections the phone holds, as bottom tabs: `pages.md`, The structure. A
// tab shows once the phone holds a page under its section, and a bar of one
// tab names nothing, so it shows from the second section on
const SECTIONS = [
  { name: 'practice', title: 'Practice', icon: 'target' },
  { name: 'problems', title: 'Problems', icon: 'format-list-bulleted' },
  { name: 'cards', title: 'Cards', icon: 'cards-outline' },
  { name: 'index', title: 'Knowledge', icon: 'brain' },
] as const;

// Knowledge opens first, and back from another tab returns there: it holds the
// redirect to the login, and it serves offline where the board cannot
export const unstable_settings = { anchor: 'index' };

export default function TabsLayout() {
  return (
    <Tabs
      backBehavior="initialRoute"
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
