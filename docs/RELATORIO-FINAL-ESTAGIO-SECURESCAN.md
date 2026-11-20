# Relatório Final de Estágio — SecureScan

**Instituição:** Tss Ciberseguridad 
**Área:** DevOps  
**Projeto:** SecureScan — Automated Security Assessment Platform  
**Autor:** Alisson Melo  
**Data de referência técnica:** 19 de novembro de 2026  
**Prazo de entrega indicado no enunciado:** 29 de novembro de 2026

---

## 1. Resumo executivo

O SecureScan é uma aplicação web concebida para analisar projetos de software submetidos em formato ZIP, identificar potenciais problemas de segurança e apresentar os resultados para revisão e correção.

O projeto combina uma aplicação web com uma API, ferramentas automatizadas de análise de segurança, containerização, integração e entrega contínuas, infraestrutura como código, monitorização e testes de carga.

A solução utiliza Docker e Docker Compose para executar os serviços. O pipeline de CI/CD é implementado com GitHub Actions, incluindo validações, testes, análise de segurança, construção de imagens e publicação no GitHub Container Registry (GHCR).

A monitorização é suportada por Prometheus, Grafana e Alertmanager. O Terraform é utilizado para definir recursos de infraestrutura Docker.

O SecureScan ultrapassa o âmbito de uma aplicação web simples ao integrar ferramentas de análise de código, segredos, dependências, containers e infraestrutura como código.

## 2. Objetivos

Os objetivos principais foram:

- Containerizar uma aplicação web utilizando Docker.
- Criar um repositório Git com pipeline CI/CD através de GitHub Actions.
- Automatizar build, testes e publicação de imagens.
- Gerir credenciais e permissões de forma controlada.
- Implementar monitorização de disponibilidade e métricas.
- Disponibilizar um dashboard de estado.
- Provisionar recursos através de Terraform.
- Orquestrar os serviços com Docker Compose.
- Executar testes de carga e observar o comportamento da aplicação.
- Integrar funcionalidades adicionais de análise de segurança.

## 3. Tecnologias utilizadas

| Área | Tecnologias |
|---|---|
| Frontend | React, TypeScript, Vite, TanStack |
| Backend | Python, FastAPI, Uvicorn |
| Testes | Pytest, Vitest, K6 |
| Qualidade | Ruff, ESLint, TypeScript |
| Análise de segurança | Gitleaks, Semgrep, Trivy, Checkov |
| Containerização | Docker |
| Orquestração | Docker Compose |
| CI/CD | GitHub Actions |
| Registry | GitHub Container Registry |
| Infraestrutura como código | Terraform |
| Monitorização | Prometheus |
| Dashboards | Grafana |
| Alertas | Alertmanager |
| Persistência | SQLite e volumes Docker |

## 4. Arquitetura funcional

A solução está organizada em componentes:

1. **Frontend:** interface web para interação com a aplicação.
2. **Backend:** API FastAPI responsável pelo processamento dos pedidos, gestão dos projetos e execução das análises.
3. **Gitleaks:** deteção de possíveis segredos e credenciais expostos.
4. **Semgrep:** análise estática de código.
5. **Trivy:** análise de dependências, imagens e configurações suportadas.
6. **Checkov:** análise de infraestrutura como código.
7. **Prometheus:** recolha de métricas.
8. **Grafana:** apresentação visual das métricas.
9. **Alertmanager:** gestão e encaminhamento de alertas.
10. **Docker Compose:** orquestração dos serviços.

O fluxo de análise começa com o envio de um projeto ZIP. O backend processa o ficheiro, realiza a extração segura, identifica características do projeto e prepara um plano de análise. Os scanners aplicáveis são executados e os resultados são normalizados e disponibilizados através da API.

Nem todos os scanners são aplicáveis a todos os projetos. Por exemplo, o Checkov pode ser ignorado quando não existe infraestrutura como código reconhecida.

## 5. Requisitos obrigatórios do enunciado

### 5.1 Containerizar uma aplicação web simples com Docker

**Estado: Implementado.**

O SecureScan utiliza imagens Docker próprias para frontend e backend. A aplicação é executada através de Docker Compose.

