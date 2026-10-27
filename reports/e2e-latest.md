# ForesightLedger: live Studionet end-to-end report

**Overall: PASS**: 59/59 steps passed, 0 deterministic failure(s), 0 model-dependent observation(s) differing from expectation.

| | |
|---|---|
| Run id | `mvqlea3n` |
| Date (UTC) | 2026-10-27T11:46:12.328Z |
| Network | GenLayer Studionet |
| Contract | [`0xa6f9aa3a264ed67E49329bC776AA88091641DCC9`](https://explorer-studio.genlayer.com/contracts/0xa6f9aa3a264ed67E49329bC776AA88091641DCC9) |
| Commit / reveal windows | 720s / 480s |
| Fixtures | https://raw.githubusercontent.com/reza9133/foresightledger/main/e2e/fixtures |
| Mode | full |
| Git commit | c89fbc8 |
| Node | v22.16.0 |

HARD steps assert deterministic contract behaviour (access rules, validation, hashes, counters, scoring arithmetic, state after a rejected transaction). MODEL steps record what real LLM validators, the web renderer or the network's finality did; a ⚠️ means the observation differed from the expectation, which is information about validators or infrastructure, not a contract defect.

## Steps

| | ID | Kind | Step | Result | Time |
|---|---|---|---|---|---|
| ✅ | S01 | HARD | Four accounts created and funded | alice 0x40686DbfE4bF823146222992F0cc1F249Ca8950f, bob 0x29E61223Fbcde0553f63fab301304da360F960E6, carol 0xe0578afe02bE28f642c977E296b49064E3B34B12, dave 0x70dEbdD6c696ae9d41741a2bc9814D5a2320Daa8 | 1.3s |
| ✅ | S02 | HARD | Evidence fixtures are reachable and match the local files | base https://raw.githubusercontent.com/reza9133/foresightledger/main/e2e/fixtures | 0.8s |
| ✅ | S03 | HARD | Contract deployed (or existing deployment reused) | deployed 0xa6f9aa3a264ed67E49329bC776AA88091641DCC9 | 36.3s |
| ✅ | S04 | HARD | get_version is 1.x and get_limits matches the source constants | version 1.0.0 | 22.8s |
| ✅ | S05 | HARD | Local commitment hash equals the contract's preview_commitment | 12dea801d185471a... | 1.1s |
| ✅ | O01 | HARD | Open question "yes" (fixture operational) | question #1 | 13.7s |
| ✅ | O02 | HARD | Open question "no" (fixture cancelled) | question #2 | 20.2s |
| ✅ | O03 | HARD | Open question "open" (fixture testing) | question #3 | 39.2s |
| ✅ | O04 | HARD | Open question "injection" (fixture injection) | question #4 | 14.5s |
| ✅ | C01 | HARD | bob commits on "yes" | forecast #1 sealed | 33.6s |
| ✅ | C02 | HARD | carol commits on "yes" | forecast #2 sealed | 18.5s |
| ✅ | C03 | HARD | dave commits on "yes" | forecast #3 sealed | 11.8s |
| ✅ | C04 | HARD | bob commits on "no" | forecast #4 sealed | 35.1s |
| ✅ | C05 | HARD | carol commits on "no" | forecast #5 sealed | 14.3s |
| ✅ | C06 | HARD | bob commits on "open" | forecast #6 sealed | 10.7s |
| ✅ | C07 | HARD | carol commits on "injection" | forecast #7 sealed | 35.4s |
| ✅ | C90 | HARD | Question counters reflect the sealed forecasts | ok | 8.2s |
| ✅ | R01 | HARD | Creator may not forecast their own question | rejected: "the question creator may not forecast their own question" | 16.2s |
| ✅ | R02 | HARD | A second commit from the same address is rejected | rejected: "this address already committed a forecast on this question" | 35.6s |
| ✅ | R03 | HARD | A malformed commitment is rejected | rejected: "commitment must be a 32-byte hex digest" | 19.3s |
| ✅ | R04 | HARD | Revealing before the commit window closes is rejected | rejected: "the reveal window has not opened yet" | 11.1s |
| ✅ | R05 | HARD | open_question rejects: private IPv4 evidence URL | rejected: "source_url must be a public https:// URL (no private IPs, odd ports, o" | 40.8s |
| ✅ | R06 | HARD | open_question rejects: cloud metadata evidence URL | rejected: "source_url must be a public https:// URL (no private IPs, odd ports, o" | 15.8s |
| ✅ | R07 | HARD | open_question rejects: plain http evidence URL | rejected: "source_url must be a public https:// URL (no private IPs, odd ports, o" | 33.0s |
| ✅ | R08 | HARD | open_question rejects: prompt delimiter inside the criteria | rejected: "text may not contain the sequences <<< or >>>" | 19.3s |
| ✅ | R09 | HARD | open_question rejects: criteria that do not say what YES means | rejected: "criteria must be at least 30 characters and say what YES means" | 32.9s |
| ✅ | R10 | HARD | open_question rejects: close_at less than five minutes away | rejected: "close_at must be at least five minutes in the future" | 19.1s |
| ✅ | R11 | HARD | open_question rejects: reveal window shorter than five minutes | rejected: "reveal window must be between five minutes and fourteen days" | 15.7s |
| ✅ | R12 | HARD | An identical question (same title and page) is rejected | rejected: "an identical question is already open as #1" | 33.0s |
| ✅ | R13 | MODEL | An unreadable evidence page is rejected | rejected | 19.3s |
| ✅ | R14 | HARD | Resolving before the reveal window ends is rejected | rejected: "resolution opens after the reveal window closes" | 32.9s |
| ✅ | R15 | HARD | Voiding before the 14 day grace period is rejected | rejected: "the void grace period has not elapsed" | 19.1s |
| ✅ | W01 | HARD | Commit window closed on the network clock | closed | 126.1s |
| ✅ | R16 | HARD | Committing after the window closed is rejected | rejected: "the commit window is closed" | 8.6s |
| ✅ | R17 | HARD | Revealing with the wrong salt is rejected | rejected: "probability and salt do not match the commitment" | 8.4s |
| ✅ | R18 | HARD | Revealing with the wrong probability is rejected | rejected: "probability and salt do not match the commitment" | 50.8s |
| ✅ | R19 | HARD | Revealing without a commitment is rejected | rejected: "no committed forecast from this address on this question" | 13.6s |
| ✅ | V08 | HARD | bob reveals 8000 on "yes" | forecast #1 revealed | 40.9s |
| ✅ | V09 | HARD | carol reveals 3000 on "yes" | forecast #2 revealed | 14.4s |
| ✅ | V10 | HARD | bob reveals 2000 on "no" | forecast #4 revealed | 12.4s |
| ✅ | V11 | HARD | carol reveals 6000 on "no" | forecast #5 revealed | 39.8s |
| ✅ | V12 | HARD | bob reveals 5000 on "open" | forecast #6 revealed | 15.4s |
| ✅ | V13 | HARD | carol reveals 6000 on "injection" | forecast #7 revealed | 38.0s |
| ✅ | R20 | HARD | A forecast cannot be revealed twice | rejected: "this forecast was already revealed" | 13.2s |
| ✅ | V90 | HARD | Revealed and forfeit-to-be counters are right | ok | 8.6s |
| ✅ | W02 | HARD | Reveal window closed on the network clock | closed | 216.1s |
| ✅ | X01 | MODEL | Validators resolve "yes" (expect RESOLVED_YES) | RESOLVED_YES, verdict YES, quote "The Aurora relay satellite has been declared fully operation" | 15.8s |
| ✅ | X02 | MODEL | Validators resolve "no" (expect RESOLVED_NO) | RESOLVED_NO, verdict NO, quote "The Aurora relay satellite program has been cancelled. The s" | 48.8s |
| ✅ | X03 | MODEL | Validators resolve "open" (expect OPEN) | OPEN, verdict NOT_YET, quote "No declaration of operational status has been made" | 28.1s |
| ✅ | R21 | HARD | A second resolve attempt right after the first is rejected by the cooldown | rejected: "resolution cooldown still active" | 36.1s |
| ✅ | X04 | MODEL | Validators resolve "injection" (expect NOT_YES) | OPEN, verdict NOT_YET, quote "The Aurora relay satellite is still in commissioning tests a" | 24.0s |
| ✅ | Y01 | HARD | Every settled question's scores equal an independent recomputation | 2 settled question(s) verified | 28.4s |
| ✅ | Y02 | HARD | A forecast that was never revealed is forfeited with the worst score | dave: FORFEITED, brier 10000 | 8.6s |
| ✅ | Y03 | HARD | Forecaster track records equal a recomputation over this run | bob, carol, dave verified | 7.0s |
| ✅ | Y04 | HARD | An unsettled question keeps its forecasts untouched | REVEALED, unscored | 8.4s |
| ✅ | K01 | HARD | get_stats equals a brute-force recount of every question | 4 questions, 7 forecasts, 4 reports | 6.2s |
| ✅ | K02 | HARD | Calibration totals equal the number of scored forecasts | 4 scored forecasts across 10 buckets | 2.3s |
| ✅ | K03 | HARD | List views are paginated and reads need no wallet | ok | 2.3s |
| ✅ | F01 | MODEL | Every transaction reaches FINALIZED | 43/43 FINALIZED | 116.8s |

## Questions

| Case | Question | Expected | Outcome |
|---|---|---|---|
| yes | #1 | RESOLVED_YES | RESOLVED_YES; verdict YES; crowd 5500 |
| no | #2 | RESOLVED_NO | RESOLVED_NO; verdict NO; crowd 4000 |
| open | #3 | OPEN | OPEN; verdict NOT_YET; crowd 0 |
| injection | #4 | NOT_YES | OPEN; verdict NOT_YET; crowd 0 |

## Transaction manifest

| # | Action | Outcome | Wait | Status | Transaction |
|---|---|---|---|---|---|
| 1 | deploy ForesightLedger (alice) | succeeded | 0s | FINALIZED | [0x90ee3f4fa1…](https://explorer-studio.genlayer.com/tx/0x90ee3f4fa194a00812228c4840cd6bbb8ab87efbea1a8268c5c59cfd8ceb4061) |
| 2 | open yes (alice) | succeeded | 11s | FINALIZED | [0x3172e254b3…](https://explorer-studio.genlayer.com/tx/0x3172e254b345b8d24cd82345b846c7ba2099b192c8720b136801ae2a3450004a) |
| 3 | open no (alice) | succeeded | 3s | FINALIZED | [0x8d9d51ca98…](https://explorer-studio.genlayer.com/tx/0x8d9d51ca98ecf43f6e0501171cf5a98ff7c9aa8e350afb4ecd67f72eab931763) |
| 4 | open open (alice) | succeeded | 11s | FINALIZED | [0x690c1a5ff5…](https://explorer-studio.genlayer.com/tx/0x690c1a5ff5ea55e3478248a721fc2ae13c7682458eea6b8686bb1bb51229cfe2) |
| 5 | open injection (alice) | succeeded | 11s | FINALIZED | [0x64e8e4fc76…](https://explorer-studio.genlayer.com/tx/0x64e8e4fc761a24fd3f1aa433e964b9d6c6c24087de7a65ad0a819cac56478b2b) |
| 6 | commit yes (bob) | succeeded | 1s | FINALIZED | [0xdc8a16b528…](https://explorer-studio.genlayer.com/tx/0xdc8a16b52824e51c67bf54f804f77a01aef7dc00538c56c9508da59037e60066) |
| 7 | commit yes (carol) | succeeded | 6s | FINALIZED | [0x5479cc77be…](https://explorer-studio.genlayer.com/tx/0x5479cc77be1cfd4feb0c3e16fd0988c11b51daf37ae5df326420a000e1513d18) |
| 8 | commit yes (dave) | succeeded | 5s | FINALIZED | [0x2946b4aa4d…](https://explorer-studio.genlayer.com/tx/0x2946b4aa4d32b85b32409d2c91770c4472aaa59bc25eefb612205a99edab2e9b) |
| 9 | commit no (bob) | succeeded | 6s | FINALIZED | [0xe91008b68d…](https://explorer-studio.genlayer.com/tx/0xe91008b68db306242d0c528fc71969a31e2dce243482402a1864596af5783d23) |
| 10 | commit no (carol) | succeeded | 0s | FINALIZED | [0x67522f72d2…](https://explorer-studio.genlayer.com/tx/0x67522f72d2b3e25ee42c099f84b20097ecfd553621bd34415fca267053d44042) |
| 11 | commit open (bob) | succeeded | 5s | FINALIZED | [0x5b9dc00591…](https://explorer-studio.genlayer.com/tx/0x5b9dc005917491d3697b6b7d74af8c58253eb4da84bf9788fce5eefbcc306c38) |
| 12 | commit injection (carol) | succeeded | 7s | FINALIZED | [0x588472e6fc…](https://explorer-studio.genlayer.com/tx/0x588472e6fc194d13634fc61e1e0e809ce662a6818e94494e51da40d2a927f222) |
| 13 | rejected: creator commits (alice) | accepted (state unchanged) | 9s | FINALIZED | [0xb7a9de4a77…](https://explorer-studio.genlayer.com/tx/0xb7a9de4a772ecda79a494602a05026bee501c7c2b4601271eb86b7ef7b7c6d4e) |
| 14 | rejected: duplicate commit (bob) | accepted (state unchanged) | 6s | FINALIZED | [0xd984296b0c…](https://explorer-studio.genlayer.com/tx/0xd984296b0c9ad75f123121a2dbd91fbaaedb7d7c1c06820ea08bea985d574f29) |
| 15 | rejected: malformed commitment (dave) | accepted (state unchanged) | 5s | FINALIZED | [0xa787c0414b…](https://explorer-studio.genlayer.com/tx/0xa787c0414b122f839730bad9ad0e936d33ff57c5252aa48f3974808d5c799ac8) |
| 16 | rejected: early reveal (bob) | accepted (state unchanged) | 3s | FINALIZED | [0x3b5ecc4a67…](https://explorer-studio.genlayer.com/tx/0x3b5ecc4a67b78c545c0270fe6297b01cec73ed14eb50579235155a08e3cc4824) |
| 17 | rejected: private IPv4 evidence URL (alice) | accepted (state unchanged) | 6s | FINALIZED | [0xce9db82673…](https://explorer-studio.genlayer.com/tx/0xce9db826732273eacabcce2e09775aa498e90e42b9e95d370c0690de5676d38a) |
| 18 | rejected: cloud metadata evidence URL (alice) | accepted (state unchanged) | 6s | FINALIZED | [0x57043483a8…](https://explorer-studio.genlayer.com/tx/0x57043483a89c80dcb84744a97eaa5f2305eb5d725c9534ab84d7b47acfd1ef7a) |
| 19 | rejected: plain http evidence URL (alice) | accepted (state unchanged) | 6s | FINALIZED | [0xf9e6cf9781…](https://explorer-studio.genlayer.com/tx/0xf9e6cf978138f6f92cd3dc15ee6730e827f2dae5167db0189518f3b67c86c31f) |
| 20 | rejected: prompt delimiter inside the criteria (alice) | accepted (state unchanged) | 5s | FINALIZED | [0xaa5b16fb66…](https://explorer-studio.genlayer.com/tx/0xaa5b16fb662776e08426373447525862d5b606f1dcff0b254adf8bee0f125bc8) |
| 21 | rejected: criteria that do not say what YES means (alice) | accepted (state unchanged) | 6s | FINALIZED | [0x3715919d2e…](https://explorer-studio.genlayer.com/tx/0x3715919d2e8a433f961e722fe216b68ca27b4a96d73c3b2dded630db751773a8) |
| 22 | rejected: close_at less than five minutes away (alice) | accepted (state unchanged) | 5s | FINALIZED | [0xa16ddcb26d…](https://explorer-studio.genlayer.com/tx/0xa16ddcb26dff8e15403ac8a8f761e2219644c1431b117f358851d01329656ab2) |
| 23 | rejected: reveal window shorter than five minutes (alice) | accepted (state unchanged) | 6s | FINALIZED | [0x6cf6ddd850…](https://explorer-studio.genlayer.com/tx/0x6cf6ddd8503a2dfb3c153b37575c4da6402323c41355b298cd2d5094401cafe1) |
| 24 | rejected: duplicate question (alice) | accepted (state unchanged) | 6s | FINALIZED | [0xf8e995d720…](https://explorer-studio.genlayer.com/tx/0xf8e995d7206df2c1c8dc24910a2de040059ea55bb24afbb2f7c3020b6bba9991) |
| 25 | rejected: unreadable page (alice) | accepted (state unchanged) | 5s | FINALIZED | [0x90a41f65ac…](https://explorer-studio.genlayer.com/tx/0x90a41f65ac9be754dfd1f0c798a3c8d9caf5f67aeaa5889c7b8c82c019195d63) |
| 26 | rejected: early resolve (bob) | accepted (state unchanged) | 6s | FINALIZED | [0x59898bff97…](https://explorer-studio.genlayer.com/tx/0x59898bff978860b26f6fb5cf4e165c344c2953fce61a5990b899a8fe7b1144b0) |
| 27 | rejected: early void (bob) | accepted (state unchanged) | 5s | FINALIZED | [0xfe05d2a806…](https://explorer-studio.genlayer.com/tx/0xfe05d2a80698c27c192465e20e18c966a86b3aab01baa5b109c912a662ddc535) |
| 28 | rejected: late commit (dave) | accepted (state unchanged) | 5s | FINALIZED | [0xb4551db63b…](https://explorer-studio.genlayer.com/tx/0xb4551db63b2fb4430a92986abf9411df78532a7260e704c96442049238069c62) |
| 29 | rejected: wrong salt (bob) | accepted (state unchanged) | 5s | FINALIZED | [0x60d67a59b0…](https://explorer-studio.genlayer.com/tx/0x60d67a59b0bf603dd685349a7cbdb4e5e9c2de6998eb44cbea54a3bbb20b0281) |
| 30 | rejected: wrong probability (bob) | accepted (state unchanged) | 5s | FINALIZED | [0x1285f02041…](https://explorer-studio.genlayer.com/tx/0x1285f02041db98409bdec9dcd2ad11dc30fa7894921194b1357157b30eedfb82) |
| 31 | rejected: reveal without commit (dave) | accepted (state unchanged) | 10s | FINALIZED | [0x2f43ea1713…](https://explorer-studio.genlayer.com/tx/0x2f43ea171379ade95fb09019eb0cece0c4033cd0eb6eade6693cfad09e14eafb) |
| 32 | reveal yes (bob) | succeeded | 5s | FINALIZED | [0x0d717aaa0a…](https://explorer-studio.genlayer.com/tx/0x0d717aaa0afa6739c4a84c6295e71675883ad6f321d4e1e2c17d01a3696d8bf6) |
| 33 | reveal yes (carol) | succeeded | 5s | FINALIZED | [0x52b77665cd…](https://explorer-studio.genlayer.com/tx/0x52b77665cd3ea6ab1760a758709886a86bd6d7c166855bb8cfb062fa83bac8e4) |
| 34 | reveal no (bob) | succeeded | 5s | FINALIZED | [0x15e4153422…](https://explorer-studio.genlayer.com/tx/0x15e41534223cb53778d38354580cdd016873fa200717e9a867483bba295e7b40) |
| 35 | reveal no (carol) | succeeded | 4s | FINALIZED | [0x8a2e5bbff7…](https://explorer-studio.genlayer.com/tx/0x8a2e5bbff7872303dd7b1cb9b9741fbd73e8281ad1e0427efe6958859f128d79) |
| 36 | reveal open (bob) | succeeded | 6s | FINALIZED | [0xb8f648ba16…](https://explorer-studio.genlayer.com/tx/0xb8f648ba167425346899c9bc1838e38c32a04dc0e7af9eb600e8e90baf30b4e1) |
| 37 | reveal injection (carol) | succeeded | 6s | FINALIZED | [0xae687f1dd8…](https://explorer-studio.genlayer.com/tx/0xae687f1dd80410c8361a032fce342dd99be5ad84ee300c12b41814d746b75280) |
| 38 | rejected: double reveal (bob) | accepted (state unchanged) | 5s | FINALIZED | [0x52881d49bc…](https://explorer-studio.genlayer.com/tx/0x52881d49bca7e70afc37826e15f94c3ef41a17a69012fa03466f7562e87f1df0) |
| 39 | resolve yes (bob) | succeeded | 10s | FINALIZED | [0xd144a978d4…](https://explorer-studio.genlayer.com/tx/0xd144a978d4103f2344ea6ea990255f9ae05ce969b81c972e6c39e9ba18b3f040) |
| 40 | resolve no (bob) | succeeded | 43s | FINALIZED | [0x3585130ec9…](https://explorer-studio.genlayer.com/tx/0x3585130ec993950f325787e8708b346f33cbb62b2dbc810f0b5ae8c7293acd18) |
| 41 | resolve open (bob) | succeeded | 17s | FINALIZED | [0x51a3a3a9fc…](https://explorer-studio.genlayer.com/tx/0x51a3a3a9fcec10e53ebbf46428c8f5e5d63049031ec56f47ad34c2de1bd0e618) |
| 42 | rejected: immediate re-resolve (carol) | accepted (state unchanged) | 6s | FINALIZED | [0x0cd9212580…](https://explorer-studio.genlayer.com/tx/0x0cd9212580cc5818725db883171544db958ac3f2bdb2a3ccecf121e033b78bb4) |
| 43 | resolve injection (bob) | succeeded | 16s | FINALIZED | [0x9b7e0e1d2a…](https://explorer-studio.genlayer.com/tx/0x9b7e0e1d2a26887fdb2ebeea82280d021250d76b3c297f1162c9b2cfa78c706e) |

## Not covered by this run

- The VOID path needs 14 days of real time after the reveal window; it is covered by `tests/contract/test_void.py` (direct mode).
- Limits that need dozens of accounts (40 forecasts per question, 25 questions per creator) are covered in direct mode, not live.
- Validator disagreement and leader rotation are properties of the network; the validator logic itself is covered by `tests/contract/test_validators.py`.
- Exact revert texts are asserted in direct mode; live, the proof of a rejection is the unchanged state and the receipt's reason when the node exposes it.
- Browser wallet signing is not exercised; this script signs with local keys.
