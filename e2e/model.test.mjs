import test from "node:test";
import assert from "node:assert/strict";
import { brier, commitment, expectedRecord, expectedSettlement } from "./model.mjs";

test("brier matches the contract's integer formula", () => {
  assert.equal(brier(8000, 10000), 400);
  assert.equal(brier(3000, 10000), 4900);
  assert.equal(brier(100, 10000), 9801);
  assert.equal(brier(9900, 0), 9801);
  assert.equal(brier(5000, 0), 2500);
});

test("settlement: crowd, hits, beat-the-crowd, forfeit", () => {
  const rows = [
    { id: 1, status: "SCORED", probability_bps: 8000 },
    { id: 2, status: "SCORED", probability_bps: 3000 },
    { id: 3, status: "FORFEITED", probability_bps: 0 },
  ];
  const s = expectedSettlement(rows, true);
  assert.equal(s.crowd, 5500);
  assert.equal(s.crowdBrier, 2025);
  assert.deepEqual(s.perRow.map((r) => [r.brier, r.hit, r.beat]), [[400, true, true], [4900, false, false], [10000, false, false]]);
});

test("aggregates", () => {
  const rows = [
    { status: "SCORED", expected: { brier: 400, crowdBrier: 2025, beat: true, hit: true } },
    { status: "FORFEITED" },
  ];
  assert.deepEqual(expectedRecord(rows), { scored: 1, forfeited: 1, brier_sum: 400, crowd_brier_sum: 2025, beat_crowd: 1, hits: 1 });
});

test("commitment is deterministic, lower-cases the address and binds every field", () => {
  const a = "0xAbCdEf0123456789aBcDeF0123456789AbCdEf01";
  const base = commitment(1, a, 7000, "saltysalt1");
  assert.equal(base.length, 64);
  assert.equal(base, commitment(1, a.toLowerCase(), 7000, "saltysalt1"));
  for (const other of [commitment(2, a, 7000, "saltysalt1"), commitment(1, a, 7001, "saltysalt1"), commitment(1, a, 7000, "saltysalt2"),
                       commitment(1, "0x" + "11".repeat(20), 7000, "saltysalt1")]) assert.notEqual(base, other);
});
