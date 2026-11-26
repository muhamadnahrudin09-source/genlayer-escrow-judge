# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class EscrowJudge(gl.Contract):
    """
    Trustless escrow for agent-to-agent deals.

    A buyer locks value for a deliverable described in natural language.
    When the buyer and the seller disagree about whether the deliverable
    satisfies the terms, the contract asks the validators' model to judge
    the evidence against the agreed terms (Equivalence Principle) and
    releases the funds to the winner. No human arbitrator, no oracle.
    """

    # ---- state ----
    buyer: str
    seller: str
    terms: str          # natural-language deliverable terms agreed up front
    amount: int         # wei locked in escrow
    released: bool      # has the escrow been settled?
    winner: str         # '' until settled, then 'buyer' or 'seller'
    verdict_reason: str # the adjudicator's justification, stored for audit
    dispute_open: bool

    def __init__(self, buyer: str, seller: str, terms: str):
        self.buyer = buyer
        self.seller = seller
        self.terms = terms
        self.amount = 0
        self.released = False
        self.winner = ''
        self.verdict_reason = ''
        self.dispute_open = False

    # ---- lifecycle ----

    @gl.public.write.payable
    def deposit(self) -> None:
        """Buyer funds the escrow. Only allowed while unset and unfunded."""
        if self.released:
            raise Exception('escrow already settled')
        if self.amount > 0:
            raise Exception('escrow already funded')
        self.amount = gl.message.value

    @gl.public.write
    def open_dispute(self) -> None:
        """Either party disputes: the deliverable was delivered (seller) or not (buyer)."""
        if self.released:
            raise Exception('escrow already settled')
        if self.amount == 0:
            raise Exception('escrow is not funded')
        if self.dispute_open:
            raise Exception('dispute already open')
        self.dispute_open = True

    @gl.public.write
    def resolve(self, buyer_evidence: str, seller_evidence: str) -> None:
        """
        Adjudicate the dispute. Both parties attach their evidence as free
        text (links to files, delivery receipts, communications). The
        validators' model reads the original terms and both sides of the
        story, then rules for the buyer or the seller.
        """
        if not self.dispute_open:
            raise Exception('no dispute to resolve')
        if self.released:
            raise Exception('escrow already settled')

        prompt = f"""You are a neutral escrow adjudicator for a deal between a BUYER and a SELLER.

AGREED TERMS (the deliverable the buyer paid for):
{self.terms}

BUYER EVIDENCE (argues the deliverable was NOT properly delivered):
{buyer_evidence}

SELLER EVIDENCE (argues the deliverable WAS properly delivered):
{seller_evidence}

Rule strictly on the evidence. Answer with JSON exactly in this shape:
{{"winner": "buyer" | "seller", "reason": "<one sentence justification>"}}
"""
        res = gl.eq_principle.prompt_compatible(prompt)
        verdict = json.loads(res)
        if verdict.get('winner') not in ('buyer', 'seller'):
            raise Exception('adjudicator returned an invalid verdict')

        self.winner = verdict['winner']
        self.verdict_reason = verdict.get('reason', '')
        self.released = True
        self.dispute_open = False

    @gl.public.write
    def settle_amicable(self, to_buyer: bool) -> None:
        """Before any dispute: both parties can settle directly, no judge needed."""
        if self.released:
            raise Exception('escrow already settled')
        if self.amount == 0:
            raise Exception('escrow is not funded')
        if self.dispute_open:
            raise Exception('dispute is open, use resolve()')
        self.winner = 'buyer' if to_buyer else 'seller'
        self.released = True

    # ---- views ----

    @gl.public.view
    def status(self) -> str:
        if not self.amount:
            return 'awaiting_funding'
        if self.released:
            return f'settled:{self.winner}'
        if self.dispute_open:
            return 'disputed'
        return 'funded'

    @gl.public.view
    def get_details(self) -> str:
        return json.dumps({
            'buyer': self.buyer,
            'seller': self.seller,
            'terms': self.terms,
            'amount': self.amount,
            'status': self.status(),
            'winner': self.winner,
            'verdict_reason': self.verdict_reason,
        })
