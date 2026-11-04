# SecureScan - Load Testing

## Objective
Evaluate backend availability and response time under normal and progressively increasing HTTP load using Grafana k6.

## Test Environment
- Tool: Grafana k6
- Execution: Docker
- Target: http://host.docker.internal:8100/health
- Backend: Terraform-provisioned Docker container
- Endpoint: GET /health

## 1. Health Test

File: health-test.js

Configuration:
- 10 virtual users
- 30 seconds
- HTTP failure rate below 1%
- P95 response time below 500 ms

Execution:
`docker run --rm --add-host=host.docker.internal:host-gateway -v "$PWD/load-tests:/scripts:ro" grafana/k6 run /scripts/health-test.js`

Results:
- HTTP requests: 300
- Failed requests: 0 (0%)
- Checks passed: 100%
- Average response time: 2.09 ms
- P95 response time: 3.46 ms
- Maximum response time: 4.77 ms

## 2. Progressive Stress Test

File: stress-test.js

Stages:
- 10 virtual users for 30 seconds
- 25 virtual users for 30 seconds
- 50 virtual users for 30 seconds
- 100 virtual users for 30 seconds
- Ramp down to 0 users over 30 seconds

Execution:
`docker run --rm --add-host=host.docker.internal:host-gateway -v "$PWD/load-tests:/scripts:ro" grafana/k6 run /scripts/stress-test.js`

Thresholds:
- HTTP failure rate below 1%
- P95 response time below 500 ms

Results:
- Maximum virtual users: 100
- HTTP requests: 5,561
- Failed requests: 0 (0%)
- Checks passed: 100%
- Average response time: 1.11 ms
- P95 response time: 2.06 ms
- Maximum response time: 8.23 ms

## 3. Results and Limitations

Both tests passed their configured thresholds. The backend health endpoint remained available throughout both tests, with no failed HTTP requests.

Important limitation: These tests target only the lightweight /health endpoint. They do not measure ZIP upload throughput, scanner execution time, concurrent scan capacity, or full application performance.

Further testing should exercise representative upload and scanning workflows before making claims about end-to-end capacity.

## 4. Reproducibility

Run the commands from the repository root. Docker must be running, and the Terraform-provisioned backend must be available on port 8100.
