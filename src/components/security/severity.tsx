import { cn } from "@/lib/utils";
import { SEVERITY_LABEL, type FindingStatus, type Severity } from "@/types/security";
import { sevBg, sevChip } from "@/components/security/severity-styles";

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 font-mono text-[10.5px] font-medium uppercase tracking-wider",
        sevChip[severity],
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", sevBg[severity])} aria-hidden />
      {severity === "info" ? "Info" : SEVERITY_LABEL[severity]}
    </span>
  );
}

const statusStyle: Record<FindingStatus, string> = {
  open: "text-foreground border-border bg-secondary",
  resolved: "text-success border-success/30 bg-success/10",
  ignored: "text-muted-foreground border-border bg-muted",
};

export function StatusBadge({ status }: { status: FindingStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs capitalize transition-colors",
        statusStyle[status],
      )}
    >
      {status}
    </span>
  );
}
