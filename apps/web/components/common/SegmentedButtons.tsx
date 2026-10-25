"use client";

import { useId } from "react";
import { Icon } from "@/components/common/Icon";
import { cn } from "@/lib/cn";

type Props<T extends string> = {
  options: { value: T; label: string; title?: string; testId?: string }[];
  value: T;
  onChange: (value: T) => void;
  label: string;
  name?: string;
  disabled?: boolean;
  compact?: boolean;
  semantics?: "radio" | "pressed";
  className?: string;
};

/** Outlined segments. Native radios retain arrow-key selection and form semantics. */
export function SegmentedButtons<T extends string>({
  options,
  value,
  onChange,
  label,
  name,
  disabled,
  compact,
  semantics = "radio",
  className,
}: Props<T>) {
  const id = useId();
  const segmentClass = (active: boolean) =>
    cn(
      "touch-target relative flex min-h-9 min-w-11 flex-1 cursor-pointer items-center justify-center gap-1 rounded-none px-2 text-[13px] font-medium whitespace-nowrap transition-colors duration-[var(--dur-fast)] first:rounded-l-md last:rounded-r-md has-[:focus-visible]:z-10 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent",
      active ? "bg-accent-soft text-accent" : "bg-surface text-text-2 hover:bg-accent-soft/50",
      disabled && "cursor-default opacity-60",
    );
  return (
    <div
      role={semantics === "radio" ? "radiogroup" : "group"}
      aria-label={label}
      className={cn(
        "inline-flex rounded-md border border-border divide-x divide-border",
        className,
      )}
    >
      {options.map((option) => {
        const active = value === option.value;
        const content = (
          <>
            {!compact && active && <Icon name="check" size={14} />}
            <span>{option.label}</span>
          </>
        );
        return semantics === "pressed" ? (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            title={option.title}
            data-testid={option.testId}
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={segmentClass(active)}
          >
            {content}
          </button>
        ) : (
          <label key={option.value} title={option.title} className={segmentClass(active)}>
            <input
              type="radio"
              name={name ?? id}
              value={option.value}
              checked={active}
              disabled={disabled}
              data-testid={option.testId}
              onChange={() => onChange(option.value)}
              className="sr-only"
            />
            {content}
          </label>
        );
      })}
    </div>
  );
}
