import { render, screen, fireEvent } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import { useProposalList } from "@/lib/api/hooks";
import { useRetryProposal } from "@/lib/api/research";
import en from "@/messages/en.json";
import { ProposalList } from "./ProposalList";

vi.mock("@/lib/api/hooks", () => ({useProposalList:vi.fn()}));
vi.mock("@/lib/api/research", () => ({useRetryProposal:vi.fn()}));
vi.mock("@/components/common/EntityLink", () => ({EntityLink:({entity}:{entity:{id:string}}) => <span>{entity.id}</span>}));
const retry = vi.fn();
const proposal = {id:"proposal-1",symbols:["ASML","MSFT"],hypothesis:"Original hypothesis",status:"failed",depth:"deep",created_at:"2026-10-28T12:00:00Z",verdict:'{"summary":"llm_unavailable: private details"}',error_code:"analysis_failed",analysis_links:[]};
function show(extra = {}) {
  vi.mocked(useProposalList).mockReturnValue({data:[{...proposal,...extra}],isLoading:false,error:null} as unknown as ReturnType<typeof useProposalList>);
  vi.mocked(useRetryProposal).mockReturnValue({mutate:retry,isPending:false,error:null} as unknown as ReturnType<typeof useRetryProposal>);
  return render(<NextIntlClientProvider locale="en" messages={en} timeZone="UTC"><ProposalList/></NextIntlClientProvider>);
}
it("shows a safe failure, preserves hypothesis and retries the same saved proposal", () => {
  show();
  expect(screen.getByRole("alert")).toHaveTextContent("Your proposal is saved");
  expect(screen.getByText(/Original hypothesis/)).toBeVisible();
  expect(screen.queryByText(/private details/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button",{name:"Try again"}));
  expect(retry).toHaveBeenCalledWith("proposal-1");
});
it("separates the validated hypothesis verdict, symbol analyses and exact signal link", () => {
  show({status:"done",error_code:null,signal_id:"signal-1",verdict_result:{verdict:"supports",summary:"Supported by official evidence",key_points:["Evidence one"],risks:["Risk one"]},analysis_links:[{id:"run-1",symbol:"ASML",status:"done"},{id:"run-2",symbol:"MSFT",status:"running"}]});
  expect(screen.getByText("Supported by official evidence")).toBeVisible();
  expect(screen.getByRole("link",{name:/ASML.*Completed/})).toHaveAttribute("href","/analysis/run-1");
  expect(screen.getByRole("link",{name:/MSFT.*Running/})).toHaveAttribute("href","/analysis/run-2");
  expect(screen.getByRole("link",{name:/Open signal/})).toHaveAttribute("href","/signals?peek=signal:signal-1");
});
