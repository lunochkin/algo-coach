// Draws Mermaid sources to SVG, once in the light scheme and once in the dark:
// `knowledge.md`, Diagrams. Reads a JSON list of sources on stdin, and writes
// {"tool": version, "drawings": [{"light", "dark"}, ...]} in the same order.
// `--version` prints the version alone, which the seed keys its drawings by.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { text } from 'node:stream/consumers';

import { renderMermaid } from '@mermaid-js/mermaid-cli';
import puppeteer from 'puppeteer';

import { prepare } from './prepare.mjs';

const HERE = new URL('.', import.meta.url);

// a change to the pinned packages or to either script draws every source again
function version() {
  const hash = createHash('sha256');
  for (const name of ['package-lock.json', 'draw.mjs', 'prepare.mjs']) hash.update(readFileSync(new URL(name, HERE)));
  return hash.digest('hex').slice(0, 16);
}

// labels as SVG text: the phone draws no HTML inside an SVG
const CONFIG = { htmlLabels: false, flowchart: { htmlLabels: false } };
const SCHEMES = { light: 'default', dark: 'dark' };

async function draw(browser, source, theme) {
  const { data } = await renderMermaid(browser, source, 'svg', {
    backgroundColor: 'transparent',
    mermaidConfig: { ...CONFIG, theme },
    fontEmbed: false,
    svgId: 'd',
  });
  const prefix = 'm' + createHash('sha256').update(source).digest('hex').slice(0, 8);
  return prepare(new TextDecoder().decode(data), prefix);
}

async function main() {
  if (process.argv.includes('--version')) {
    process.stdout.write(version() + '\n');
    return;
  }
  const sources = JSON.parse(await text(process.stdin));
  const browser = await puppeteer.launch({ headless: true });
  try {
    const drawings = [];
    for (const [i, source] of sources.entries()) {
      try {
        drawings.push({ light: await draw(browser, source, SCHEMES.light), dark: await draw(browser, source, SCHEMES.dark) });
      } catch (e) {
        process.stderr.write(`source ${i}: ${e.message}\n${source}\n`);
        process.exitCode = 1;
        return;
      }
    }
    process.stdout.write(JSON.stringify({ tool: version(), drawings }));
  } finally {
    await browser.close();
  }
}

await main();
