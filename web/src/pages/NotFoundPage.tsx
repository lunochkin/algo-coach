import { BACK_BOARD, NOT_FOUND } from '@climb/core'

import { PageHeader } from '@/components/PageHeader'

export function NotFoundPage() {
  return <PageHeader back={{ to: '/', label: BACK_BOARD }} title={NOT_FOUND} />
}
