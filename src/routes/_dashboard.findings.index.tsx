import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ArrowUpDown, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { z } from "zod";

import { PageHeader } from "@/components/security/brand";
import { SeverityBadge, StatusBadge } from "@/components/security/severity";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { findingsQuery } from "@/services/queries";
import { SEVERITY_ORDER, type Finding } from "@/types/security";

const searchSchema = z.object({
  severity: z.enum(["critical", "high", "medium", "low", "info"]).optional(),
});

export const Route = createFileRoute("/_dashboard/findings/")({
  validateSearch: searchSchema,
  head: () => ({
    meta: [
      { title: "Security Findings — SecureScan" },
      {
        name: "description",
        content: "Explore, filter and triage all security findings from the latest scan.",
      },
      { property: "og:title", content: "Security Findings — SecureScan" },
      {
        property: "og:description",
        content: "Filterable explorer of all findings by severity, category, scanner and status.",
      },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(findingsQuery),
  component: FindingsPage,
});

type SortKey = "severity" | "title" | "category" | "file" | "scanner" | "status";

const ALL = "all";

function Filter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-full sm:w-40" aria-label={label}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>All {label.toLowerCase()}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option} value={option} className="capitalize">
            {option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function FindingsPage() {
  const { data: findings } = useSuspenseQuery(findingsQuery);
  const { severity: sevParam } = Route.useSearch();
  const navigate = useNavigate({ from: "/findings/" });

  const [q, setQ] = useState("");
  const [cat, setCat] = useState(ALL);
  const [scanner, setScanner] = useState(ALL);
  const [status, setStatus] = useState(ALL);
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({
    key: "severity",
    dir: 1,
  });

  const sev = sevParam ?? ALL;

  const uniq = (key: keyof Finding) =>
    Array.from(new Set(findings.map((finding) => String(finding[key]))));

  const rows = useMemo(() => {
    const query = q.toLowerCase();

    return findings
      .filter(
        (finding) =>
          (sev === ALL || finding.severity === sev) &&
          (cat === ALL || finding.category === cat) &&
          (scanner === ALL || finding.scanner === scanner) &&
          (status === ALL || finding.status === status),
      )
      .filter(
        (finding) =>
          !query ||
          `${finding.title} ${finding.file} ${finding.ruleId}`.toLowerCase().includes(query),
      )
      .sort((a, b) => {
        const comparison =
          sort.key === "severity"
            ? SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)
            : String(a[sort.key]).localeCompare(String(b[sort.key]));

        return comparison * sort.dir;
      });
  }, [findings, q, sev, cat, scanner, status, sort]);

  const Th = ({ k, children }: { k: SortKey; children: React.ReactNode }) => (
    <th scope="col" className="px-4 py-3 text-left font-normal">
      <button
        className="inline-flex items-center gap-1 eyebrow hover:text-foreground"
        onClick={() =>
          setSort((current) => ({
            key: k,
            dir: current.key === k ? (current.dir === 1 ? -1 : 1) : 1,
          }))
        }
      >
        {children}
        <ArrowUpDown className="size-3" />
      </button>
    </th>
  );

  return (
    <div>
      <PageHeader
        eyebrow="Persisted scan results"
        title="Security Findings"
        subtitle={`${findings.length} findings available · showing ${rows.length}`}
      />

      <div className="panel mb-4 flex flex-col gap-3 p-3 lg:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={q}
            onChange={(event) => setQ(event.target.value)}
            placeholder="Search findings..."
            className="pl-9"
            aria-label="Search findings"
          />
        </div>

        <div className="grid grid-cols-2 gap-3 sm:flex">
          <Filter
            label="Severity"
            value={sev}
            onChange={(value) =>
              navigate({
                search: value === ALL ? {} : { severity: value as Finding["severity"] },
              })
            }
            options={SEVERITY_ORDER}
          />

          <Filter label="Categories" value={cat} onChange={setCat} options={uniq("category")} />

          <Filter
            label="Scanners"
            value={scanner}
            onChange={setScanner}
            options={uniq("scanner")}
          />

          <Filter
            label="Statuses"
            value={status}
            onChange={setStatus}
            options={["open", "resolved", "ignored"]}
          />
        </div>
      </div>

      {/* Desktop table */}
      <div className="panel hidden overflow-x-auto md:block">
        <table className="w-full text-sm">
          <thead className="border-b bg-surface-2">
            <tr>
              <Th k="severity">Severity</Th>
              <Th k="title">Finding</Th>
              <Th k="category">Category</Th>
              <Th k="file">File</Th>
              <Th k="scanner">Scanner</Th>
              <Th k="status">Status</Th>
            </tr>
          </thead>

          <tbody className="divide-y">
            {rows.map((finding) => (
              <tr
                key={finding.id}
                className="cursor-pointer transition-colors hover:bg-accent/40"
                onClick={() =>
                  navigate({
                    to: "/findings/$findingId",
                    params: { findingId: finding.id },
                  })
                }
              >
                <td className="px-4 py-3">
                  <SeverityBadge severity={finding.severity} />
                </td>

                <td className="px-4 py-3">
                  <Link
                    to="/findings/$findingId"
                    params={{ findingId: finding.id }}
                    className="font-medium hover:text-primary"
                    onClick={(event) => event.stopPropagation()}
                  >
                    {finding.title}
                  </Link>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    {finding.id} · {finding.ruleId}
                  </p>
                </td>

                <td className="px-4 py-3 text-muted-foreground">{finding.category}</td>

                <td className="px-4 py-3 font-mono text-xs">
                  {finding.file}
                  {finding.line ? `:${finding.line}` : ""}
                </td>

                <td className="px-4 py-3 text-muted-foreground">{finding.scanner}</td>

                <td className="px-4 py-3">
                  <StatusBadge status={finding.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!rows.length && (
          <p className="p-10 text-center text-sm text-muted-foreground">
            {findings.length === 0
              ? "No findings have been returned by the API yet. Upload a project ZIP and run a scan first."
              : "No findings match the current filters."}
          </p>
        )}
      </div>

      {/* Mobile cards */}
      <ul className="space-y-3 md:hidden">
        {rows.map((finding) => (
          <li key={finding.id}>
            <Link
              to="/findings/$findingId"
              params={{ findingId: finding.id }}
              className="panel block p-4"
            >
              <div className="flex items-center justify-between">
                <SeverityBadge severity={finding.severity} />
                <StatusBadge status={finding.status} />
              </div>

              <p className="mt-3 font-medium">{finding.title}</p>

              <p className="mt-1 font-mono text-xs text-muted-foreground">
                {finding.file}
                {finding.line ? `:${finding.line}` : ""} · {finding.scanner}
              </p>
            </Link>
          </li>
        ))}
      </ul>

      {rows.length === 0 && (
        <div className="panel mt-3 p-6 text-center text-sm text-muted-foreground md:hidden">
          {findings.length === 0
            ? "No findings have been returned by the API yet. Upload a project ZIP and run a scan first."
            : "No findings match the current filters."}
        </div>
      )}
    </div>
  );
}
