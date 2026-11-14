import { drawingSize, type Snapshot } from '@climb/core'
import { useContext, useMemo } from 'react'

import { PlainCode } from '@/components/PythonCode'
import { KnowledgeContext } from '@/knowledge/context'

// The seed prepared the SVG for the phone, which reads text raw, so it may
// hold a bare `&`. The HTML parser accepts that, and the serializer writes
// back the strict XML an image needs.
function asImage(svg: string): string {
  const drawn = new DOMParser().parseFromString(svg, 'text/html').querySelector('svg')
  const xml = drawn ? new XMLSerializer().serializeToString(drawn) : svg
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(xml)}`
}

// a Mermaid source as the seed drew it, in the page's scheme, never wider
// than drawn: `knowledge.md`, Diagrams. An image runs no script the SVG holds.
export function Diagram({ source }: { source: string }) {
  const snapshot = useContext(KnowledgeContext)?.snapshot as Snapshot | undefined
  const drawn = snapshot?.diagrams?.[source]
  const images = useMemo(() => drawn && { light: asImage(drawn.light), dark: asImage(drawn.dark) }, [drawn])
  if (!drawn || !images) return <PlainCode>{source}</PlainCode>
  const size = drawingSize(drawn.light)
  const style = { maxWidth: size ? `${size.width}px` : undefined }
  return (
    <figure className="my-4">
      <img src={images.light} alt={source} style={style} className="h-auto w-full dark:hidden" />
      <img src={images.dark} alt={source} style={style} className="hidden h-auto w-full dark:block" />
    </figure>
  )
}
