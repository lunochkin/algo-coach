import { useEffect, useState } from 'react'

type Answer<T> = { data?: T; error?: unknown }
type State<T> = { key: string; data?: T; error?: string }

// `key` names what is loaded: a change reloads, and the answer for a key the
// page has moved past is never shown
export function useLoaded<T>(load: (signal: AbortSignal) => Promise<Answer<T>>, key: string) {
  const [state, setState] = useState<State<T>>({ key })
  // bumped by `retry`, which asks again for the same key
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    load(controller.signal)
      .then(({ data, error }) =>
        setState(data !== undefined ? { key, data } : { key, error: described(error) }),
      )
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setState({ key, error: String(reason) })
      })
    return () => controller.abort()
    // `key` and `attempt` alone: `load` is a new closure on every render, and
    // `key` names what it loads
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, attempt])

  function retry() {
    setState({ key })
    setAttempt((one) => one + 1)
  }

  return { ...(state.key === key ? state : { key }), retry }
}

export function described(error: unknown): string {
  // the API refuses with the domain's own sentence
  if (error && typeof error === 'object' && 'detail' in error) return String(error.detail)
  return JSON.stringify(error)
}
