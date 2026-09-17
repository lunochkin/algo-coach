import { PageHeader } from '@/components/PageHeader'

export function NotFoundPage() {
  return <PageHeader back={{ to: '/', label: 'Board' }} title="No page here" />
}
