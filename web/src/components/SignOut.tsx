import { LogOut } from 'lucide-react'
import { useState, type ReactNode } from 'react'

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
            <AlertDialogTitle>Sign out and lose unsent records?</AlertDialogTitle>
            <AlertDialogDescription>
              {unsent === 1 ? 'One record' : `${unsent} records`} did not reach the engine. Signing
              out now deletes {unsent === 1 ? 'it' : 'them'} from this browser.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Stay signed in</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => void leave(true)}>
              <LogOut />
              Sign out
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
