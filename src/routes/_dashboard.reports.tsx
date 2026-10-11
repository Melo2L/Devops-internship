import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Download, Eye, FileJson, FileText } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { reportsQuery, dashboardQuery } from "@/services/queries";
import { SEVERITY_LABEL, SEVERITY_ORDER, type Report } from "@/types/security";
import { sevText } from "@/components/security/severity-styles";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_dashboard/reports")({
  head: () => ({
    meta: [
      { title: "Reports — SecureScan" },
      {
        name: "description",
        content: "Security Assessment Reports for each scan, viewable and exportable.",
      },
      { property: "og:title", content: "Reports — SecureScan" },
      { property: "og:description", content: "View and export Security Assessment Reports." },
    ],
  }),
  loader: ({ context }) =>
    Promise.all([
      context.queryClient.ensureQueryData(reportsQuery),
      context.queryClient.ensureQueryData(dashboardQuery),
    ]),
  component: ReportsPage,
});

function fmtDate(d: string) {
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

function ReportsPage() {
  const { data: reports } = useSuspenseQuery(reportsQuery);
  const { data: dash } = useSuspenseQuery(dashboardQuery);
  const [open, setOpen] = useState<Report | null>(null);
  const latest = reports[0]!;

  function exportJson(r: Report) {
    const blob = new Blob(
      [
        JSON.stringify(
          { ...r, severityCounts: dash.severityCounts, categories: dash.categories },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${r.id}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle="Assessment reports are generated at the end of every scan."

      />

      <section className="panel grid gap-6 p-6 md:grid-cols-[1fr_auto] md:items-center">
        <div className="flex gap-4">
          <div className="grid size-12 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
            <FileText className="size-6" />
          </div>
          <div>
            <p className="eyebrow">Latest</p>
            <h2 className="mt-1 text-lg font-semibold">{latest.title}</h2>
            <dl className="mt-3 grid grid-cols-2 gap-x-8 gap-y-1 text-sm sm:grid-cols-4">
              <div>
                <dt className="text-xs text-muted-foreground">Generated</dt>
                <dd>{fmtDate(latest.generated)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Project</dt>
                <dd className="font-mono">{latest.projectName}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Score</dt>
                <dd className="font-mono">{latest.score} / 100</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Findings</dt>
                <dd className="font-mono">{latest.findingCount}</dd>
              </div>
            </dl>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => setOpen(latest)}>
            <Eye /> View Report
          </Button>
          <Button
            variant="outline"
            onClick={() => toast.info("PDF generation will be provided by the backend.")}
          >
            <Download /> Download PDF
          </Button>
          <Button variant="outline" onClick={() => exportJson(latest)}>
            <FileJson /> Export JSON
          </Button>
        </div>
      </section>

      <section className="panel mt-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b bg-surface-2">
            <tr className="text-left">
              {["Report", "Scan", "Generated", "Score", "Findings", ""].map((h) => (
                <th key={h} className="eyebrow px-5 py-3 font-normal">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {reports.map((r) => (
              <tr key={r.id}>
                <td className="px-5 py-3">{r.title}</td>
                <td className="px-5 py-3 font-mono text-xs">{r.scanId.replace("scan_", "#")}</td>
                <td className="px-5 py-3 text-muted-foreground">{fmtDate(r.generated)}</td>
                <td className="px-5 py-3 font-mono">{r.score}</td>
                <td className="px-5 py-3 font-mono">{r.findingCount}</td>
                <td className="px-5 py-3 text-right">
                  <Button size="sm" variant="ghost" onClick={() => setOpen(r)}>
                    View
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <Dialog open={!!open} onOpenChange={(o) => !o && setOpen(null)}>
        <DialogContent className="max-w-2xl">
          {open && (
            <>
              <DialogHeader>
                <DialogTitle>{open.title}</DialogTitle>
                <DialogDescription>
                  {open.projectName} · Scan {open.scanId.slice(0, 8)} ·{" "}
                  {fmtDate(open.generated)}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border p-4">
                  <p className="eyebrow">Security Score</p>
                  <p className="mt-2 text-3xl font-semibold">
                    {open.score}
                    <span className="text-base text-muted-foreground"> / 100</span>
                  </p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="eyebrow">Findings</p>
                  <p className="mt-2 text-3xl font-semibold">{open.findingCount}</p>
                </div>
              </div>
              {open.id === latest.id && (
                <div className="space-y-2">
                  <p className="eyebrow">Severity breakdown</p>
                  {SEVERITY_ORDER.map((s) => (
                    <div key={s} className="flex justify-between text-sm">
                      <span>{SEVERITY_LABEL[s]}</span>
                      <span className={cn("font-mono", sevText[s])}>{dash.severityCounts[s]}</span>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                This report reflects automated analysis results and is not a guarantee of security.
              </p>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
