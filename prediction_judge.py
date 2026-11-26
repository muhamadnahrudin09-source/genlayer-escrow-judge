# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class PredictionJudge(gl.Contract):
    """
    A prediction market whose questions are plain language and whose
    outcomes are decided by GenLayer's AI validators — things oracles
    cannot parse: 'Will the COP31 final text include a fossil-fuel
    roadmap?', 'Did the talks overrun their deadline?'
    """

    question: str
    rules: str           # what counts as YES, agreed when the market opens
    closes_at: int       # unix seconds; betting stops then
    yes_pool: int
    no_pool: int
    resolved: bool
    outcome: str         # '' | 'yes' | 'no'
    reason: str
    # stakes: address -> amount
    stakes: dict[str, int]
    claimed: dict[str, bool]

    def __init__(self, question: str, rules: str, closes_at: int):
        self.question = question
        self.rules = rules
        self.closes_at = closes_at
        self.yes_pool = 0
        self.no_pool = 0
        self.resolved = False
        self.outcome = ''
        self.reason = ''
        self.stakes = {}
        self.claimed = {}

    @gl.public.write.payable
    def bet_yes(self) -> None:
        self._bet()

    @gl.public.write.payable
    def bet_no(self) -> None:
        self._bet(no=True)

    def _bet(self, no: bool = False) -> None:
        if self.resolved:
            raise Exception('market resolved')
        if gl.message.timestamp >= self.closes_at:
            raise Exception('market closed')
        amt = gl.message.value
        if amt <= 0:
            raise Exception('bet must be positive')
        key = gl.message.caller
        self.stakes[key] = (self.stakes.get(key) or 0) + amt
        if no:
            self.no_pool += amt
        else:
            self.yes_pool += amt

    @gl.public.write
    def resolve(self) -> None:
        """Anyone may trigger resolution after close; the validators'
        model reads the question, the rules and live web context."""
        if self.resolved:
            raise Exception('already resolved')
        if gl.message.timestamp < self.closes_at:
            raise Exception('market still open')
        if self.yes_pool + self.no_pool == 0:
            raise Exception('no stakes')

        prompt = f"""You are the resolution authority of a prediction market.

QUESTION: {self.question}

RESOLUTION RULES (agreed when the market opened):
{self.rules}

Using everything you know, and searching the web if needed, decide whether
the question's answer is YES or NO under the rules. Answer with JSON exactly:
{{"outcome": "yes" | "no", "reason": "<one sentence citing the deciding fact>"}}
"""
        res = gl.eq_principle.prompt_compatible(prompt)
        verdict = json.loads(res)
        if verdict.get('outcome') not in ('yes', 'no'):
            raise Exception('adjudicator returned an invalid outcome')
        self.outcome = verdict['outcome']
        self.reason = verdict.get('reason', '')
        self.resolved = True

    @gl.public.write
    def claim(self) -> None:
        """Winners withdraw their pro-rata share of the full pool."""
        if not self.resolved:
            raise Exception('market not resolved yet')
        key = gl.message.caller
        if self.claimed.get(key):
            raise Exception('already claimed')
        stake = self.stakes.get(key) or 0
        if stake == 0:
            raise Exception('nothing staked')
        pool = self.yes_pool if self.outcome == 'yes' else self.no_pool
        loser_pool = self.no_pool if self.outcome == 'yes' else self.yes_pool
        if pool == 0:
            raise Exception('you are on the losing side')
        payout = stake + (stake * loser_pool) // pool
        self.claimed[key] = True
        gl.message.caller.send(payout)

    @gl.public.view
    def odds(self) -> str:
        total = self.yes_pool + self.no_pool
        if total == 0:
            return json.dumps({'yes': 0.5, 'no': 0.5})
        return json.dumps({
            'yes': self.yes_pool / total,
            'no': self.no_pool / total,
        })

    @gl.public.view
    def details(self) -> str:
        return json.dumps({
            'question': self.question,
            'rules': self.rules,
            'closes_at': self.closes_at,
            'yes_pool': self.yes_pool,
            'no_pool': self.no_pool,
            'resolved': self.resolved,
            'outcome': self.outcome,
            'reason': self.reason,
        })
