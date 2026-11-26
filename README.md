# GenLayer Escrow Judge

An **Intelligent Contract** for [GenLayer](https://genlayer.com): trustless escrow where an AI adjudicator — the validators' model reached through GenLayer's Equivalence Principle — settles buyer–seller disputes from natural-language evidence. No human arbitrator, no oracle, no multisig.

## Why this matters

Agentic commerce (x402, A2A, ERC-8004, agent payment protocols) all engineer the happy path — none of them ships **dispute resolution**. This contract fills that gap for machine-to-machine deals: the terms are plain language, the evidence is plain language, and the judgment is delegated to the decentralized AI validators GenLayer runs.

## How it works

1. **Fund** — the buyer deploys the contract with the deal terms (natural language) and deposits value via `deposit()`.
2. **Deliver** — the seller delivers the work off-chain.
3. **Dispute** — if the parties disagree, either calls `open_dispute()`.
4. **Adjudicate** — `resolve(buyer_evidence, seller_evidence)` sends the terms + both sides' evidence through the Equivalence Principle; the validators' model returns `{"winner": "buyer"|"seller", "reason": "..."}` which is written into the contract state for audit.
5. **Settle** — funds are released to the winner (`settle_amicable()` handles the no-dispute case).

## Files

- `contract.py` — **EscrowJudge**: escrow whose delivery dispute is adjudicated by the validators' model from plain-language evidence.
- `prediction_judge.py` — **PredictionJudge**: a prediction market on plain-language questions (things oracles can't parse), resolved by AI consensus, pro-rata payouts.
- `agent_reputation.py` — **AgentReputation**: staked vouch/accuse reputation for autonomous agents, AI-verified interaction reviews, challenge adjudication.
- `LICENSE` — MIT.

## Deploy

Open [GenLayer Studio](https://studio.genlayer.com), import any of the `.py` files, deploy to the Clarke testnet, and interact per the methods below. See the [GenLayer docs](https://docs.genlayer.com) for validator context.

## Contract surface

### EscrowJudge (`contract.py`)
| Method | Kind | Purpose |
|---|---|---|
| `deposit()` | write, payable | fund the escrow |
| `open_dispute()` | write | open a delivery dispute |
| `resolve(buyer_evidence, seller_evidence)` | write | AI adjudication via Equivalence Principle |
| `settle_amicable(to_buyer)` | write | settle without a dispute |
| `status()` / `get_details()` | view | state |

### PredictionJudge (`prediction_judge.py`)
| Method | Kind | Purpose |
|---|---|---|
| `bet_yes()` / `bet_no()` | write, payable | stake on the outcome until close |
| `resolve()` | write | AI resolution against the agreed rules |
| `claim()` | write | winners withdraw pro-rata |
| `odds()` / `details()` | view | live odds, state |

### AgentReputation (`agent_reputation.py`)
| Method | Kind | Purpose |
|---|---|---|
| `vouch(note)` / `accuse(note)` | write, payable | staked reputation |
| `add_ai_verified_review(transcript)` | write | validators grade a real interaction 0-10 |
| `close_challenge()` | write | AI rules on the accusations |
| `claim()` | write | winners withdraw |
| `reputation()` | view | public reputation line |

## License

MIT
