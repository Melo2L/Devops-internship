import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  Box,
  FileCode2,
  KeyRound,
  Network,
  Package,
  ShieldCheck,
  Upload,
  Settings2,
  Activity,
  FileText,
} from "lucide-react";
import { Brand } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { ScoreRing } from "@/components/security/score-ring";
import { SeverityBadge } from "@/components/security/severity";
import { sevBg } from "@/components/security/severity-styles";
import { mockCategories, mockFindings } from "@/data/mock";
import { SEVERITY_ORDER, SEVERITY_LABEL } from "@/types/security";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      {
        title: "DevOps Project TSSCiberseguridad",
      },
      {
        name: "description",
        content:
          "Upload a software project and receive an automated security assessment with an actionable Security Score.",
      },
      {
        property: "og:title",
        content: "DevOps Project TSSCiberseguridad",
      },
      {
        property: "og:description",
        content:
          "Upload a project, analyze its security posture, understand the risks, and know what to fix.",
      },
    ],
  }),
  component: Landing,
});

const CAPS = [
  { icon: FileCode2, label: "SAST" },
  { icon: Package, label: "Dependency Analysis" },
  { icon: KeyRound, label: "Secret Detection" },
  { icon: Box, label: "Container Security" },
  { icon: Network, label: "Infrastructure Security" },
];

const STEPS = [
  {
    icon: Upload,
    title: "Upload",
    text: "Submit a project archive. It is treated as untrusted input.",
  },
  {
    icon: Settings2,
    title: "Configure",
    text: "Choose which analysis engines run against the source tree.",
  },
  {
    icon: Activity,
    title: "Analyze",
    text: "Findings from every engine are normalized and scored.",
  },
  {
    icon: FileText,
    title: "Remediate",
    text: "Prioritized findings with clear, actionable remediation.",
  },
];

function Landing() {
  const counts = SEVERITY_ORDER.map((s) => ({
    s,
    n: mockFindings.filter((f) => f.severity === s).length,
  }));

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Brand />

          <nav className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link to="/overview">Demo</Link>
            </Button>

            <Button asChild size="sm">
              <Link to="/scan/new">Analyze a Project</Link>
            </Button>
          </nav>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0 bg-grid [mask-image:linear-gradient(to_bottom,black,transparent_85%)]"
          aria-hidden
        />

        <div className="absolute inset-0 bg-hero-glow" aria-hidden />

        <div className="relative mx-auto max-w-6xl px-6 pb-20 pt-20 text-center md:pt-28">
          <p className="eyebrow inline-flex items-center gap-2 rounded-full border bg-surface px-3 py-1">
            <span className="size-1.5 rounded-full bg-primary" />
            Automated security assessment
          </p>

          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
            Find vulnerabilities before attackers do.
          </h1>

          <p className="mx-auto mt-5 max-w-xl text-base text-muted-foreground md:text-lg">
            SecureScan analyzes your software projects and transforms security findings into an
            actionable security posture score.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button asChild size="lg">
              <Link to="/scan/new">
                Analyze a Project <ArrowRight />
              </Link>
            </Button>

            <Button asChild size="lg" variant="outline">
              <Link to="/overview">Explore Demo</Link>
            </Button>
          </div>

          {/* Dashboard preview */}
          <div className="panel mx-auto mt-16 max-w-5xl p-2 text-left">
            <div className="flex items-center gap-1.5 border-b px-3 pb-2 pt-1">
              <span className="size-2.5 rounded-full bg-muted" />
              <span className="size-2.5 rounded-full bg-muted" />
              <span className="size-2.5 rounded-full bg-muted" />

              <span className="ml-3 font-mono text-xs text-muted-foreground">
                DevOps Project TSSCiberseguridad / example-project / overview
              </span>
            </div>

            <div className="grid gap-4 p-4 md:grid-cols-[220px_1fr_1fr]">
              <div className="flex flex-col items-center justify-center rounded-lg border bg-background p-5">
                <p className="eyebrow mb-3">Security Score</p>

                <ScoreRing score={74} size={136} />

                <p className="mt-3 font-mono text-xs text-sev-medium">RISK: MODERATE</p>
              </div>

              <div className="space-y-3 rounded-lg border bg-background p-5">
                <p className="eyebrow">Categories</p>

                {mockCategories.map((c) => (
                  <div key={c.id}>
                    <div className="flex justify-between text-xs">
                      <span>{c.name}</span>
                      <span className="font-mono text-muted-foreground">{c.score}</span>
                    </div>

                    <div className="mt-1 h-1.5 rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${c.score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="space-y-3 rounded-lg border bg-background p-5">
                <p className="eyebrow">Severity</p>

                <div className="flex h-2 overflow-hidden rounded-full">
                  {counts.map(({ s, n }) => (
                    <div key={s} className={sevBg[s]} style={{ width: `${(n / 34) * 100}%` }} />
                  ))}
                </div>

                <ul className="space-y-1.5 text-xs">
                  {counts.map(({ s, n }) => (
                    <li key={s} className="flex justify-between">
                      <span className="text-muted-foreground">{SEVERITY_LABEL[s]}</span>

                      <span className="font-mono">{n}</span>
                    </li>
                  ))}
                </ul>

                <div className="space-y-2 border-t pt-3">
                  {mockFindings.slice(0, 2).map((f) => (
                    <div key={f.id} className="flex items-center gap-2 text-xs">
                      <SeverityBadge severity={f.severity} />
                      <span className="truncate">{f.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <p className="mt-3 text-xs text-muted-foreground">Preview uses simulated demo data.</p>
        </div>
      </section>

      <section className="border-y bg-surface">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-6 py-8 md:grid-cols-5">
          {CAPS.map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-3 text-sm text-muted-foreground">
              <Icon className="size-4 text-primary" />
              {label}
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20">
        <p className="eyebrow">Workflow</p>

        <h2 className="mt-2 text-2xl font-semibold tracking-tight md:text-3xl">
          From archive to actionable remediation.
        </h2>

        <div className="mt-10 grid gap-4 md:grid-cols-4">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <div key={title} className="panel p-5">
              <div className="flex items-center justify-between">
                <Icon className="size-5 text-primary" />

                <span className="font-mono text-xs text-muted-foreground">0{i + 1}</span>
              </div>

              <h3 className="mt-6 font-medium">{title}</h3>

              <p className="mt-1.5 text-sm text-muted-foreground">{text}</p>
            </div>
          ))}
        </div>

        <div className="panel mt-10 flex flex-col items-start gap-4 p-6 md:flex-row md:items-center">
          <ShieldCheck className="size-6 text-primary" />

          <p className="flex-1 text-sm text-muted-foreground">
            Planned analysis engines:{" "}
            <span className="text-foreground">Semgrep, Gitleaks, Trivy, Checkov</span> and SBOM
            generation. The current frontend runs a simulated demo — no real scans are executed yet.
          </p>

          <Button asChild variant="outline">
            <Link to="/overview">Explore Demo</Link>
          </Button>
        </div>
      </section>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-xs text-muted-foreground md:flex-row md:justify-between">
          <span>DevOps Project TSSCiberseguridad · Automated Security Assessment</span>

          <span>Alisson Melo Internship Project · 2026</span>
        </div>
      </footer>
    </div>
  );
}
