import { GOOD, replay } from './fsrs';
import { dayStart } from './queue';
import type { Board } from './schedule';
import type { Attempt } from './types';
import { FORECAST_TODAY, forecastSummary } from './words/home';

const DAY = 86_400_000;
export const FORECAST_DAYS = 14;

/** One learning day of the forecast: its start and the reviews falling in it. */
export interface DayLoad {
  start: number;
  reviews: number;
}

/**
 * Reviews per learning day over the next `days`, from the questions already seen in served
 * modules. Each review is assumed to pass: `knowledge.md`, Projections.
 */
export function reviewForecast(b: Board, now: number, days = FORECAST_DAYS, offsetMinutes?: number): DayLoad[] {
  const first = dayStart(now, offsetMinutes);
  // a day is 24 h from 04:00 local; a DST shift moves one boundary by an hour
  const out: DayLoad[] = Array.from({ length: days }, (_, i) => ({ start: first + i * DAY, reviews: 0 }));
  const end = first + days * DAY;
  for (const q of b.servedGroups().flat()) {
    const seen = b.attempts(q);
    if (!seen.length) continue;
    let mem = b.memory(q);
    const attempts: Attempt[] = [...seen];
    while (mem) {
      // an overdue review is owed today
      const t = Math.max(mem.due, now);
      if (t >= end) break;
      out[Math.floor((t - first) / DAY)].reviews++;
      attempts.push({ t, rating: GOOD });
      mem = replay(attempts, b.rules.fsrs);
    }
  }
  return out;
}

const WEEKDAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** A day's name, as "Thu 12 Nov", in the device's time zone; formatted here so both clients read it alike. */
export function dayName(start: number, offsetMinutes = -new Date(start).getTimezoneOffset()): string {
  const d = new Date(start + offsetMinutes * 60_000);
  return `${WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`;
}

export interface ForecastBar {
  reviews: number;
  day: string;
  today: boolean;
  labelled: boolean; // today and the busiest day carry their count; the rest read on hover or in the list
}

export interface ForecastView {
  bars: ForecastBar[];
  max: number;
  summary: string;
  first: string;
  last: string;
}

export function forecastView(days: DayLoad[], offsetMinutes?: number): ForecastView {
  const max = Math.max(0, ...days.map((d) => d.reviews));
  const busiest = days.findIndex((d) => d.reviews === max);
  const bars = days.map((d, i) => ({
    reviews: d.reviews,
    day: i === 0 ? FORECAST_TODAY : dayName(d.start, offsetMinutes),
    today: i === 0,
    labelled: i === 0 || (max > 0 && i === busiest),
  }));
  const sum = days.reduce((n, d) => n + d.reviews, 0);
  return {
    bars,
    max,
    summary: forecastSummary(sum, days.length, days[0]?.reviews ?? 0),
    first: FORECAST_TODAY,
    last: days.length ? dayName(days[days.length - 1].start, offsetMinutes) : '',
  };
}
