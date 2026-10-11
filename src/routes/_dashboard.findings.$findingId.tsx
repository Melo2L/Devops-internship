import { useState } from "react";
import {
  createFileRoute,
  Link,
  notFound,
} from "@tanstack/react-router";
import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import {
  SeverityBadge,
  StatusBadge,
} from "@/components/security/severity";
import { CodeSnippet } from "@/components/security/code-snippet";
import { Button } from "@/components/ui/button";
import { findingService } from "@/services";
import { findingsQuery } from "@/services/queries";
import {
  SEVERITY_LABEL,
  type FindingStatus,
} from "@/types/security";

export const Route = createFileRoute("/_dashboard/findings/$findingId")({
  loader: async ({ params, context }) => {
    const findings =
      await context.queryClient.ensureQueryData(findingsQuery);

    const finding = findings.find((item) => item.id === params.findingId);

    if (!finding) {
      throw notFound();
    }

    return { title: finding.title };
  },

  head: ({ loaderData }) => ({
    meta: [
      {
        title: loaderData
          ? `${loaderData.title} — SecureScan`
          : "Finding not found — SecureScan",
      },
      {
        name: "description",
        content: "Details of a security finding returned by the analysis.",
      },
    ],
  }),

  notFoundComponent: FindingNotFound,
  component: FindingDetail,
});

function FindingNotFound() {
  return (
    <div className="panel mx-auto max-w-md p-8 text-center">
      <p className="font-medium">Finding not found</p>

      <p className="mt-2 text-sm text-muted-foreground">
        This finding could not be found in the API results. Upload and scan a
        project first, then select a finding from the results list.
      </p>

      <Button asChild variant="outline" className="mt-4">
        <Link to="/findings">Back to findings</Link>
      </Button>
    </div>
  );
}

function Meta({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2.5 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right">{children}</dd>
    </div>
  );
}

function FindingDetail() {
  const { findingId } = Route.useParams();
  const queryClient = useQueryClient();
  const { data: findings } = useSuspenseQuery(findingsQuery);
  const [statusOverride, setStatusOverride] =
    useState<FindingStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);

  const finding = findings.find((item) => item.id === findingId);

  const statusMutation = useMutation({
    mutationFn: (nextStatus: FindingStatus) =>
      findingService.updateStatus(findingId, nextStatus),

    onSuccess: async (updatedFinding) => {
      setStatusOverride(updatedFinding.status);
      setStatusError(null);

      await queryClient.invalidateQueries({
        queryKey: findingsQuery.queryKey,
      });
    },

    onError: (error) => {
      setStatusError(
        error instanceof Error
          ? error.message
          : "Could not update the finding status.",
      );
    },
  });

  if (!finding) {
    return <FindingNotFound />;
  }

  const status = statusOverride ?? finding.status;

  function updateStatus(nextStatus: FindingStatus) {
    if (statusMutation.isPending || nextStatus === status) {
      return;
    }

    setStatusError(null);
    statusMutation.mutate(nextStatus);
  }

  return (
    <div className="mx-auto max-w-6xl">
      <Link
        to="/findings"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        Security Findings
      </Link>

      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <StatusBadge status={status} />

          <span className="font-mono text-xs text-muted-foreground">
            {finding.id}
          </span>
        </div>

        <h1 className="mt-3 text-2xl font-semibold tracking-tight md:text-3xl">
          {finding.title}
        </h1>

        <p className="mt-1 font-mono text-sm text-muted-foreground">
          {finding.file}
          {finding.line ? `:${finding.line}` : ""}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {status === "open" ? (
            <>
              <Button
                onClick={() => updateStatus("resolved")}
                disabled={statusMutation.isPending}
              >
                {statusMutation.isPending
                  ? "Saving..."
                  : "Mark as Resolved"}
              </Button>

              <Button
                variant="outline"
                onClick={() => updateStatus("ignored")}
                disabled={statusMutation.isPending}
              >
                Ignore Finding
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              onClick={() => updateStatus("open")}
              disabled={statusMutation.isPending}
            >
              {statusMutation.isPending ? "Saving..." : "Reopen Finding"}
            </Button>
          )}
        </div>

        {statusError ? (
          <p role="alert" className="mt-3 text-sm text-destructive">
            Failed to update status: {statusError}
          </p>
        ) : (
          <p className="mt-2 text-xs text-muted-foreground">
            Status changes are saved to the backend and persist after reloading.
          </p>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="space-y-6">
          <section className="panel p-6">
            <p className="eyebrow mb-2">Description</p>
            <p className="text-sm leading-relaxed">{finding.description}</p>
          </section>

          <section className="panel p-6">
            <p className="eyebrow mb-4">Code location</p>

            {finding.snippet ? (
              <CodeSnippet snippet={finding.snippet} file={finding.file} />
            ) : (
              <p className="break-all rounded-lg border bg-background p-4 font-mono text-xs text-muted-foreground">
                {finding.file}
                {finding.line ? `:${finding.line}` : ""}
              </p>
            )}
          </section>

          <section className="panel p-6">
            <p className="eyebrow mb-4">Recommended remediation</p>

            {finding.remediation.length > 0 ? (
              <ol className="list-inside list-decimal space-y-3 text-sm">
                {finding.remediation.map((item, index) => (
                  <li key={`${index}-${item}`}>{item}</li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-muted-foreground">
                No remediation guidance was returned by the scanner.
              </p>
            )}
          </section>
        </div>

        <aside>
          <dl className="panel divide-y px-5 py-2">
            <Meta label="Severity">
              {SEVERITY_LABEL[finding.severity]}
            </Meta>

            <Meta label="Confidence">
              <span className="capitalize">{finding.confidence}</span>
            </Meta>

            <Meta label="Scanner">
              <span className="font-mono">{finding.scanner}</span>
            </Meta>

            <Meta label="Category">{finding.category}</Meta>

            <Meta label="File">
              <span className="break-all font-mono text-xs">
                {finding.file}
              </span>
            </Meta>

            <Meta label="Line">
              <span className="font-mono">{finding.line ?? "—"}</span>
            </Meta>

            <Meta label="Rule">
              <span className="break-all font-mono text-xs">
                {finding.ruleId || "—"}
              </span>
            </Meta>
          </dl>
        </aside>
      </div>
    </div>
  );
}
