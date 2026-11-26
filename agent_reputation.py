# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class AgentReputation(gl.Contract):
    """
    Reputation for autonomous agents in the agentic economy.

    Anyone stakes value to vouch for (or accuse) a registered agent.
    At challenge time the validators' model reads the evidence both
    sides submitted and either upholds or reverses the challenge —
    stakers on the losing side lose their stake to the winners.

    Complements ERC-8004 agent identity: an agent's on-chain reputation
    here is backed by economic skin-in-the-game and AI adjudication.
    """

    agent: str
    agent_name: str
    service_summary: str
    vouch_pool: int     # value staked FOR the agent
    accuse_pool: int    # value staked AGAINST
    closed: bool
    verdict: str        # '' | 'agent_cleared' | 'agent_condemned'
    reason: str
    stakes: dict[str, list[int]]  # address -> [amount, side(0=vouch,1=accuse)]
    claimed: dict[str, bool]
    # audit trail of AI-verified review scores
    reviews: list[str]

    def __init__(self, agent: str, agent_name: str, service_summary: str):
        self.agent = agent
        self.agent_name = agent_name
        self.service_summary = service_summary
        self.vouch_pool = 0
        self.accuse_pool = 0
        self.closed = False
        self.verdict = ''
        self.reason = ''
        self.stakes = {}
        self.claimed = {}
        self.reviews = []

    @gl.public.write.payable
    def vouch(self, note: str) -> None:
        """Stake value FOR the agent's good behavior, with a note."""
        self._stake(note, accuse=False)

    @gl.public.write.payable
    def accuse(self, note: str) -> None:
        """Stake value AGAINST the agent, with evidence in the note."""
        self._stake(note, accuse=True)

    def _stake(self, note: str, accuse: bool) -> None:
        if self.closed:
            raise Exception('challenge window closed')
        amt = gl.message.value
        if amt <= 0:
            raise Exception('stake must be positive')
        key = gl.message.caller
        self.stakes[key] = [amt, 1 if accuse else 0]
        if accuse:
            self.accuse_pool += amt
        else:
            self.vouch_pool += amt

    @gl.public.write
    def add_ai_verified_review(self, interaction_transcript: str) -> None:
        """A past customer submits the transcript of an interaction with the
        agent; the validators' model grades the agent's conduct 0-10."""
        if self.closed:
            raise Exception('challenge window closed')
        prompt = f"""You are grading one interaction between a customer and an AI agent.

AGENT: {self.agent_name} — {self.service_summary}

INTERACTION TRANSCRIPT:
{interaction_transcript}

Grade the agent's conduct 0-10 (10 = flawless, honest, competent; 0 = deceptive,
harmful, incompetent). Answer with JSON exactly:
{{"score": <0-10>, "justification": "<one sentence>"}}
"""
        res = gl.eq_principle.prompt_compatible(prompt)
        verdict = json.loads(res)
        score = verdict.get('score')
        if not isinstance(score, int) or not 0 <= score <= 10:
            raise Exception('adjudicator returned an invalid score')
        self.reviews.append(json.dumps({'score': score, 'why': verdict.get('justify', verdict.get('justification', ''))}))

    @gl.public.write
    def close_challenge(self) -> None:
        """End the window. If accusations exist, the validators' model weighs
        the accumulated evidence and rules on the agent."""
        if self.closed:
            raise Exception('already closed')
        self.closed = True
        if self.accuse_pool == 0:
            self.verdict = 'agent_cleared'
            self.reason = 'no accusations were staked'
            return

        prompt = f"""You are adjudicating an agent-reputation challenge.

AGENT: {self.agent_name} — {self.service_summary}
AI-VERIFIED REVIEW SCORES ON RECORD: {json.dumps(self.reviews)}

Vouching stakers back the agent; accusing stakers backed the accusations with
stake. Rule on whether the accusations are substantiated. Answer with JSON
exactly: {{"verdict": "agent_cleared" | "agent_condemned", "reason": "<one sentence>"}}
"""
        res = gl.eq_principle.prompt_compatible(prompt)
        verdict = json.loads(res)
        if verdict.get('verdict') not in ('agent_cleared', 'agent_condemned'):
            raise Exception('adjudicator returned an invalid verdict')
        self.verdict = verdict['verdict']
        self.reason = verdict.get('reason', '')

    @gl.public.write
    def claim(self) -> None:
        """Vouchers win if the agent is cleared; accusers win if condemned."""
        if not self.closed:
            raise Exception('challenge still open')
        key = gl.message.caller
        if self.claimed.get(key):
            raise Exception('already claimed')
        row = self.stakes.get(key)
        if not row:
            raise Exception('nothing staked')
        amt, side = row
        cleared = self.verdict == 'agent_cleared'
        win_pool = self.vouch_pool if cleared else self.accuse_pool
        lose_pool = self.accuse_pool if cleared else self.vouch_pool
        my_side_wins = (side == 0) == cleared
        if not my_side_wins:
            raise Exception('you are on the losing side')
        if win_pool == 0:
            raise Exception('no pool')
        payout = amt + (amt * lose_pool) // win_pool
        self.claimed[key] = True
        gl.message.caller.send(payout)

    @gl.public.view
    def reputation(self) -> str:
        """The agent's public reputation line: pools, verdict, review mean."""
        scores = [json.loads(r)['score'] for r in self.reviews]
        mean = sum(scores) / len(scores) if scores else None
        return json.dumps({
            'agent': self.agent,
            'name': self.agent_name,
            'vouch_pool': self.vouch_pool,
            'accuse_pool': self.accuse_pool,
            'closed': self.closed,
            'verdict': self.verdict,
            'reviews': len(scores),
            'mean_review_score': mean,
        })
