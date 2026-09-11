import { Link } from 'react-router'

import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">No page here</h1>
      <Button variant="outline" asChild>
        <Link to="/">Back to the board</Link>
      </Button>
    </section>
  )
}
