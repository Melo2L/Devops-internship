import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { useScanSession } from "@/hooks/use-scan-session";

export const Route = createFileRoute("/_dashboard/scan/configure")({
  head: () => ({
    meta: [
      { title: "Analysis results — SecureScan" },
      {
        name: "description",
        content: "View results from the completed backend analysis.",
      },
    ],
  }),
  component: ConfigurePage,
});

function ConfigurePage() {
  const navigate = useNavigate();
  const upload = useScanSession((s) => s.upload);
  const result = useScanSession((s) => s.uploadResult);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        eyebrow="Analysis complete"
        title="Your analysis has already run"
        subtitle={`Target: ${upload?.name ?? result?.filename ?? "uploaded project"}`}
      />

      <div className="panel p-6">
        <p className="text-sm text-muted-foreground">
          SecureScan runs its configured scanners during upload. This page does not change scanner
          settings or start another scan.
        </p>

        {result && (
          <p className="mt-4 text-sm">
            Files detected: {result.files_detected} · Findings reported: {result.findings_count}
          </p>
        )}

        <Button className="mt-5" onClick={() => navigate({ to: "/scan/progress" })}>
          View analysis results
        </Button>
      </div>
    </div>
  );
}
