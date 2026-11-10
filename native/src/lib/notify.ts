import * as Notifications from 'expo-notifications';

import { earliestReview, nextReminderAt, reviewCount, type Board } from '@algo-coach/core';

import { getMeta, setMeta } from './db';
import { APP_NAME } from './name';

const CHANNEL = 'reminders';

async function permitted(): Promise<boolean> {
  await Notifications.setNotificationChannelAsync(CHANNEL, {
    name: 'Review reminders',
    importance: Notifications.AndroidImportance.DEFAULT,
  });
  const cur = await Notifications.getPermissionsAsync();
  if (cur.granted) return true;
  // Ask once, the first time a reminder would be scheduled.
  if (await getMeta('notify_asked')) return false;
  await setMeta('notify_asked', '1');
  return (await Notifications.requestPermissionsAsync()).granted;
}

/** One local notification at the first reminder hour at or after reviews become available. */
/** A signed-out device reminds nobody of a log it no longer holds. */
export async function cancelReminders(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
}

export async function scheduleReminder(b: Board, hour: number): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
  const now = Date.now();
  const first = earliestReview(b, now);
  if (first === null) return;
  const at = nextReminderAt(Math.max(first, now + 60_000), hour);
  const n = reviewCount(b, at);
  if (n === 0 || !(await permitted())) return;
  await Notifications.scheduleNotificationAsync({
    content: { title: APP_NAME, body: `${n} ${n === 1 ? 'review' : 'reviews'} due` },
    trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: at, channelId: CHANNEL },
  });
}
