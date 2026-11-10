import type { Me } from '@/api/client'

// the address the provider verified, and the engine's own id where no
// provider linked one
export function named(me: Me | undefined): string {
  if (me === undefined) return 'Signed in'
  return me.email ?? me.user_id
}
