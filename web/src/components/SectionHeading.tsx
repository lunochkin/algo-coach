// a section's heading and how many rows it holds, the same on every page that
// splits a list into sections
export function SectionHeading({ title, count }: { title: string; count: number }) {
  return (
    <h2 className="flex items-baseline gap-2 text-heading font-medium">
      {title}
      <span className="text-meta font-normal text-muted-foreground tabular-nums">{count}</span>
    </h2>
  )
}
