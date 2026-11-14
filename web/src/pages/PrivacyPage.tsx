import { privacyPolicy, privacyUpdated, BACK_SIGN_IN } from '@climb/core'

import { LOGIN } from '@/api/client'
import { Markdown } from '@/components/Markdown'
import { PageHeader } from '@/components/PageHeader'

const POLICY = privacyPolicy()

export function PrivacyPage() {
  return (
    <article className="space-y-section">
      {/* the login is the page this one is reached from, so it is the way
          back. No section: the page opens with no session */}
      <PageHeader
        back={{ to: LOGIN, label: BACK_SIGN_IN }}
        title={POLICY.title}
        note={POLICY.updated && privacyUpdated(POLICY.updated)}
      />
      <Markdown>{POLICY.body}</Markdown>
    </article>
  )
}
