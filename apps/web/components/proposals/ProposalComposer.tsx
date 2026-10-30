"use client";

import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { Dialog } from "radix-ui";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { SegmentedButtons } from "@/components/common/SegmentedButtons";
import { useBackToClose } from "@/lib/useBackToClose";
import { cn } from "@/lib/cn";
import { spring } from "@/lib/motion";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { keys, useCreateProposal } from "@/lib/api/hooks";
import { PROPOSE_EVENT, type ProposeDetail } from "@/stores/proposals";
import { api, ApiError } from "@/lib/api/client";
import type { ProposalOut } from "@/lib/api/types";
import {
  canonicalBody,
  clearAcknowledgedFields,
  DRAFT_KEY,
  DraftStorageError,
  loadDraft,
  matchesOperation,
  prepareOperation,
  saveDraftFields,
  setOperationState,
  startNewIntention,
  type DraftFields,
  type DraftOperation,
} from "@/lib/proposal-draft";

type ProposalDepth = "quick" | "standard" | "deep";
type ProposalDirection = "up" | "down" | "unsure";
type ProposalSaveTo = "active" | "reserve" | "once";
type Horizon = "days" | "weeks" | "months" | "years";

const DEPTHS: ProposalDepth[] = ["quick", "standard", "deep"];
const DIRECTIONS: ProposalDirection[] = ["up", "down", "unsure"];
const HORIZONS: Horizon[] = ["days", "weeks", "months", "years"];
const SAVE_TO: ProposalSaveTo[] = ["active", "reserve", "once"];

const fieldClass =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-text placeholder:text-text-3 hover:border-text-3 focus:border-accent";

