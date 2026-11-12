import { useLayoutEffect, useRef, useState } from 'react'

// the columns an element holds, from its width and the width of one character
// of its own font, averaged over `probe`
export function useColumns(probe = 'M'.repeat(40)) {
  const ref = useRef<HTMLElement>(null)
  const [cols, setCols] = useState(Infinity)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const span = document.createElement('span')
    span.textContent = probe
    span.style.cssText = 'position:absolute;visibility:hidden;white-space:pre'
    el.appendChild(span)
    const measure = () => {
      const char = span.getBoundingClientRect().width / probe.length
      const style = getComputedStyle(el)
      const width = el.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight)
      if (char) setCols(Math.floor(width / char))
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(el)
    return () => {
      observer.disconnect()
      span.remove()
    }
  }, [probe])
  return { ref, cols }
}