Foram também aplicadas medidas adicionais de segurança nos serviços, incluindo execução sem privilégios elevados, sistemas de ficheiros read-only quando aplicável, utilização de tmpfs e volumes persistentes.

**Evidências:**
- `docs/evidencias/prints/07-infraestrutura/`
- `docs/evidencias/prints/01-frontend/`
- `compose.yaml`
- `Dockerfile`
- `backend/Dockerfile`

### 5.2 Repositório Git com pipeline CI/CD através de GitHub Actions

**Estado: Implementado.**

O workflow `.github/workflows/ci.yml` automatiza diferentes fases de validação e entrega.

Entre os trabalhos configurados encontram-se:

- Validação de qualidade do frontend.
- Verificação de TypeScript.
- Lint e testes do frontend.
- Testes e análise estática do backend.
- Validação de configuração Terraform.
- Análise de segurança com Trivy.
- Validação das regras Prometheus.
- Construção e análise das imagens Docker.
- Publicação das imagens no GHCR.
- Deployment condicionado à execução num runner self-hosted com as etiquetas configuradas.

A publicação das imagens é condicionada a um push na branch `main`.

**Evidências:**
- `docs/evidencias/prints/03-cicd/`
- `.github/workflows/ci.yml`

### 5.3 Build automático, testes automatizados e deployment automático da imagem

**Estado: Implementado, com evidências de execução.**

O pipeline inclui validações automatizadas, construção das imagens e publicação no GHCR.

Foi também executado um pipeline completo com publicação e deployment no ambiente Ubuntu configurado para o projeto.

O deployment não corresponde a alojamento público num VPS. O ambiente de demonstração é a máquina Ubuntu utilizada pelo projeto, através do runner self-hosted configurado.

**Evidências:**
- Capturas de CI/CD.
- Workflow GitHub Actions.
- Imagens publicadas no GHCR.

### 5.4 Gestão de segredos e credenciais via GitHub Secrets

**Estado: Parcial — abordagem de autenticação documentada.**

A publicação das imagens utiliza o `GITHUB_TOKEN` disponibilizado automaticamente pelo GitHub Actions.

O job `docker-publish` declara:

- `contents: read`
- `packages: write`

A permissão de escrita em pacotes é atribuída ao job responsável pela publicação.

Na verificação realizada em 19/11/2026, a página de configuração do repositório indicava que não existiam Secrets adicionais configurados ao nível do repositório ou dos ambientes.

Assim, não se afirma que foram criados GitHub Secrets personalizados. O projeto utiliza o mecanismo automático de autenticação do GitHub Actions para a publicação no GHCR.

A aplicação e os serviços locais possuem também configurações sensíveis que não devem ser incluídas no controlo de versões.

**Evidência:** captura da página GitHub Actions Secrets e configuração do job `docker-publish`.

### 5.5 Sistema de monitorização e alertas

**Estado: Implementado.**

O projeto utiliza Prometheus para recolha de métricas, Grafana para visualização e Alertmanager para gestão de alertas.

A monitorização contempla métricas HTTP, incluindo:

- `securescan_http_requests_total`
- `securescan_http_request_duration_seconds`

Existem regras de alerta e testes das regras Prometheus.

O Alertmanager encontra-se configurado para encaminhamento de alertas por email, com configuração de credenciais através de ficheiro externo.

**Evidências:**
- `docs/evidencias/prints/04-grafana/`
- `docs/evidencias/prints/05-prometheus/`
- `docs/evidencias/prints/06-alertas-email/`
- `monitoring/prometheus/`
- `monitoring/grafana/`
- `monitoring/alertmanager/`

## 6. Itens indicados para nota máxima

### 6.1 Infraestrutura como Código com Terraform

**Estado: Implementado.**

O projeto inclui configuração Terraform para definir recursos Docker, incluindo rede, volumes, imagens e containers.

Principais ficheiros:

- `terraform/main.tf`
- `terraform/variables.tf`
- `terraform/outputs.tf`
- `terraform/versions.tf`

O objetivo é permitir a definição declarativa dos recursos utilizados pela aplicação.

A infraestrutura é demonstrativa e local. Não se afirma que foi provisionada numa cloud pública.

### 6.2 Orquestração com Docker Compose

