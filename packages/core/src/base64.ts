const ABC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
const INDEX = new Map([...ABC].map((c, i) => [c, i]));

export function utf8Encode(s: string): number[] {
  const out: number[] = [];
  for (const ch of s) {
    const c = ch.codePointAt(0) as number;
    if (c < 0x80) out.push(c);
    else if (c < 0x800) out.push(0xc0 | (c >> 6), 0x80 | (c & 63));
    else if (c < 0x10000) out.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    else out.push(0xf0 | (c >> 18), 0x80 | ((c >> 12) & 63), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
  }
  return out;
}

export function utf8Decode(b: Uint8Array): string {
  const parts: string[] = [];
  let chunk: number[] = [];
  for (let i = 0; i < b.length;) {
    const x = b[i];
    let c: number;
    if (x < 0x80) ((c = x), (i += 1));
    else if (x < 0xe0) ((c = ((x & 31) << 6) | (b[i + 1] & 63)), (i += 2));
    else if (x < 0xf0) ((c = ((x & 15) << 12) | ((b[i + 1] & 63) << 6) | (b[i + 2] & 63)), (i += 3));
    else ((c = ((x & 7) << 18) | ((b[i + 1] & 63) << 12) | ((b[i + 2] & 63) << 6) | (b[i + 3] & 63)), (i += 4));
    if (c >= 0x10000) {
      c -= 0x10000;
      chunk.push(0xd800 + (c >> 10), 0xdc00 + (c & 1023));
    } else chunk.push(c);
    if (chunk.length >= 8192) {
      parts.push(String.fromCharCode(...chunk));
      chunk = [];
    }
  }
  parts.push(String.fromCharCode(...chunk));
  return parts.join('');
}

export function encodeBase64(s: string): string {
  const b = utf8Encode(s);
  let out = '';
  for (let i = 0; i < b.length; i += 3) {
    const n = (b[i] << 16) | ((b[i + 1] ?? 0) << 8) | (b[i + 2] ?? 0);
    out += ABC[(n >> 18) & 63] + ABC[(n >> 12) & 63];
    out += i + 1 < b.length ? ABC[(n >> 6) & 63] : '=';
    out += i + 2 < b.length ? ABC[n & 63] : '=';
  }
  return out;
}

/** Decodes base64 (GitHub wraps it with newlines) into a UTF-8 string. */
export function decodeBase64(b64: string): string {
  const clean = b64.replace(/[^A-Za-z0-9+/]/g, '');
  const bytes = new Uint8Array(Math.floor((clean.length * 3) / 4));
  let j = 0;
  for (let i = 0; i < clean.length; i += 4) {
    const n =
      ((INDEX.get(clean[i]) ?? 0) << 18) |
      ((INDEX.get(clean[i + 1]) ?? 0) << 12) |
      ((INDEX.get(clean[i + 2]) ?? 0) << 6) |
      (INDEX.get(clean[i + 3]) ?? 0);
    bytes[j++] = (n >> 16) & 255;
    if (i + 2 < clean.length) bytes[j++] = (n >> 8) & 255;
    if (i + 3 < clean.length) bytes[j++] = n & 255;
  }
  return utf8Decode(bytes.subarray(0, j));
}
