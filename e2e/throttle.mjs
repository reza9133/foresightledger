// Client-side rate limiter for the public Studionet RPC (it answers
// "Rate limit exceeded: 30 requests per minute" and then fails every call).
//
// Import this module FIRST (before genlayer-js / viem): it wraps globalThis.fetch,
// the one transport every RPC call, receipt poll and read goes through, so no call
// site has to know about it. A sliding window keeps the run under the limit, and a
// response that is still rate limited is retried after a pause instead of failing a step.
//
//   E2E_RPC_PER_MINUTE   max RPC requests per window (default 22, the server allows 30)
//   E2E_RPC_WINDOW_MS    window length (default 60000)
//   E2E_RPC_PENALTY_MS   base pause after a rate-limit answer (default 12000)
const LIMIT = Math.max(1, Number(process.env.E2E_RPC_PER_MINUTE) || 22);
const WINDOW_MS = Number(process.env.E2E_RPC_WINDOW_MS) || 60_000;
const PENALTY_MS = Number(process.env.E2E_RPC_PENALTY_MS) || 12_000;
const MAX_RETRIES = 6;
const EXEMPT_HOSTS = /(^|\.)(github\.com|githubusercontent\.com)$/i;

const realFetch = globalThis.fetch;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const stamps = [];
let queue = Promise.resolve();

function takeSlot() {
  const job = queue.then(async () => {
    for (;;) {
      const now = Date.now();
      while (stamps.length && now - stamps[0] >= WINDOW_MS) stamps.shift();
      if (stamps.length < LIMIT) { stamps.push(now); return; }
      await sleep(stamps[0] + WINDOW_MS - now + 25);
    }
  });
  queue = job.catch(() => {});
  return job;
}

globalThis.fetch = async function throttledFetch(input, init) {
  let host = "";
  try { host = new URL(typeof input === "string" || input instanceof URL ? String(input) : input.url).hostname; } catch { /* leave empty */ }
  if (EXEMPT_HOSTS.test(host)) return realFetch(input, init);
  const replayable = typeof input === "string" || input instanceof URL; // a Request body can only be sent once

  for (let attempt = 0; ; attempt++) {
    await takeSlot();
    const res = await realFetch(input, init);
    let limited = res.status === 429;
    if (!limited && res.ok) {
      try { limited = /rate limit exceeded/i.test((await res.clone().text()).slice(0, 400)); } catch { /* body unreadable: treat as fine */ }
    }
    if (!limited || !replayable || attempt >= MAX_RETRIES) return res;
    const pause = PENALTY_MS + attempt * 4000;
    process.stdout.write(`\n    (RPC rate limit hit; pausing ${Math.round(pause / 1000)}s) `);
    await sleep(pause);
  }
};
