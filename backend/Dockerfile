FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SECURESCAN_DATABASE_PATH=/data/securescan.db \
    GITLEAKS_PATH=/usr/local/bin/gitleaks \
    SEMGREP_PATH=/opt/semgrep-venv/bin/semgrep

ARG GITLEAKS_VERSION=8.30.1
ARG SEMGREP_VERSION=1.180.0
ARG TRIVY_VERSION=0.74.0
ARG CHECKOV_VERSION=3.3.26
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl coreutils tar unzip \
    && rm -rf /var/lib/apt/lists/*

# Gitleaks: verify the official release checksum.
RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      amd64) GITLEAKS_ARCH="x64" ;; \
      arm64) GITLEAKS_ARCH="arm64" ;; \
      *) echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    BASE="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}"; \
    CHECKSUMS="gitleaks_${GITLEAKS_VERSION}_checksums.txt"; \
    ARCHIVE="gitleaks_${GITLEAKS_VERSION}_linux_${GITLEAKS_ARCH}.tar.gz"; \
    curl -fsSLo "/tmp/${CHECKSUMS}" "${BASE}/${CHECKSUMS}"; \
    curl -fsSLo "/tmp/${ARCHIVE}" "${BASE}/${ARCHIVE}"; \
    cd /tmp; \
    grep " ${ARCHIVE}$" "${CHECKSUMS}" > checksums.txt; \
    sha256sum -c checksums.txt; \
    tar -xzf "${ARCHIVE}" gitleaks; \
    install -m 0755 gitleaks /usr/local/bin/gitleaks; \
    rm -f "${CHECKSUMS}" "${ARCHIVE}" checksums.txt gitleaks

# Semgrep stays isolated from Checkov's Python dependencies.
RUN python -m venv /opt/semgrep-venv \
    && /opt/semgrep-venv/bin/pip install --no-cache-dir "semgrep==${SEMGREP_VERSION}" \
    && /opt/semgrep-venv/bin/semgrep --version

# Trivy: verify the official release checksum.
RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      amd64) TRIVY_ARCH="64bit" ;; \
      arm64) TRIVY_ARCH="ARM64" ;; \
      *) echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    BASE="https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}"; \
    CHECKSUMS="trivy_${TRIVY_VERSION}_checksums.txt"; \
    ARCHIVE="trivy_${TRIVY_VERSION}_Linux-${TRIVY_ARCH}.tar.gz"; \
    curl -fsSLo "/tmp/${CHECKSUMS}" "${BASE}/${CHECKSUMS}"; \
    curl -fsSLo "/tmp/${ARCHIVE}" "${BASE}/${ARCHIVE}"; \
    cd /tmp; \
    grep " ${ARCHIVE}$" "${CHECKSUMS}" > trivy-checksums.txt; \
    sha256sum -c trivy-checksums.txt; \
    tar -xzf "${ARCHIVE}" trivy; \
    install -m 0755 trivy /usr/local/bin/trivy; \
    rm -f "${CHECKSUMS}" "${ARCHIVE}" trivy-checksums.txt trivy; \
    trivy --version

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "checkov==${CHECKOV_VERSION}" \
    && checkov --version

COPY backend ./backend

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
