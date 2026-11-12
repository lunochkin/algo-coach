import assert from 'node:assert/strict';
import { test } from 'node:test';

import { joinWords, markersInDefs, plainText, prepare } from './prepare.mjs';

const LABEL =
  '<text><tspan class="text-outer-tspan row" x="0"><tspan class="text-inner-tspan">trial</tspan>' +
  '<tspan class="text-inner-tspan"> fails</tspan></tspan></text>';

const MERMAID =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><style>.edge{stroke:#d3d3d3}</style>' +
  '<marker id="arrow" fill="#d3d3d3" stroke="#d3d3d3" viewBox="0 0 10 10"><path d="M0 0L10 5L0 10z"/></marker>' +
  '<g class="root"><path class="edge" fill="none" marker-end="url(#arrow)" d="M0 0V9"/>' +
  `<path class="edge" fill="none" marker-end="url(#arrow)" d="M5 0V9"/>${LABEL}</g></svg>`;

test('joins a label\'s words into its row, which the phone places as one', () => {
  assert.equal(joinWords(LABEL), '<text><tspan class="text-outer-tspan row" x="0">trial fails</tspan></text>');
});

test('moves markers into defs and paints their paths, which the phone leaves unpainted', () => {
  const out = markersInDefs('<svg a="1"><marker fill="#fff" stroke="#000"><path d="M0 0"/></marker><g/></svg>');
  assert.equal(out, '<svg a="1"><defs><marker fill="#fff" stroke="#000"><path d="M0 0" fill="#fff" stroke="#000"/></marker></defs><g/></svg>');
});

test('keeps a path\'s own paint inside a marker', () => {
  const out = markersInDefs('<svg><marker fill="#fff"><path fill="red"/></marker></svg>');
  assert.match(out, /<path fill="red"\/>/);
});

test('decodes entities in text, which the phone shows as written', () => {
  assert.equal(plainText('<text>failures &gt; threshold &amp; &quot;x&quot;</text>'), '<text>failures > threshold & "x"</text>');
});

test('wraps text holding a less-than sign in CDATA, since the phone ends text at the first one', () => {
  assert.equal(plainText('<text>a &lt; b</text>'), '<text><![CDATA[a < b]]></text>');
});

test('leaves each edge its own arrowhead, which moving it onto the group loses', () => {
  const out = prepare(MERMAID, 'p');
  assert.equal(out.match(/marker-end=/g).length, 2);
  assert.doesNotMatch(out, /<g[^>]*marker-end/);
});

test('inlines the styles and drops the style element, which the phone ignores', () => {
  const out = prepare(MERMAID, 'p');
  assert.doesNotMatch(out, /<style/);
  assert.equal(out.match(/<path fill="none" stroke="#d3d3d3"/g).length, 2);
});

test('opens every id on the prefix, so two diagrams on one page keep their own markers', () => {
  const out = prepare(MERMAID, 'p');
  const ids = [...out.matchAll(/id="([^"]+)"/g)].map((m) => m[1]);
  assert.ok(ids.length > 0 && ids.every((id) => id.startsWith('p')));
  assert.match(out, new RegExp(`url\\(#${ids[0]}\\)`));
});
