import { cn } from "@/lib/utils";
import type { Finding } from "@/types/security";

const TOKEN =
  /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|#.*$|\b(?:def|return|import|from|for|in|if|else|class|RUN|COPY|CMD|WORKDIR|FROM|USER)\b)/g;

function highlight(line: string) {
  const parts = line.split(TOKEN);
  return parts.map((p, i) => {
    if (!p) return null;
    if (p.startsWith("#"))
      return (
        <span key={i} className="text-muted-foreground italic">
          {p}
        </span>
      );
    if (p.startsWith('"') || p.startsWith("'"))
      return (
        <span key={i} className="text-success">
          {p}
        </span>
      );
    if (i % 2 === 1)
      return (
        <span key={i} className="text-primary">
          {p}
        </span>
      );
    return <span key={i}>{p}</span>;
  });
}

export function CodeSnippet({
  snippet,
  file,
}: {
  snippet: NonNullable<Finding["snippet"]>;
  file: string;
}) {
  return (
    <div className="overflow-hidden rounded-lg border bg-background">
      <div className="flex items-center justify-between border-b bg-surface-2 px-4 py-2">
        <span className="font-mono text-xs text-muted-foreground">{file}</span>
        <span className="eyebrow">{snippet.language}</span>
      </div>
      <pre className="overflow-x-auto py-3 font-mono text-[13px] leading-6">
        {snippet.lines.map((l, i) => {
          const n = snippet.startLine + i;
          const hit = n === snippet.highlight;
          return (
            <div
              key={i}
              className={cn(
                "flex pr-4",
                hit && "bg-sev-critical/10 shadow-[inset_2px_0_0_var(--sev-critical)]",
              )}
            >
              <span className="w-12 shrink-0 select-none pr-4 text-right text-muted-foreground/60">
                {n}
              </span>
              <code>{highlight(l)}</code>
            </div>
          );
        })}
      </pre>
    </div>
  );
}
