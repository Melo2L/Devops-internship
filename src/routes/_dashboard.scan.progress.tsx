import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, CheckCircle2, FileSearch } from "lucide-react";
import { PageHeader } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { useDemoStore } from "@/hooks/use-demo-store";

export const Route = createFileRoute("/_dashboard/scan/progress")({
  head: () => ({
    meta: [
      { title: "Analysis Results — SecureScan" },
      {
        name: "description",
        content: "Results returned by the actual backend analysis.",
      },
    ],
  }),
  component: ProgressPage,
});

function ProgressPage() {
  const upload = useDemoStore((state) => state.upload);
  const result = useDemoStore((state) => state.uploadResult);

  if (!result) {
    return (
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Security analysis"
          title="No analysis result available"
          subtitle="Upload a project to execute the backend analysis."
        />
        <div className="panel p-6">
          <p className="text-sm text-muted-foreground">
            There is no real analysis result in the current session. No progress or findings are
            being simulated.
          </p>
          <Button asChild className="mt-4">
            <Link to="/scan/new">Upload a project</Link>
          </Button>
        </div>
      </div>
    );
  }

  const findings = result.scans.flatMap((scan) => scan.findings);
  const scannersRun = result.scans.map((scan) => scan.scanner);
  const scannersSkipped = result.scan_plan.skipped;

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Backend analysis result"
        title="Analysis completed"
        subtitle={upload?.name ?? result.filename}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <section className="panel p-5">
          <p className="eyebrow">Files detected</p>
          <p className="mt-3 text-3xl font-semibold tabular-nums">{result.files_detected}</p>
        </section>
        <section className="panel p-5">
          <p className="eyebrow">Files extracted</p>
          <p className="mt-3 text-3xl font-semibold tabular-nums">{result.files_extracted}</p>
        </section>
        <section className="panel p-5">
          <p className="eyebrow">Findings returned</p>
          <p className="mt-3 text-3xl font-semibold tabular-nums">{findings.length}</p>
        </section>
      </div>

      <section className="panel mt-4 p-6">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="size-5 text-primary" />
          <h2 className="font-semibold">Scanner results</h2>
        </div>
        {scannersRun.length ? (
          <ul className="mt-4 space-y-2">
            {scannersRun.map((scanner) => (
              <li key={scanner} className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="size-4 text-primary" />
                {scanner}: result returned by backend
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-muted-foreground">
            The backend returned no scanner result entries.
          </p>
        )}
        {scannersSkipped.length > 0 && (
          <div className="mt-5 border-t pt-4">
            <p className="flex items-center gap-2 text-sm font-medium">
              <AlertTriangle className="size-4" />
              Scanners skipped by the backend
            </p>
            <p className="mt-2 text-sm text-muted-foreground">{scannersSkipped.join(", ")}</p>
          </div>
        )}
      </section>

      <section className="panel mt-4 p-6">
        <div className="flex items-center gap-2">
          <FileSearch className="size-5 text-primary" />
          <h2 className="font-semibold">Analysis summary</h2>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{result.message}</p>
        <p className="mt-2 text-sm">
          Technologies detected:{" "}
          {result.analysis.technologies.length
            ? result.analysis.technologies.join(", ")
            : "None reported"}
        </p>
        <Button asChild className="mt-5">
          <Link to="/findings">View findings</Link>
        </Button>
      </section>
    </div>
  );
}
