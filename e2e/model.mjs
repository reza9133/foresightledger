// Pure helpers shared by the live run and its offline tests: no network, no chain.
import { keccak256, toHex } from "viem";

export const BPS = 10000;
export const WORST = 10000;

/** Same preimage and hash the contract uses (keccak256 over UTF-8, lower-case address). */
export function commitment(questionId, forecasterAddress, probabilityBps, salt) {
  return keccak256(toHex(`foresight-v1|${questionId}|${forecasterAddress.toLowerCase()}|${probabilityBps}|${salt}`)).slice(2);
}

export const brier = (probabilityBps, outcomeBps) => Math.floor(((probabilityBps - outcomeBps) ** 2) / BPS);

/**
 * Expected result of settling one question.
 * `rows` are the forecasts as stored AFTER settlement (status SCORED or FORFEITED, probability on SCORED rows).
 * Returns the expected crowd and one expectation per row.
 */
export function expectedSettlement(rows, yes) {
  const outcome = yes ? BPS : 0;
  const shown = rows.filter((r) => r.status === "SCORED");
  const crowd = shown.length ? Math.floor(shown.reduce((s, r) => s + r.probability_bps, 0) / shown.length) : 0;
  const crowdBrier = shown.length ? brier(crowd, outcome) : 0;
  const perRow = rows.map((r) => {
    if (r.status === "FORFEITED") return { id: r.id, brier: WORST, hit: false, beat: false, crowdBrier: 0 };
    const b = brier(r.probability_bps, outcome);
    const hit = (r.probability_bps > 5000 && yes) || (r.probability_bps < 5000 && !yes);
    return { id: r.id, brier: b, hit, beat: b < crowdBrier, crowdBrier };
  });
  return { crowd, crowdBrier, perRow };
}

/** Expected per-forecaster aggregates from a list of settled forecast rows (any questions). */
export function expectedRecord(rows) {
  const rec = { scored: 0, forfeited: 0, brier_sum: 0, crowd_brier_sum: 0, beat_crowd: 0, hits: 0 };
  for (const r of rows) {
    if (r.status === "FORFEITED") { rec.forfeited += 1; continue; }
    rec.scored += 1;
    rec.brier_sum += r.expected.brier;
    rec.crowd_brier_sum += r.expected.crowdBrier;
    rec.beat_crowd += r.expected.beat ? 1 : 0;
    rec.hits += r.expected.hit ? 1 : 0;
  }
  return rec;
}
