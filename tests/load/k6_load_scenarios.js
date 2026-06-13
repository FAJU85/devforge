// Phase 8.4: Load Testing Scenarios
// Run with: k6 run tests/load/k6_load_scenarios.js

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const chatLatency = new Trend('chat_response_latency_ms');
const errorRate = new Rate('errors');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const USER_TOKEN = __ENV.USER_TOKEN || 'test-token';

export const options = {
  stages: [
    { duration: '5m', target: 100 },   // Ramp-up
    { duration: '10m', target: 100 },  // Sustained
    { duration: '2m', target: 500 },   // Spike
    { duration: '5m', target: 100 },   // Recovery
    { duration: '5m', target: 0 },     // Ramp-down
  ],
  thresholds: {
    'chat_response_latency_ms': ['p(95) < 500', 'p(99) < 1000'],
    'errors': ['rate < 0.01'],
  },
};

export default function () {
  group('Chat Endpoint', () => {
    const payload = JSON.stringify({
      conversation_id: `conv-${__VU}-${__ITER}`,
      message: 'Analyze this code for bugs: def foo(): pass',
      model: 'claude-3-5-sonnet-20241022',
    });

    const params = {
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `session_token=${USER_TOKEN}`,
      },
    };

    const res = http.post(`${BASE_URL}/api/chat/send`, payload, params);
    chatLatency.add(res.timings.duration);

    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
    }) || errorRate.add(1);
  });

  sleep(1);
}
