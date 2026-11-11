
# SecureScan - Load Testing

## Objective

Evaluate backend availability, API response time and behavior under normal and progressively increasing HTTP load using Grafana k6.

## Test Environment

- Tool: Grafana k6
- Execution: Docker
- Backend: Terraform-provisioned Docker container
- Backend URL: `http://host.docker.internal:8100`

## 1. Health Test

**File:** `health-test.js`

**Endpoint:** `GET /health`

### Configuration

- 10 virtual users
- 30 seconds
- HTTP failure rate below 1%
- P95 response time below 500 ms

### Execution

```bash
docker run --rm --add-host=host.docker.internal:host-gateway -v "$PWD/load-tests:/scripts:ro" grafana/k6 run /scripts/health-test.js
```

### Results

- HTTP requests: 300
- Failed requests: 0 (0%)
- Checks passed: 100%
- Average response time: 2.09 ms
- P95 response time: 3.46 ms
- Maximum response time: 4.77 ms

## 2. Progressive Health Stress Test

**File:** `stress-test.js`

**Endpoint:** `GET /health`

### Stages

- 10 virtual users for 30 seconds
- 25 virtual users for 30 seconds
- 50 virtual users for 30 seconds
- 100 virtual users for 30 seconds
- Ramp down to 0 users over 30 seconds

### Execution

```bash
docker run --rm --add-host=host.docker.internal:host-gateway -v "$PWD/load-tests:/scripts:ro" grafana/k6 run /scripts/stress-test.js
```

### Thresholds

- HTTP failure rate below 1%
- P95 response time below 500 ms

### Results

- Maximum virtual users: 100
- HTTP requests: 5,561
- Failed requests: 0 (0%)
- Checks passed: 100%
- Average response time: 1.11 ms
- P95 response time: 2.06 ms
- Maximum response time: 8.23 ms

## 3. API Load Test

**File:** `api-load-test.js`

**Endpoints:**
- `GET /api/scans`
- `GET /api/findings`

### Configuration

- 10 virtual users
- 30 seconds
- HTTP failure rate below 1%
- P95 response time below 500 ms
- Validates HTTP 200 responses and array response bodies

### Execution

```bash
docker run --rm --add-host=host.docker.internal:host-gateway -v "$PWD/load-tests:/scripts:ro" grafana/k6 run /scripts/api-load-test.js
```

### Results

- Virtual users: 10
- Duration: 30 seconds
- Iterations: 300
- HTTP requests: 600
- Request rate: 19.87 requests/second
- Failed requests: 0 (0%)
- Checks passed: 100% (1,200 checks)
- Average response time: 2.72 ms
- P95 response time: 6.93 ms
- Maximum response time: 12 ms

### Thresholds

- HTTP failure rate below 1%: passed
- P95 response time below 500 ms: passed

## 4. API Progressive Stress Test

**File:** `api-stress-test.js`

**Endpoints:**
- `GET /api/scans`
- `GET /api/findings`

### Stages

- 10 virtual users for 30 seconds
- 25 virtual users for 30 seconds
- 50 virtual users for 30 seconds
- 100 virtual users for 30 seconds
- Ramp down to 0 users over 30 seconds

### Execution

```bash
docker run --rm --add-host=host.docker.internal:host-gateway -v "$PWD/load-tests:/scripts:ro" grafana/k6 run /scripts/api-stress-test.js
```

### Results

- Maximum virtual users: 100
- Duration: 2 minutes and 30 seconds
- Iterations: 5,552
- HTTP requests: 11,104
- Request rate: 73.78 requests/second
- Failed requests: 0 (0%)
- Checks passed: 100% (22,208 checks)
- Average response time: 1.5 ms
- P95 response time: 3.8 ms
- Maximum response time: 20.52 ms

### Thresholds

- HTTP failure rate below 1%: passed
- P95 response time below 500 ms: passed

## 5. Results and Limitations

All four tests passed their configured thresholds.

The health tests evaluated backend availability under normal and progressively increasing load. The API tests additionally exercised the scan and finding list endpoints.

**Important limitation:** The database contained no scan or finding records during both API tests. Therefore, their results represent read requests returning empty arrays.

These tests do not measure:
- ZIP upload throughput.
- Scanner execution time.
- Concurrent scan capacity.
- Performance with populated datasets.
- Full application performance under realistic workloads.

Further testing should exercise representative upload and scanning workflows, with controlled test projects and populated datasets, before making claims about end-to-end capacity.

## 6. Reproducibility

Run the commands from the repository root. Docker must be running, and the Terraform-provisioned backend must be available on port 8100.
