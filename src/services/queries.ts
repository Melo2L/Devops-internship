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
  queryFn: () => findingService.list(),
});
export const findingQuery = (id: string) =>
  queryOptions({ queryKey: ["finding", id], queryFn: () => findingService.get(id) });
export const reportsQuery = queryOptions({ queryKey: ["reports"], queryFn: reportService.list });
export const historyQuery = queryOptions({ queryKey: ["history"], queryFn: scanService.history });
export const projectsQuery = queryOptions({ queryKey: ["projects"], queryFn: projectService.list });
