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
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Brand />

          <nav className="flex items-center gap-2">
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
          </div>

          <div className="panel mx-auto mt-16 max-w-5xl p-8 text-left md:p-12">
            <div className="flex items-start gap-4">
              <div className="grid size-12 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                <ShieldCheck className="size-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">Your project. Your results.</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                  Upload a ZIP archive to run the configured backend analysis. Findings, scanner
                  results and detected technologies are shown from the actual API response, not from
                  pre-filled sample data.
                </p>
                <Button asChild className="mt-5">
                  <Link to="/scan/new">
                    Upload a project <ArrowRight />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
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
          <ShieldCheck className="size-6 shrink-0 text-primary" />
          <p className="flex-1 text-sm text-muted-foreground">
            SecureScan reports the results returned by its configured backend scanners. Scanner
            availability depends on the backend configuration and the uploaded project.
          </p>
          <Button asChild variant="outline">
            <Link to="/scan/new">Analyze a project</Link>
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
