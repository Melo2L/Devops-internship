import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { CheckCircle2, FileArchive, Lock, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/security/brand";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { scanSessionStore, useScanSession } from "@/hooks/use-scan-session";
import { projectService } from "@/services";

export const Route = createFileRoute("/_dashboard/scan/new")({
  head: () => ({
    meta: [
      { title: "Analyze your project — SecureScan" },
      {
        name: "description",
        content: "Upload a project archive to start an automated security assessment.",
      },
      { property: "og:title", content: "Analyze your project — SecureScan" },
      {
        property: "og:description",
        content: "Upload a ZIP archive and receive an automated security assessment.",
      },
    ],
  }),
  component: UploadPage,
});

const MAX = 100 * 1024 * 1024;

function UploadPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const upload = useScanSession((state) => state.upload);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  async function accept(file: File): Promise<void> {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      toast.error("Only .zip archives are supported.");
      return;
    }

    if (file.size === 0) {
      toast.error("The selected file is empty.");
      return;
    }

    if (file.size > MAX) {
      toast.error("The archive exceeds the 100 MB limit.");
      return;
    }

    setBusy(true);

    try {
      const result = await projectService.upload(file);

      scanSessionStore.set({
        upload: {
          name: result.filename,
          size: result.size_bytes,
        },
        uploadResult: result,
        scanComplete: true,
        statuses: {},
      });

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["findings"] }),
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["history"] }),
        queryClient.invalidateQueries({ queryKey: ["reports"] }),
      ]);
      toast.success("Project uploaded and analyzed successfully.");
      await navigate({ to: "/overview" });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "An unexpected error occurred while uploading the project.";

      toast.error(`Upload failed: ${message}`);
    } finally {
      setBusy(false);

      if (input.current) {
        input.current.value = "";
      }
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="New scan · Step 1 of 3"
        title="Analyze your project"
        subtitle="Upload your project and receive an automated security assessment."
      />

      {!upload ? (
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDrag(false);

            const file = event.dataTransfer.files[0];

            if (file && !busy) {
              void accept(file);
            }
          }}
          className={cn(
            "panel flex flex-col items-center justify-center border-dashed px-6 py-16 text-center transition-all",
            drag && "border-primary bg-primary/5 scale-[1.01]",
          )}
        >
          <div className="grid size-14 place-items-center rounded-full border border-primary/30 bg-primary/10 text-primary">
            <UploadCloud className="size-6" />
          </div>

          <p className="mt-5 font-medium">
            {busy ? "Uploading and analyzing…" : "Drag and drop your project archive"}
          </p>

          <p className="mt-1 text-sm text-muted-foreground">
            Supported format: ZIP · Maximum file size: 100 MB
          </p>

          <div className="mt-6 flex flex-wrap justify-center gap-2">
            <Button variant="outline" onClick={() => input.current?.click()} disabled={busy}>
              Browse files
            </Button>
          </div>

          <input
            ref={input}
            type="file"
            accept=".zip,application/zip"
            className="sr-only"
            aria-label="Upload project archive"
            disabled={busy}
            onChange={(event) => {
              const file = event.target.files?.[0];

              if (file) {
                void accept(file);
              }
            }}
          />
        </div>
      ) : (
        <div className="panel flex items-center gap-4 p-5 animate-fade-up">
          <div className="grid size-11 place-items-center rounded-lg bg-primary/10 text-primary">
            <FileArchive className="size-5" />
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate font-mono text-sm">{upload.name}</p>

            <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
              {(upload.size / 1024 / 1024).toFixed(1)} MB ·
              <CheckCircle2 className="size-3.5 text-success" />
              Uploaded and analyzed
            </p>
          </div>

          <Button
            variant="ghost"
            size="icon"
            aria-label="Remove file"
            onClick={() =>
              scanSessionStore.set({
                upload: null,
                uploadResult: null,
                scanComplete: false,
                statuses: {},
              })
            }
          >
            <X className="size-4" />
          </Button>
        </div>
      )}

      <div className="mt-6 flex items-start gap-3 rounded-lg border bg-surface-2 p-4 text-sm text-muted-foreground">
        <Lock className="mt-0.5 size-4 shrink-0 text-primary" />
        Uploaded projects are treated as untrusted input and analyzed in an isolated scanning
        environment.
      </div>

      <div className="mt-8 flex justify-end">
        <Button
          size="lg"
          disabled={!upload || busy}
          onClick={() => navigate({ to: "/scan/progress" })}
        >
          View Analysis Results
        </Button>
      </div>
    </div>
  );
}
