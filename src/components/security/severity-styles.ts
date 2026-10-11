import type { Severity } from "@/types/security";

export const sevText: Record<Severity, string> = {
  critical: "text-sev-critical",
  high: "text-sev-high",
  medium: "text-sev-medium",
  low: "text-sev-low",
  info: "text-sev-info",
};

export const sevBg: Record<Severity, string> = {
  critical: "bg-sev-critical",
  high: "bg-sev-high",
  medium: "bg-sev-medium",
  low: "bg-sev-low",
  info: "bg-sev-info",
};

export const sevChip: Record<Severity, string> = {
  critical: "bg-sev-critical/12 text-sev-critical border-sev-critical/30",
  high: "bg-sev-high/12 text-sev-high border-sev-high/30",
  medium: "bg-sev-medium/12 text-sev-medium border-sev-medium/30",
  low: "bg-sev-low/12 text-sev-low border-sev-low/30",
  info: "bg-sev-info/12 text-sev-info border-sev-info/30",
};