**Estado: Implementado.**

O Docker Compose coordena os serviços da solução, incluindo frontend, backend, Prometheus, Grafana e Alertmanager.

O ficheiro principal é `compose.yaml`.

### 6.3 Testes simples de escalabilidade

**Estado: Implementado e executado com K6.**

Foram realizados testes de carga com diferentes níveis de concorrência.

**Teste 1 — 10 utilizadores virtuais durante 30 segundos**

- 600 pedidos HTTP.
- 19,746 pedidos por segundo.
- 1.200 verificações concluídas.
- 0% de falhas.
- Tempo médio: 5,15 ms.
- Percentil 95: 21,12 ms.
- Máximo: 44 ms.

**Teste 2 — até 100 utilizadores virtuais durante 2 minutos e 30 segundos**

- 11.052 pedidos HTTP.
- 73,40875 pedidos por segundo.
- 5.526 iterações.
- 22.104 verificações concluídas.
- 0% de falhas HTTP.
- Tempo médio: 3,49 ms.
- Percentil 95: 5,09 ms.
- Máximo: 35,5 ms.

Estes resultados representam as condições específicas dos testes executados e não constituem uma garantia de desempenho em qualquer ambiente ou carga.

**Evidências:**
- `docs/evidencias/prints/08-testes/K6-001.png`
- `docs/evidencias/prints/08-testes/K6-002.png`
- `docs/evidencias/prints/08-testes/K6-003.png`
- `docs/evidencias/prints/08-testes/K6-004.png`

## 7. Testes automatizados

Foram executados testes automatizados no backend e frontend.

O registo de execução do backend documenta 236 testes aprovados e 100% de cobertura no contexto dessa execução.

O frontend inclui testes com Vitest e verificações de TypeScript, lint e build através do pipeline.

Os testes automatizados verificam o comportamento dos componentes e serviços, mas não substituem testes de aceitação completos de todas as funcionalidades da interface.

## 8. Funcionalidades adicionais de segurança

Para além do núcleo DevOps, o SecureScan integra capacidades de DevSecOps.

### 8.1 Análise de projetos ZIP

O backend recebe projetos ZIP e utiliza mecanismos de validação e extração segura.

### 8.2 Análise estática

O Semgrep identifica padrões potencialmente inseguros no código-fonte.

### 8.3 Deteção de segredos

O Gitleaks procura possíveis credenciais e segredos expostos.

### 8.4 Análise de dependências e imagens

O Trivy analisa dependências e imagens Docker, conforme o tipo de análise configurado.

### 8.5 Análise de infraestrutura como código

O Checkov analisa ficheiros de infraestrutura suportados.

### 8.6 Normalização dos resultados

Os resultados dos scanners são normalizados para apresentação consistente na aplicação.

### 8.7 Gestão de findings

A API disponibiliza operações para consultar resultados e atualizar o estado de findings.

Estas funcionalidades adicionais tornam o projeto mais abrangente do que uma aplicação web simples e aproximam-no de um fluxo de trabalho DevSecOps.

## 9. Evidências de integração dos scanners

Foram executados testes com projetos de demonstração preparados para produzir resultados conhecidos.

### 9.1 Projeto de teste simples

Ficheiro: `test-vulnerable-project.zip`

Resultado:

- Estado da análise: completed.
- Gitleaks: concluído, sem findings.
- Semgrep: 1 finding Medium.
- Trivy: concluído, sem findings.
- Checkov: ignorado por ausência de infraestrutura aplicável.
- O finding Semgrep foi posteriormente marcado como `resolved`.

### 9.2 Projeto de integração final

Ficheiro: `securescan-final-integration.zip`

Resultado:

- Estado da análise: completed.
- 4 ficheiros processados.
- Gitleaks: concluído, sem findings.
- Semgrep: 2 findings — Medium e High.
- Trivy: 14 findings.
- Checkov: 10 findings classificados como Informational pelo SecureScan.
- Total: 26 findings.

Os resultados incluem exemplos de problemas no código-fonte, dependências, configurações Docker e regras de infraestrutura AWS presentes no projeto de teste.

**Nota importante:** estes 26 findings pertencem ao projeto de teste enviado para análise. Não representam 26 vulnerabilidades confirmadas no próprio SecureScan.

