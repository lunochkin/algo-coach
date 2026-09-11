import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { BoardPage } from '@/pages/BoardPage'

function App() {
  // the board is where every sitting starts: the user picks the technique,
  // never a problem id
  const [technique, setTechnique] = useState<string | null>(null)

  return (
    <main className="mx-auto max-w-4xl p-6">
      {technique === null ? (
        <BoardPage onPick={setTechnique} />
      ) : (
        <section className="space-y-4">
          <Button variant="outline" onClick={() => setTechnique(null)}>
            Back to the board
          </Button>
          <h1 className="text-2xl font-semibold">{technique}</h1>
        </section>
      )}
    </main>
  )
}

export default App
