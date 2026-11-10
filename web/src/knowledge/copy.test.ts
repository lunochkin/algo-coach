import 'fake-indexeddb/auto'

import { afterEach, describe, expect, it } from 'vitest'

import { Copy, eraseCopy, type Cursor, type Line, type Transport } from '@/knowledge/copy'

const USER = 'u-4f9c2a'
const T = '2026-11-10T10:00:00.000Z'

// the engine as the copy sees it: a snapshot behind an ETag, and a log
function fakeEngine(user = USER) {
  const log: Line[] = []
  const sent: Line[][] = []
  let snapshots = 0
  const transport: Transport = {
    async snapshot(etag) {
      snapshots += 1
      return etag === 'v1' ? null : { text: '{"courses":[]}', etag: 'v1' }
    },
    async sync(records: Line[], since: Cursor) {
      sent.push(records)
      for (const one of records) {
        if (!log.some((x) => x.client_id === one.client_id)) log.push({ ...one, device: 'web' })
      }
      const after = since.all ?? 0
      return { user_id: user, records: log.slice(after), cursor: { all: log.length } }
    },
  }
  return { transport, log, sent, snapshots: () => snapshots }
}

// a copy left open blocks the erase the next test starts from
const opened: Copy[] = []
async function open(transport: Transport, user = USER) {
  const copy = await Copy.open(user, transport)
  opened.push(copy)
  return copy
}

afterEach(async () => {
  for (const copy of opened.splice(0)) copy.close()
  await eraseCopy(USER)
})

describe('the copy', () => {
  it('keeps a record in the outbox until the engine has it', async () => {
    const engine = fakeEngine()
    const copy = await open(engine.transport)
    await copy.add('order', { t: T, courses: ['python'] })
    expect(await copy.outbox()).toBe(1)

    await copy.sync()

    expect(await copy.outbox()).toBe(0)
    expect(engine.log.map((x) => x.kind)).toEqual(['order'])
  })

  it('takes the records another device wrote, once', async () => {
    const engine = fakeEngine()
    engine.log.push({ kind: 'setting', client_id: 'p1', device: 'phone', t: T, name: 'exam_size', n: 25 })
    const copy = await open(engine.transport)

    expect((await copy.sync()).logChanged).toBe(true)
    expect((await copy.sync()).logChanged).toBe(false)
    const [held] = await copy.records()
    expect([held.kind, held.device, held.line.n]).toEqual(['setting', 'phone', 25])
  })

  it('sends from the cursor it kept, so a second sync asks for nothing old', async () => {
    const engine = fakeEngine()
    const copy = await open(engine.transport)
    await copy.add('order', { t: T, courses: ['python'] })
    await copy.sync()
    await copy.sync()

    expect(engine.sent.map((x) => x.length)).toEqual([1, 0])
  })

  it('keeps the snapshot its ETag still names', async () => {
    const engine = fakeEngine()
    const copy = await open(engine.transport)

    expect((await copy.sync()).contentChanged).toBe(true)
    expect((await copy.sync()).contentChanged).toBe(false)
    expect(await copy.snapshot()).toBe('{"courses":[]}')
  })

  it('outlives the page: a reopened copy reads what the last one kept', async () => {
    const engine = fakeEngine()
    const first = await open(engine.transport)
    await first.add('order', { t: T, courses: ['python'] })
    first.close()
    const again = await open(engine.transport)
    expect(await again.outbox()).toBe(1)
  })

  it("refuses a reply naming another user's log", async () => {
    const copy = await open(fakeEngine('u-7d31b0').transport)

    await expect(copy.sync()).rejects.toThrow('another user')
  })

  it('is gone once erased', async () => {
    const engine = fakeEngine()
    const copy = await open(engine.transport)
    await copy.add('order', { t: T, courses: ['python'] })
    copy.close()
    await eraseCopy(USER)
    const again = await open(engine.transport)
    expect(await again.records()).toEqual([])
  })
})
