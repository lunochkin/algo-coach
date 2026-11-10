import { File, Paths } from 'expo-file-system';

import { loadSnapshot, type Catalog, type Snapshot } from '@algo-coach/core';

const file = () => new File(Paths.document, 'courses.json');

export async function readCatalog(): Promise<Catalog | null> {
  const f = file();
  if (!f.exists) return null;
  return loadSnapshot(JSON.parse(await f.text()) as Snapshot);
}

/** Validates before writing, so a bad download never replaces a good cache. */
export async function writeCatalog(text: string): Promise<Catalog> {
  const cat = loadSnapshot(JSON.parse(text) as Snapshot);
  await file().write(text);
  return cat;
}
