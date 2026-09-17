import { LOGIN } from '@/api/client'
import { BackLink } from '@/components/BackLink'
import { Markdown } from '@/components/Markdown'
import policy from '@/pages/privacy.md?raw'

export function PrivacyPage() {
  return (
    <article className="space-y-stack">
      {/* the way back, and no section: the page opens with no session, and the
          policy's own heading is its title */}
      <BackLink to={LOGIN} label="Sign in" />
      <Markdown>{policy}</Markdown>
    </article>
  )
}
