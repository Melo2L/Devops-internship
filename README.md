# SecureScan
## Automated Security Assessment Platform

**Alisson Melo — DevOps Internship Project, 2026**

SecureScan is a DevSecOps platform designed to assess software project security through automated analysis. It accepts uploaded ZIP archives, orchestrates security scanners, collects findings and provides an API for reviewing and managing scan results.

The project combines a web frontend, a FastAPI backend, multiple security scanners, containerized infrastructure, automated CI/CD, Infrastructure as Code and observability.

> **Project status:** SecureScan is an internship and portfolio project under active development. Backend scanning components, automated tests, Docker infrastructure, CI/CD and monitoring are implemented. Some frontend areas still use demonstration/mock data and should not be assumed to be fully integrated with live backend responses. The project is not presented as a production-ready commercial security product.

---

# Contents

1. [Architecture](#architecture)
2. [Technology Stack](#technology-stack)
3. [Security Scanning](#security-scanning)
4. [Current Capabilities](#current-capabilities)
5. [Architecture and Infrastructure](#architecture-and-infrastructure)
6. [Getting Started](#getting-started)
7. [Running Tests](#running-tests)
8. [API Reference](#api-reference)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Monitoring and Observability](#monitoring-and-observability)
11. [Infrastructure as Code](#infrastructure-as-code)
12. [Security Considerations](#security-considerations)
13. [Evidence and Validation](#evidence-and-validation)
14. [Known Limitations and Roadmap](#known-limitations-and-roadmap)
15. [Author](#author)

---

## Architecture

SecureScan follows a modular architecture in which the frontend communicates with a FastAPI backend responsible for project uploads, scan orchestration, persistence and findings management.

```text
                         Developer
                             |
                             v
                    React / TypeScript
                       Frontend :3000
                             |
                             v
                       FastAPI Backend
                          :8000
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
           Gitleaks       Semgrep         Trivy
         Secret scan    SAST analysis   Vulnerability
                                          analysis
              |              |              |
              +--------------+--------------+
                             |
                             v
                          Checkov
                      IaC Security Scan
                             |
                             v
                    Findings Normalization
                             |
                             v
                     SQLite Persistence
                          /data

        Observability and Infrastructure Services
        +-------------+  +-------------+  +-------------+
        | Prometheus  |  |   Grafana   |  | Alertmanager|
        |   :9090     |  |    :3001    |  |    :9093    |
        +-------------+  +-------------+  +-------------+
```

The diagram represents the implemented scanning architecture and infrastructure components. Actual scanner execution depends on the uploaded project, the scan plan and the availability of the relevant files and tools. For example, Checkov may be skipped when no supported Infrastructure as Code files are present.

Some frontend views still contain demonstration data. Therefore, the diagram must not be interpreted as proof that every dashboard element is connected to a live API response.

### Docker Compose services

| Service | Purpose | Local URL |
|---|---|---|
| backend | FastAPI application and scan orchestration | http://localhost:8000 |
| frontend | Web application | http://localhost:3000 |
| prometheus | Metrics collection and alert evaluation | http://localhost:9090 |
| grafana | Dashboards and visualization | http://localhost:3001 |
| alertmanager | Alert handling and notification routing | http://localhost:9093 |

### Persistent volumes

The Compose configuration defines persistent storage for:

- `securescan_data` — application data.
- `prometheus_data` — Prometheus time-series data.
- `grafana_data` — Grafana data.
- `trivy_cache` — persistent Trivy cache, configured as an external Docker volume named `securescan-trivy-cache`.

The external Trivy cache volume must exist before starting the Compose stack.

---

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- TanStack Start / Router
- Tailwind CSS
- pnpm
- Vitest
- ESLint

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- SQLite
- Pytest
- Ruff

### Security tools

- Gitleaks
- Semgrep
- Trivy
- Checkov

### DevOps and infrastructure

- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)
- Terraform
- Prometheus
- Grafana
- Alertmanager
- K6

---

## Security Scanning

SecureScan integrates several security tools to analyze different aspects of software projects.

| Scanner | Purpose | Analysis area |
|---|---|---|
| Gitleaks | Detects exposed secrets and credentials | Secret detection |
| Semgrep | Identifies potentially insecure code patterns | Static Application Security Testing (SAST) |
| Trivy | Detects known vulnerabilities in supported dependencies and components | Vulnerability analysis |
| Checkov | Evaluates Infrastructure as Code configurations | IaC security |

### Scan workflow

1. A project archive is uploaded through the backend API.
2. Upload validation and secure archive extraction are performed.
3. The project analyzer identifies relevant project characteristics.
4. The scan planner determines which scanners are applicable.
5. The scan executor runs the selected security tools.
6. Scanner outputs are normalized into a common findings structure.
7. Scan information and findings are persisted for retrieval and review.

Scanner availability and results depend on the contents of the uploaded archive. A scanner can be skipped when its required project files or configuration are not present.

Automated findings require human review. A scanner result is not, by itself, proof that a vulnerability is exploitable.

---

## Current Capabilities

The repository includes the following implemented components:

- React and TypeScript web frontend.
- FastAPI backend.
- Project upload API.
- Secure upload validation and archive extraction components.
- Project analysis and scan planning.
- Scan execution orchestration.
- Gitleaks integration and findings normalization.
- Semgrep integration and findings normalization.
- Trivy integration and findings normalization.
- Checkov integration and findings normalization.
- SQLite-backed scan persistence.
- Scan retrieval and findings management endpoints.
- Prometheus HTTP metrics.
- Prometheus alert rules and tests.
- Grafana dashboard provisioning.
- Alertmanager configuration.
- Docker Compose infrastructure.
- Terraform configuration for Docker resources.
- GitHub Actions CI/CD workflow.
- GHCR image publication.
- Automated backend and frontend checks.
- K6 load-testing scripts.

Some frontend screens still use mock or demonstration data. The availability of a backend endpoint does not automatically mean that every corresponding frontend component consumes it.

---

## Architecture and Infrastructure

### Backend container security

The backend Compose service includes several hardening measures:

- Read-only container filesystem.
- Dedicated writable temporary filesystem.
- Non-root application user.
- Persistent application data volume.
- Dedicated persistent Trivy cache volume.
- HTTP health check.
- Automatic restart policy.

### Frontend container security

The frontend service includes:

- Read-only container filesystem.
- Temporary filesystem for runtime temporary data.
- Dropped Linux capabilities.
- `no-new-privileges` security option.
- Backend health dependency.

These controls reduce the container's writable surface and privileges. They do not replace host hardening, network controls or a complete container security assessment.

---

## Getting Started

### Prerequisites

- Git
- Docker Engine
- Docker Compose v2
- Access to the project repository
- A configured `.env` file
- The external Docker volume `securescan-trivy-cache`
- The Alertmanager SMTP secret file required by the Compose configuration

### 1. Clone the repository

```bash
git clone https://github.com/Melo2L/Devops-internship.git
cd Devops-internship
```

### 2. Configure environment variables and secrets

Configure the local `.env` file before starting the stack.

At minimum, the Compose configuration requires:

- `GRAFANA_ADMIN_PASSWORD` — Grafana administrator password.
- Any additional environment variables required by the local deployment.

The Alertmanager service mounts the SMTP password from:

```text
secrets/smtp_password
```

Provide the required secret locally. Do not commit `.env`, SMTP credentials, tokens or passwords to Git.

### 3. Create the external Trivy cache volume

```bash
docker volume create securescan-trivy-cache
```

This command creates the external volume expected by Compose. If it already exists, preserve it.

### 4. Build and start the services

```bash
docker compose up --build -d
```

### 5. Check service status

```bash
docker compose ps
```

Inspect logs:

```bash
docker compose logs --tail=100
```

Follow logs continuously:

```bash
docker compose logs -f
```

### 6. Access the application

| Component | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend health | http://localhost:8000/health |
| Interactive API documentation | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| Alertmanager | http://localhost:9093 |

Grafana credentials depend on the local environment configuration.

### 7. Stop the services

```bash
docker compose down
```

This stops and removes the Compose containers and network without deleting the named volumes.

> **Data warning:** Avoid `docker compose down -v` unless you intentionally want to remove Compose-managed volumes and their stored data. Preserve the external Trivy cache volume unless you explicitly intend to remove it.

---

## Running Tests

### Backend tests

The project uses Pytest for backend testing.

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install pytest
```

Run the backend test suite with an isolated temporary SQLite database:

```bash
SECURESCAN_DATABASE_PATH=/tmp/securescan-tests.db \
python -m pytest backend/tests/ -q
```

The temporary database path prevents the test run from using the application's normal database.

### Backend lint

```bash
ruff check backend
```

### Frontend tests and quality checks

The frontend uses pnpm.

Install dependencies:

```bash
pnpm install --frozen-lockfile
```

Run the available scripts:

```bash
pnpm test
pnpm run lint
pnpm run build
```

TypeScript validation:

```bash
pnpm exec tsc --noEmit
```

The exact test results depend on the code revision and environment. Refer to the corresponding CI run for the validation status of a specific commit.

### Load testing

K6 scripts are available in:

```text
load-tests/
```

The repository includes API load and stress testing scripts. Run them only against an environment you control.

Example:

```bash
k6 run load-tests/api-load-test.js
```

Consult `load-tests/README.md` and the individual scripts for their specific parameters and target endpoints.

---

## API Reference

The backend is implemented with FastAPI.

Interactive documentation is available at:

```text
http://localhost:8000/docs
```

### Health and monitoring endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Backend health check |
| GET | `/metrics` | Prometheus metrics endpoint |

The metrics endpoint is excluded from the generated OpenAPI schema.

### Project upload

| Method | Declared route | Description |
|---|---|---|
| POST | `/upload` | Upload a project archive for analysis |

### Scan operations

| Method | Declared route | Description |
|---|---|---|
| GET | `/scans` | Retrieve scans |
| GET | `/scans/{scan_id}` | Retrieve a specific scan |
| GET | `/scans/{scan_id}/findings` | Retrieve findings associated with a scan |

### Findings operations

| Method | Declared route | Description |
|---|---|---|
| GET | `/findings` | Retrieve findings |
| PATCH | `/findings/{finding_id}/status` | Update a finding status |

> **Routing note:** The paths above reflect the route declarations in the backend router modules. Router prefixes may be applied when the routers are registered in the FastAPI application. Consult `/docs` for the effective full paths and request schemas of the running API.

Example health check:

```bash
curl -fsS http://localhost:8000/health
```

---

## CI/CD Pipeline

SecureScan uses GitHub Actions to automate quality checks, testing, security validation, image building and publication.

The workflow is defined in:

```text
.github/workflows/ci.yml
```

### Pipeline jobs

| Job | Responsibility |
|---|---|
| Frontend quality checks | TypeScript validation, lint, tests and build |
| Backend tests and lint | Secret scanning, Ruff and Pytest |
| Terraform quality gate | Formatting, initialization and validation |
| Trivy security quality gate | Dependency and infrastructure/configuration security checks |
| Validate Prometheus alert rules | Alert rule syntax and rule tests |
| Build and scan Docker images | Build and vulnerability scan of container images |
| Publish Docker images to GHCR | Publish frontend and backend images |
| Deploy SecureScan on Ubuntu | Pull, update and verify services on the configured self-hosted runner |

### Container registry

Published images:

```text
ghcr.io/melo2l/devops-internship-backend
ghcr.io/melo2l/devops-internship-frontend
```

The workflow publishes:

- `latest`
- Commit-specific `sha-*` tags

The commit-specific tags provide a way to identify images associated with a particular source revision.

### Deployment

The deployment job runs on a configured self-hosted Ubuntu runner labelled:

```text
securescan-deploy
```

The workflow pulls the published images, updates the backend and frontend services and checks their availability.

This describes the configured deployment workflow. It does not imply that SecureScan is publicly accessible or deployed to a VPS.

### GitHub Actions security

The workflow uses GitHub-provided permissions and secrets for operations such as GHCR authentication. Deployment environment files and credentials are kept outside the repository.

---

## Monitoring and Observability

SecureScan includes a monitoring stack based on Prometheus, Grafana and Alertmanager.

### Prometheus

Configuration:

```text
monitoring/prometheus/prometheus.yml
monitoring/prometheus/rules/securescan-alerts.yml
monitoring/prometheus/tests/securescan-alerts-test.yml
```

Prometheus collects application metrics and evaluates configured alert rules.

The backend exposes HTTP metrics, including:

- `securescan_http_requests_total`
- `securescan_http_request_duration_seconds`

### Grafana

Grafana is provisioned with:

- Prometheus data source.
- Dashboard provisioning.
- SecureScan overview dashboard.

Dashboard definition:

```text
monitoring/grafana/dashboards/securescan-overview.json
```

### Alertmanager

Configuration:

```text
monitoring/alertmanager/alertmanager.yml
```

Alertmanager handles alert routing and notification configuration. SMTP credentials are supplied through a locally mounted secret file.

### Validation

Prometheus alert rules are validated and tested by the GitHub Actions workflow.

---

## Infrastructure as Code

Terraform configuration is located in:

```text
terraform/
```

The current configuration uses the Docker provider and defines resources including:

- Docker network.
- Docker volumes.
- Backend and frontend Docker images.
- Backend and frontend Docker containers.

Main files:

| File | Purpose |
|---|---|
| `main.tf` | Resource definitions |
| `variables.tf` | Configurable deployment variables |
| `outputs.tf` | Deployment outputs |
| `versions.tf` | Terraform and provider requirements |

Useful validation commands:

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
```

Terraform state files may contain sensitive infrastructure information. They must not be committed to the repository.

---

## Security Considerations

SecureScan processes potentially untrusted software archives. Upload handling, archive extraction, scanner execution and result handling must therefore be treated as security-sensitive operations.

Recommended practices:

- Run SecureScan in a controlled environment.
- Do not upload confidential source code unless the environment is approved for it.
- Never commit passwords, tokens, private keys or environment files.
- Keep scanner binaries and dependencies updated.
- Verify downloaded binaries using trusted checksums.
- Restrict network access to the API and monitoring interfaces.
- Preserve container isolation and least-privilege settings.
- Review findings manually before taking remediation decisions.
- Treat uploaded archives and scanner output as untrusted input.
- Protect persistent data, credentials and Terraform state.
- Use appropriate resource limits when processing untrusted projects.

Automated scanning cannot guarantee that an application is secure. Results may include false positives, and scanners may not detect every vulnerability.

---

## Evidence and Validation

Project validation and evidence are organized around the following areas:

- Frontend application.
- Security scanning.
- GitHub Actions CI/CD.
- Grafana dashboards.
- Prometheus metrics.
- Alertmanager configuration and alerts.
- Docker infrastructure.
- K6 load testing.

Evidence screenshots and scanner notes are stored under:

```text
docs/evidencias/prints/
```

The image security assessment report is available at:

```text
docs/RELATORIO-SEGURANCA-IMAGENS-2026-11-19.md
```

### Container image security assessment — 19 November 2026

The published GHCR images were scanned with Trivy 0.76.2 using the `vuln` scanner, HIGH and CRITICAL severities and the `--ignore-unfixed` option.

| Image | Base OS | HIGH | CRITICAL |
|---|---|---:|---:|
| Backend | Alpine 3.23.7 | 0 | 0 |
| Frontend | Alpine 3.24.4 | 0 | 0 |

The backend scan excluded `**/pip/_vendor/bom.cdx.json`, consistently with the CI adjustment.

These results mean that no HIGH or CRITICAL vulnerabilities were reported under the specified scan criteria. They do not establish the absence of all vulnerabilities, lower-severity issues or vulnerabilities without available fixes.

The original JSON reports are stored locally under `reports/`, a directory excluded from Git tracking.

---

## Known Limitations and Roadmap

The project is still evolving. The following areas are potential improvements and must not be interpreted as fully completed features:

- Complete frontend integration with live backend API responses.
- Replace remaining demonstration data with persisted backend data.
- Expand end-to-end tests across the full user workflow.
- Improve report generation and export capabilities.
- Further refine security posture scoring and prioritization.
- Continue improving scanner coverage and normalization.
- Review operational hardening before public production deployment.
- Expand deployment documentation and threat modelling.

Existing functionality should be distinguished from planned improvements when evaluating the project.

---

## Author

**Alisson Melo**

DevOps / DevSecOps Internship Project — 2026

Repository:

https://github.com/Melo2L/Devops-internship

---

# SecureScan
## Plataforma Automatizada de Avaliação de Segurança

**Alisson Melo — Projeto de Estágio DevOps, 2026**

SecureScan é uma plataforma DevSecOps concebida para avaliar a segurança de projetos de software através de análises automatizadas. Permite carregar arquivos ZIP, orquestrar ferramentas de análise de segurança, recolher vulnerabilidades e disponibilizar uma API para consultar e gerir os resultados.

O projeto combina uma interface web, um backend FastAPI, várias ferramentas de segurança, infraestrutura baseada em containers, CI/CD automatizado, Infraestrutura como Código e observabilidade.

> **Estado do projeto:** SecureScan é um projeto de estágio e portfólio em desenvolvimento. Os componentes de análise do backend, os testes automatizados, a infraestrutura Docker, o CI/CD e a monitorização estão implementados. Algumas áreas do frontend ainda utilizam dados demonstrativos/mock e não devem ser consideradas totalmente integradas com respostas reais do backend. O projeto não é apresentado como um produto comercial de segurança pronto para produção.

---

# Índice

1. [Arquitetura](#arquitetura)
2. [Tecnologias](#tecnologias)
3. [Análise de Segurança](#análise-de-segurança)
4. [Funcionalidades Implementadas](#funcionalidades-implementadas)
5. [Infraestrutura e Arquitetura](#infraestrutura-e-arquitetura)
6. [Instalação e Execução](#instalação-e-execução)
7. [Execução dos Testes](#execução-dos-testes)
8. [Referência da API](#referência-da-api)
9. [Pipeline CI/CD](#pipeline-cicd)
10. [Monitorização e Observabilidade](#monitorização-e-observabilidade)
11. [Infraestrutura como Código](#infraestrutura-como-código)
12. [Considerações de Segurança](#considerações-de-segurança)
13. [Evidências e Validação](#evidências-e-validação)
14. [Limitações e Roadmap](#limitações-e-roadmap)
15. [Autor](#autor)

---

## Arquitetura

O SecureScan utiliza uma arquitetura modular na qual o frontend comunica com um backend FastAPI responsável pelo carregamento de projetos, orquestração das análises, persistência e gestão dos resultados.

```text
                         Programador
                              |
                              v
                    React / TypeScript
                       Frontend :3000
                              |
                              v
                       Backend FastAPI
                           :8000
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
           Gitleaks         Semgrep         Trivy
       Deteção de segredos  Análise SAST  Vulnerabilidades
              |               |               |
              +---------------+---------------+
                              |
                              v
                           Checkov
                     Análise de segurança IaC
                              |
                              v
                    Normalização dos resultados
                              |
                              v
                     Persistência SQLite
                           /data

           Serviços de Observabilidade e Infraestrutura
        +-------------+  +-------------+  +-------------+
        | Prometheus  |  |   Grafana   |  | Alertmanager|
        |   :9090     |  |    :3001    |  |    :9093    |
        +-------------+  +-------------+  +-------------+
```

O diagrama representa a arquitetura de análise e os componentes de infraestrutura implementados. A execução efetiva de cada scanner depende do conteúdo do projeto carregado, do plano de análise e da existência dos ficheiros e ferramentas necessários. Por exemplo, o Checkov pode ser ignorado quando não existem ficheiros de Infrastructure as Code suportados.

Algumas vistas do frontend ainda utilizam dados demonstrativos. Portanto, o diagrama não significa que todos os elementos do dashboard estejam ligados a respostas reais da API.

### Serviços Docker Compose

| Serviço | Finalidade | URL local |
|---|---|---|
| backend | Aplicação FastAPI e orquestração das análises | http://localhost:8000 |
| frontend | Aplicação web | http://localhost:3000 |
| prometheus | Recolha de métricas e avaliação de alertas | http://localhost:9090 |
| grafana | Dashboards e visualização | http://localhost:3001 |
| alertmanager | Gestão e encaminhamento de alertas | http://localhost:9093 |

### Volumes persistentes

A configuração do Compose define armazenamento persistente para:

- `securescan_data` — dados da aplicação.
- `prometheus_data` — dados temporais do Prometheus.
- `grafana_data` — dados do Grafana.
- `trivy_cache` — cache persistente do Trivy, configurada como volume Docker externo denominado `securescan-trivy-cache`.

O volume externo da cache Trivy tem de existir antes de iniciar a infraestrutura Compose.

---

## Tecnologias

### Frontend

- React
- TypeScript
- Vite
- TanStack Start / Router
- Tailwind CSS
- pnpm
- Vitest
- ESLint

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- SQLite
- Pytest
- Ruff

### Ferramentas de segurança

- Gitleaks
- Semgrep
- Trivy
- Checkov

### DevOps e infraestrutura

- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)
- Terraform
- Prometheus
- Grafana
- Alertmanager
- K6

---

## Análise de Segurança

O SecureScan integra várias ferramentas para analisar diferentes aspetos da segurança dos projetos de software.

| Scanner | Finalidade | Área de análise |
|---|---|---|
| Gitleaks | Deteta segredos e credenciais expostos | Deteção de segredos |
| Semgrep | Identifica padrões de código potencialmente inseguros | Análise Estática de Segurança (SAST) |
| Trivy | Deteta vulnerabilidades conhecidas em dependências e componentes suportados | Análise de vulnerabilidades |
| Checkov | Avalia configurações de Infrastructure as Code | Segurança IaC |

### Fluxo de análise

1. Um arquivo de projeto é carregado através da API do backend.
2. São executadas a validação do carregamento e a extração segura do arquivo.
3. O analisador identifica características relevantes do projeto.
4. O planeador determina quais os scanners aplicáveis.
5. O executor realiza as ferramentas de segurança selecionadas.
6. Os resultados dos scanners são normalizados para uma estrutura comum.
7. A informação das análises e os resultados são persistidos para consulta e revisão.

A disponibilidade e os resultados dos scanners dependem do conteúdo do arquivo carregado. Um scanner pode ser ignorado quando os ficheiros ou configurações necessários não estão presentes.

Os resultados automatizados requerem revisão humana. Um resultado de scanner não constitui, por si só, prova de que uma vulnerabilidade é explorável.

---

## Funcionalidades Implementadas

O repositório inclui os seguintes componentes implementados:

- Frontend web em React e TypeScript.
- Backend FastAPI.
- API para carregamento de projetos.
- Componentes de validação de uploads e extração segura de arquivos.
- Análise de projetos e planeamento de análises.
- Orquestração da execução dos scanners.
- Integração e normalização de resultados do Gitleaks.
- Integração e normalização de resultados do Semgrep.
- Integração e normalização de resultados do Trivy.
- Integração e normalização de resultados do Checkov.
- Persistência de análises em SQLite.
- Endpoints para consulta de análises e gestão de resultados.
- Métricas HTTP através do Prometheus.
- Regras de alerta e testes do Prometheus.
- Provisionamento de dashboards Grafana.
- Configuração do Alertmanager.
- Infraestrutura Docker Compose.
- Configuração Terraform para recursos Docker.
- Pipeline CI/CD com GitHub Actions.
- Publicação de imagens no GHCR.
- Verificações automatizadas do backend e frontend.
- Scripts de testes de carga com K6.

Algumas páginas do frontend ainda utilizam dados simulados ou demonstrativos. A existência de um endpoint no backend não significa automaticamente que todos os componentes correspondentes do frontend o estejam a utilizar.

---

## Infraestrutura e Arquitetura

### Segurança do container Backend

O serviço backend no Compose inclui várias medidas de reforço de segurança:

- Sistema de ficheiros do container em modo somente de leitura.
- Sistema de ficheiros temporário dedicado.
- Utilizador de aplicação sem privilégios de root.
- Volume persistente para dados da aplicação.
- Volume persistente dedicado à cache Trivy.
- Verificação HTTP de saúde.
- Política de reinício automático.

### Segurança do container Frontend

O serviço frontend inclui:

- Sistema de ficheiros do container em modo somente de leitura.
- Sistema de ficheiros temporário para dados temporários de execução.
- Remoção de capabilities Linux.
- Opção de segurança `no-new-privileges`.
- Dependência da disponibilidade do backend.

Estas medidas reduzem a superfície de escrita e os privilégios dos containers. Não substituem o reforço de segurança do host, os controlos de rede ou uma avaliação completa da segurança dos containers.

---

## Instalação e Execução

### Pré-requisitos

- Git
- Docker Engine
- Docker Compose v2
- Acesso ao repositório do projeto
- Ficheiro `.env` configurado
- Volume Docker externo `securescan-trivy-cache`
- Ficheiro secreto SMTP do Alertmanager exigido pela configuração Compose

### 1. Clonar o repositório

```bash
git clone https://github.com/Melo2L/Devops-internship.git
cd Devops-internship
```

### 2. Configurar variáveis de ambiente e segredos

Configure o ficheiro local `.env` antes de iniciar a infraestrutura.

No mínimo, a configuração Compose exige:

- `GRAFANA_ADMIN_PASSWORD` — palavra-passe do administrador do Grafana.
- Quaisquer outras variáveis necessárias para a instalação local.

O serviço Alertmanager utiliza o ficheiro:

```text
secrets/smtp_password
```

Disponibilize o segredo necessário localmente. Não coloque `.env`, credenciais SMTP, tokens ou palavras-passe no Git.

### 3. Criar o volume externo da cache Trivy

```bash
docker volume create securescan-trivy-cache
```

Este comando cria o volume externo esperado pelo Compose. Se já existir, preserve-o.

### 4. Construir e iniciar os serviços

```bash
docker compose up --build -d
```

### 5. Verificar o estado dos serviços

```bash
docker compose ps
```

Consultar os logs:

```bash
docker compose logs --tail=100
```

Acompanhar os logs continuamente:

```bash
docker compose logs -f
```

### 6. Aceder à aplicação

| Componente | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Saúde do Backend | http://localhost:8000/health |
| Documentação interativa da API | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| Alertmanager | http://localhost:9093 |

As credenciais do Grafana dependem da configuração do ambiente local.

### 7. Parar os serviços

```bash
docker compose down
```

Este comando para e remove os containers e a rede do Compose sem eliminar os volumes nomeados.

> **Aviso sobre os dados:** evite `docker compose down -v`, a menos que pretenda eliminar intencionalmente os volumes geridos pelo Compose e os respetivos dados. Preserve o volume externo da cache Trivy, salvo se pretender removê-lo expressamente.

---

## Execução dos Testes

### Testes do Backend

O projeto utiliza Pytest para os testes do backend.

Criar e ativar um ambiente virtual Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalar dependências:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install pytest
```

Executar os testes com uma base de dados SQLite temporária isolada:

```bash
SECURESCAN_DATABASE_PATH=/tmp/securescan-tests.db \
python -m pytest backend/tests/ -q
```

O caminho temporário da base de dados impede que os testes utilizem a base de dados normal da aplicação.

### Lint do Backend

```bash
ruff check backend
```

### Testes e verificações de qualidade do Frontend

O frontend utiliza pnpm.

Instalar dependências:

```bash
pnpm install --frozen-lockfile
```

Executar os scripts disponíveis:

```bash
pnpm test
pnpm run lint
pnpm run build
```

Validação de TypeScript:

```bash
pnpm exec tsc --noEmit
```

Os resultados concretos dos testes dependem da revisão do código e do ambiente. Consulte a execução CI correspondente para conhecer o estado de validação de um commit específico.

### Testes de carga

Os scripts K6 estão disponíveis em:

```text
load-tests/
```

O repositório inclui scripts de carga e stress da API. Execute-os apenas contra um ambiente que controla.

Exemplo:

```bash
k6 run load-tests/api-load-test.js
```

Consulte `load-tests/README.md` e os scripts individuais para conhecer os parâmetros e endpoints específicos.

---

## Referência da API

O backend é implementado com FastAPI.

A documentação interativa está disponível em:

```text
http://localhost:8000/docs
```

### Endpoints de saúde e monitorização

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/health` | Verificação de saúde do backend |
| GET | `/metrics` | Endpoint de métricas Prometheus |

O endpoint de métricas está excluído do esquema OpenAPI gerado.

### Carregamento de projetos

| Método | Rota declarada | Descrição |
|---|---|---|
| POST | `/upload` | Carregar um arquivo de projeto para análise |

### Operações de análise

| Método | Rota declarada | Descrição |
|---|---|---|
| GET | `/scans` | Consultar análises |
| GET | `/scans/{scan_id}` | Consultar uma análise específica |
| GET | `/scans/{scan_id}/findings` | Consultar resultados associados a uma análise |

### Operações sobre resultados

| Método | Rota declarada | Descrição |
|---|---|---|
| GET | `/findings` | Consultar resultados |
| PATCH | `/findings/{finding_id}/status` | Atualizar o estado de um resultado |

> **Nota sobre o encaminhamento:** os caminhos acima refletem as declarações das rotas nos módulos do backend. Podem ser aplicados prefixos quando os routers são registados na aplicação FastAPI. Consulte `/docs` para verificar os caminhos completos e os esquemas de pedido efetivos da API em execução.

Exemplo de verificação de saúde:

```bash
curl -fsS http://localhost:8000/health
```

---

## Pipeline CI/CD

O SecureScan utiliza GitHub Actions para automatizar verificações de qualidade, testes, validação de segurança, construção e publicação de imagens.

O workflow está definido em:

```text
.github/workflows/ci.yml
```

### Jobs do pipeline

| Job | Responsabilidade |
|---|---|
| Frontend quality checks | Validação TypeScript, lint, testes e build |
| Backend tests and lint | Análise de segredos, Ruff e Pytest |
| Terraform quality gate | Formatação, inicialização e validação |
| Trivy security quality gate | Verificações de segurança de dependências e infraestrutura/configuração |
| Validate Prometheus alert rules | Sintaxe e testes das regras de alerta |
| Build and scan Docker images | Construção e análise de vulnerabilidades das imagens |
| Publish Docker images to GHCR | Publicação das imagens frontend e backend |
| Deploy SecureScan on Ubuntu | Atualização e verificação dos serviços no runner self-hosted configurado |

### Registry de containers

Imagens publicadas:

```text
ghcr.io/melo2l/devops-internship-backend
ghcr.io/melo2l/devops-internship-frontend
```

O workflow publica:

- `latest`
- Tags específicas de commit `sha-*`

As tags específicas de commit permitem identificar as imagens associadas a uma revisão do código.

### Deployment

O job de deployment é executado num runner Ubuntu self-hosted configurado com a etiqueta:

```text
securescan-deploy
```

O workflow descarrega as imagens publicadas, atualiza os serviços backend e frontend e verifica a sua disponibilidade.

Esta descrição corresponde ao workflow de deployment configurado. Não significa que o SecureScan esteja publicamente acessível ou instalado num VPS.

### Segurança do GitHub Actions

O workflow utiliza permissões e segredos fornecidos pelo GitHub para operações como autenticação no GHCR. Os ficheiros de ambiente e as credenciais de deployment são mantidos fora do repositório.

---

## Monitorização e Observabilidade

O SecureScan inclui uma infraestrutura de monitorização baseada em Prometheus, Grafana e Alertmanager.

### Prometheus

Configuração:

```text
monitoring/prometheus/prometheus.yml
monitoring/prometheus/rules/securescan-alerts.yml
monitoring/prometheus/tests/securescan-alerts-test.yml
```

O Prometheus recolhe métricas da aplicação e avalia as regras de alerta configuradas.

O backend disponibiliza métricas HTTP, incluindo:

- `securescan_http_requests_total`
- `securescan_http_request_duration_seconds`

### Grafana

O Grafana está configurado com:

- Fonte de dados Prometheus.
- Provisionamento de dashboards.
- Dashboard de visão geral do SecureScan.

Definição do dashboard:

```text
monitoring/grafana/dashboards/securescan-overview.json
```

### Alertmanager

Configuração:

```text
monitoring/alertmanager/alertmanager.yml
```

O Alertmanager gere o encaminhamento de alertas e a configuração das notificações. As credenciais SMTP são fornecidas através de um ficheiro secreto montado localmente.

### Validação

As regras de alerta do Prometheus são validadas e testadas pelo workflow GitHub Actions.

---

## Infraestrutura como Código

A configuração Terraform está localizada em:

```text
terraform/
```

A configuração atual utiliza o provider Docker e define recursos como:

- Rede Docker.
- Volumes Docker.
- Imagens Docker do backend e frontend.
- Containers Docker do backend e frontend.

Ficheiros principais:

| Ficheiro | Finalidade |
|---|---|
| `main.tf` | Definição de recursos |
| `variables.tf` | Variáveis de configuração |
| `outputs.tf` | Outputs da infraestrutura |
| `versions.tf` | Requisitos de versões do Terraform e provider |

Comandos úteis de validação:

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
```

Os ficheiros de estado do Terraform podem conter informações sensíveis da infraestrutura. Não devem ser enviados para o repositório.

---

## Considerações de Segurança

O SecureScan processa arquivos de software potencialmente não confiáveis. O tratamento de uploads, a extração de arquivos, a execução dos scanners e o processamento dos resultados devem, por isso, ser considerados operações sensíveis do ponto de vista da segurança.

Práticas recomendadas:

- Executar o SecureScan num ambiente controlado.
- Não carregar código-fonte confidencial sem aprovação do ambiente.
- Nunca colocar palavras-passe, tokens, chaves privadas ou ficheiros de ambiente no Git.
- Manter os scanners e as dependências atualizados.
- Verificar os binários descarregados através de checksums confiáveis.
- Restringir o acesso de rede à API e às interfaces de monitorização.
- Preservar o isolamento dos containers e os princípios de privilégio mínimo.
- Rever manualmente os resultados antes de decidir medidas de correção.
- Tratar arquivos carregados e resultados dos scanners como dados não confiáveis.
- Proteger dados persistentes, credenciais e estados Terraform.
- Utilizar limites de recursos adequados ao processar projetos não confiáveis.

A análise automatizada não garante que uma aplicação esteja segura. Os resultados podem conter falsos positivos e os scanners podem não detetar todas as vulnerabilidades.

---

## Evidências e Validação

A validação e as evidências do projeto estão organizadas em torno das seguintes áreas:

- Aplicação frontend.
- Análise de segurança.
- CI/CD GitHub Actions.
- Dashboards Grafana.
- Métricas Prometheus.
- Configuração e alertas Alertmanager.
- Infraestrutura Docker.
- Testes de carga K6.

As capturas de ecrã e notas dos scanners estão organizadas em:

```text
docs/evidencias/prints/
```

O relatório de segurança das imagens está disponível em:

```text
docs/RELATORIO-SEGURANCA-IMAGENS-2026-11-19.md
```

### Análise de segurança das imagens — 19 de novembro de 2026

As imagens publicadas no GHCR foram analisadas com Trivy 0.76.2, utilizando o scanner `vuln`, severidades HIGH e CRITICAL e a opção `--ignore-unfixed`.

| Imagem | Sistema base | HIGH | CRITICAL |
|---|---|---:|---:|
| Backend | Alpine 3.23.7 | 0 | 0 |
| Frontend | Alpine 3.24.4 | 0 | 0 |

A análise do backend excluiu `**/pip/_vendor/bom.cdx.json`, em conformidade com o ajuste aplicado no CI.

Estes resultados significam que não foram reportadas vulnerabilidades HIGH ou CRITICAL segundo os critérios especificados. Não demonstram ausência de todas as vulnerabilidades, de problemas de severidade inferior ou de vulnerabilidades sem correção disponível.

Os relatórios JSON originais estão guardados localmente em `reports/`, um diretório excluído do controlo de versões do Git.

---

## Limitações e Roadmap

O projeto continua em evolução. As seguintes áreas são melhorias potenciais e não devem ser interpretadas como funcionalidades totalmente concluídas:

- Completar a integração do frontend com respostas reais da API.
- Substituir os restantes dados demonstrativos por dados persistidos no backend.
- Expandir os testes end-to-end de todo o fluxo de utilização.
- Melhorar a geração e exportação de relatórios.
- Aperfeiçoar a classificação e priorização da postura de segurança.
- Continuar a melhorar a cobertura e normalização dos scanners.
- Rever o reforço operacional antes de uma instalação pública em produção.
- Expandir a documentação de deployment e o modelo de ameaças.

As funcionalidades existentes devem ser distinguidas das melhorias planeadas durante a avaliação do projeto.

---

## Autor

**Alisson Melo**

Projeto de Estágio DevOps / DevSecOps — 2026

Repositório:

https://github.com/Melo2L/Devops-internship

---

# SecureScan
## Plataforma Automatizada de Evaluación de Seguridad

**Alisson Melo — Proyecto de Prácticas DevOps, 2026**

SecureScan es una plataforma DevSecOps diseñada para evaluar la seguridad de proyectos de software mediante análisis automatizados. Permite cargar archivos ZIP, orquestar herramientas de análisis de seguridad, recopilar hallazgos y proporcionar una API para consultar y gestionar los resultados.

El proyecto combina una interfaz web, un backend FastAPI, varias herramientas de seguridad, infraestructura basada en contenedores, CI/CD automatizado, Infraestructura como Código y observabilidad.

> **Estado del proyecto:** SecureScan es un proyecto de prácticas y portafolio en desarrollo. Los componentes de análisis del backend, las pruebas automatizadas, la infraestructura Docker, CI/CD y la monitorización están implementados. Algunas áreas del frontend todavía utilizan datos de demostración/mock y no deben considerarse totalmente integradas con respuestas reales del backend. El proyecto no se presenta como un producto comercial de seguridad listo para producción.

---

# Índice

1. [Arquitectura](#arquitectura)
2. [Tecnologías](#tecnologías)
3. [Análisis de Seguridad](#análisis-de-seguridad)
4. [Funcionalidades Implementadas](#funcionalidades-implementadas)
5. [Infraestructura y Arquitectura](#infraestructura-y-arquitectura)
6. [Instalación y Ejecución](#instalación-y-ejecución)
7. [Ejecución de Pruebas](#ejecución-de-pruebas)
8. [Referencia de la API](#referencia-de-la-api)
9. [Pipeline CI/CD](#pipeline-cicd-1)
10. [Monitorización y Observabilidad](#monitorización-y-observabilidad)
11. [Infraestructura como Código](#infraestructura-como-código)
12. [Consideraciones de Seguridad](#consideraciones-de-seguridad)
13. [Evidencias y Validación](#evidencias-y-validación)
14. [Limitaciones y Roadmap](#limitaciones-y-roadmap)
15. [Autor](#autor-1)

---

## Arquitectura

SecureScan utiliza una arquitectura modular en la que el frontend se comunica con un backend FastAPI responsable de la carga de proyectos, la orquestación de análisis, la persistencia y la gestión de hallazgos.

```text
                         Desarrollador
                               |
                               v
                    React / TypeScript
                       Frontend :3000
                               |
                               v
                       Backend FastAPI
                           :8000
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
           Gitleaks          Semgrep           Trivy
       Detección secretos  Análisis SAST  Vulnerabilidades
              |                |                |
              +----------------+----------------+
                               |
                               v
                            Checkov
                      Análisis de seguridad IaC
                               |
                               v
                    Normalización de hallazgos
                               |
                               v
                      Persistencia SQLite
                           /data

             Servicios de Observabilidad e Infraestructura
        +-------------+  +-------------+  +-------------+
        | Prometheus  |  |   Grafana   |  | Alertmanager|
        |   :9090     |  |    :3001    |  |    :9093    |
        +-------------+  +-------------+  +-------------+
```

El diagrama representa la arquitectura de análisis y los componentes de infraestructura implementados. La ejecución efectiva de cada scanner depende del contenido del proyecto cargado, del plan de análisis y de la disponibilidad de los archivos y herramientas necesarios. Por ejemplo, Checkov puede omitirse cuando no existen archivos de Infrastructure as Code compatibles.

Algunas vistas del frontend todavía utilizan datos de demostración. Por tanto, el diagrama no significa que todos los elementos del dashboard estén conectados a respuestas reales de la API.

### Servicios Docker Compose

| Servicio | Finalidad | URL local |
|---|---|---|
| backend | Aplicación FastAPI y orquestación de análisis | http://localhost:8000 |
| frontend | Aplicación web | http://localhost:3000 |
| prometheus | Recopilación de métricas y evaluación de alertas | http://localhost:9090 |
| grafana | Dashboards y visualización | http://localhost:3001 |
| alertmanager | Gestión y enrutamiento de alertas | http://localhost:9093 |

### Volúmenes persistentes

La configuración de Compose define almacenamiento persistente para:

- `securescan_data` — datos de la aplicación.
- `prometheus_data` — datos temporales de Prometheus.
- `grafana_data` — datos de Grafana.
- `trivy_cache` — caché persistente de Trivy, configurada como volumen Docker externo denominado `securescan-trivy-cache`.

El volumen externo de la caché Trivy debe existir antes de iniciar la infraestructura Compose.

---

## Tecnologías

### Frontend

- React
- TypeScript
- Vite
- TanStack Start / Router
- Tailwind CSS
- pnpm
- Vitest
- ESLint

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- SQLite
- Pytest
- Ruff

### Herramientas de seguridad

- Gitleaks
- Semgrep
- Trivy
- Checkov

### DevOps e infraestructura

- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)
- Terraform
- Prometheus
- Grafana
- Alertmanager
- K6

---

## Análisis de Seguridad

SecureScan integra varias herramientas para analizar diferentes aspectos de la seguridad de los proyectos de software.

| Scanner | Finalidad | Área de análisis |
|---|---|---|
| Gitleaks | Detecta secretos y credenciales expuestos | Detección de secretos |
| Semgrep | Identifica patrones de código potencialmente inseguros | Análisis Estático de Seguridad (SAST) |
| Trivy | Detecta vulnerabilidades conocidas en dependencias y componentes compatibles | Análisis de vulnerabilidades |
| Checkov | Evalúa configuraciones de Infrastructure as Code | Seguridad IaC |

### Flujo de análisis

1. Se carga un archivo de proyecto mediante la API del backend.
2. Se realizan la validación de la carga y la extracción segura del archivo.
3. El analizador identifica las características relevantes del proyecto.
4. El planificador determina qué scanners son aplicables.
5. El ejecutor realiza las herramientas de seguridad seleccionadas.
6. Los resultados de los scanners se normalizan en una estructura común.
7. La información de los análisis y los hallazgos se persiste para su consulta y revisión.

La disponibilidad y los resultados de los scanners dependen del contenido del archivo cargado. Un scanner puede omitirse cuando los archivos o configuraciones necesarios no están presentes.

Los hallazgos automatizados requieren revisión humana. El resultado de un scanner no constituye, por sí solo, una prueba de que una vulnerabilidad sea explotable.

---

## Funcionalidades Implementadas

El repositorio incluye los siguientes componentes implementados:

- Frontend web en React y TypeScript.
- Backend FastAPI.
- API para carga de proyectos.
- Componentes de validación de cargas y extracción segura de archivos.
- Análisis de proyectos y planificación de análisis.
- Orquestación de ejecución de scanners.
- Integración y normalización de resultados de Gitleaks.
- Integración y normalización de resultados de Semgrep.
- Integración y normalización de resultados de Trivy.
- Integración y normalización de resultados de Checkov.
- Persistencia de análisis mediante SQLite.
- Endpoints para consultar análisis y gestionar hallazgos.
- Métricas HTTP mediante Prometheus.
- Reglas de alerta y pruebas de Prometheus.
- Aprovisionamiento de dashboards de Grafana.
- Configuración de Alertmanager.
- Infraestructura Docker Compose.
- Configuración Terraform para recursos Docker.
- Pipeline CI/CD con GitHub Actions.
- Publicación de imágenes en GHCR.
- Comprobaciones automatizadas del backend y frontend.
- Scripts de pruebas de carga con K6.

Algunas páginas del frontend todavía utilizan datos simulados o de demostración. La existencia de un endpoint en el backend no significa automáticamente que todos los componentes correspondientes del frontend lo estén utilizando.

---

## Infraestructura y Arquitectura

### Seguridad del contenedor Backend

El servicio backend en Compose incluye varias medidas de refuerzo de seguridad:

- Sistema de archivos del contenedor en modo de solo lectura.
- Sistema de archivos temporal dedicado.
- Usuario de aplicación sin privilegios de root.
- Volumen persistente para datos de la aplicación.
- Volumen persistente dedicado a la caché Trivy.
- Comprobación HTTP de salud.
- Política de reinicio automático.

### Seguridad del contenedor Frontend

El servicio frontend incluye:

- Sistema de archivos del contenedor en modo de solo lectura.
- Sistema de archivos temporal para datos temporales de ejecución.
- Eliminación de capacidades Linux.
- Opción de seguridad `no-new-privileges`.
- Dependencia de la disponibilidad del backend.

Estas medidas reducen la superficie de escritura y los privilegios de los contenedores. No sustituyen el refuerzo de seguridad del host, los controles de red ni una evaluación completa de la seguridad de los contenedores.

---

## Instalación y Ejecución

### Requisitos previos

- Git
- Docker Engine
- Docker Compose v2
- Acceso al repositorio del proyecto
- Archivo `.env` configurado
- Volumen Docker externo `securescan-trivy-cache`
- Archivo secreto SMTP de Alertmanager requerido por la configuración Compose

### 1. Clonar el repositorio

```bash
git clone https://github.com/Melo2L/Devops-internship.git
cd Devops-internship
```

### 2. Configurar variables de entorno y secretos

Configura el archivo local `.env` antes de iniciar la infraestructura.

Como mínimo, la configuración Compose requiere:

- `GRAFANA_ADMIN_PASSWORD` — contraseña del administrador de Grafana.
- Cualquier otra variable de entorno necesaria para la instalación local.

El servicio Alertmanager monta el archivo:

```text
secrets/smtp_password
```

Proporciona el secreto necesario localmente. No incluyas `.env`, credenciales SMTP, tokens ni contraseñas en Git.

### 3. Crear el volumen externo de caché Trivy

```bash
docker volume create securescan-trivy-cache
```

Este comando crea el volumen externo esperado por Compose. Si ya existe, consérvalo.

### 4. Construir e iniciar los servicios

```bash
docker compose up --build -d
```

### 5. Comprobar el estado de los servicios

```bash
docker compose ps
```

Consultar los registros:

```bash
docker compose logs --tail=100
```

Seguir los registros continuamente:

```bash
docker compose logs -f
```

### 6. Acceder a la aplicación

| Componente | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Salud del Backend | http://localhost:8000/health |
| Documentación interactiva de la API | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| Alertmanager | http://localhost:9093 |

Las credenciales de Grafana dependen de la configuración del entorno local.

### 7. Detener los servicios

```bash
docker compose down
```

Este comando detiene y elimina los contenedores y la red de Compose sin eliminar los volúmenes con nombre.

> **Advertencia sobre los datos:** evita `docker compose down -v` a menos que quieras eliminar intencionadamente los volúmenes gestionados por Compose y sus datos almacenados. Conserva el volumen externo de la caché Trivy, salvo que quieras eliminarlo expresamente.

---

## Ejecución de Pruebas

### Pruebas del Backend

El proyecto utiliza Pytest para las pruebas del backend.

Crear y activar un entorno virtual Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalar dependencias:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install pytest
```

Ejecutar las pruebas con una base de datos SQLite temporal aislada:

```bash
SECURESCAN_DATABASE_PATH=/tmp/securescan-tests.db \
python -m pytest backend/tests/ -q
```

La ruta temporal de la base de datos evita que las pruebas utilicen la base de datos normal de la aplicación.

### Lint del Backend

```bash
ruff check backend
```

### Pruebas y controles de calidad del Frontend

El frontend utiliza pnpm.

Instalar dependencias:

```bash
pnpm install --frozen-lockfile
```

Ejecutar los scripts disponibles:

```bash
pnpm test
pnpm run lint
pnpm run build
```

Validación de TypeScript:

```bash
pnpm exec tsc --noEmit
```

Los resultados concretos de las pruebas dependen de la revisión del código y del entorno. Consulta la ejecución CI correspondiente para conocer el estado de validación de un commit específico.

### Pruebas de carga

Los scripts K6 están disponibles en:

```text
load-tests/
```

El repositorio incluye scripts de carga y estrés de la API. Ejecútalos únicamente contra un entorno que controles.

Ejemplo:

```bash
k6 run load-tests/api-load-test.js
```

Consulta `load-tests/README.md` y los scripts individuales para conocer sus parámetros y endpoints específicos.

---

## Referencia de la API

El backend está implementado con FastAPI.

La documentación interactiva está disponible en:

```text
http://localhost:8000/docs
```

### Endpoints de salud y monitorización

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Comprobación de salud del backend |
| GET | `/metrics` | Endpoint de métricas Prometheus |

El endpoint de métricas está excluido del esquema OpenAPI generado.

### Carga de proyectos

| Método | Ruta declarada | Descripción |
|---|---|---|
| POST | `/upload` | Cargar un archivo de proyecto para su análisis |

### Operaciones de análisis

| Método | Ruta declarada | Descripción |
|---|---|---|
| GET | `/scans` | Consultar análisis |
| GET | `/scans/{scan_id}` | Consultar un análisis específico |
| GET | `/scans/{scan_id}/findings` | Consultar hallazgos asociados a un análisis |

### Operaciones de hallazgos

| Método | Ruta declarada | Descripción |
|---|---|---|
| GET | `/findings` | Consultar hallazgos |
| PATCH | `/findings/{finding_id}/status` | Actualizar el estado de un hallazgo |

> **Nota sobre el enrutamiento:** las rutas anteriores reflejan las declaraciones de los módulos router del backend. Pueden aplicarse prefijos al registrar los routers en la aplicación FastAPI. Consulta `/docs` para comprobar las rutas completas y los esquemas de solicitud efectivos de la API en ejecución.

Ejemplo de comprobación de salud:

```bash
curl -fsS http://localhost:8000/health
```

---

## Pipeline CI/CD

SecureScan utiliza GitHub Actions para automatizar controles de calidad, pruebas, validación de seguridad, construcción y publicación de imágenes.

El workflow está definido en:

```text
.github/workflows/ci.yml
```

### Jobs del pipeline

| Job | Responsabilidad |
|---|---|
| Frontend quality checks | Validación TypeScript, lint, pruebas y build |
| Backend tests and lint | Análisis de secretos, Ruff y Pytest |
| Terraform quality gate | Formato, inicialización y validación |
| Trivy security quality gate | Comprobaciones de seguridad de dependencias e infraestructura/configuración |
| Validate Prometheus alert rules | Sintaxis y pruebas de reglas de alerta |
| Build and scan Docker images | Construcción y análisis de vulnerabilidades de imágenes |
| Publish Docker images to GHCR | Publicación de imágenes frontend y backend |
| Deploy SecureScan on Ubuntu | Actualización y verificación de servicios en el runner self-hosted configurado |

### Registro de contenedores

Imágenes publicadas:

```text
ghcr.io/melo2l/devops-internship-backend
ghcr.io/melo2l/devops-internship-frontend
```

El workflow publica:

- `latest`
- Etiquetas específicas de commit `sha-*`

Las etiquetas específicas de commit permiten identificar las imágenes asociadas a una revisión concreta del código.

### Deployment

El job de deployment se ejecuta en un runner Ubuntu self-hosted configurado con la etiqueta:

```text
securescan-deploy
```

El workflow descarga las imágenes publicadas, actualiza los servicios backend y frontend y comprueba su disponibilidad.

Esta descripción corresponde al workflow de deployment configurado. No significa que SecureScan sea accesible públicamente o esté instalado en un VPS.

### Seguridad de GitHub Actions

El workflow utiliza permisos y secretos proporcionados por GitHub para operaciones como la autenticación en GHCR. Los archivos de entorno y las credenciales de deployment se mantienen fuera del repositorio.

---

## Monitorización y Observabilidad

SecureScan incluye una infraestructura de monitorización basada en Prometheus, Grafana y Alertmanager.

### Prometheus

Configuración:

```text
monitoring/prometheus/prometheus.yml
monitoring/prometheus/rules/securescan-alerts.yml
monitoring/prometheus/tests/securescan-alerts-test.yml
```

Prometheus recopila métricas de la aplicación y evalúa las reglas de alerta configuradas.

El backend expone métricas HTTP, entre ellas:

- `securescan_http_requests_total`
- `securescan_http_request_duration_seconds`

### Grafana

Grafana está aprovisionado con:

- Fuente de datos Prometheus.
- Aprovisionamiento de dashboards.
- Dashboard general de SecureScan.

Definición del dashboard:

```text
monitoring/grafana/dashboards/securescan-overview.json
```

### Alertmanager

Configuración:

```text
monitoring/alertmanager/alertmanager.yml
```

Alertmanager gestiona el enrutamiento de alertas y la configuración de notificaciones. Las credenciales SMTP se proporcionan mediante un archivo secreto montado localmente.

### Validación

Las reglas de alerta de Prometheus son validadas y probadas por el workflow de GitHub Actions.

---

## Infraestructura como Código

La configuración Terraform se encuentra en:

```text
terraform/
```

La configuración actual utiliza el provider Docker y define recursos como:

- Red Docker.
- Volúmenes Docker.
- Imágenes Docker del backend y frontend.
- Contenedores Docker del backend y frontend.

Archivos principales:

| Archivo | Finalidad |
|---|---|
| `main.tf` | Definición de recursos |
| `variables.tf` | Variables de configuración |
| `outputs.tf` | Outputs de infraestructura |
| `versions.tf` | Requisitos de versiones de Terraform y provider |

Comandos útiles de validación:

```bash
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
```

Los archivos de estado de Terraform pueden contener información sensible de la infraestructura. No deben subirse al repositorio.

---

## Consideraciones de Seguridad

SecureScan procesa archivos de software potencialmente no confiables. Por ello, la gestión de cargas, la extracción de archivos, la ejecución de scanners y el procesamiento de resultados deben tratarse como operaciones sensibles desde el punto de vista de la seguridad.

Prácticas recomendadas:

- Ejecutar SecureScan en un entorno controlado.
- No cargar código fuente confidencial sin aprobación del entorno.
- Nunca incluir contraseñas, tokens, claves privadas o archivos de entorno en Git.
- Mantener actualizados los scanners y las dependencias.
- Verificar los binarios descargados mediante checksums confiables.
- Restringir el acceso de red a la API y a las interfaces de monitorización.
- Mantener el aislamiento de contenedores y los principios de mínimo privilegio.
- Revisar manualmente los hallazgos antes de decidir medidas correctivas.
- Tratar los archivos cargados y los resultados de los scanners como datos no confiables.
- Proteger los datos persistentes, las credenciales y el estado de Terraform.
- Utilizar límites de recursos adecuados al procesar proyectos no confiables.

El análisis automatizado no puede garantizar que una aplicación sea segura. Los resultados pueden incluir falsos positivos y los scanners pueden no detectar todas las vulnerabilidades.

---

## Evidencias y Validación

La validación y las evidencias del proyecto están organizadas en torno a las siguientes áreas:

- Aplicación frontend.
- Análisis de seguridad.
- CI/CD de GitHub Actions.
- Dashboards de Grafana.
- Métricas de Prometheus.
- Configuración y alertas de Alertmanager.
- Infraestructura Docker.
- Pruebas de carga K6.

Las capturas de pantalla y notas de los scanners están organizadas en:

```text
docs/evidencias/prints/
```

El informe de seguridad de imágenes está disponible en:

```text
docs/RELATORIO-SEGURANCA-IMAGENS-2026-11-19.md
```

### Análisis de seguridad de imágenes — 19 de noviembre de 2026

Las imágenes publicadas en GHCR se analizaron con Trivy 0.76.2, utilizando el scanner `vuln`, las severidades HIGH y CRITICAL y la opción `--ignore-unfixed`.

| Imagen | Sistema base | HIGH | CRITICAL |
|---|---|---:|---:|
| Backend | Alpine 3.23.7 | 0 | 0 |
| Frontend | Alpine 3.24.4 | 0 | 0 |

El análisis del backend excluyó `**/pip/_vendor/bom.cdx.json`, de acuerdo con el ajuste aplicado en CI.

Estos resultados significan que no se reportaron vulnerabilidades HIGH o CRITICAL según los criterios especificados. No demuestran la ausencia de todas las vulnerabilidades, de problemas de severidad inferior ni de vulnerabilidades sin una corrección disponible.

Los informes JSON originales se guardan localmente en `reports/`, un directorio excluido del control de versiones de Git.

---

## Limitaciones y Roadmap

El proyecto continúa evolucionando. Las siguientes áreas son mejoras potenciales y no deben interpretarse como funcionalidades totalmente completadas:

- Completar la integración del frontend con respuestas reales de la API.
- Sustituir los datos de demostración restantes por datos persistidos en el backend.
- Ampliar las pruebas end-to-end del flujo completo de uso.
- Mejorar la generación y exportación de informes.
- Perfeccionar la clasificación y priorización de la postura de seguridad.
- Seguir mejorando la cobertura y normalización de los scanners.
- Revisar el refuerzo operativo antes de una instalación pública en producción.
- Ampliar la documentación de deployment y el modelo de amenazas.

Las funcionalidades existentes deben distinguirse de las mejoras planificadas durante la evaluación del proyecto.

---

## Autor

**Alisson Melo**

Proyecto de Prácticas DevOps / DevSecOps — 2026

Repositorio:

https://github.com/Melo2L/Devops-internship
