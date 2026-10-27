// Shared helpers for the Studionet deploy script. Plain ESM: runs with `node` and genlayer-js only.
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createAccount, createClient, generatePrivateKey } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const CONTRACT_PATH = resolve(ROOT, "contracts", "foresight_ledger.py");
export const EXPLORER = "https://explorer-studio.genlayer.com";
export { createAccount, createClient, generatePrivateKey, studionet, TransactionStatus };

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** genlayer-js returns bigint, Map and Uint8Array values; turn them into plain JSON-friendly data. */
export function normalize(value, depth = 0) {
  if (depth > 12) return null;
  if (typeof value === "bigint") return Number(value) <= Number.MAX_SAFE_INTEGER ? Number(value) : value.toString();
  if (value instanceof Uint8Array) return value.length === 20 ? "0x" + Buffer.from(value).toString("hex") : Array.from(value);
  if (value instanceof Map) return Object.fromEntries([...value.entries()].map(([k, v]) => [String(k), normalize(v, depth + 1)]));
  if (Array.isArray(value)) return value.map((v) => normalize(v, depth + 1));
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, normalize(v, depth + 1)]));
  return value;
}

export function makeClient(account) {
  return createClient({ chain: studionet, account });
}

export async function fund(client, address, amount = 10 ** 20) {
  try {
    await client.request({ method: "sim_fundAccount", params: [address, amount] });
    return true;
  } catch (err) {
    return String(err?.message ?? err);
  }
}

export function receiptFailed(receipt) {
  return receipt?.txExecutionResultName === "FINISHED_WITH_ERROR";
}

/** Digs the contract's own "[EXPECTED] ..." / "[EXTERNAL] ..." text out of any receipt shape. */
export function taggedMessage(value, depth = 0) {
  if (depth > 7 || value == null) return null;
  if (typeof value === "string") {
    const m = value.match(/\[(EXPECTED|EXTERNAL)\]\s*([^"\\]*)/);
    return m ? m[2].trim() : null;
  }
  if (Array.isArray(value)) {
    for (const v of value) { const f = taggedMessage(v, depth + 1); if (f) return f; }
    return null;
  }
  if (typeof value === "object") {
    for (const v of Object.values(value)) { const f = taggedMessage(v, depth + 1); if (f) return f; }
  }
  return null;
}

export function findAddress(value, depth = 0) {
  if (depth > 7 || value == null) return null;
  if (typeof value === "string") return /^0x[0-9a-fA-F]{40}$/.test(value) ? value : null;
  if (typeof value === "object") {
    for (const key of ["contract_address", "contractAddress", "recipient", "to_address"]) {
      const hit = typeof value[key] === "string" && /^0x[0-9a-fA-F]{40}$/.test(value[key]) ? value[key] : null;
      if (hit) return hit;
    }
    for (const v of Object.values(value)) { const f = findAddress(v, depth + 1); if (f) return f; }
  }
  return null;
}

export async function deployLedger(client, log = console.log) {
  const code = readFileSync(CONTRACT_PATH, "utf8");
  log("deploying contracts/foresight_ledger.py to Studionet ...");
  const hash = await client.deployContract({ code, args: [], leaderOnly: false });
  log(`deploy tx ${hash}`);
  const receipt = await client.waitForTransactionReceipt({ hash, status: TransactionStatus.FINALIZED, interval: 3000, retries: 200 });
  if (receiptFailed(receipt)) throw new Error("deployment failed: " + (taggedMessage(receipt) ?? "see explorer"));
  const address = findAddress(receipt?.data) ?? findAddress(receipt?.txDataDecoded) ?? findAddress(receipt);
  if (!address) throw new Error(`deployed (tx ${hash}) but the address could not be read from the receipt; copy it from ${EXPLORER}/tx/${hash}`);
  return { address, hash };
}
