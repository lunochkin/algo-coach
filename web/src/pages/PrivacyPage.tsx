import { Markdown } from '@/components/Markdown'
import policy from '@/pages/privacy.md?raw'

export function PrivacyPage() {
  return <Markdown>{policy}</Markdown>
}
