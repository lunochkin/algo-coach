import { LogOut, X } from 'lucide-react'
import { useState } from 'react'

import {
  deviceLine,
  REVOKE,
  REVOKED_NOTE,
  SIGN_OUT,
  SIGNED_IN_DEVICES,
  OF,
  deviceTitle,
  revokeDevice,
} from '@algo-coach/core'

import { api, type SignedInDevice } from '@/api/client'
import { useLoaded } from '@/api/useLoaded'
import { ErrorLine } from '@/components/ErrorLine'
import { PickPanel, PickRow } from '@/components/PickRow'
import { Loaded } from '@/components/Loaded'
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
    const revoked = await revokeDevice(api, device)
    if (!revoked.ok) setFailed(revoked.refused)
    devices.retry()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{SIGNED_IN_DEVICES}</DialogTitle>
          <DialogDescription>{REVOKED_NOTE}</DialogDescription>
        </DialogHeader>
        <Loaded of={OF.devices} state={devices}>
          {(listed) => (
            <div className="max-h-[60vh] overflow-y-auto">
              <PickPanel>
                {listed.map((device) => (
                  <PickRow
                    key={device.id}
                    title={deviceTitle(device, 'browser')}
                    note={deviceLine(device, now)}
                    stats={[]}
                    aside={
                      device.current ? (
                        <SignOut>
                          {(start) => (
                            <Button variant="outline" size="sm" onClick={start}>
                              <LogOut />
                              {SIGN_OUT}
                            </Button>
                          )}
                        </SignOut>
                      ) : (
                        <Button variant="outline" size="sm" onClick={() => void revoke(device)}>
                          <X />
                          {REVOKE}
                        </Button>
                      )
                    }
                  />
                ))}
              </PickPanel>
            </div>
          )}
        </Loaded>
        {failed ? <ErrorLine>{failed}</ErrorLine> : null}
      </DialogContent>
    </Dialog>
  )
}
