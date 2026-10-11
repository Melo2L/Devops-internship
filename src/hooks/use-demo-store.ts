// Tiny client-side store for the upload, analysis results and finding triage.
import { useSyncExternalStore } from "react";
import type { ProjectUploadResponse } from "@/services";
import type { CheckId, FindingStatus } from "@/types/security";

export interface DemoState {
  upload: { name: string; size: number } | null;
  uploadResult: ProjectUploadResponse | null;
  checks: Record<CheckId, boolean>;
  statuses: Record<string, FindingStatus>;
  scanComplete: boolean;
}

const initial: DemoState = {
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

export const demoStore = {
  get: () => state,

  set: (patch: Partial<DemoState> | ((s: DemoState) => Partial<DemoState>)) => {
    const next = typeof patch === "function" ? patch(state) : patch;
    state = { ...state, ...next };
    listeners.forEach((listener) => listener());
  },

  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};

export function useDemoStore<T>(selector: (s: DemoState) => T): T {
  return useSyncExternalStore(
    demoStore.subscribe,
    () => selector(state),
    () => selector(initial),
  );
}
