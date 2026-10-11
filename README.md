##### Alisson Melo Internship Project

##### SecureScan

**Automated Security Assessment Platform**

SecureScan is a DevSecOps internship project focused on automated application security assessment.

The platform is designed to allow a developer or organization to upload a software project and receive an automated security posture assessment, including security findings, severity classification, risk analysis, remediation guidance, reports, and scan history.

> **Current status:** The frontend currently uses simulated/demo scan data. Real security scanners and the FastAPI backend will be integrated in later phases.

###### Planned security analysis

- SAST / source-code analysis
- Dependency vulnerability analysis
- Secret detection
- Container security
- Infrastructure-as-Code security
- SBOM generation
- Security posture scoring

Planned scanner integrations include Semgrep, Gitleaks, Trivy and Checkov.

###### Frontend stack

- React
- TypeScript
- Vite
- TanStack Start / Router
- Tailwind CSS
- Recharts
- Vitest

###### Development

```sh
npm install
npm run dev
```

The development server runs on:

```text
http://localhost:3000
```

###### Project direction

The frontend is intentionally structured around service abstractions and domain types so that the current mock implementation can later be replaced by a FastAPI backend without rewriting the UI.

The long-term platform architecture will include:

```text
React / TypeScript
        |
        v
     FastAPI
        |
   +----+----+
   |         |
PostgreSQL Redis
             |
             v
        Scan Workers
             |
      +------+------+------+
      |      |      |      |
   Semgrep Gitleaks Trivy Checkov
```

The DevOps/DevSecOps layer will subsequently add Docker, Docker Compose, GitHub Actions, container security, observability, Terraform, and load testing.

###### Author

**Alisson Melo**

DevOps Internship Project — 2026
