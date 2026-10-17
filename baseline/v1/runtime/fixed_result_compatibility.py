"""RR40: fixed-result constraints over later contexts, without selecting one.

Full response family: all signed symmetric trace-one contexts satisfying
K_D(Y) z_D^+ = F for the designated promoted action. Certified family also
requires the RR38 regular affine chart. Context arrival is an explicit event.
Neither family is the union over every possible later upper operation.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from pathlib import Path
from itertools import product
import hashlib
import json

from closed_boundary_loop import fixture
from recursive_upper_decoder import (
    AffineLetter, ExecutionState, UpperState, tuples, NEG_ONE, inverse,
    kernel, qmul, certify_word, promote_word, regular, decode, encode,
)
from future_existence_residual import boundary, lincomb, five_basis, zero


def context(value):
    y=tuple(tuple(Q(x) for x in row) for row in value)
    if (len(y)!=3 or any(len(row)!=3 for row in y)
            or any(y[i][j]!=y[j][i] for i in range(3) for j in range(3))
            or sum(y[i][i] for i in range(3))!=1):
        raise ValueError('a signed symmetric trace-one context is required')
    return y


@dataclass(frozen=True)
class FixedResultRequest:
    operation: object
    inherited: ExecutionState
    result: tuple

    def __post_init__(self):
        f=tuple(Q(x) for x in self.result)
        inverse(f)
        if promote_word(self.operation.cell)!=self.operation:
            raise ValueError('verified active phase-closure operation required')
        if self.inherited!=self.operation.cell.endpoint:
            raise ValueError('the actual certified endpoint must be inherited')
        inverse(self.inherited.live.accumulated)
        object.__setattr__(self,'result',f)

    @property
    def required_net_action(self):
        return tuple(qmul(self.result,inverse(self.inherited.live.accumulated)))

    def response(self,later_context):
        y=context(later_context)
        return tuple(qmul(self.operation.kernel(y),self.inherited.live.accumulated))

    def compatible(self,later_context):
        # This full response predicate has no regularity restriction.
        return self.response(later_context)==self.result

    def certifiable(self,later_context):
        y=context(later_context)
        library=self.operation.leaves()[0].library
        return self.compatible(y) and regular(y,library)


def generate_request(operation,result=NEG_ONE):
    """Partial application of a fixed-result relation; no future argument."""
    return FixedResultRequest(operation,operation.cell.endpoint,tuple(result))


@dataclass(frozen=True)
class ArrivalAttempt:
    request: FixedResultRequest
    arrived_context: tuple
    staged: ExecutionState
    response: tuple
    compatible: bool
    certifiable: bool
    decoded: object
    next_request: object
    status: str

    @property
    def actual_state(self):
        return self.staged if self.decoded is None else self.decoded.state


def arrive(request,later_context):
    """Explicit context renewal; do not reexecute the old source cell.

    A failed arrival still changes the live context. Its upper action remains
    unexecuted, exactly as in RR38's open suffix semantics.
    """
    y=context(later_context)
    staged=ExecutionState(UpperState(y,request.inherited.live.accumulated),
                          request.inherited.executed_word)
    response=request.response(y)
    compatible=request.compatible(y)
    certifiable=request.certifiable(y)
    if not regular(y,request.operation.leaves()[0].library):
        return ArrivalAttempt(request,y,staged,response,compatible,False,None,None,'OutsideCertifiedChart')
    result=decode(staged,(request.operation,),(request.result,))
    next_request=generate_request(result.outputs[0],request.result) if result.outputs else None
    return ArrivalAttempt(request,y,staged,response,compatible,certifiable,result,next_request,
                          'Closed' if result.outputs else 'NoTerminalPrefix')


def examples():
    initial,a,b,_=fixture()
    # Same live value as B at Y0, but a different exact diagonal boundary.
    bp=AffineLetter((Q(2,5),Q(1,10),Q(1,2),0,0,0),a.library)
    op=promote_word(certify_word(initial,(a,b),NEG_ONE))
    changed=promote_word(certify_word(initial,(a,bp),NEG_ONE))
    reversed_op=promote_word(certify_word(initial,(b,a),NEG_ONE))
    first=context([[Q(3,2),0,0],[0,Q(3,4),0],[0,0,Q(-5,4)]])
    second=context([[Q(3,2),0,0],[0,-1,0],[0,0,Q(1,2)]])
    return initial,op,changed,reversed_op,first,second


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    initial,op,changed,reversed_op,first,second=examples()
    r,rp,rr=(generate_request(o) for o in (op,changed,reversed_op))
    check('constraints are generated from certified records with one fixed result and no future value',
          r.result==rp.result==tuple(NEG_ONE) and r.required_net_action==rp.required_net_action==(1,0,0,0)
          and op.visible==changed.visible and r.inherited.live==rp.inherited.live,
          fixed_result=r.result,required_net_action=r.required_net_action)
    check('the two fixed-result families are nonempty and neither contains the other',
          r.compatible(first) and not rp.compatible(first)
          and rp.compatible(second) and not r.compatible(second)
          and r.certifiable(first) and rp.certifiable(second),
          first_context=first,first_outputs=[r.response(first),rp.response(first)],
          second_context=second,second_outputs=[r.response(second),rp.response(second)])
    records=[]
    for t in (Q(-2),Q(-1),Q(0),Q(3,4),Q(1),Q(2)):
        y=context([[Q(3,2),0,0],[0,t,0],[0,0,-Q(1,2)-t]])
        records.append(dict(t=t,ab_kernel=op.kernel(y),changed_kernel=changed.kernel(y),
                            ab_compatible=r.compatible(y),changed_compatible=rp.compatible(y)))
        assert op.kernel(y)==(4*t-2,0,0,0)
        assert changed.kernel(y)==(-Q(3,5)-Q(8,5)*t,0,0,0)
    check('one public line has exact different closure roots without restricting the full family',True,
          ab_root=Q(3,4),changed_root=Q(-1),line_samples=records)
    attempts=[arrive(request,y) for request in (r,rp) for y in (first,second)]
    check('compatible contexts execute the designated promoted operation through the original decoder',
          [x.status for x in attempts]==['Closed','NoTerminalPrefix','NoTerminalPrefix','Closed']
          and all(x.actual_state.live.accumulated==tuple(NEG_ONE) and x.decoded.outputs[0].level==3
                  for x in (attempts[0],attempts[3])),statuses=[x.status for x in attempts])
    for failed in attempts[1:3]:
        assert failed.actual_state==failed.staged
        assert failed.actual_state.live.context==failed.arrived_context
        assert failed.actual_state.executed_word==failed.request.inherited.executed_word
        assert failed.decoded.tail==(failed.request.operation,)
        assert failed.decoded.boundaries==(failed.request.result,)
        assert failed.next_request is None
    check('failed arrivals retain the arrived context but do not commit the unclosed upper action',True,
          failed_cases=2)
    first_success=attempts[0]
    next_success=arrive(first_success.next_request,first)
    check('success emits another content-free constraint and can close at the next scale',
          next_success.status=='Closed' and next_success.decoded.outputs[0].level==4
          and next_success.next_request.result==tuple(NEG_ONE)
          and len(next_success.actual_state.executed_word)==len(r.inherited.executed_word)+2,
          levels=[2,3,4])
    check('context arrival never reinterprets or mutates the old certified past',
          op.cell.start==initial and op.cell.endpoint.live.context==initial.live.context
          and first_success.staged.executed_word==op.cell.endpoint.executed_word
          and first_success.staged.live.accumulated==op.cell.endpoint.live.accumulated
          and first_success.staged.live.context!=op.cell.endpoint.live.context)
    samples=[context(boundary(lincomb(c,five_basis()))) for c in product((-1,0,1),repeat=5)]
    samples += [first,second,initial.live.context]
    for y in samples:
        assert r.compatible(y)==rr.compatible(y)
        assert r.compatible(y)==(op.kernel(y)==r.required_net_action)
        assert r.certifiable(y)==(r.compatible(y) and regular(y,op.leaves()[0].library))
    check('AB and BA have the same fixed central-result family despite different kernels',True,
          tested_contexts=len(samples),proof='ba=1 iff b=a^-1 iff ab=1 in the quaternion division algebra')
    erased=op.visible
    check('retaining only the visible net label destroys both nonempty families in this comparison',
          erased==tuple(NEG_ONE) and tuple(qmul(erased,r.inherited.live.accumulated))==(1,0,0,0)
          and (1,0,0,0)!=r.result and r.compatible(first) and rp.compatible(second),
          constant_label_response=(1,0,0,0),required_result=r.result)
    singular=context([[0,0,0],[0,0,0],[0,0,1]])
    singular_attempt=arrive(r,singular)
    check('full response compatibility and chart-certified execution are separate predicates',
          singular_attempt.status=='OutsideCertifiedChart'
          and singular_attempt.compatible and singular_attempt.decoded is None
          and not singular_attempt.certifiable
          and singular_attempt.actual_state.executed_word==r.inherited.executed_word,
          response_compatible_but_not_chart_certified=singular)
    bad=False
    try:
        FixedResultRequest(replace(op,visible=(1,0,0,0)),op.cell.endpoint,tuple(NEG_ONE))
    except ValueError:
        bad=True
    check('forged source labels cannot produce a valid constraint',bad)
    root=Path(__file__).resolve().parent
    paths=['fixed_result_compatibility.py','test_fixed_result_compatibility.py','closed_boundary_loop.py',
           'test_closed_boundary_loop.py','recursive_upper_decoder.py','test_recursive_upper_decoder.py',
           'certified_cell_bridge.py','test_certified_cell_bridge.py',
           'residual_extraction_transport.py','future_existence_residual.py',
           'vendor/two_flower_kernel_certificate.py','vendor/internal_port_certificate.py']
    return dict(note='RR40',passed=True,groups=len(checks),checks=checks,
                source_base_commit='71872f940c3b708ea00cd15d3772edd4a4c01398',
                full_family='all signed symmetric trace-one Y with K_D(Y) z_D^+ = F',
                certified_family='full family intersected with RR38 regular action chart',
                declared_extension='explicit later context arrival and one designated promoted operation',
                causal_status='history-preserving forward realization of compatibility, not future-origin C',
                limits=['F, live-context arrivals, and designated next-action protocol remain supplied',
                        'family is not the union over all possible later operations',
                        'no general v18 Gamma or autonomous context source derived'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('fixed_result_compatibility_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'])))
