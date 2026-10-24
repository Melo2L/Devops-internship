// Tiny client-side store for the upload, analysis results and finding triage.
import { useSyncExternalStore } from "react";
import type { ApiScan } from "@/services";
import type { CheckId, FindingStatus } from "@/types/security";

export interface ScanSessionState {
  upload: { name: string; size: number } | null;
  uploadResult: ApiScan | null;
  checks: Record<CheckId, boolean>;
  statuses: Record<string, FindingStatus>;
  scanComplete: boolean;
}

const initial: ScanSessionState = {
  upload: null,
  uploadResult: null,
  checks: {
    sast: true,
    dependencies: true,
    secrets: true,
    containers: true,
    iac: true,
  },
  statuses: {},
  scanComplete: false,
};

let state = initial;
const listeners = new Set<() => void>();

export const scanSessionStore = {
  get: () => state,

  set: (
    patch: Partial<ScanSessionState> | ((s: ScanSessionState) => Partial<ScanSessionState>),
  ) => {
    const next = typeof patch === "function" ? patch(state) : patch;
    state = { ...state, ...next };

    // Store only the backend ID; restore the actual result through the API.
    if (typeof window !== "undefined" && "uploadResult" in next) {
      try {
        if (next.uploadResult?.id) {
          window.localStorage.setItem("securescan:last-scan-id", next.uploadResult.id);
        } else if (next.uploadResult === null) {
          window.localStorage.removeItem("securescan:last-scan-id");
        }
      } catch {
        // The in-memory session still works if browser storage is unavailable.
      }
    }

    listeners.forEach((listener) => listener());
  },

  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};

export function useScanSession<T>(selector: (s: ScanSessionState) => T): T {
  return useSyncExternalStore(
    scanSessionStore.subscribe,
    () => selector(state),
    () => selector(initial),
  );
}
