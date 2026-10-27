#!/usr/bin/env node
// Deploys contracts/foresight_ledger.py to GenLayer Studionet and prints the address.
//   FL_PRIVATE_KEY=0x...   optional (a throw-away key is generated otherwise)
//   node e2e/deploy.mjs
import { createAccount, EXPLORER, fund, generatePrivateKey, makeClient, deployLedger } from "./lib.mjs";

const key = process.env.FL_PRIVATE_KEY || generatePrivateKey();
const account = createAccount(key);
const client = makeClient(account);
const funded = await fund(client, account.address);
console.log(`deployer ${account.address}${funded === true ? " (funded via sim_fundAccount)" : ` (funding note: ${funded})`}`);
const { address, hash } = await deployLedger(client);
console.log(`\nForesightLedger deployed\n  address : ${address}\n  tx      : ${EXPLORER}/tx/${hash}\n  contract: ${EXPLORER}/contracts/${address}`);
console.log(`\nNext: open a question with open_question(title, criteria, source_url, close_at, reveal_window_seconds)`);
