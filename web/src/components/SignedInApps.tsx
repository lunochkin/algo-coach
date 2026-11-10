import { useState } from 'react'

import { api, type SignedInApp } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { lastAt } from '@/lib/format'

// the native apps signed in as this account. Revoking one cuts off a lost
// phone, which its own sign-out cannot reach
export function SignedInApps({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const apps = useLoaded((signal) => api.GET('/api/apps', { signal }), `apps-${open}`)
  const [failed, setFailed] = useState<string | null>(null)

  async function revoke(app: SignedInApp) {
    setFailed(null)
    const { error } = await api.DELETE('/api/apps/{app_id}', {
      params: { path: { app_id: app.id } },
    })
    if (error) setFailed(described(error))
    apps.retry()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Signed-in apps</DialogTitle>
          <DialogDescription>A revoked app is signed out at its next sync.</DialogDescription>
        </DialogHeader>
        {apps.error ? (
          <p className="text-destructive">{apps.error}</p>
        ) : apps.data === undefined ? (
          <p className="text-muted-foreground">Reading the signed-in apps…</p>
        ) : apps.data.length === 0 ? (
          <p className="text-muted-foreground">No app is signed in.</p>
        ) : (
          <ul className="divide-y rounded-lg border">
            {apps.data.map((app) => (
              <li key={app.id} className="flex items-center gap-3 px-3 py-2">
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{app.device}</p>
                  <p className="text-meta text-muted-foreground">
                    {`used ${lastAt(app.last_used_at)} · signed in ${lastAt(app.created_at)}`}
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void revoke(app)}>
                  Revoke
                </Button>
              </li>
            ))}
          </ul>
        )}
        {failed ? <p className="text-destructive">{failed}</p> : null}
      </DialogContent>
    </Dialog>
  )
}
