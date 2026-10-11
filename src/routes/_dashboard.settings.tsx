import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/security/brand";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import { demoStore, useDemoStore } from "@/hooks/use-demo-store";
import type { CheckId } from "@/types/security";

export const Route = createFileRoute("/_dashboard/settings")({
  head: () => ({
    meta: [
      { title: "Settings — SecureScan" },
      {
        name: "description",
        content: "Project, scan, notification and theme settings, plus About SecureScan.",
      },
      { property: "og:title", content: "Settings — SecureScan" },
      { property: "og:description", content: "Configure SecureScan and learn about the project." },
    ],
  }),
  component: SettingsPage,
});

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="panel grid gap-6 p-6 md:grid-cols-[220px_1fr]">
      <h2 className="font-medium">{title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function Row({
  id,
  label,
  desc,
  checked,
  onChange,
}: {
  id: string;
  label: string;
  desc?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <Label htmlFor={id}>{label}</Label>
        {desc && <p className="text-xs text-muted-foreground">{desc}</p>}
      </div>
      <Switch id={id} checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

const CHECK_LABELS: Record<CheckId, string> = {
  sast: "SAST",
  dependencies: "Dependency analysis",
  secrets: "Secret detection",
  containers: "Container security",
  iac: "IaC security",
};

function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const checks = useDemoStore((s) => s.checks);
  return (
    <div className="space-y-4">
      <PageHeader title="Settings" />
      <Section title="Project information">
        <div className="grid gap-2">
          <Label htmlFor="pname">Project name</Label>
          <Input id="pname" defaultValue="Example Project" />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="pdesc">Description</Label>
          <Input id="pdesc" defaultValue="Demo Python web API" />
        </div>
      </Section>
      <Section title="Default scan configuration">
        {(Object.keys(CHECK_LABELS) as CheckId[]).map((k) => (
          <Row
            key={k}
            id={`s-${k}`}
            label={CHECK_LABELS[k]}
            checked={checks[k]}
            onChange={(v) => demoStore.set((s) => ({ checks: { ...s.checks, [k]: v } }))}
          />
        ))}
      </Section>
      <Section title="Notifications">
        <Row
          id="n1"
          label="Scan completed"
          desc="Notify when an analysis finishes."
          checked
          onChange={() => {}}
        />
        <Row
          id="n2"
          label="New critical findings"
          desc="Alert when critical findings are detected."
          checked
          onChange={() => {}}
        />
      </Section>
      <Section title="Theme">
        <div className="flex gap-2">
          <Button
            variant={theme === "dark" ? "default" : "outline"}
            onClick={() => setTheme("dark")}
          >
            Dark
          </Button>
          <Button
            variant={theme === "light" ? "default" : "outline"}
            onClick={() => setTheme("light")}
          >
            Light
          </Button>
        </div>
      </Section>
      <Section title="About SecureScan">
        <p className="text-sm text-muted-foreground">
          SecureScan is an internship project focused on applying DevSecOps principles to automated
          application security assessment.
        </p>
        <div className="rounded-lg border bg-surface-2 p-4">
          <p className="font-medium">Alisson Melo</p>
          <p className="text-sm text-muted-foreground">DevOps Internship Project · 2026</p>
        </div>
        <p className="text-xs text-muted-foreground">
          Planned stack: Python, FastAPI, PostgreSQL, Redis, Docker, GitHub Actions, Semgrep,
          Gitleaks, Trivy, Checkov, Prometheus, Grafana, Terraform, k6.
        </p>
      </Section>
    </div>
  );
}
