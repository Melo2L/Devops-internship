from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "securescan_http_requests_total",
    "Total number of HTTP requests processed by SecureScan.",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "securescan_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
)

SCANS_TOTAL = Counter(
    "securescan_scans_total",
    "Total number of project scans by final status.",
    ["status"],
)

SCANNER_EXECUTIONS_TOTAL = Counter(
    "securescan_scanner_executions_total",
    "Total number of scanner executions by scanner and result.",
    ["scanner", "status"],
)

SCANNER_DURATION_SECONDS = Histogram(
    "securescan_scanner_duration_seconds",
    "Scanner execution duration in seconds.",
    ["scanner"],
)

FINDINGS_TOTAL = Counter(
    "securescan_findings_total",
    "Total number of security findings by severity.",
    ["severity"],
)


def get_metrics() -> tuple[bytes, str]:
    """Return application metrics in Prometheus exposition format."""
    return generate_latest(), CONTENT_TYPE_LATEST
