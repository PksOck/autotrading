import { Fragment } from "react";
import { parseMarkdown, type Inline } from "@/lib/markdown";
import { cn } from "@/lib/cn";

function Spans({ inline }: { inline: Inline[] }) {
  return inline.map((s, i) =>
    s.bold ? (
      <strong key={i} className="font-semibold text-text">{s.text}</strong>
    ) : s.code ? (
      <code key={i} className="num rounded bg-surface-2 px-1 text-[0.92em]">{s.text}</code>
    ) : (
      <Fragment key={i}>{s.text}</Fragment>
    ),
  );
}

/** Safe markdown (no raw HTML, only React text nodes): headings, bold, lists, paragraphs. */
export function Markdown({ source, className }: { source: string; className?: string }) {
  return (
    <div className={cn("flex flex-col gap-2 text-[14px] leading-6 text-text-2 [overflow-wrap:anywhere]", className)}>
      {parseMarkdown(source).map((b, i) => {
        if (b.type === "heading") {
          const H = (`h${b.level}`) as "h3" | "h4" | "h5";
          return <H key={i} className="mt-1 text-[15px] font-semibold text-text"><Spans inline={b.inline} /></H>;
        }
        if (b.type === "list") {
          const L = b.ordered ? "ol" : "ul";
          return (
            <L key={i} className={cn("flex flex-col gap-1 pl-5", b.ordered ? "list-decimal" : "list-disc")}>
              {b.items.map((it, j) => <li key={j}><Spans inline={it} /></li>)}
            </L>
          );
        }
        return <p key={i}><Spans inline={b.inline} /></p>;
      })}
    </div>
  );
}
