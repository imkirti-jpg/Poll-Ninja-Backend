import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 20,
  iterations: 1000,
  thresholds: {
    http_req_failed: ["rate<0.01"],      // <1% failures
    http_req_duration: ["p(95)<200"],    // 95% under 200 ms
  },
};

const BASE_URL = "http://localhost:8000";

export default function () {
  // List polls
  let res = http.get(`${BASE_URL}/api/polls`);

  check(res, {
    "GET /api/polls status is 200": (r) => r.status === 200,
  });

  // If polls exist, fetch one poll
  if (res.status === 200) {
    const polls = res.json();

    if (polls.length > 0) {
      const pollId = polls[0].id;

      let pollRes = http.get(`${BASE_URL}/api/polls/${pollId}`);

      check(pollRes, {
        "GET /api/polls/{id} status is 200": (r) => r.status === 200,
      });
    }
  }

  sleep(1);
}