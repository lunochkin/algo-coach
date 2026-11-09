// how far a count has got, as a thin bar in the flame: progress is the
// study's own, never a verdict, so it reads in the brand rather than in a
// verdict's colour
type Props = { value: number; total: number; label: string }

export function ProgressBar({ value, total, label }: Props) {
  const share = total === 0 ? 0 : Math.min(1, value / total)
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-valuenow={value}
      className="h-1 w-full overflow-hidden rounded-full bg-muted"
    >
      <div className="h-full rounded-full bg-brand" style={{ width: `${share * 100}%` }} />
    </div>
  )
}
