// Domain types shared by the UI and the service layer.

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type FindingStatus = "open" | "resolved" | "ignored";
export type Scanner = "Semgrep" | "Gitleaks" | "Trivy" | "Checkov";
export type FindingCategory = "SAST" | "Secrets" | "SCA" | "Container" | "IaC" | "Configuration";
export type CheckId = "sast" | "dependencies" | "secrets" | "containers" | "iac";
export type RiskLevel = "NOT_SCANNED" | "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export interface Finding {
  id: string;
  scan_id?: string;
  severity: Severity;
  title: string;
  description: string;
  impact: string;
  category: FindingCategory;
  scanner: Scanner;
  file: string;
  line: number | null;
  status: FindingStatus;
  remediation: string[];
  snippet?: { startLine: number; lines: string[]; highlight: number; language: string } | undefined;
  ruleId: string;
}

export interface SecurityCategory {
  id: string;
  name: string;
  score: number;
}

export interface SecurityScore {
  score: number;
  max: 100;
  riskLevel: RiskLevel;
  previous: number | null;
}

export interface Scan {
  id: string;
  number: number;
  projectId: string;
  score: number;
  date: string; // ISO
  findingCount: number;
  status: "completed" | "running" | "failed";
}

export interface Project {
  id: string;
  name: string;
  description: string;
  language: string;
  sizeMb: number;
  lastScanId: string;
}

export interface Report {
  id: string;
  title: string;
  projectName: string;
  scanId: string;
  generated: string;
  score: number;
  findingCount: number;
  severityCounts: Record<Severity, number>;
}

export interface ScanStage {
  id: string;
  label: string;
  check?: CheckId;
}

export interface Dashboard {
  project: Project;
  scan: Scan;
  score: SecurityScore;
  severityCounts: Record<Severity, number>;
  categories: SecurityCategory[];
  history: Scan[];
  topFindings: Finding[];
}

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];
export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  info: "Informational",
};
