import { Link } from "@tanstack/react-router";
import {
  FileText,
  FolderGit2,
  LayoutDashboard,
  Menu,
  Moon,
  PlusCircle,
  Settings,
  ShieldAlert,
  Sun,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { Brand } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { useTheme } from "@/hooks/use-theme";
import { useDemoStore } from "@/hooks/use-demo-store";

const NAV = [
  { to: "/overview", label: "Overview", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: FolderGit2 },
  { to: "/scan/new", label: "New Scan", icon: PlusCircle },
  { to: "/findings", label: "Findings", icon: ShieldAlert },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center px-5">
        <Link to="/" onClick={onNavigate}>
          <Brand />
        </Link>
      </div>
      <nav className="flex-1 space-y-0.5 px-3 py-4" aria-label="Main">
        {NAV.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            onClick={onNavigate}
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            activeProps={{
              className:
                "bg-sidebar-accent text-sidebar-accent-foreground font-medium shadow-[inset_2px_0_0_var(--sidebar-primary)]",
            }}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        ))}
      </nav>
      <div className="border-t border-sidebar-border px-5 py-4">
        <p className="eyebrow">Internship</p>
        <p className="mt-1 text-xs text-sidebar-foreground">Alisson Melo Internship Project</p>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { theme, toggle } = useTheme();
  const upload = useDemoStore((s) => s.upload);
  const complete = useDemoStore((s) => s.scanComplete);

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 border-r border-sidebar-border bg-sidebar lg:block">
        <SidebarNav />
      </aside>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="w-64 bg-sidebar p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarNav onNavigate={() => setOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b bg-background/85 px-4 backdrop-blur md:px-8">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="size-5" />
          </Button>
          <div className="flex min-w-0 items-center gap-3">
            <span className="eyebrow hidden sm:inline">Project</span>
            <span className="truncate font-mono text-sm">
              {upload?.name.replace(/\.zip$/i, "") ?? "No project selected"}
            </span>
            <span className="hidden items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs text-muted-foreground md:inline-flex">
              <span
                className={
                  complete
                    ? "size-1.5 rounded-full bg-success"
                    : "size-1.5 rounded-full bg-primary animate-pulse-dot"
                }
              />
              {complete ? "Latest scan completed" : upload ? "Ready to scan" : "No scan selected"}
            </span>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
              {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
            <div className="flex items-center gap-2 rounded-full border py-1 pl-1 pr-3">
              <span className="grid size-6 place-items-center rounded-full bg-primary/15 font-mono text-[10px] text-primary">
                SS
              </span>
              <span className="hidden text-xs sm:inline">Security Analyst</span>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-[1400px] px-4 py-8 md:px-8 animate-fade-up">{children}</main>
      </div>
    </div>
  );
}
