# Relatório de Segurança das Imagens Docker — SecureScan

**Data:** 19/11/2026  
**Ferramenta:** Trivy 0.76.2  
**Âmbito:** imagens Backend e Frontend publicadas no GitHub Container Registry (GHCR).

## 1. Objetivo

Verificar vulnerabilidades nas imagens Docker publicadas do SecureScan, com especial atenção às vulnerabilidades de severidade HIGH e CRITICAL.

## 2. Resultados

| Componente | Imagem | Sistema base | HIGH | CRITICAL |
|---|---|---|---:|---:|
| Backend | `ghcr.io/melo2l/devops-internship-backend:latest` | Alpine 3.23.7 | 0 | 0 |
| Frontend | `ghcr.io/melo2l/devops-internship-frontend:latest` | Alpine 3.24.4 | 0 | 0 |

## 3. Critérios de análise

- Scanner: `vuln`.
- Severidades selecionadas: `HIGH,CRITICAL`.
- Opção `--ignore-unfixed`.
- Formato de saída: JSON.

Na análise do Backend foi excluído o ficheiro `**/pip/_vendor/bom.cdx.json`, conforme o ajuste aplicado ao processo de CI.

## 4. Evidências técnicas

Relatórios JSON gerados localmente:

- `reports/trivy-backend-ghcr-current-20261119.json`
- `reports/trivy-frontend-ghcr-current-20261119.json`

A leitura dos dois relatórios confirmou zero vulnerabilidades HIGH ou CRITICAL segundo os critérios definidos.

## 5. Conclusão

As duas imagens publicadas no GHCR passaram a verificação realizada, sem vulnerabilidades HIGH ou CRITICAL reportadas pelos critérios utilizados.

Este resultado não representa ausência absoluta de vulnerabilidades. A análise está limitada às severidades selecionadas e à opção `--ignore-unfixed`. Não permite concluir que não existem vulnerabilidades de severidade inferior ou vulnerabilidades sem correção disponível.

## 6. Limitações e âmbito

- A análise incidiu sobre as imagens identificadas pela tag `latest` no momento da execução.
- Os resultados não substituem uma auditoria completa da aplicação, uma análise dinâmica ou uma revisão manual do código.
- Os relatórios JSON originais permanecem na pasta `reports/`, excluída do controlo de versões pelo `.gitignore`.
