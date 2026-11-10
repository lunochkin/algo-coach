import { api } from '@/api/client'
import { described } from '@/api/useLoaded'
import { DEVICE, type Transport } from '@/knowledge/copy'

// the engine's two knowledge endpoints, as the copy reads them
export const engine: Transport = {
  async snapshot(etag) {
    const response = await fetch('/api/knowledge/snapshot', {
      headers: etag ? { 'if-none-match': etag } : {},
    })
    if (response.status === 304) return null
    if (!response.ok) throw new Error(`the snapshot answered ${response.status}`)
    return { text: await response.text(), etag: response.headers.get('etag') ?? '' }
  },
  async sync(records, since) {
    const { data, error } = await api.POST('/api/knowledge/sync', {
      body: { device: DEVICE, records, since },
    })
    if (data === undefined) throw new Error(described(error))
    return { user_id: data.user_id, records: data.records, cursor: data.cursor }
  },
}
