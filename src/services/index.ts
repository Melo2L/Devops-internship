import type {
  Dashboard,
  Finding,
  Project,
  Report,
  RiskLevel,
  Scan,
  Severity,
} from "@/types/security";

export const API_BASE =
  typeof window === "undefined"
    ? (process.env["SECURESCAN_API_INTERNAL_URL"] ?? "http://127.0.0.1:8000/api")
    : "/api";

interface ApiFinding {
  id?: string;
  scan_id?: string;
  scanner: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  file: string;
  line: number | null;
  status: string;
  remediation?: string | null;
  rule_id?: string | null;
  fingerprint?: string | null;
}

interface ApiScanSummary {
  id: string;
  filename: string;
  created_at: string;
  status: string;
  size_bytes: number;
  files_detected: number;
  files_extracted: number;
  findings_count: number;
}

export interface ApiScan extends ApiScanSummary {
  analysis?: {
    total_files?: number;
    languages?: Record<string, number>;
    technologies?: string[];
    detected_files?: string[];
  };
  scan_plan?: {
    enabled?: string[];
    skipped?: string[];
  };
  scans?: Array<{
    scanner: string;
    findings: ApiFinding[];
  }>;
  message?: string;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      body && typeof body.detail === "string"
        ? body.detail
        : `${response.status} ${response.statusText}`;

    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

function normalizeSeverity(value: string): Severity {
  switch (value.toLowerCase()) {
    case "critical":
      return "critical";
    case "high":
      return "high";
    case "medium":
      return "medium";
    case "low":
      return "low";
    default:
      return "info";
  }
}

function normalizeScanner(value: string): Finding["scanner"] {
  switch (value.toLowerCase()) {
    case "semgrep":
      return "Semgrep";
    case "gitleaks":
      return "Gitleaks";
    case "trivy":
      return "Trivy";
    case "checkov":
      return "Checkov";
    default:
      return value as Finding["scanner"];
  }
}

function normalizeCategory(value: string, scanner: string): Finding["category"] {
  const category = value.toLowerCase();

  if (category.includes("secret") || scanner === "Gitleaks") {
    return "Secrets";
  }
  if (category.includes("dependency") || category.includes("sca")) {
    return "SCA";
  }
  if (category.includes("container")) {
    return "Container";
  }
  if (
    category.includes("iac") ||
    category.includes("infrastructure") ||
    category.includes("terraform")
  ) {
    return "IaC";
  }
  if (category.includes("sast") || scanner === "Semgrep") {
    return "SAST";
  }
  return "Configuration";
}

function normalizeStatus(value: string): Finding["status"] {
  switch (value.toLowerCase()) {
    case "resolved":
      return "resolved";
    case "ignored":
    case "suppressed":
      return "ignored";
    default:
      return "open";
  }
}

function toFinding(raw: ApiFinding): Finding {
  const scanner = normalizeScanner(raw.scanner);

  return {
    id:
      raw.id ??
      `${raw.scan_id ?? "scan"}:${raw.fingerprint ?? `${raw.file}:${raw.line ?? 0}:${raw.rule_id ?? raw.title}`}`,
    ...(raw.scan_id ? { scan_id: raw.scan_id } : {}),
    severity: normalizeSeverity(raw.severity),
    title: raw.title,
    description: raw.description,
    impact: raw.description,
    category: normalizeCategory(raw.category, scanner),
    scanner,
    file: raw.file,
    line: raw.line,
    status: normalizeStatus(raw.status),
    remediation: raw.remediation ? [raw.remediation] : [],
    ruleId: raw.rule_id ?? "",
  };
}
export function mapApiFindings(scan: ApiScan): Finding[] {
  return findingsFromScan(scan);
}

function findingsFromScan(scan: ApiScan): Finding[] {
  return (scan.scans ?? []).flatMap((scanner) =>
    scanner.findings.map((finding) =>
      toFinding({
        ...finding,
        scanner: finding.scanner || scanner.scanner,
        scan_id: scan.id,
      }),
    ),
  );
}

async function originalFindingsForScan(scanId: string): Promise<Finding[]> {
  const snapshot = await apiFetch<ApiScan>(`/scans/${encodeURIComponent(scanId)}`);
  return findingsFromScan(snapshot);
}

const severityOrder: Severity[] = ["critical", "high", "medium", "low", "info"];

const penalties: Record<Severity, number> = {
  critical: 25,
  high: 15,
  medium: 7,
  low: 3,
  info: 1,
};

function riskFor(score: number): RiskLevel {
  if (score >= 85) return "LOW";
  if (score >= 65) return "MODERATE";
  if (score >= 45) return "HIGH";
  return "CRITICAL";
}

function scoreFindings(findings: Finding[]): number {
  return Math.max(
    0,
    100 - findings.reduce((total, finding) => total + penalties[finding.severity], 0),
  );
}

function toScan(summary: ApiScanSummary, number: number): Scan {
  return {
    id: summary.id,
    number,
    projectId: summary.filename,
    score: 0,
    date: summary.created_at,
    findingCount: summary.findings_count,
    status: summary.status === "completed" ? "completed" : "failed",
  };
}

export const scanService = {
  history: async (): Promise<Scan[]> => {
    const summaries = (await apiFetch<ApiScanSummary[]>("/scans")).sort(
      (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at),
    );

    return Promise.all(
      summaries.map(async (summary, index) => {
        const findings = await originalFindingsForScan(summary.id);

        return {
          ...toScan(summary, summaries.length - index),
          score: scoreFindings(findings),
          findingCount: findings.length,
        };
      }),
    );
  },

  getResult: async (scanId: string): Promise<ApiScan | undefined> => {
    try {
      return await apiFetch<ApiScan>(`/scans/${encodeURIComponent(scanId)}`);
    } catch (error) {
      if (error instanceof Error && error.message.includes("404")) {
        return undefined;
      }
      throw error;
    }
  },

  get: async (scanId: string): Promise<Scan | undefined> => {
    try {
      const scan = await apiFetch<ApiScan>(`/scans/${encodeURIComponent(scanId)}`);
      const findings = await originalFindingsForScan(scanId);

      return {
        ...toScan(scan, 1),
        score: scoreFindings(findings),
        findingCount: findings.length,
      };
    } catch (error) {
      if (error instanceof Error && error.message.includes("404")) {
        return undefined;
      }
      throw error;
    }
  },

  start: async (_projectId: string, _checks: string[]): Promise<{ scanId: string }> => {
    throw new Error("A nova análise é executada durante o upload do projeto ZIP.");
  },
};

export const projectService = {
  list: async (): Promise<Project[]> => {
    const scans = (await apiFetch<ApiScanSummary[]>("/scans")).sort(
      (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at),
    );
    const latestByFilename = new Map<string, ApiScanSummary>();

    for (const scan of scans) {
      if (!latestByFilename.has(scan.filename)) {
        latestByFilename.set(scan.filename, scan);
      }
    }

    return [...latestByFilename.values()].map((scan) => ({
      id: scan.filename,
      name: scan.filename,
      description: `${scan.files_extracted} ficheiros analisados`,
      language: "Consultar análise",
      sizeMb: scan.size_bytes / (1024 * 1024),
      lastScanId: scan.id,
    }));
  },

  upload: async (file: File): Promise<ApiScan> => {
    const formData = new FormData();
    formData.append("file", file);

    return apiFetch<ApiScan>("/projects/upload", {
      method: "POST",
      body: formData,
    });
  },
};

export const findingService = {
  list: async (scanId?: string): Promise<Finding[]> => {
    const query = scanId ? `?scan_id=${encodeURIComponent(scanId)}` : "";
    const findings = await apiFetch<ApiFinding[]>(`/findings${query}`);
    return findings.map(toFinding);
  },

  get: async (id: string): Promise<Finding | null> => {
    const findings = await findingService.list();
    return findings.find((finding) => finding.id === id) ?? null;
  },

  updateStatus: async (id: string, status: Finding["status"]): Promise<Finding> => {
    const updated = await apiFetch<ApiFinding>(`/findings/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status }),
    });

    return toFinding(updated);
  },
};

export const reportService = {
  list: async (): Promise<Report[]> => {
    const scans = (await apiFetch<ApiScanSummary[]>("/scans")).sort(
      (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at),
    );

    return Promise.all(
      scans.map(async (scan) => {
        const findings = await originalFindingsForScan(scan.id);

        const severityCounts: Record<Severity, number> = {
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
          info: 0,
        };

        for (const finding of findings) {
          severityCounts[finding.severity] += 1;
        }

        return {
          id: scan.id,
          title: `Relatório — ${scan.filename}`,
          projectName: scan.filename,
          scanId: scan.id,
          generated: scan.created_at,
          score: scoreFindings(findings),
          findingCount: findings.length,
          severityCounts,
        };
      }),
    );
  },

  get: async (id: string) => {
    const reports = await reportService.list();
    return reports.find((report) => report.id === id) ?? null;
  },
};

export const dashboardService = {
  get: async (): Promise<Dashboard> => {
    const summaries = (await apiFetch<ApiScanSummary[]>("/scans")).sort(
      (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at),
    );

    if (summaries.length === 0) {
      const emptyCounts: Record<Severity, number> = {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        info: 0,
      };

      return {
        project: {
          id: "",
          name: "Nenhum projeto analisado",
          description: "Envia um ficheiro ZIP para começar.",
          language: "—",
          sizeMb: 0,
          lastScanId: "",
        },
        scan: {
          id: "no-scan",
          number: 0,
          projectId: "",
          score: 0,
          date: "",
          findingCount: 0,
          status: "failed",
        },
        score: {
          score: 0,
          max: 100,
          riskLevel: "NOT_SCANNED",
          previous: null,
        },
        severityCounts: emptyCounts,
        categories: [],
        history: [],
        topFindings: [],
      };
    }

    // Prefer the scan from the most recent upload when the browser has
    // a saved ID; otherwise fall back to the newest scan returned by the API.
    let preferredScanId: string | null = null;
    try {
      if (typeof window !== "undefined") {
        preferredScanId = window.localStorage.getItem("securescan:last-scan-id");
      }
    } catch {
      // Browser storage may be unavailable; use the API's newest scan.
    }

    const latestSummary =
      summaries.find((summary) => summary.id === preferredScanId) ?? summaries[0];

    if (!latestSummary) {
      throw new Error("No scan summary available.");
    }

    const latest = await apiFetch<ApiScan>(`/scans/${encodeURIComponent(latestSummary.id)}`);
    // Read persisted finding statuses rather than the original scan snapshot.
    const allFindings = await findingService.list(latest.id);
    const findings = allFindings.filter((finding) => finding.status === "open");
    const score = scoreFindings(findings);

    // Compare only with the closest older scan of the same project.
    const previousSummary = summaries.find(
      (summary) =>
        summary.filename === latest.filename &&
        summary.id !== latest.id &&
        Date.parse(summary.created_at) < Date.parse(latest.created_at),
    );

    let previousScore: number | null = null;

    if (previousSummary) {
      const previousFindings = await originalFindingsForScan(previousSummary.id);
      previousScore = scoreFindings(previousFindings);
    }

    const severityCounts = findings.reduce(
      (counts, finding) => {
        counts[finding.severity] += 1;
        return counts;
      },
      {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        info: 0,
      } as Record<Severity, number>,
    );

    const categoryDefinitions = [
      { id: "SAST", name: "Source Code (SAST)" },
      { id: "Secrets", name: "Secrets" },
      { id: "SCA", name: "Dependencies (SCA)" },
      { id: "Container", name: "Containers" },
      { id: "IaC", name: "Infrastructure as Code" },
      { id: "Configuration", name: "Configuration" },
    ];

    const categories = categoryDefinitions.map((category) => {
      const categoryFindings = findings.filter((finding) => finding.category === category.id);

      return {
        ...category,
        score: scoreFindings(categoryFindings),
      };
    });

    const languageEntries = Object.entries(latest.analysis?.languages ?? {});
    const language = languageEntries.sort((a, b) => b[1] - a[1])[0]?.[0] ?? "Unknown";

    return {
      project: {
        id: latest.filename,
        name: latest.filename,
        description: latest.message ?? "Análise concluída.",
        language,
        sizeMb: latest.size_bytes / (1024 * 1024),
        lastScanId: latest.id,
      },
      scan: {
        ...toScan(latest, summaries.length),
        score,
      },
      score: {
        score,
        max: 100,
        riskLevel: riskFor(score),
        previous: previousScore,
      },
      severityCounts,
      categories,
      history: await Promise.all(
        summaries.slice(0, 10).map(async (summary, index) => {
          const historyFindings = await originalFindingsForScan(summary.id);

          return {
            ...toScan(summary, summaries.length - index),
            score: scoreFindings(historyFindings),
            findingCount: historyFindings.length,
          };
        }),
      ),
      topFindings: [...findings]
        .sort((a, b) => severityOrder.indexOf(a.severity) - severityOrder.indexOf(b.severity))
        .slice(0, 6),
    };
  },
};
