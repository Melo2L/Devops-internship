import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ArrowUpRight, Info, TrendingUp } from "lucide-react";
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";
import { PageHeader } from "@/components/security/brand";
import { ScoreRing } from "@/components/security/score-ring";
import { SeverityBadge } from "@/components/security/severity";
import { sevBg, sevText } from "@/components/security/severity-styles";
import { HistoryChart } from "@/components/security/history-chart";
import { Button } from "@/components/ui/button";
import { dashboardQuery } from "@/services/queries";
import { SEVERITY_LABEL, SEVERITY_ORDER } from "@/types/security";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_dashboard/overview")({
  head: () => ({
    meta: [
      { title: "Security Assessment — SecureScan" },
      {
        name: "description",
        content:
          "Security Score, risk level, category posture and top findings for the latest scan.",
      },
      { property: "og:title", content: "Security Assessment — SecureScan" },
      {
        property: "og:description",
        content: "Security posture overview for the latest automated assessment.",
      },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(dashboardQuery),
  component: Overview,
});

function Overview() {
  const { data } = useSuspenseQuery(dashboardQuery);
  const { score, severityCounts: c, categories, history, topFindings, scan } = data;
  const delta = score.previous != null ? score.score - score.previous : 0;

  return (
    <div>
      <PageHeader eyebrow={`Scan #${scan.number} · ${scan.date}`} title="Security Assessment" />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,340px)_1fr]">
        <section
          className="panel flex flex-col items-center p-6 text-center"
          aria-labelledby="score-h"
        >
          <p id="score-h" className="eyebrow mb-5">
            Security Score
          </p>
          {scan.id === "no-scan" ? (
            <div className="flex h-[168px] flex-col items-center justify-center text-sm text-muted-foreground">
              <span className="text-2xl font-semibold">Not scanned</span>
              <span className="mt-2">Upload a ZIP to calculate a score.</span>
            </div>
          ) : (
            <ScoreRing score={score.score} />
          )}
          <div className="mt-5 flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Risk Level</span>
            <span className="rounded-md border border-sev-medium/30 bg-sev-medium/10 px-2 py-0.5 font-mono text-xs font-medium text-sev-medium">
              {score.riskLevel}
            </span>
          </div>
          <p className="mt-5 flex gap-2 text-left text-xs leading-relaxed text-muted-foreground">
            <Info className="mt-0.5 size-3.5 shrink-0" />
            This score represents the security posture detected by the automated analysis. It is not
            a guarantee that the project is secure or insecure.
          </p>
        </section>

        <div className="grid gap-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
            {SEVERITY_ORDER.map((s) => (
              <Link
                key={s}
                to="/findings"
                search={{ severity: s }}
                className="panel group p-4 transition-colors hover:border-primary/40"
              >
                <div className="flex items-center gap-2">
                  <span className={cn("size-2 rounded-full", sevBg[s])} />
                  <span className="text-xs text-muted-foreground">{SEVERITY_LABEL[s]}</span>
                </div>
                <p className={cn("mt-3 text-3xl font-semibold tabular-nums", sevText[s])}>{c[s]}</p>
              </Link>
            ))}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <section className="panel p-5">
              <p className="eyebrow mb-4">Risk Summary</p>
              <ul className="space-y-3 text-sm">
                <li className="flex gap-3">
                  <span className="mt-1.5 size-2 shrink-0 rounded-full bg-sev-critical" />
                  <span>
                    <b className="font-medium">{c.critical} Critical</b> findings require immediate
                    attention.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-1.5 size-2 shrink-0 rounded-full bg-sev-high" />
                  <span>
                    <b className="font-medium">{c.high} High</b> severity findings should be
                    addressed soon.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-1.5 size-2 shrink-0 rounded-full bg-sev-medium" />
                  <span>
                    <b className="font-medium">{c.medium} Medium</b> findings should be reviewed
                    during remediation.
                  </span>
                </li>
              </ul>
            </section>
            <section className="panel p-5">
              <div className="flex items-start justify-between">
                <p className="eyebrow">Score trend</p>
                <span className="inline-flex items-center gap-1 text-xs text-success">
                  <TrendingUp className="size-3.5" />
                  {delta >= 0 ? "+" : ""}
                  {delta}
                </span>
              </div>
              {history.length > 0 ? (
                <HistoryChart history={history} height={120} />
              ) : (
                <div className="flex h-[120px] items-center justify-center text-sm text-muted-foreground">
                  No historical scans available yet.
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                {history.length > 1
                  ? `${history.length} scans recorded. Current score: ${score.score} / 100. Change from the previous scan: ${delta >= 0 ? "+" : ""}${delta} points.`
                  : "Complete another scan to compare your security score over time."}
              </p>
            </section>
          </div>
        </div>
      </div>

      <section className="mt-4 grid gap-4 lg:grid-cols-[1fr_380px]">
        <div className="panel p-6">
          <p className="eyebrow mb-5">Security Categories</p>
          <div className="space-y-4">
            {categories.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Upload a project to see real category results.
              </p>
            ) : (
              categories.map((cat) => (
                <div key={cat.id}>
                  <div className="flex justify-between text-sm">
                    <span>{cat.name}</span>
                    <span className="font-mono text-muted-foreground">{cat.score} / 100</span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className={cn(
                        "h-full rounded-full transition-[width] duration-700",
                        cat.score >= 80
                          ? "bg-success"
                          : cat.score >= 70
                            ? "bg-primary"
                            : "bg-sev-medium",
                      )}
                      style={{ width: `${cat.score}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        <div className="panel p-4">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart
              data={categories.map((c) => ({
                name: c.name.replace("Infrastructure as Code", "IaC"),
                score: c.score,
              }))}
              outerRadius="72%"
            >
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis
                dataKey="name"
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              />
              <Radar
                dataKey="score"
                stroke="var(--primary)"
                fill="var(--primary)"
                fillOpacity={0.18}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel mt-4 overflow-hidden">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <p className="eyebrow">Top Findings</p>
          <Button asChild variant="ghost" size="sm">
            <Link to="/findings">
              All findings <ArrowUpRight />
            </Link>
          </Button>
        </div>
        <ul className="divide-y">
          {topFindings.length === 0 ? (
            <li className="px-6 py-8 text-sm text-muted-foreground">
              {scan.id === "no-scan"
                ? "No scan results yet. Upload a ZIP archive to begin."
                : "No findings were returned by the enabled scanners."}
            </li>
          ) : (
            topFindings.map((f) => (
              <li key={f.id} className="flex flex-col gap-3 px-6 py-4 md:flex-row md:items-center">
                <SeverityBadge severity={f.severity} className="w-fit md:w-24 md:justify-center" />
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{f.title}</p>
                  <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                    {f.file}
                    {f.line ? `:${f.line}` : ""} · {f.category} · {f.scanner}
                  </p>
                </div>
                <Button asChild variant="outline" size="sm">
                  <Link to="/findings/$findingId" params={{ findingId: f.id }}>
                    View Finding
                  </Link>
                </Button>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
