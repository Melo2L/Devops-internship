import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { PageHeader } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";

export const Route = createFileRoute("/_dashboard/settings")({
  head: () => ({
    meta: [
      { title: "Settings — SecureScan" },
      {
        name: "description",
        content: "Manage the SecureScan interface appearance.",
      },
    ],
  }),
  component: SettingsPage,
});

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel space-y-4 p-5">
      <h2 className="font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="space-y-4">
      <PageHeader title="Settings" />

      <Section title="Appearance">
        <p className="text-sm text-muted-foreground">
          Choose the appearance of the SecureScan interface.
        </p>
        <div className="flex flex-wrap gap-2">
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
        <p className="text-sm leading-6 text-muted-foreground">
          SecureScan is a DevSecOps internship project for automated application security
          assessment. It reports the results returned by the configured backend analysis. Available
          scanners and findings depend on the backend configuration and uploaded project.
        </p>
        <div className="border-t pt-4">
          <p className="font-medium">Alisson Melo</p>
          <p className="text-sm text-muted-foreground">DevOps Internship Project · 2026</p>
        </div>
      </Section>
    </div>
  );
}
