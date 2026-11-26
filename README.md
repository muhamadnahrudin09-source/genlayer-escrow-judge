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

- `contract.py` — the Intelligent Contract (GenVM, Python).
- `LICENSE` — MIT.

## Deploy

Open [GenLayer Studio](https://studio.genlayer.com), create a new project from `contract.py`, deploy to the Clarke testnet, and call `deposit()` with value to fund it. See the [GenLayer docs](https://docs.genlayer.com) for validator context.

## Contract surface

| Method | Kind | Purpose |
|---|---|---|
| `deposit()` | write, payable | fund the escrow |
| `open_dispute()` | write | open a delivery dispute |
| `resolve(buyer_evidence, seller_evidence)` | write | AI adjudication via Equivalence Principle |
| `settle_amicable(to_buyer)` | write | settle without a dispute |
| `status()` | view | `awaiting_funding / funded / disputed / settled:<winner>` |
| `get_details()` | view | full state as JSON |

## License

MIT
