import { useState } from 'react'

import {
  DEVICES_LOADING,
  deviceLine,
  deviceName,
  REVOKE,
  REVOKED_NOTE,
  SIGN_OUT,
  SIGNED_IN_DEVICES,
  thisDevice,
} from '@algo-coach/core'

import { api, type SignedInDevice } from '@/api/client'
import { described, useLoaded } from '@/api/useLoaded'
import { SignOut } from '@/components/SignOut'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

// every browser and app signed in as this account, as the phone lists them.
// Revoking one cuts off a lost phone or a forgotten browser; the one read on
// signs out instead, so its outbox is sent first
export function SignedInDevices({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const devices = useLoaded((signal) => api.GET('/api/devices', { signal }), `devices-${open}`)
  const [failed, setFailed] = useState<string | null>(null)
  // the moment the dialog opened, which its lines are read at
  const [now] = useState(() => Date.now())

  async function revoke(device: SignedInDevice) {
    setFailed(null)
    const { error } = await api.DELETE('/api/devices/{kind}/{device_id}', {
      params: { path: { kind: device.kind, device_id: device.id } },
    })
    if (error) setFailed(described(error))
    devices.retry()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{SIGNED_IN_DEVICES}</DialogTitle>
          <DialogDescription>{REVOKED_NOTE}</DialogDescription>
        </DialogHeader>
        {devices.error ? (
          <p className="text-destructive">{devices.error}</p>
        ) : devices.data === undefined ? (
          <p className="text-muted-foreground">{DEVICES_LOADING}</p>
        ) : (
          <ul className="max-h-[60vh] divide-y overflow-y-auto rounded-lg border">
            {devices.data.map((device) => (
              <li key={device.id} className="flex items-center gap-3 px-3 py-2">
                <div className="min-w-0 flex-1">
                  <p className="font-medium">
                    {deviceName(device)}
                    {device.current && (
                      <span className="font-normal text-muted-foreground">
                        {' '}
                        · {thisDevice('browser')}
                      </span>
                    )}
                  </p>
                  <p className="text-meta text-muted-foreground">{deviceLine(device, now)}</p>
                </div>
                {device.current ? (
                  <SignOut>
                    {(start) => (
                      <Button variant="outline" size="sm" onClick={start}>
                        {SIGN_OUT}
                      </Button>
                    )}
                  </SignOut>
                ) : (
                  <Button variant="outline" size="sm" onClick={() => void revoke(device)}>
                    {REVOKE}
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
        {failed ? <p className="text-destructive">{failed}</p> : null}
      </DialogContent>
    </Dialog>
  )
}
