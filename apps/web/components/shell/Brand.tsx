/** Preža mark: three-quarter radar arc with a detected dot (BRAND.md §5). */
export function BrandMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" aria-hidden>
      <path d="M14 3a11 11 0 1 0 11 11" fill="none" stroke="var(--accent)" strokeWidth={2.4} strokeLinecap="round" />
      <path d="M14 8.5a5.5 5.5 0 1 0 5.5 5.5" fill="none" stroke="var(--accent)" strokeWidth={2.4} strokeLinecap="round" opacity={0.55} />
      <circle cx={22.5} cy={5.5} r={2.6} fill="var(--accent)" />
    </svg>
  );
}
