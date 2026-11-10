import { api, LOGIN, type Me } from '@/api/client'

// revoked on the server, not only dropped from the browser, then to the login
export async function signOut() {
  await api.DELETE('/api/session')
  window.location.assign(LOGIN)
}

// the address the provider verified, and the engine's own id where no
// provider linked one
export function named(me: Me | undefined): string {
  if (me === undefined) return 'Signed in'
  return me.email ?? me.user_id
}
