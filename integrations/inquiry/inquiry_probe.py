"""RR59: a declared inspection trigger, separate from acceptance certificates.

This is one projected-response trigger in RR58's one-dimensional source family.
It is not a measured model of the LLM event that motivated the investigation.
Only the frame that has arrived is supplied; no target or later frame is read.
"""
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'free_numbers'))
import deferred as d


@dataclass(frozen=True)
class InspectionSignal:
    pair_digest: str
    scope: d.Scope
    factor: tuple
    requested: bool

    @property
    def digest(self):
        return d.fingerprint((self.pair_digest,self.scope.contexts,self.scope.observation,
                              self.scope.entry,self.factor,self.requested))


def initiate(pair,scope):
    """Request inspection when an arrived kernel exposes the retained direction.

    K_original(Y)-K_reference(Y) = shift * factor(Y).  We test nonzero
    factors without expanding that product or evaluating the original leaf.
    This answers a kernel question, not a closure or importance question.
    """
    if (type(pair) is not d.RetainedPair or type(scope) is not d.Scope
            or scope.observation!='kernel' or len(scope.contexts)!=1):
        raise ValueError('one retained pair and one arrived kernel observation are required')
    y=scope.contexts[0]
    if not d.regular(y,pair.original.library):
        raise ValueError('the arrived frame must be in the declared regular chart')
    values=d.base_responses(pair.original.library,y)
    factor=tuple(sum(v[j]*weight for v,weight in zip(values,pair.direction)) for j in range(4))
    return InspectionSignal(pair.digest,scope,factor,bool(pair.shift and any(factor)))


def verify_signal(pair,scope,signal):
    if type(signal) is not InspectionSignal or signal!=initiate(pair,scope):
        raise ValueError('the pair, arrived frame, entry or initiation evidence changed')
    return True
