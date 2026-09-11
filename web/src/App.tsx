import { Route, Routes } from 'react-router'

import { BoardPage } from '@/pages/BoardPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { TechniquePage } from '@/pages/TechniquePage'

function App() {
  return (
    <main className="mx-auto max-w-4xl p-6">
      <Routes>
        {/* the board is where every sitting starts: the user picks the
            technique, never a problem id */}
        <Route index element={<BoardPage />} />
        <Route path="techniques/:technique" element={<TechniquePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </main>
  )
}

export default App
