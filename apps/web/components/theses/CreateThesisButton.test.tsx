import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import en from "@/messages/en.json";
import { useCreateThesisDraft } from "@/lib/api/hooks";
import { revision, runId } from "@/test/thesis-fixtures";
import { CreateThesisButton } from "./CreateThesisButton";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/lib/api/hooks", () => ({ useCreateThesisDraft: vi.fn() }));

it("creates nothing on render and navigates only after the user creates a draft", () => {
  const mutate = vi.fn((_data, options) => options.onSuccess(revision));
  vi.mocked(useCreateThesisDraft).mockReturnValue({
    mutate,
    isPending: false,
    error: null,
  } as unknown as ReturnType<typeof useCreateThesisDraft>);
  render(
    <NextIntlClientProvider locale="en" messages={en}>
      <CreateThesisButton runId={runId} />
    </NextIntlClientProvider>,
  );
  expect(mutate).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Create thesis draft" }));
  expect(mutate).toHaveBeenCalledWith({ analysis_run_id: runId }, expect.any(Object));
  expect(push).toHaveBeenCalledWith(`/theses/${revision.thesis_id}`);
});
