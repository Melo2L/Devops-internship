import { queryOptions } from "@tanstack/react-query";
import {
  dashboardService,
  findingService,
  projectService,
  reportService,
  scanService,
} from "./index";

export const dashboardQuery = queryOptions({
  queryKey: ["dashboard"],
  queryFn: dashboardService.get,
});
export const findingsQuery = queryOptions({
  queryKey: ["findings"],
  queryFn: () => {
    let scanId: string | null = null;
    try {
      if (typeof window !== "undefined") {
        scanId = window.localStorage.getItem("securescan:last-scan-id");
      }
    } catch {
      // If storage is unavailable, retain the API's unfiltered behaviour.
    }
    return findingService.list(scanId ?? undefined);
  },
});
export const findingQuery = (id: string) =>
  queryOptions({ queryKey: ["finding", id], queryFn: () => findingService.get(id) });
export const reportsQuery = queryOptions({ queryKey: ["reports"], queryFn: reportService.list });
export const historyQuery = queryOptions({ queryKey: ["history"], queryFn: scanService.history });
export const projectsQuery = queryOptions({ queryKey: ["projects"], queryFn: projectService.list });
