import { createFileRoute, Outlet } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/app-shell";

export const Route = createFileRoute("/_dashboard")({
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
});
