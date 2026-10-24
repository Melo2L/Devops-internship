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


def get_metrics() -> tuple[bytes, str]:
    """Return application metrics in Prometheus exposition format."""
    return generate_latest(), CONTENT_TYPE_LATEST
