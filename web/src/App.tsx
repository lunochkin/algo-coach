import { Fragment, lazy, Suspense } from 'react'
import { Route, Routes, useMatch } from 'react-router'

import { LOGIN, PRIVACY } from '@/api/client'
import { NavMenu } from '@/components/NavMenu'
import { KnowledgeProvider } from '@/knowledge/KnowledgeProvider'
import { cn } from '@/lib/utils'
import { BoardPage } from '@/pages/BoardPage'
import { CardsPage } from '@/pages/CardsPage'
import { KnowledgePage } from '@/pages/KnowledgePage'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ProblemPage } from '@/pages/ProblemPage'
import { ProblemsPage } from '@/pages/ProblemsPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { TechniquePage } from '@/pages/TechniquePage'

// loaded when first opened: the editor and the markdown with its math are most
// of the bundle, and the board needs neither
const CardPage = lazy(() => import('@/pages/CardPage').then((m) => ({ default: m.CardPage })))
const RecallPage = lazy(() =>
  import('@/pages/RecallPage').then((m) => ({ default: m.RecallPage })),
)
const DrawnRecallPage = lazy(() =>
  import('@/pages/RecallPage').then((m) => ({ default: m.DrawnRecallPage })),
)
const SittingPage = lazy(() =>
  import('@/pages/SittingPage').then((m) => ({ default: m.SittingPage })),
)
const PrivacyPage = lazy(() =>
  import('@/pages/PrivacyPage').then((m) => ({ default: m.PrivacyPage })),
)
// the ternary folds in a production build, so the gallery and every example it
// renders leave the bundle
const GalleryPage = import.meta.env.DEV
  ? lazy(() => import('@/pages/GalleryPage').then((m) => ({ default: m.GalleryPage })))
  : null

function App() {
  // the statement and the editor sit side by side, which a reading column is
  // too narrow for
  const wide = useMatch('/sittings/:sittingId') !== null
  // nothing in the menu is reachable before signing in, and both pages open
  // without a session
  const signingIn = useMatch(LOGIN) !== null
  const readingPolicy = useMatch(PRIVACY) !== null

  // the copy is kept for a session alone: both pages open without one
  const Session = signingIn || readingPolicy ? Fragment : KnowledgeProvider

  return (
    <Session>
      {!signingIn && !readingPolicy && <NavMenu wide={wide} />}
      <main className={cn('mx-auto p-gutter', wide ? 'max-w-wide' : 'max-w-reading')}>
        <Suspense fallback={<p className="text-muted-foreground">Loading…</p>}>
          <Routes>
            {/* the board is where every sitting starts: the user picks the
                technique, never a problem id */}
            <Route index element={<BoardPage />} />
            <Route path="problems" element={<ProblemsPage />} />
            <Route path="cards" element={<CardsPage />} />
            <Route path="cards/:slug" element={<CardPage />} />
            <Route path="cards/:slug/recall" element={<DrawnRecallPage />} />
            <Route path="cards/:slug/recall/:template" element={<RecallPage />} />
            <Route path="techniques/:technique" element={<TechniquePage />} />
            {/* the path names the problem, and `?technique=` names where the
                pick came from: Phase 11 opens the same page from a ladder */}
            <Route path="problems/:problemId" element={<ProblemPage />} />
            <Route path="sittings/:sittingId" element={<SittingPage />} />
            <Route path="knowledge" element={<KnowledgePage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path={LOGIN} element={<LoginPage />} />
            <Route path={PRIVACY} element={<PrivacyPage />} />
            {GalleryPage && <Route path="gallery" element={<GalleryPage />} />}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </main>
    </Session>
  )
}

export default App
