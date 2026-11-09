import { LOGIN } from '@/api/client'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'
import policy from '@/pages/privacy.md?raw'

// the file opens with its title and the date it was last updated. Both are
// the page's header, so they are taken off the prose rather than printed
// twice
const TITLE = /^#\s+(.+)$/m.exec(policy)?.[1] ?? 'Privacy policy'
const UPDATED = /^Last updated:\s*(.+)$/m.exec(policy)?.[1] ?? null
const BODY = policy.replace(/^#\s+.+$/m, '').replace(/^Last updated:.*$/m, '').trimStart()

export function PrivacyPage() {
  return (
    <article className="space-y-section">
      {/* the login is the page this one is reached from, so it is the way
          back. No section: the page opens with no session */}
      <PageHeader
        back={{ to: LOGIN, label: 'Sign in' }}
        title={TITLE}
        note={UPDATED && `Last updated ${UPDATED}`}
      />
      <Markdown>{BODY}</Markdown>
    </article>
  )
}
