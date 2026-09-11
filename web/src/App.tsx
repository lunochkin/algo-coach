import { lazy, Suspense } from 'react'
import { Route, Routes, useMatch } from 'react-router'

import { NavMenu } from '@/components/NavMenu'
import { cn } from '@/lib/utils'
import { BoardPage } from '@/pages/BoardPage'
import { CardsPage } from '@/pages/CardsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ProblemPage } from '@/pages/ProblemPage'
import { TechniquePage } from '@/pages/TechniquePage'

// loaded when first opened: the editor and the markdown with its math are most
// of the bundle, and the board needs neither
const CardPage = lazy(() => import('@/pages/CardPage').then((m) => ({ default: m.CardPage })))
const SittingPage = lazy(() =>
  import('@/pages/SittingPage').then((m) => ({ default: m.SittingPage })),
)

function App() {
  // the statement and the editor sit side by side, which a reading column is
  // too narrow for
  const wide = useMatch('/sittings/:sittingId') !== null

  return (
    <>
      <NavMenu />
      <main className={cn('mx-auto p-6', wide ? 'max-w-screen-2xl' : 'max-w-4xl')}>
        <Suspense fallback={<p className="text-muted-foreground">Loading…</p>}>
          <Routes>
            {/* the board is where every sitting starts: the user picks the
                technique, never a problem id */}
            <Route index element={<BoardPage />} />
            <Route path="cards" element={<CardsPage />} />
            <Route path="cards/:slug" element={<CardPage />} />
            <Route path="techniques/:technique" element={<TechniquePage />} />
            <Route path="techniques/:technique/problems/:problemId" element={<ProblemPage />} />
            <Route path="sittings/:sittingId" element={<SittingPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </main>
    </>
  )
}

export default App
