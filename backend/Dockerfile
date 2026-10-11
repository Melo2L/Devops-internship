
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
ARG TARGETARCH

# Install system dependencies and Gitleaks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        coreutils \
        tar \
    && set -eux; \
       case "${TARGETARCH:-amd64}" in \
         amd64) GITLEAKS_ARCH="x64" ;; \
         arm64) GITLEAKS_ARCH="arm64" ;; \
         *) echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
       esac; \
       DOWNLOAD_URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}"; \
       CHECKSUMS_FILE="gitleaks_${GITLEAKS_VERSION}_checksums.txt"; \
       ARCHIVE_FILE="gitleaks_${GITLEAKS_VERSION}_linux_${GITLEAKS_ARCH}.tar.gz"; \
       curl -fsSLo "/tmp/${CHECKSUMS_FILE}" "${DOWNLOAD_URL}/${CHECKSUMS_FILE}"; \
       curl -fsSLo "/tmp/${ARCHIVE_FILE}" "${DOWNLOAD_URL}/${ARCHIVE_FILE}"; \
       cd /tmp; \
       grep " ${ARCHIVE_FILE}$" "${CHECKSUMS_FILE}" > /tmp/gitleaks-checksum.txt; \
       sha256sum -c /tmp/gitleaks-checksum.txt; \
       tar -xzf "${ARCHIVE_FILE}" gitleaks; \
       install -m 0755 /tmp/gitleaks /usr/local/bin/gitleaks; \
       gitleaks version; \
       rm -f "/tmp/${CHECKSUMS_FILE}" "/tmp/${ARCHIVE_FILE}" \
             /tmp/gitleaks /tmp/gitleaks-checksum.txt \
    && rm -rf /var/lib/apt/lists/*

# Install Semgrep in an isolated Python environment.
RUN python -m venv /opt/semgrep-venv \
    && /opt/semgrep-venv/bin/pip install \
        --no-cache-dir \
        "semgrep==${SEMGREP_VERSION}" \
    && /opt/semgrep-venv/bin/semgrep --version

# Install backend dependencies independently of Semgrep.
COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY backend ./backend

# Run the application as a non-root user.
RUN useradd \
    --create-home \
    --shell /usr/sbin/nologin \
    appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]