/** CMP-30 (DESIGN.md §11): the user proposes a symbol or hypothesis for analysis. */
export function ProposalComposer() {
  const t = useTranslations();
  const id = useId();
  const router = useRouter();
  const create = useCreateProposal();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLElement | null>(null);
  const isOpen = useRef(false);
  useEffect(() => {
    isOpen.current = open;
  }, [open]);
  const close = useBackToClose(open, () => setOpen(false));
  const [symbols, setSymbols] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [source, setSource] = useState("");
  const [direction, setDirection] = useState<ProposalDirection>("unsure");
  const [horizon, setHorizon] = useState<Horizon>("months");
  const [depth, setDepth] = useState<ProposalDepth>("standard");
  const [saveTo, setSaveTo] = useState<ProposalSaveTo>("reserve");
  const [error, setError] = useState(false);
  const hydrated = useRef(false);
  const draftId = useRef("");
  const busy = useRef(false);
  const dirtyFields = useRef(false);
  const [checking, setChecking] = useState(false);
  const [storageError, setStorageError] = useState(false);
  const [operation, setOperation] = useState<DraftOperation | null>(null);
  const fieldsRef = useRef<DraftFields>({
    symbols,
    hypothesis,
    source,
    direction,
    horizon,
    depth,
    saveTo,
  });
  useEffect(() => {
    fieldsRef.current = { symbols, hypothesis, source, direction, horizon, depth, saveTo };
  }, [symbols, hypothesis, source, direction, horizon, depth, saveTo]);

  function restoreFields(value: DraftFields) {
    setSymbols(value.symbols);
    setHypothesis(value.hypothesis);
    setSource(value.source);
    setDirection(value.direction);
    setHorizon(value.horizon);
    setDepth(value.depth);
    setSaveTo(value.saveTo);
  }

  function editField<T>(setter: (value: T) => void, value: T) {
    dirtyFields.current = true;
    setter(value);
  }

  useEffect(() => {
    if (!open || !draftId.current || !dirtyFields.current) return;
    dirtyFields.current = false;
    let current = true;
    void saveDraftFields(draftId.current, fieldsRef.current)
      .then((saved) => {
        if (!current) return;
        setOperation(saved.operation);
        if (saved.draft_id !== draftId.current) {
          draftId.current = saved.draft_id;
          restoreFields(saved.fields);
        }
        setStorageError(false);
      })
      .catch(() => {
        if (current) setStorageError(true);
      });
    return () => {
      current = false;
    };
  }, [open, symbols, hypothesis, source, direction, horizon, depth, saveTo]);

  useEffect(() => {
    const onPropose = (event: Event) => {
      if (!isOpen.current && document.activeElement instanceof HTMLElement) {
        opener.current = document.activeElement;
      }
      if (!hydrated.current) {
        hydrated.current = true;
        try {
          const draft = loadDraft();
          draftId.current = draft.draft_id;
          restoreFields(draft.fields);
          setOperation(draft.operation);
        } catch {
          setStorageError(true);
        }
      }
      const detail = (event as CustomEvent<ProposeDetail>).detail ?? {};
      if (detail.symbols) editField(setSymbols, detail.symbols.join(", "));
      if (detail.hypothesis !== undefined) editField(setHypothesis, detail.hypothesis);
      setError(false);
      setOpen(true);
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key !== DRAFT_KEY) return;
      try {
        // Another tab can refresh safety state, but cannot replace active edits.
        setOperation(loadDraft().operation);
      } catch {
        setStorageError(true);
      }
    };
    window.addEventListener(PROPOSE_EVENT, onPropose);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(PROPOSE_EVENT, onPropose);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const newIntention = async () => {
    if (busy.current) return;
    busy.current = true;
    try {
      const draft = await startNewIntention(draftId.current, fieldsRef.current);
      draftId.current = draft.draft_id;
      setOperation(draft.operation);
      setStorageError(false);
    } catch {
      setStorageError(true);
    } finally {
      busy.current = false;
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (busy.current || create.isPending) return;
    if (!operation && !canonicalBody(fieldsRef.current).symbols.length) {
      setError(true);
      return;
    }
    // This explicit action persists the current fields itself, including after storage recovery.
    dirtyFields.current = false;
    busy.current = true;
    setChecking(true);
    let frozen: DraftOperation | null = null;
    try {
      // A temporary read failure while opening must not require discarding visible edits.
      if (!draftId.current) draftId.current = loadDraft().draft_id;
      const draft = await prepareOperation(draftId.current, fieldsRef.current);
      draftId.current = draft.draft_id;
      frozen = draft.operation;
      setOperation(frozen);
      if (!frozen || frozen.state === "acknowledged" || frozen.state === "conflict") return;
      const submitting = await setOperationState(frozen.request_id, "submitting");
      setOperation(submitting.operation);
      if (
        submitting.operation?.state === "acknowledged" ||
        submitting.operation?.state === "conflict"
      )
        return;
      let accepted: ProposalOut;
      try {
        accepted = await api.get<ProposalOut>(`/proposals/${frozen.request_id}`);
      } catch (failure) {
        if (!(failure instanceof ApiError) || failure.status !== 404) throw failure;
        // A stale 404 must not regress an acceptance saved by another tab.
        const ready = await setOperationState(frozen.request_id, "submitting");
        setOperation(ready.operation);
        if (ready.operation?.state === "acknowledged" || ready.operation?.state === "conflict")
          return;
        accepted = await create.mutateAsync({
          ...frozen.canonical_body,
          request_id: frozen.request_id,
        });
      }
      if (!matchesOperation(frozen, accepted)) {
        const conflict = await setOperationState(frozen.request_id, "conflict");
        setOperation(conflict.operation);
        return;
      }
      const acknowledged = await setOperationState(frozen.request_id, "acknowledged");
      setOperation(acknowledged.operation);
      void queryClient.invalidateQueries({ queryKey: keys.proposals });
      setStorageError(false);
      if (
        JSON.stringify(canonicalBody(fieldsRef.current)) === JSON.stringify(frozen.canonical_body)
      ) {
        const expectedFields = fieldsRef.current;
        const current = await clearAcknowledgedFields(frozen.request_id, expectedFields);
        if (JSON.stringify(fieldsRef.current) === JSON.stringify(expectedFields))
          restoreFields(current.fields);
      }
      close();
      toast.success(
        t("proposal.submitted", { symbols: frozen.canonical_body.symbols.join(", ") }),
        {
          description: t("proposal.previewNote"),
          action: { label: t("nav.proposals"), onClick: () => router.push("/proposals") },
        },
      );
    } catch (failure) {
      if (failure instanceof DraftStorageError || !frozen) setStorageError(true);
      else {
        try {
          const saved = await setOperationState(
            frozen.request_id,
            failure instanceof ApiError && failure.status === 409 ? "conflict" : "outcome_unknown",
          );
          setOperation(saved.operation);
        } catch {
          setStorageError(true);
        }
      }
    } finally {
      busy.current = false;
      setChecking(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={(next) => (next ? setOpen(true) : close())}>
      <AnimatePresence>
        {open && (
          <Dialog.Portal forceMount>
            <Dialog.Overlay asChild forceMount>
              <motion.div
                className="fixed inset-0 z-50 bg-black/40"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              />
            </Dialog.Overlay>
            <Dialog.Content
              asChild
              forceMount
              onCloseAutoFocus={(event) => {
                if (opener.current?.isConnected) {
                  event.preventDefault();
                  opener.current.focus({ preventScroll: true });
                }
              }}
            >
              <motion.div
                initial={{ opacity: 0, y: 16, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={spring.soft}
                className="card fixed top-[6vh] left-1/2 z-50 max-h-[88vh] w-[min(640px,calc(100vw-24px))] -translate-x-1/2 overflow-y-auto p-6 shadow-float"
              >
                <Dialog.Title className="text-xl leading-7 font-semibold">
                  {t("proposal.title")}
                </Dialog.Title>
                <Dialog.Description className="mt-1 text-text-2">
                  {t("proposal.intro")}
                </Dialog.Description>

                <form onSubmit={submit} className="mt-5 flex flex-col gap-4" noValidate>
                  {storageError && (
                    <p role="alert" className="rounded-md border border-neg p-3 text-sm">
                      {t("proposal.durable.storageError")}
                    </p>
                  )}
                  {operation && (
                    <section
                      aria-live="polite"
                      className="rounded-md border border-border bg-surface-2 p-3 text-sm"
                    >
                      <p role={operation.state === "conflict" ? "alert" : "status"}>
                        {t(
                          `proposal.durable.${operation.state === "acknowledged" ? "acknowledged" : operation.state === "conflict" ? "conflict" : operation.state === "outcome_unknown" ? "unknown" : "prepared"}`,
                        )}
                      </p>
                      <p className="mt-2 font-medium">
                        {t("proposal.durable.savedSymbols", {
                          symbols: operation.canonical_body.symbols.join(", "),
                        })}
                      </p>
                      {operation.canonical_body.hypothesis && (
                        <p
                          className="mt-1 whitespace-pre-wrap"
                          aria-label={t("proposal.durable.savedHypothesis")}
                        >
                          {operation.canonical_body.hypothesis}
                        </p>
                      )}
                      <p className="mt-2 text-text-3">{t("proposal.durable.workingCopy")}</p>
                    </section>
                  )}
                  <div>
                    <label htmlFor={`${id}-symbols`} className="label">
                      {t("proposal.symbols")}
                    </label>
                    <input
                      id={`${id}-symbols`}
                      value={symbols}
                      onChange={(e) => {
                        editField(setSymbols, e.target.value);
                        setError(false);
                      }}
                      autoFocus
                      autoComplete="off"
                      aria-invalid={error}
                      aria-describedby={`${id}-symbols-hint`}
                      className={cn(fieldClass, "num mt-1 uppercase", error && "border-neg")}
                    />
                    <p
                      id={`${id}-symbols-hint`}
                      className={cn("mt-1 text-xs", error ? "text-neg" : "text-text-3")}
                    >
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
                      onChange={(e) => editField(setHypothesis, e.target.value)}
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
                      onChange={(e) => editField(setSource, e.target.value)}
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
                      onChange={(value) => editField(setDirection, value)}
                    />
                    <Segmented
                      legend={t("proposal.horizon")}
                      name={`${id}-horizon`}
                      options={HORIZONS.map((h) => ({ value: h, label: t(`signal.horizon.${h}`) }))}
                      value={horizon}
                      onChange={(value) => editField(setHorizon, value)}
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
                            onChange={() => editField(setDepth, d)}
                            className="sr-only"
                          />
                          <span className="font-medium">{t(`proposal.depth.${d}`)}</span>
                          <span className="text-xs text-text-3">
                            {t(`proposal.depth.${d}Hint`)}
                          </span>
                        </label>
                      ))}
                    </div>
                  </fieldset>

                  <Segmented
                    legend={t("proposal.saveTo.label")}
                    name={`${id}-save`}
                    options={SAVE_TO.map((s) => ({ value: s, label: t(`proposal.saveTo.${s}`) }))}
                    value={saveTo}
                    onChange={(value) => editField(setSaveTo, value)}
                  />

                  <div className="mt-2 flex flex-wrap items-center justify-end gap-2">
                    <Dialog.Close
                      type="button"
                      className="min-h-12 rounded-md border border-border px-4 font-medium hover:bg-surface-2"
                    >
                      {t("action.cancel")}
                    </Dialog.Close>
                    {operation && ["acknowledged", "conflict"].includes(operation.state) ? (
                      <button
                        type="button"
                        onClick={newIntention}
                        disabled={checking}
                        className="min-h-12 rounded-md bg-accent px-4 font-medium text-on-accent disabled:opacity-60"
                      >
                        {t("proposal.durable.newIntention")}
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={checking || create.isPending}
                        className="min-h-12 rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90 disabled:opacity-60"
                      >
                        {t(
                          checking
                            ? "proposal.durable.checking"
                            : operation
                              ? "proposal.durable.check"
                              : "proposal.submit",
                        )}
                      </button>
                    )}
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
      <SegmentedButtons
        className="flex w-full"
        label={legend}
        name={name}
        options={options}
        value={value}
        onChange={onChange}
      />
    </fieldset>
  );
}
