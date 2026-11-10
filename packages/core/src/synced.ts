/** A record the sync returned, split into the fields a merge reads and learn's line. */
export interface SyncedLine {
  kind: string;
  client_id: string;
  device: string;
  t: string;
  // the line as learn wrote it: every field but the kind, the client id and the device
  rest: Record<string, unknown>;
}

/**
 * A returned record's fields, checked rather than assumed: the schema types a record as
 * learn's free-form line. `null` where one is missing, so the merge skips the record
 * instead of writing it.
 */
export function syncedLine(record: Record<string, unknown>): SyncedLine | null {
  const { kind, client_id, device, ...rest } = record;
  if (typeof kind !== 'string' || typeof client_id !== 'string' || typeof device !== 'string') return null;
  if (typeof rest.t !== 'string') return null;
  return { kind, client_id, device, t: rest.t, rest };
}
