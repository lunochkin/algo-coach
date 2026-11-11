import { Fragment, lazy, Suspense } from 'react'
import { Route, Routes, useMatch } from 'react-router'

import { LOADING } from '@algo-coach/core'
import { LOGIN, PRIVACY } from '@/api/client'
import { NavMenu } from '@/components/NavMenu'
import { KnowledgeProvider } from '@/knowledge/KnowledgeProvider'
import { cn } from '@/lib/utils'
import { BoardPage } from '@/pages/BoardPage'
import { CardsPage } from '@/pages/CardsPage'
import { KnowledgePage } from '@/pages/KnowledgePage'
import { LoginPage } from '@/pages/LoginPage'
import { ModulePage } from '@/pages/ModulePage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ProblemPage } from '@/pages/ProblemPage'
import { ProblemsPage } from '@/pages/ProblemsPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { TechniquePage } from '@/pages/TechniquePage'

// loaded when first opened: the editor and the markdown with its math are most
// of the bundle, and the board needs neither
const CardPage = lazy(() => import('@/pages/CardPage').then((m) => ({ default: m.CardPage })))
// lazy, as the card is: a lesson the queue offers reads through the Markdown renderer
const QueuePage = lazy(() => import('@/pages/QueuePage').then((m) => ({ default: m.QueuePage })))
const LessonsPage = lazy(() =>
  import('@/pages/LessonsPage').then((m) => ({ default: m.LessonsPage })),
)
const LessonPage = lazy(() => import('@/pages/LessonPage').then((m) => ({ default: m.LessonPage })))
const ExamPage = lazy(() => import('@/pages/ExamPage').then((m) => ({ default: m.ExamPage })))
const CertificationsPage = lazy(() =>
  import('@/pages/CertificationsPage').then((m) => ({ default: m.CertificationsPage })),
)
const RecallPage = lazy(() => import('@/pages/RecallPage').then((m) => ({ default: m.RecallPage })))
const DrawnRecallPage = lazy(() =>
  import('@/pages/RecallPage').then((m) => ({ default: m.DrawnRecallPage })),
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
  // too narrow for. The problem's page holds them
  const wide = useMatch('/problems/:problemId') !== null
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
        <Suspense fallback={<p className="text-meta text-muted-foreground">{LOADING}</p>}>
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
            <Route path="knowledge" element={<KnowledgePage />} />
            <Route path="knowledge/queue" element={<QueuePage />} />
            <Route path="knowledge/modules/:module" element={<ModulePage />} />
            <Route path="knowledge/lessons" element={<LessonsPage />} />
            <Route path="knowledge/lessons/:module/:lesson" element={<LessonPage />} />
            <Route path="knowledge/certifications" element={<CertificationsPage />} />
            <Route path="knowledge/exam" element={<ExamPage />} />
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