## 10. Análise de segurança das imagens Docker publicadas

Em 19/11/2026 foi realizada uma análise das imagens publicadas no GHCR com Trivy 0.76.2.

| Imagem | Sistema base | HIGH | CRITICAL |
|---|---|---:|---:|
| Backend | Alpine 3.23.7 | 0 | 0 |
| Frontend | Alpine 3.24.4 | 0 | 0 |

Critérios utilizados:

- Scanner: `vuln`.
- Severidades: `HIGH,CRITICAL`.
- Opção `--ignore-unfixed`.
- Relatórios em formato JSON.

Na análise do backend foi excluído `**/pip/_vendor/bom.cdx.json`, conforme o ajuste aplicado ao processo de CI.

Os resultados não significam ausência absoluta de vulnerabilidades. A análise está limitada às severidades selecionadas e às opções indicadas.

Relatório técnico complementar:

`docs/RELATORIO-SEGURANCA-IMAGENS-2026-11-19.md`

Os relatórios JSON originais permanecem localmente em `reports/`, pasta excluída do controlo de versões.

## 11. API e operação

A API FastAPI disponibiliza funcionalidades para:

- Receber projetos.
- Consultar análises.
- Consultar findings.
- Atualizar o estado de findings.
- Verificar a saúde do serviço.
- Expor métricas Prometheus.

Entre as rotas implementadas encontram-se:

- `POST /upload`
- `GET /scans`
- `GET /scans/{scan_id}`
- `GET /scans/{scan_id}/findings`
- `GET /findings`
- `PATCH /findings/{finding_id}/status`
- `GET /health`
- `GET /metrics`

Os prefixos efetivos dependem da configuração dos routers. A documentação OpenAPI disponibilizada pela aplicação deve ser utilizada para consultar os caminhos completos.

## 12. Evidências documentais

O diretório `docs/evidencias/prints/` contém 28 ficheiros de evidência, organizados por categoria:

| Categoria | Conteúdo |
|---|---|
| 01-frontend | Interface da aplicação |
| 02-security | Evidência de segurança |
| 03-cicd | Pipeline e publicação |
| 04-grafana | Dashboards |
| 05-prometheus | Métricas e regras |
| 06-alertas-email | Alertas por email |
| 07-infraestrutura | Docker e infraestrutura |
| 08-testes | Testes K6 e registo de scanners |

O README do repositório complementa estas evidências com instruções de utilização, arquitetura, configuração e execução.

## 13. Limitações conhecidas

O estado do projeto deve ser apresentado com transparência:

- Algumas áreas do frontend ainda utilizam dados demonstrativos e não estão totalmente integradas com a API real.
- Os resultados dos scanners dependem do conteúdo do projeto submetido e da aplicabilidade de cada ferramenta.
- A classificação de findings informacionais não deve ser interpretada como severidade de segurança confirmada pelo scanner de origem.
- Os resultados dos testes de carga são específicos do ambiente e das condições utilizadas.
- O deployment demonstrativo é realizado no ambiente Ubuntu local, não num VPS público.
- Não foram configurados GitHub Secrets personalizados no repositório; a publicação GHCR utiliza o `GITHUB_TOKEN` automático.
- Os resultados de segurança das imagens não substituem uma auditoria completa da aplicação.

## 14. Conclusão

O SecureScan implementa os principais elementos do projeto DevOps proposto no enunciado: containerização, automação CI/CD, testes, deployment, monitorização, alertas, infraestrutura como código, orquestração e testes de carga.

O projeto acrescenta ainda funcionalidades DevSecOps, integrando ferramentas especializadas para análise de código, segredos, dependências, containers e infraestrutura como código.

A combinação destas tecnologias demonstra a aplicação prática de conceitos de DevOps e DevSecOps num projeto integrado, com evidências técnicas de execução e documentação de limitações.

O resultado é uma plataforma demonstrativa que permite analisar projetos de software e acompanhar os resultados de segurança num fluxo automatizado.

---

**Autor:** Alisson Melo  
**Projeto:** SecureScan — DevOps Internship Project  
**Instituição:** Tss Ciberseguridad
