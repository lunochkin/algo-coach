import { Link, useParams } from 'react-router'

import { Button } from '@/components/ui/button'

export function TechniquePage() {
  const { technique } = useParams<{ technique: string }>()

  return (
    <section className="space-y-4">
      <Button variant="outline" asChild>
        <Link to="/">Back to the board</Link>
      </Button>
      <h1 className="text-2xl font-semibold">{technique}</h1>
    </section>
  )
}
