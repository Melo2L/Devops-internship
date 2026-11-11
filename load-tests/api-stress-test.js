import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://host.docker.internal:8100";

export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "30s", target: 25 },
    { duration: "30s", target: 50 },
    { duration: "30s", target: 100 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export default function () {
  const scans = http.get(`${BASE_URL}/api/scans`);
  check(scans, {
    "Scans HTTP 200": (r) => r.status === 200,
    "Scans response is an array": (r) => {
      try {
        return Array.isArray(r.json());
      } catch {
        return false;
      }
    },
  });

  const findings = http.get(`${BASE_URL}/api/findings`);
  check(findings, {
    "Findings HTTP 200": (r) => r.status === 200,
    "Findings response is an array": (r) => {
      try {
        return Array.isArray(r.json());
      } catch {
        return false;
      }
    },
  });

  sleep(1);
}
