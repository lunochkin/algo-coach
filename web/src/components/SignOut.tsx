import { LogOut } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { SIGN_OUT, SIGN_OUT_TITLE, signOutWarning, STAY_SIGNED_IN } from '@algo-coach/core'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useKnowledge } from '@/knowledge/context'

// signing out sends the outbox, then deletes the copy. An outbox that cannot
// be sent is named first, so the user decides whether those records are lost:
// `knowledge.md`, A client's store
export function SignOut({ children }: { children: (start: () => void) => ReactNode }) {
  const { leave } = useKnowledge()
  const [unsent, setUnsent] = useState(0)

  async function start() {
    setUnsent(await leave(false))
  }

  return (
    <>
      {children(() => void start())}
      <AlertDialog open={unsent > 0} onOpenChange={(open) => !open && setUnsent(0)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{SIGN_OUT_TITLE}</AlertDialogTitle>
            <AlertDialogDescription>{signOutWarning(unsent, 'browser')}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{STAY_SIGNED_IN}</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => void leave(true)}>
              <LogOut />
              {SIGN_OUT}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
