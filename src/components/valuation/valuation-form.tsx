"use client";

export interface ValuationFormValues {
  growthPercent: string;
  explicitYears: string;
  terminalPercent: string;
  discountPercent: string;
  normalizedFcf: string;
  netDebt: string;
  dilutedShares: string;
}

export function ValuationForm({
  values,
  currency,
  unit,
  onChange,
}: {
  values: ValuationFormValues;
  currency: string;
  unit: string;
  onChange: (field: keyof ValuationFormValues, value: string) => void;
}) {
  const fields: { key: keyof ValuationFormValues; label: string; step: string }[] = [
    { key: "growthPercent", label: "Annual growth (%)", step: "0.1" },
    { key: "explicitYears", label: "Explicit years", step: "1" },
    { key: "terminalPercent", label: "Terminal growth (%)", step: "0.1" },
    { key: "discountPercent", label: "Discount rate (%)", step: "0.1" },
    { key: "normalizedFcf", label: `Normalized FCF (${currency} ${unit})`, step: "1" },
    { key: "netDebt", label: `Net debt (${currency} ${unit})`, step: "1" },
    { key: "dilutedShares", label: `Diluted shares (${unit})`, step: "1" },
  ];

  return (
    <fieldset className="valuation-form">
      <legend>Valuation assumptions</legend>
      {fields.map((field) => (
        <label key={field.key}>
          {field.label}
          <input
            type="number"
            step={field.step}
            value={values[field.key]}
            onChange={(event) => onChange(field.key, event.target.value)}
          />
        </label>
      ))}
    </fieldset>
  );
}
