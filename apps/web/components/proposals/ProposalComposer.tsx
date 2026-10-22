"use client";

import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { Dialog } from "radix-ui";
import { useEffect, useId, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/cn";
import { spring } from "@/lib/motion";
import {
  PROPOSE_EVENT,
  parseSymbols,
  useProposals,
  type Proposal,
  type ProposalDepth,
  type ProposalDirection,
  type ProposalSaveTo,
  type ProposeDetail,
} from "@/stores/proposals";

const DEPTHS: ProposalDepth[] = ["quick", "standard", "deep"];
const DIRECTIONS: ProposalDirection[] = ["up", "down", "unsure"];
const HORIZONS: Proposal["horizon"][] = ["days", "weeks", "months", "years"];
const SAVE_TO: ProposalSaveTo[] = ["active", "reserve", "once"];

const fieldClass =
  "w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-text placeholder:text-text-3 focus:border-accent focus:outline-none";

/** CMP-30 (DESIGN.md §11): the user proposes a symbol or hypothesis for analysis. */
export function ProposalComposer() {
  const t = useTranslations();
  const id = useId();
  const add = useProposals((s) => s.add);
  const remove = useProposals((s) => s.remove);
  const [open, setOpen] = useState(false);
  const [symbols, setSymbols] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [source, setSource] = useState("");
  const [direction, setDirection] = useState<ProposalDirection>("unsure");
  const [horizon, setHorizon] = useState<Proposal["horizon"]>("months");
  const [depth, setDepth] = useState<ProposalDepth>("standard");
  const [saveTo, setSaveTo] = useState<ProposalSaveTo>("reserve");
  const [error, setError] = useState(false);

  useEffect(() => {
    const onPropose = (event: Event) => {
      const detail = (event as CustomEvent<ProposeDetail>).detail ?? {};
      setSymbols(detail.symbols?.join(", ") ?? "");
      setHypothesis(detail.hypothesis ?? "");
      setSource("");
      setError(false);
      setOpen(true);
    };
    window.addEventListener(PROPOSE_EVENT, onPropose);
    return () => window.removeEventListener(PROPOSE_EVENT, onPropose);
  }, []);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const parsed = parseSymbols(`${symbols} ${source.match(/\$[A-Za-z.]{1,10}/g)?.join(" ") ?? ""}`);
    if (!parsed.length) {
      setError(true);
      return;
    }
    const proposal: Proposal = {
      id: crypto.randomUUID(),
      symbols: parsed,
      hypothesis: hypothesis.trim(),
      source: source.trim(),
      direction,
      horizon,
      depth,
      saveTo,
      createdAt: new Date().toISOString(),
      status: "draft",
    };
    add(proposal);
    setOpen(false);
    toast.success(t("proposal.submitted", { symbols: parsed.join(", ") }), {
      description: t("proposal.previewNote"),
      action: {
        label: t("proposal.undo"),
        onClick: () => {
          remove(proposal.id);
          toast(t("proposal.undone"));
        },
      },
    });
  };

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <AnimatePresence>
        {open && (
          <Dialog.Portal forceMount>
            <Dialog.Overlay asChild forceMount>
              <motion.div
                className="fixed inset-0 z-50 bg-black/30 backdrop-blur-[2px]"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              />
            </Dialog.Overlay>
            <Dialog.Content asChild forceMount>
              <motion.div
                initial={{ opacity: 0, y: 16, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={spring.soft}
                className="card fixed top-[6vh] left-1/2 z-50 max-h-[88vh] w-[min(640px,calc(100vw-24px))] -translate-x-1/2 overflow-y-auto p-6 shadow-float"
              >
                <Dialog.Title className="text-xl leading-7 font-semibold">{t("proposal.title")}</Dialog.Title>
                <Dialog.Description className="mt-1 text-text-2">{t("proposal.intro")}</Dialog.Description>

                <form onSubmit={submit} className="mt-5 flex flex-col gap-4" noValidate>
                  <div>
                    <label htmlFor={`${id}-symbols`} className="label">
                      {t("proposal.symbols")}
                    </label>
                    <input
                      id={`${id}-symbols`}
                      value={symbols}
                      onChange={(e) => {
                        setSymbols(e.target.value);
                        setError(false);
                      }}
                      autoFocus
                      autoComplete="off"
                      aria-invalid={error}
                      aria-describedby={`${id}-symbols-hint`}
                      className={cn(fieldClass, "num mt-1 uppercase", error && "border-neg")}
                    />
                    <p id={`${id}-symbols-hint`} className={cn("mt-1 text-xs", error ? "text-neg" : "text-text-3")}>
                      {error ? t("proposal.required") : t("proposal.symbolsHint")}
                    </p>
                  </div>

                  <div>
                    <label htmlFor={`${id}-hypothesis`} className="label">
                      {t("proposal.hypothesis")}
                    </label>
                    <textarea
                      id={`${id}-hypothesis`}
                      value={hypothesis}
                      onChange={(e) => setHypothesis(e.target.value)}
                      placeholder={t("proposal.hypothesisHint")}
                      rows={3}
                      className={cn(fieldClass, "mt-1 resize-y")}
                    />
                  </div>

                  <div>
                    <label htmlFor={`${id}-source`} className="label">
                      {t("proposal.source")}
                    </label>
                    <textarea
                      id={`${id}-source`}
                      value={source}
                      onChange={(e) => setSource(e.target.value)}
                      rows={2}
                      className={cn(fieldClass, "mt-1 resize-y")}
                    />
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <Segmented
                      legend={t("proposal.direction")}
                      name={`${id}-direction`}
                      options={DIRECTIONS.map((d) => ({ value: d, label: t(`proposal.${d}`) }))}
                      value={direction}
                      onChange={setDirection}
                    />
                    <Segmented
                      legend={t("proposal.horizon")}
                      name={`${id}-horizon`}
                      options={HORIZONS.map((h) => ({ value: h, label: t(`signal.horizon.${h}`) }))}
                      value={horizon}
                      onChange={setHorizon}
                    />
                  </div>

                  <fieldset>
                    <legend className="label mb-1">{t("proposal.depth.label")}</legend>
                    <div className="grid gap-2 sm:grid-cols-3">
                      {DEPTHS.map((d) => (
                        <label
                          key={d}
                          className={cn(
                            "relative flex cursor-pointer flex-col gap-0.5 rounded-md border border-border p-3 transition-colors duration-[var(--dur-fast)] hover:bg-surface-2",
                            depth === d && "border-accent bg-accent-soft hover:bg-accent-soft",
                          )}
                        >
                          <input
                            type="radio"
                            name={`${id}-depth`}
                            value={d}
                            checked={depth === d}
                            onChange={() => setDepth(d)}
                            className="sr-only"
                          />
                          <span className="font-medium">{t(`proposal.depth.${d}`)}</span>
                          <span className="text-xs text-text-3">{t(`proposal.depth.${d}Hint`)}</span>
                        </label>
                      ))}
                    </div>
                  </fieldset>

                  <Segmented
                    legend={t("proposal.saveTo.label")}
                    name={`${id}-save`}
                    options={SAVE_TO.map((s) => ({ value: s, label: t(`proposal.saveTo.${s}`) }))}
                    value={saveTo}
                    onChange={setSaveTo}
                  />

                  <div className="mt-2 flex flex-wrap items-center justify-end gap-2">
                    <Dialog.Close className="h-10 rounded-md border border-border px-4 font-medium hover:bg-surface-2">
                      {t("action.cancel")}
                    </Dialog.Close>
                    <button type="submit" className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90">
                      {t("proposal.submit")}
                    </button>
                  </div>
                </form>
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  );
}

function Segmented<T extends string>({
  legend,
  name,
  options,
  value,
  onChange,
}: {
  legend: string;
  name: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <fieldset>
      <legend className="label mb-1">{legend}</legend>
      <div className="flex flex-wrap gap-0.5 rounded-md bg-surface-2 p-0.5">
        {options.map((option) => (
          <label
            key={option.value}
            className={cn(
              "relative flex h-9 flex-1 cursor-pointer items-center justify-center rounded-[5px] px-2 text-[13px] font-medium whitespace-nowrap text-text-2 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent",
              value === option.value && "text-text",
            )}
          >
            {value === option.value && (
              <motion.span
                layoutId={`${name}-pill`}
                transition={spring.snappy}
                className="absolute inset-0 rounded-[5px] bg-surface shadow-[0_0_0_1px_var(--border)]"
              />
            )}
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="sr-only"
            />
            <span className="relative">{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
