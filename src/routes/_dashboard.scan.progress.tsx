import { useEffect, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  CheckCircle2,
  CircleAlert,
  FileSearch,
  LoaderCircle,
  XCircle,
} from "lucide-react";
import { PageHeader } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { scanSessionStore, useScanSession } from "@/hooks/use-scan-session";
import { scanService } from "@/services";

export const Route = createFileRoute("/_dashboard/scan/progress")({
  validateSearch: (search: Record<string, unknown>) => ({
    scanId: typeof search["scanId"] === "string" ? search["scanId"] : undefined,
  }),
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

type Status = "completed" | "running" | "partial" | "failed";

function getStatusLabel(status: Status | string): string {
  switch (status) {
    case "completed":
      return "Completed";
    case "running":
      return "Running";
    case "partial":
      return "Partially completed";
    case "failed":
      return "Failed";
    default:
      return "Unknown";
  }
}

function getStatusStyle(status: Status | string): string {
  switch (status) {
    case "completed":
      return "text-primary";
    case "running":
      return "text-blue-500";
    case "partial":
      return "text-amber-500";
    case "failed":
      return "text-destructive";
    default:
      return "text-muted-foreground";
  }
}

function StatusIcon({ status }: { status: Status | string }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="size-4 text-primary" />;
    case "running":
      return <LoaderCircle className="size-4 animate-spin text-blue-500" />;
    case "partial":
      return <CircleAlert className="size-4 text-amber-500" />;
    case "failed":
      return <XCircle className="size-4 text-destructive" />;
    default:
      return <AlertTriangle className="size-4 text-muted-foreground" />;
  }
}

function ProgressPage() {
  const { scanId: requestedScanId } = Route.useSearch();

  const upload = useScanSession((state) => state.upload);
  const result = useScanSession((state) => state.uploadResult);

  const [restoring, setRestoring] = useState(true);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function restore() {
      setRestoreError(null);

      let scanId = requestedScanId ?? null;

      if (!scanId) {
        try {
          scanId = window.localStorage.getItem("securescan:last-scan-id");
        } catch {
          // Storage can be unavailable in restricted browser contexts.
        }
      }

      if (!scanId) {
        setRestoring(false);
        return;
      }

      if (result?.id === scanId) {
        setRestoring(false);
        return;
      }

      setRestoring(true);

      try {
        const saved = await scanService.getResult(scanId);

        if (cancelled) return;

        if (saved) {
          scanSessionStore.set({
            uploadResult: saved,
            upload: {
              name: saved.filename,
              size: saved.size_bytes,
            },
            scanComplete: true,
          });
        } else {
          setRestoreError("The requested scan was not found by the backend.");
        }
      } catch {
        if (!cancelled) {
          setRestoreError("Could not restore results. Check that the backend is running.");
        }
      } finally {
        if (!cancelled) {
          setRestoring(false);
        }
      }
    }

    void restore();

    return () => {
      cancelled = true;
    };
  }, [requestedScanId, result?.id]);

  const displayingRequestedScan = !requestedScanId || !result || result.id === requestedScanId;

  if (restoring || !displayingRequestedScan) {
    return (
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Security analysis"
          title="Restoring analysis results"
          subtitle="Retrieving the saved scan from the backend."
        />
        <div className="panel p-6 text-sm text-muted-foreground">
          Please wait while SecureScan retrieves the analysis.
        </div>
      </div>
    );
  }

  if (!result || (requestedScanId && result.id !== requestedScanId)) {
    return (
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Security analysis"
          title="No analysis result available"
          subtitle="The requested analysis could not be loaded."
        />
        <div className="panel p-6">
          <p className="text-sm text-muted-foreground">
            {restoreError ?? "No saved analysis was found. Upload a project to run an analysis."} No
            progress or findings are simulated.
          </p>
          <Button asChild className="mt-4">
            <Link to="/scan/new">Upload a project</Link>
          </Button>
        </div>
      </div>
    );
  }

  const findings = (result.scans ?? []).flatMap((scan) => scan.findings);
  const scanners = result.scans ?? [];
  const scannersSkipped = result.scan_plan?.skipped ?? [];
  const overallStatus = result.status ?? "completed";

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Backend analysis result"
        title={
          overallStatus === "completed"
            ? "Analysis completed"
            : overallStatus === "partial"
              ? "Analysis partially completed"
              : overallStatus === "failed"
                ? "Analysis failed"
                : "Analysis in progress"
        }
        subtitle={upload?.name ?? result.filename}
      />

      <section className="panel mb-4 p-5">
        <div className="flex flex-wrap items-center gap-3">
          <StatusIcon status={overallStatus} />
          <div>
            <p className="text-sm font-medium">Overall scan status</p>
            <p className={`mt-1 text-sm font-semibold ${getStatusStyle(overallStatus)}`}>
              {getStatusLabel(overallStatus)}
            </p>
          </div>
        </div>
      </section>

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
          <FileSearch className="size-5 text-primary" />
          <h2 className="font-semibold">Scanner results</h2>
        </div>

        {scanners.length > 0 ? (
          <ul className="mt-4 space-y-4">
            {scanners.map((scan) => (
              <li key={scan.scanner} className="rounded-lg border p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="font-medium capitalize">{scan.scanner}</span>

                  <span className="flex items-center gap-2 text-sm">
                    <StatusIcon status={scan.status} />
                    <span className={getStatusStyle(scan.status)}>
                      {getStatusLabel(scan.status)}
                    </span>
                  </span>
                </div>

                <p className="mt-2 text-sm text-muted-foreground">
                  {scan.findings.length} finding(s) returned.
                </p>

                {scan.error && (
                  <div className="mt-3 rounded-md border border-destructive/30 bg-destructive/5 p-3">
                    <p className="flex items-center gap-2 text-sm font-medium text-destructive">
                      <AlertTriangle className="size-4" />
                      Scanner error
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">{scan.error}</p>
                  </div>
                )}
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
          {(result.analysis?.technologies ?? []).length
            ? (result.analysis?.technologies ?? []).join(", ")
            : "None reported"}
        </p>

        <Button asChild className="mt-5">
          <Link to="/findings">View findings</Link>
        </Button>
      </section>
    </div>
  );
}
