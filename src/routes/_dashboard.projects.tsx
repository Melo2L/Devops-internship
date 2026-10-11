import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { FolderGit2, Plus } from "lucide-react";
import { PageHeader } from "@/components/security/brand";
import { HistoryChart } from "@/components/security/history-chart";
import { Button } from "@/components/ui/button";
import { historyQuery, projectsQuery } from "@/services/queries";

export const Route = createFileRoute("/_dashboard/projects")({
  head: () => ({
    meta: [
      { title: "Projects & Scan History — SecureScan" },
      {
        name: "description",
        content: "Project history and Security Score evolution across scans.",
      },
      { property: "og:title", content: "Projects & Scan History — SecureScan" },
      {
        property: "og:description",
        content: "Track continuous security improvement across scans.",
      },
    ],
  }),
  loader: ({ context }) =>
    Promise.all([
      context.queryClient.ensureQueryData(projectsQuery),
      context.queryClient.ensureQueryData(historyQuery),
    ]),
  component: ProjectsPage,
});

const fmt = (d: string) => {
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
};

function ProjectsPage() {
  const { data: projects } = useSuspenseQuery(projectsQuery);
  const { data: history } = useSuspenseQuery(historyQuery);
  const p = projects[0]!;
  const scans = [...history].reverse();

  return (
    <div>
      <PageHeader
        title="Projects"
        subtitle="Scan history demonstrates continuous security improvement."
        actions={
          <>
            <Button asChild>
              <Link to="/scan/new">
                <Plus /> New Scan
              </Link>
            </Button>
          </>
        }
      />
      <section className="panel p-6">
        <div className="flex items-start gap-4">
          <div className="grid size-11 place-items-center rounded-lg bg-primary/10 text-primary">
            <FolderGit2 className="size-5" />
          </div>
          <div>
            <h2 className="font-semibold">{p?.name ?? "No projects yet"}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{p?.description ?? "Upload a ZIP archive to start your first analysis."}</p>
            <p className="mt-1 font-mono text-xs text-muted-foreground">
              {p ? `${p.language} · ${p.sizeMb} MB` : "No project uploaded"} · {history.length} scans
            </p>
          </div>
        </div>
        <div className="mt-6">
          <p className="eyebrow mb-2">Security Score evolution</p>
          <HistoryChart history={history} height={240} />
        </div>
      </section>
      <section className="panel mt-6 divide-y">
        {scans.map((s, i) => {
          const prev = scans[i + 1];
          const d = prev ? s.score - prev.score : null;
          return (
            <div key={s.id} className="flex items-center gap-4 px-6 py-4">
              <span className="font-mono text-sm">Scan #{s.number}</span>
              <span className="text-sm text-muted-foreground">{fmt(s.date)}</span>
              <span className="ml-auto text-xs text-muted-foreground">
                {s.findingCount} findings
              </span>
              {d != null && (
                <span
                  className={
                    d >= 0
                      ? "w-10 text-right font-mono text-xs text-success"
                      : "w-10 text-right font-mono text-xs text-sev-critical"
                  }
                >
                  {d >= 0 ? "+" : ""}
                  {d}
                </span>
              )}
              <span className="w-20 text-right font-mono">{s.score} / 100</span>
            </div>
          );
        })}
      </section>
    </div>
  );
}
