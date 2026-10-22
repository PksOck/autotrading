/** Motion tokens (DESIGN.md §8.1). Components never invent their own timings. */
export const duration = { fast: 0.12, base: 0.2, slow: 0.32 } as const;

export const ease = {
  standard: [0.2, 0, 0, 1],
  exit: [0.4, 0, 1, 1],
} as const;

export const spring = {
  snappy: { type: "spring", stiffness: 520, damping: 38 },
  soft: { type: "spring", stiffness: 260, damping: 30 },
} as const;

/** MO-03: entering list item. */
export const listItem = {
  initial: { opacity: 0, y: -8 },
  animate: { opacity: 1, y: 0, transition: spring.snappy },
  exit: { opacity: 0, scale: 0.98, transition: { duration: duration.fast, ease: ease.exit } },
} as const;
