
# Etapa 1: compilar Gitleaks oficial com dependências atualizadas.
FROM golang:1.27-alpine AS gitleaks-build

RUN apk add --no-cache git

WORKDIR /src/gitleaks
RUN git init \
    && git remote add origin https://github.com/gitleaks/gitleaks.git \
    && git fetch --depth 1 origin 5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c \
    && git checkout FETCH_HEAD

COPY gitleaks/go.mod gitleaks/go.sum ./
COPY gitleaks/vendor/ ./vendor/

RUN GOPROXY=off CGO_ENABLED=0 go build -mod=vendor -trimpath -ldflags="-s -w" -o /out/gitleaks .

# Etapa 2: imagem do backend SecureScan.
FROM semgrep/semgrep:1.184.0

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SECURESCAN_DATABASE_PATH=/data/securescan.db \
    GITLEAKS_PATH=/usr/local/bin/gitleaks \
    SEMGREP_PATH=/usr/bin/semgrep \
    PATH="/opt/backend-venv/bin:${PATH}"

ARG TRIVY_VERSION=0.76.2
ARG CHECKOV_VERSION=3.4.5
ARG TARGETARCH

# Atualizar Alpine e instalar ferramentas do sistema.
RUN apk update \
    && apk upgrade \
    && apk add --no-cache ca-certificates curl coreutils tar unzip \
    && rm -rf /var/cache/apk/*

# Instalar Gitleaks compilado na primeira etapa.
COPY --from=gitleaks-build /out/gitleaks /usr/local/bin/gitleaks

# Trivy: binário local com SHA256 previamente validado.
COPY tools/trivy /usr/local/bin/trivy

RUN echo "d73380ef5e4128b14fe172849e3692addbc7d994b84a7b840b8c400985db0f6a  /usr/local/bin/trivy" | sha256sum -c - \
    && chmod 0755 /usr/local/bin/trivy \
    && trivy --version

# Backend e Checkov num ambiente Python isolado do Semgrep.
COPY backend/requirements.txt ./requirements.txt

RUN python -m venv /opt/backend-venv \
    && /opt/backend-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/backend-venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /opt/backend-venv/bin/pip install --no-cache-dir "checkov==${CHECKOV_VERSION}" \
    && /opt/backend-venv/bin/pip check \
    && /opt/backend-venv/bin/checkov --version \
    && /opt/backend-venv/bin/uvicorn --version \
    && semgrep --version

COPY backend ./backend

# Utilizador sem privilégios e diretório persistente.
RUN adduser -D -u 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
