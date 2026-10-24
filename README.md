# SecureScan

### Automated Security Assessment Platform

**Alisson Melo — DevOps Internship Project, 2026**

SecureScan is a DevSecOps project designed to assess application security by analyzing uploaded software projects, identifying potential security issues, and organizing findings for review and remediation.

The repository contains a web frontend, a FastAPI backend, security scanning components, automated tests, and Docker-based deployment configuration.

> **Project status:** The backend and scanning components are implemented with automated tests. The frontend still contains demo/mock service data and is not yet fully integrated with the backend API. Treat the application as an internship project under active development, not as a production-ready security product.

## Contents

- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Current Capabilities](#current-capabilities)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [API](#api)
- [Security Considerations](#security-considerations)
- [Roadmap](#roadmap)
- [Author](#author)

## Architecture

The current deployment uses Docker Compose to run the frontend and backend as separate services.

```text
                  Developer
                      |
                      v
              Web Frontend :3000
              React / TypeScript
                      |
          Frontend integration pending
                      |
                      v
                FastAPI :8000
                      |
             Project upload and
              scan orchestration
                      |
             +--------+--------+
             |                 |
             v                 v
        Semgrep             Gitleaks
       Source analysis     Secret detection
             |                 |
             +--------+--------+
                      |
                      v
              Security findings
                      |
                      v
             SQLite persistence
               /data volume
```

The diagram describes the current project direction. The frontend-to-backend integration is not complete, and the architecture should not be interpreted as proof that every UI feature is connected end to end.

### Docker Compose services

| Service | Purpose | Local URL |
|---|---|---|
| `frontend` | Web application | http://localhost:3000 |
| `backend` | FastAPI application | http://localhost:8000 |
| Backend health endpoint | Service health check | http://localhost:8000/health |
| API documentation | Interactive API docs | http://localhost:8000/docs |

The backend uses a named Docker volume for persistent scan data. Keep this volume when restarting the application if you need to preserve saved scans.

## Technology Stack

### Frontend
- React
- TypeScript
- Vite and TanStack Start/Router
- Tailwind CSS
- Vitest
- ESLint

### Backend
- Python
- FastAPI
- Uvicorn
- SQLite persistence
- Pytest

### Security analysis
- Semgrep for source-code security analysis
- Gitleaks for secret detection

### DevOps
- Docker
- Docker Compose
- Multi-stage frontend Docker build
- Container health checks
- Git and GitHub

Additional scanners and infrastructure tooling are roadmap items unless explicitly implemented and verified.

## Current Capabilities

The repository currently includes:

- A web dashboard and security-oriented UI.
- A FastAPI backend with a health endpoint and project/scan API components.
- Secure upload and archive-extraction components.
- Scan planning and execution services.
- Semgrep and Gitleaks integration components and finding normalizers.
- SQLite-backed persistence for scan data.
- Automated backend tests.
- Docker Compose configuration for running the frontend and backend.

The frontend currently uses demo/mock service data in parts of the application. Do not assume that all dashboard, report, history, or finding views are backed by live API responses.

## Getting Started

### Prerequisites

- Git
- Docker Engine
- Docker Compose v2

Docker is the recommended way to run the complete local environment because the frontend and backend have separate runtime requirements.

### 1. Clone the repository

```bash
git clone https://github.com/Melo2L/Devops-internship.git
cd Devops-internship
```

### 2. Build and start the services

```bash
docker compose up --build -d
```

### 3. Check service status

```bash
docker compose ps
```

Inspect the service logs if a container fails to start:

```bash
docker compose logs --tail=100
```

To follow the logs continuously:

```bash
docker compose logs -f
```

### 4. Open the application

- Frontend: http://localhost:3000
- API health check: http://localhost:8000/health
- Interactive API documentation: http://localhost:8000/docs

The backend health endpoint should return a healthy status when the service is running correctly.

### 5. Stop the services

```bash
docker compose down
```

This command stops and removes the Compose containers and network without deleting the named data volume.

**Data warning:** Avoid `docker compose down -v` unless you intentionally want to delete the Compose-managed volumes and their stored data.

## Running Tests

### Backend tests

Create and activate a Python virtual environment if you want to run the backend tests directly on your host. On Ubuntu, install the Python venv support package for your installed Python version if it is missing.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m pip install pytest
```

Run the backend tests with an isolated temporary SQLite database:

```bash
SECURESCAN_DATABASE_PATH=/tmp/securescan-tests.db \
python -m pytest backend/tests/ -q
```

The environment variable keeps the test database separate from the application's default database path. The test suite should be rerun after code changes; test results can vary as the project evolves.

### Frontend tests and quality checks

The frontend uses pnpm. With a compatible Node.js installation and Corepack/pnpm available, install dependencies from the lockfile:

```bash
pnpm install --frozen-lockfile
```

Run the scripts defined by `package.json`. To inspect the available scripts:

```bash
pnpm run
```

For example, if the corresponding scripts are present:

```bash
pnpm test
pnpm lint
pnpm build
```

## API

The backend is implemented with FastAPI.

- Health check: `GET /health`
- Interactive API documentation: `/docs`

Additional API routes are implemented in the backend source. Use the interactive API documentation to inspect the available operations and their request/response schemas.

Example health check:

```bash
curl -fsS http://localhost:8000/health
```

## Security Considerations

SecureScan analyzes software projects and therefore handles potentially untrusted input. The project includes upload-validation and secure-extraction components, but these controls must be reviewed and tested before any public or production deployment.

Recommended operational practices:

- Run the application in a controlled environment.
- Do not upload confidential or production source code unless the environment is approved for it.
- Never commit API tokens, passwords, private keys, or environment files containing secrets.
- Keep dependencies and scanner versions reviewed and updated.
- Restrict network exposure and access to the API when deploying beyond localhost.
- Review security findings manually; automated scanners can produce false positives and miss vulnerabilities.
- Treat uploaded archives and all scan results as untrusted data.
- Validate container permissions, resource limits, and isolation before accepting untrusted projects from external users.

This project is not a substitute for a comprehensive security review or a guarantee that an analyzed application is secure.

## Roadmap

Potential next improvements include:

- Complete the frontend-to-backend API integration.
- Replace demo data with persisted backend responses.
- Improve end-to-end and integration test coverage.
- Add continuous integration with automated tests, linting, and build checks.
- Introduce dependency, container, and Infrastructure-as-Code scanning where required.
- Generate software bills of materials (SBOMs).
- Improve report generation and security posture scoring.
- Add structured logging, metrics, and operational monitoring.
- Harden deployment configuration and document a production threat model.

Roadmap items are proposals and should not be interpreted as existing features.

## Author

**Alisson Melo**

DevOps Internship Project — 2026

Repository: https://github.com/Melo2L/Devops-internship
