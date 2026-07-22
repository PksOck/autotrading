const unavailable = "Not available";

export function formatCurrency(value: number | null, currency: string): string {
  if (value === null) return unavailable;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number | null): string {
  if (value === null) return unavailable;
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatMultiple(value: number | null): string {
  if (value === null) return unavailable;
  return `${value.toFixed(1)}×`;
}

export function formatCompactNumber(value: number | null): string {
  if (value === null) return unavailable;
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatExactNumber(value: number | null): string {
  if (value === null) return unavailable;
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 20,
  }).format(value);
}
