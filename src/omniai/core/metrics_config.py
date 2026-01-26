from prometheus_client import Counter, Histogram, Gauge

# Request counters
REQUEST_COUNT = Counter(
    "omniai_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

# Latency histogram
REQUEST_LATENCY = Histogram(
    "omniai_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# Active tenants/users (optional)
ACTIVE_TENANTS = Gauge("omniai_active_tenants", "Number of active tenants")