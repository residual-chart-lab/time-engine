"""RR41: append-only compensation by a sealed stock of same-level operations.

The stock comes from one committed preparation path before context arrival.
Replacing the designated head is a separate counterfactual. Fresh primitive
affine corrections are diagnostic algebra only, not available stock.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from fixed_result_compatibility import (
    fixture, context, generate_request, arrive, AffineLetter, ExecutionState,
    UpperState, NEG_ONE, certify_word, promote_word, decode, qmul, inverse, encode,
)
from recursive_upper_decoder import resume, action_matrix, solve, regular


@dataclass(frozen=True)
class PreparedPast:
    initial: ExecutionState
    operations: tuple

    def __post_init__(self):
        object.__setattr__(self,'operations',tuple(self.operations))
        cursor=self.initial
        for operation in self.operations:
            if promote_word(operation.cell)!=operation or operation.cell.start!=cursor:
                raise ValueError('stock must come from one actually committed source path')
            if operation.level!=2:
                raise ValueError('this experiment uses level-two stock')
            cursor=operation.cell.endpoint

    @property
    def endpoint(self):
        return self.initial if not self.operations else self.operations[-1].cell.endpoint


@dataclass(frozen=True)
class Experiment:
    prepared: PreparedPast
    request: object

    def __post_init__(self):
        if self.request.operation.cell.start!=self.prepared.endpoint:
            raise ValueError('designated head must follow the same committed preparation')
        if self.request.operation.level!=2:
            raise ValueError('level-two designated head required')

    @property
    def stock(self):
        # The head's own source cell has also closed before arrival.
        return self.prepared.operations+(self.request.operation,)

    def check_available(self,word):
        for operation in word:
            if operation.level!=self.request.operation.level:
                raise ValueError('a correction at a different scale is not admissible')
            if operation not in self.stock:
                raise ValueError('certificate alone is insufficient: operation was not in the sealed stock')


@dataclass(frozen=True)
class Continuation:
    experiment: Experiment
    arrival: object
    offered_word: tuple
    decoded: object


def start(experiment,later_context):
    attempt=arrive(experiment.request,later_context)
    if attempt.decoded is None:
        raise ValueError('this continuation experiment requires the regular chart')
    return Continuation(experiment,attempt,(experiment.request.operation,),attempt.decoded)


def append(result,extra_word):
    extra=tuple(extra_word)
    result.experiment.check_available(extra)
    if result.decoded.outputs:
        raise ValueError('the current boundary is already certified; open a new request instead')
    fresh=resume(result.decoded,extra_word=extra)
    return Continuation(result.experiment,result.arrival,result.offered_word+extra,fresh)


def replace_head(result,replacement_word):
    """Separate comparison: does NOT count as append-only compensation."""
    word=tuple(replacement_word)
    if not word:
        raise ValueError('a nonempty replacement word is required')
    result.experiment.check_available(word)
    return decode(result.arrival.staged,word,(result.experiment.request.result,))


def valuation(value,prime=3):
    value=Q(value)
    if prime!=3:
        raise ValueError('the present exact certificate uses prime three')
    if not value:
        return None
    n=abs(value.numerator);d=value.denominator;v=0
    while n%prime==0:
        n//=prime;v+=1
    while d%prime==0:
        d//=prime;v-=1
    return v


def no_repair_certificate(result):
    head_response=result.arrival.response
    if not any(head_response):
        return dict(kind='zero-absorbing',scope='any subsequent left-multiplication actions',
                    reason='a quaternion multiplier times zero remains zero')
    wanted=tuple(qmul(result.experiment.request.result,inverse(head_response)))
    values=[operation.kernel(result.arrival.arrived_context) for operation in result.experiment.stock]
    if any(wanted[1:]) or any(any(value[1:]) for value in values):
        return None
    required=valuation(wanted[0])
    valuations=[valuation(value[0]) for value in values]
    if required is not None and required<0 and all(v is None or v>=0 for v in valuations):
        return dict(kind='rational-valuation',prime=3,required_multiplier=wanted[0],
                    required_valuation=required,available_values=[v[0] for v in values],
                    available_valuations=valuations,scope='every finite suffix over the sealed stock',
                    reason='nonzero stock products add nonnegative valuations; zero products cannot reach F')
    return None


def diagnostic_primitive_correction(result):
    """New post-arrival algebra, explicitly unpromoted and unavailable."""
    response=result.arrival.response
    wanted=tuple(qmul(result.experiment.request.result,inverse(response)))
    library=result.experiment.request.operation.leaves()[0].library
    coefficients=solve(action_matrix(result.arrival.arrived_context,library),[Q(1),*wanted])
    leaf=AffineLetter(tuple(coefficients),library)
    assert leaf.kernel(result.arrival.arrived_context)==wanted
    return leaf


def fixtures():
    initial,a,b,_=fixture()
    c=AffineLetter((0,0,1,0,0,0),a.library)
    # Public preparation, independent of any later Y; ABC takes 2/5 to 1.
    preparation_start=ExecutionState(UpperState(initial.live.context,(Q(2,5),Q(0),Q(0),Q(0))))
    cursor=preparation_start;operations=[]
    for leaf,target in zip((a,b,c),(Q(4,5),Q(-2,5),Q(1))):
        operation=promote_word(certify_word(cursor,(leaf,),(target,Q(0),Q(0),Q(0))))
        operations.append(operation);cursor=operation.cell.endpoint
    prepared=PreparedPast(preparation_start,tuple(operations))
    bp=AffineLetter((Q(2,5),Q(1,10),Q(1,2),0,0,0),a.library)
    experiments=[]
    # Two separate runs from one common preparation, not a pooled branch stock.
    for leaf in (b,bp):
        source=promote_word(certify_word(prepared.endpoint,(a,leaf),NEG_ONE))
        experiments.append(Experiment(prepared,generate_request(source)))
    first=context([[Q(3,2),0,0],[0,Q(3,4),0],[0,0,Q(-5,4)]])
    second=context([[Q(3,2),0,0],[0,-1,0],[0,0,Q(1,2)]])
    zero_context=context([[Q(1,2),0,0],[0,Q(3,2),0],[0,0,-1]])
    return experiments[0],experiments[1],first,second,zero_context


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    ab,changed,first,second,zero_context=fixtures()
    stock=ab.prepared.operations
    check('same-level stock is certified along one committed path before later-context input',
          ab.prepared==changed.prepared and ab.prepared.endpoint.live.accumulated==(1,0,0,0)
          and all(op.level==2 for op in ab.stock+changed.stock)
          and ab.request.inherited.live==changed.request.inherited.live,
          preparation_initial=ab.prepared.initial.live.accumulated,
          preparation_targets=[op.cell.target for op in stock],stock_size=4,level=2)
    canonical=ab.prepared.endpoint.live.context
    open_trial=start(ab,canonical)
    repaired=append(open_trial,stock[:2])
    check('available same-level suffix repairs an open designated head without changing it',
          open_trial.arrival.response==(1,0,0,0) and not open_trial.decoded.outputs
          and repaired.offered_word[0]==ab.request.operation
          and len(repaired.decoded.outputs)==1 and len(repaired.decoded.outputs[0].cell.beta)==3
          and repaired.decoded.state.live.accumulated==tuple(NEG_ONE)
          and repaired.decoded.outputs[0].level==3,
          trial_states=[(1,0,0,0),(2,0,0,0),(-1,0,0,0)],suffix='U_A,U_B')
    split=append(append(open_trial,stock[:1]),stock[1:2])
    check('append-and-resume preserves the mandatory prefix and matches one-shot decoding',
          split==repaired and repaired.decoded==decode(repaired.arrival.staged,repaired.offered_word,(NEG_ONE,))
          and open_trial.decoded.state==open_trial.arrival.staged)
    reused=append(open_trial,(ab.request.operation,))
    check('reusing the already certified head as a later same-level letter is a distinct valid suffix',
          len(reused.decoded.outputs)==1 and len(reused.decoded.outputs[0].cell.beta)==2,
          suffix='M_AB',terminal_length=2)
    failures=[start(ab,second),start(changed,first)]
    certificates=[no_repair_certificate(result) for result in failures]
    check('both RR40 failures have all-length non-repair certificates for this sealed stock',
          [result.arrival.response[0] for result in failures]==[Q(6),Q(9,5)]
          and [certificate['required_valuation'] for certificate in certificates]==[-1,-2]
          and all(certificate['kind']=='rational-valuation' for certificate in certificates),
          certificates=certificates)
    for result in failures:
        expanded=append(result,result.experiment.stock*4)
        assert expanded.decoded.stop=='NoTerminalPrefix'
        assert expanded.decoded.state==result.arrival.staged
        assert len(expanded.decoded.tail)==17
    check('unclosed suffix trials never commit the speculative head or correction letters',True,
          tested_suffix_letters=16,scope='illustration; universal non-repair comes from valuation proof')
    replacement=replace_head(failures[1],stock[:2])
    check('replacement can succeed where append-only compensation is impossible',
          len(replacement.outputs)==1 and replacement.state.live.accumulated==tuple(NEG_ONE)
          and replacement.outputs[0].cell.beta==stock[:2]
          and no_repair_certificate(failures[1]) is not None,
          context=first,replacement='U_A,U_B',distinction='designated M_ABprime is absent in the replacement')
    illegal=[]
    for result in failures:
        leaf=diagnostic_primitive_correction(result)
        try:
            append(result,(leaf,))
        except ValueError:
            illegal.append(True)
        else:
            illegal.append(False)
        rejected=False
        try:
            decode(result.arrival.staged,(result.experiment.request.operation,leaf),(NEG_ONE,))
        except ValueError:
            rejected=True
        assert rejected
        assert tuple(qmul(leaf.kernel(result.arrival.arrived_context),result.arrival.response))==tuple(NEG_ONE)
    check('post-arrival level-one algebraic correction is rejected as legal level-two compensation',
          all(illegal),primitive_required_values=[Q(-1,6),Q(-5,9)],
          certification='not constructed or promoted as a new available correction operation')
    rejected=False
    try:
        append(failures[0],(changed.request.operation,))
    except ValueError:
        rejected=True
    check('an alternative source branch cannot be pooled into the actual available stock',rejected)
    zero_trial=start(ab,zero_context)
    zero_certificate=no_repair_certificate(zero_trial)
    zero_extension=append(zero_trial,ab.stock*4)
    check('zero trial state is absorbing even with arbitrary later left multipliers',
          regular(zero_context,ab.request.operation.leaves()[0].library)
          and zero_trial.arrival.response==(0,0,0,0)
          and zero_certificate['kind']=='zero-absorbing'
          and zero_extension.decoded.stop=='NoTerminalPrefix'
          and zero_extension.decoded.state==zero_trial.arrival.staged,
          regular_context=zero_context,proof=zero_certificate)
    check('a completed cell keeps its original committed preparation and designated source',
          repaired.decoded.outputs[0].cell.start==repaired.arrival.staged
          and repaired.decoded.outputs[0].cell.beta[0]==ab.request.operation
          and ab.request.operation.cell.start==ab.prepared.endpoint
          and ab.request.operation.cell.endpoint.live.context==canonical)
    root=Path(__file__).resolve().parent
    paths=['same_level_continuation.py','test_same_level_continuation.py',
           'fixed_result_compatibility.py','test_fixed_result_compatibility.py',
           'closed_boundary_loop.py','test_closed_boundary_loop.py',
           'recursive_upper_decoder.py','test_recursive_upper_decoder.py',
           'certified_cell_bridge.py','test_certified_cell_bridge.py',
           'residual_extraction_transport.py','future_existence_residual.py',
           'vendor/two_flower_kernel_certificate.py','vendor/internal_port_certificate.py']
    return dict(note='RR41',passed=True,groups=len(checks),checks=checks,
                source_base_commit='a7315f4f05572c650e8b55ea9b35b0110f385493',
                fixed_result=tuple(NEG_ONE),same_level_stock='U_A,U_B,U_C and the actual designated source M_D',
                temporal_rule='all available operations certified on one actual history before context arrival',
                compensation='append after the immutable designated head; no context or result change',
                proofs=['prime-three valuation obstruction for any finite stock suffix',
                        'zero is absorbing for every subsequent left-multiplication action'],
                limits=['stock is a declared actual finite inventory, not the entire v18 operation grammar',
                        'new post-arrival correction operations need separate construction and availability protocol',
                        'no autonomous context source or future-origin C derived'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('same_level_continuation_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'])))
