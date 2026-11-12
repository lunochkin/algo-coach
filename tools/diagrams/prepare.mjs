import { optimize } from 'svgo';

// What react-native-svg, the phone's drawer, cannot read in Mermaid's own
// SVG, and the seed fixes: `knowledge.md`, Diagrams.

const svgo = (prefix) => ({
  multipass: true,
  plugins: [
    { name: 'inlineStyles', params: { onlyMatchedOnce: false, removeMatchedSelectors: true } },
    'convertStyleToAttrs',
    {
      name: 'preset-default',
      // moving an edge's marker-end onto its group loses the arrowhead
      params: { overrides: { inlineStyles: false, moveElemsAttrsToGroup: false, moveGroupAttrsToElems: false } },
    },
    'removeStyleElement',
    { name: 'removeAttrs', params: { attrs: ['data-.*', 'class', 'aria-.*'] } },
    // a page drawing several diagrams would otherwise resolve one's url(#a) in another
    { name: 'prefixIds', params: { prefix, delim: '' } },
  ],
});

const ENTITIES = { '&gt;': '>', '&lt;': '<', '&amp;': '&', '&quot;': '"', '&apos;': "'", '&#39;': "'" };

/** One label's words, each its own span, joined: the phone places nested spans apart. */
export function joinWords(svg) {
  return svg.replace(/<tspan[^>]*class="text-inner-tspan"[^>]*>([^<]*)<\/tspan>/g, '$1');
}

/** Markers inside `<defs>`, where the phone does not draw them as shapes, each child painted as its marker. */
export function markersInDefs(svg) {
  const markers = (svg.match(/<marker[\s\S]*?<\/marker>/g) ?? []).map(paintChildren);
  if (!markers.length) return svg;
  const rest = svg.replace(/<marker[\s\S]*?<\/marker>/g, '');
  return rest.replace(/(<svg[^>]*>)/, `$1<defs>${markers.join('')}</defs>`);
}

// the phone passes no fill or stroke from a marker down to its paths
function paintChildren(marker) {
  const open = marker.match(/^<marker[^>]*>/)[0];
  const paint = ['fill', 'stroke'].flatMap((a) => {
    const m = open.match(new RegExp(` ${a}="([^"]*)"`));
    return m ? [[a, m[1]]] : [];
  });
  return marker.replace(/<(path|circle|polygon|rect)\b([^>]*?)(\/?)>/g, (tag, name, attrs, close) => {
    const added = paint.filter(([a]) => !new RegExp(` ${a}=`).test(attrs)).map(([a, v]) => ` ${a}="${v}"`);
    return `<${name}${attrs}${added.join('')}${close}>`;
  });
}

/** Text with its entities decoded, since the phone reads text raw up to the next `<`; a `<` goes in CDATA. */
export function plainText(svg) {
  return svg.replace(/>([^<]+)</g, (_, text) => {
    const plain = text.replace(/&(gt|lt|amp|quot|apos|#39);/g, (e) => ENTITIES[e]);
    return '>' + (plain.includes('<') ? `<![CDATA[${plain}]]>` : plain) + '<';
  });
}

/** Mermaid's SVG as the phone and the web both draw it, its ids opening on `prefix`. */
export function prepare(svg, prefix) {
  return plainText(markersInDefs(optimize(joinWords(svg), svgo(prefix)).data));
}
