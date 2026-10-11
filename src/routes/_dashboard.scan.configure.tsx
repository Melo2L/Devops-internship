import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Box, FileCode2, KeyRound, Network, Package } from "lucide-react";
import { PageHeader } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useDemoStore } from "@/hooks/use-demo-store";
import type { CheckId } from "@/types/security";

export const Route = createFileRoute("/_dashboard/scan/configure")({
  head: () => ({
    meta: [
      { title: "Configure Security Analysis — SecureScan" },
      { name: "description", content: "Choose which security checks run against your project." },
      { property: "og:title", content: "Configure Security Analysis — SecureScan" },
      {
        property: "og:description",
        content: "Enable SAST, dependency, secret, container and IaC checks.",
      },
    ],
  }),
  component: ConfigurePage,
});

const CHECKS: {
  id: CheckId;
  group: string;
  label: string;
  desc: string;
  icon: typeof Box;
  engine: string;
}[] = [
  {
    id: "sast",
    group: "Source Code Analysis",
    label: "SAST",
    desc: "Detect insecure code patterns such as injection and unsafe deserialization.",
    icon: FileCode2,
    engine: "Semgrep",
  },
  {
    id: "dependencies",
    group: "Dependencies",
    label: "Dependency vulnerability analysis",
    desc: "Match declared packages against known vulnerability databases.",
    icon: Package,
    engine: "Trivy",
  },
  {
    id: "secrets",
    group: "Secrets",
    label: "Secret detection",
    desc: "Find credentials, tokens and keys committed to the source tree.",
    icon: KeyRound,
    engine: "Gitleaks",
  },
  {
    id: "containers",
    group: "Containers",
    label: "Container security",
    desc: "Evaluate Dockerfiles and base images for misconfigurations.",
    icon: Box,
    engine: "Trivy",
  },
  {
    id: "iac",
    group: "Infrastructure as Code",
    label: "IaC security",
    desc: "Check Terraform and other IaC for insecure cloud resources.",
    icon: Network,
    engine: "Checkov",
  },
];

function ConfigurePage() {
  const navigate = useNavigate();
  const checks = useDemoStore((s) => s.checks);
  const upload = useDemoStore((s) => s.upload);
  const enabled = Object.entries(checks)
    .filter(([, v]) => v)
    .map(([k]) => k);

  function start() {
    // The analysis already ran during upload. Show its actual results.
    navigate({ to: "/scan/progress" });
  }

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="New scan · Step 2 of 3"
        title="Configure Security Analysis"
        subtitle={`Target: ${upload?.name ?? "project.zip"}`}
        actions={undefined}
      />
      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div className="space-y-3">
          {CHECKS.map(({ id, group, label, desc, icon: Icon }) => (
            <label
              key={id}
              htmlFor={`chk-${id}`}
              className="panel flex cursor-pointer items-start gap-4 p-5 transition-colors hover:border-primary/40"
            >
              <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-secondary text-primary">
                <Icon className="size-5" />
              </div>
              <div className="flex-1">
                <p className="eyebrow">{group}</p>
                <p className="mt-1 font-medium">{label}</p>
                <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
              </div>
              <Switch
                id={`chk-${id}`}
                checked={checks[id]}
                onCheckedChange={(v) =>
                  demoStore.set((s) => ({ checks: { ...s.checks, [id]: v } }))
                }
              />
            </label>
          ))}
        </div>
        <aside className="space-y-4">
          <div className="panel p-5">
            <p className="eyebrow">Analysis engines</p>
            <ul className="mt-4 space-y-3 text-sm">
              {["Semgrep", "Gitleaks", "Trivy", "Checkov"].map((e) => (
                <li key={e} className="flex items-center justify-between">
                  <span className="font-mono">{e}</span>
                  <span className="text-xs text-muted-foreground">planned</span>
                </li>
              ))}
            </ul>
            <p className="mt-4 border-t pt-4 text-xs text-muted-foreground">
              The current backend executes its configured scanners during upload. These switches do
              not change that completed analysis.
            </p>
          </div>
          <div className="panel p-5 text-sm">
            <p className="eyebrow">Summary</p>
            <p className="mt-3">
              <span className="font-mono text-2xl">{enabled.length}</span>{" "}
              <span className="text-muted-foreground">of 5 checks enabled</span>
            </p>
          </div>
          <Button size="lg" className="w-full" disabled={!enabled.length} onClick={start}>
            Start Security Analysis
          </Button>
        </aside>
      </div>
    </div>
  );
}
