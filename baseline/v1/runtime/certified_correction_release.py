"""RR42: compute -> execute a lower cell -> publish -> consume upstairs.

Declared extension: a lower preparation lane continues the actual committed
level-one tape after context arrival while the level-two open tail waits.
This resource and its publication rule are supplied, not derived from v18.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from same_level_continuation import (
    fixtures, start, append, no_repair_certificate, AffineLetter, ExecutionState,
    UpperState, NEG_ONE, decode, qmul, inverse, encode,
)
from fixed_result_compatibility import generate_request
from closed_boundary_loop import fixture as primitive_fixture
from recursive_upper_decoder import (
    action_matrix, solve, rref, regular, kernel, resume, promote_word,
)


def active_leaf(leaf):
    x=[[sum(w*op.source.endpoint[i][j] for w,op in zip(leaf.weights,leaf.library))
        for j in range(3)] for i in range(3)]
    return any(x[i][j]!=(Q(1,3) if i==j else 0) for i in range(3) for j in range(3))


def correction_leaf(y,library,wanted):
    frame=[list(row) for row in zip(*(
        [op.source.endpoint[i][j] for i,j in ((0,0),(1,1),(2,2),(0,1),(0,2),(1,2))]
        for op in library))]
    if len(rref(frame)[1])!=6 or not regular(y,library):
        raise ValueError('the full six-generator frame and a regular context are required')
    inverse(wanted)
    matrix=action_matrix(y,library)
    weights=solve(matrix,[Q(1),*wanted])
    leaf=AffineLetter(tuple(weights),library)
    if not active_leaf(leaf):
        # In the full frame, a nonzero normalization/action-null direction
        # changes X and gives activity without changing the required value.
        reduced,pivots=rref(matrix)
        free=next(j for j in range(6) if j not in pivots)
        delta=[Q(0)]*6;delta[free]=Q(1)
        for row,pivot in zip(reduced,pivots):
            delta[pivot]=-row[free]
        leaf=AffineLetter(tuple(a+b for a,b in zip(weights,delta)),library)
    assert active_leaf(leaf) and leaf.kernel(y)==tuple(wanted)
    return leaf


@dataclass(frozen=True)
class CorrectionPlan:
    upper_snapshot: object
    lower_start: ExecutionState
    speculative_response: tuple
    wanted_action: tuple
    leaf: AffineLetter
    lower_target: tuple


@dataclass(frozen=True)
class LowerIssue:
    plan: CorrectionPlan
    decoded: object
    operation: object
    closed_at: int


@dataclass(frozen=True)
class StageEvent:
    index: int
    kind: str
    lower_state: ExecutionState
    upper_state: ExecutionState
    stock: tuple


@dataclass(frozen=True)
class CorrectionSession:
    original_trial: object
    lower: ExecutionState
    upper: object
    stock: tuple
    phase: str
    events: tuple
    plan: object=None
    issue: object=None
    next_request: object=None


def record(session,kind,**changes):
    fresh=replace(session,**changes)
    event=StageEvent(len(session.events),kind,fresh.lower,fresh.upper.state,fresh.stock)
    return replace(fresh,events=session.events+(event,))


def open_session(trial):
    if trial.decoded.outputs or trial.decoded.stop!='NoTerminalPrefix':
        raise ValueError('an actual open upper tail is required')
    # Two typed clocks share this committed boundary, not two candidate pasts.
    lower=trial.arrival.staged
    if any(letter.level!=1 for letter in lower.executed_word):
        raise ValueError('the supplied producer must continue a committed level-one tape')
    event=StageEvent(0,'context-arrived',lower,trial.decoded.state,trial.experiment.stock)
    return CorrectionSession(trial,lower,trial.decoded,trial.experiment.stock,'OPEN',(event,))


def plan_correction(session):
    if session.phase!='OPEN':
        raise ValueError('a plan can only be made for the current open session')
    y=session.upper.state.live.context
    response=tuple(qmul(kernel(session.upper.tail,y),session.upper.state.live.accumulated))
    if not any(response):
        raise ValueError('zero cannot be compensated by a later left multiplier')
    wanted=tuple(qmul(session.upper.boundaries[0],inverse(response)))
    library=session.original_trial.experiment.request.operation.leaves()[0].library
    leaf=correction_leaf(y,library,wanted)
    lower_target=tuple(qmul(wanted,session.lower.live.accumulated))
    plan=CorrectionPlan(session.upper,session.lower,response,wanted,leaf,lower_target)
    return record(session,'correction-planned',phase='PLANNED',plan=plan)


def execute_lower(session):
    if session.phase!='PLANNED' or session.plan.lower_start!=session.lower:
        raise ValueError('the planned lower start must still be the actual producer state')
    plan=session.plan
    decoded=decode(session.lower,(plan.leaf,),(plan.lower_target,))
    if len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries:
        raise ValueError('the lower preparation cell failed to close')
    operation=decoded.outputs[0]
    if operation.level!=2 or operation.kernel(session.lower.live.context)!=plan.wanted_action:
        raise ValueError('lower certification did not produce the required same-level action')
    issue=LowerIssue(plan,decoded,operation,len(session.events))
    # The source process genuinely executes: its tape grows by one leaf.
    # Certification creates the object; publication to the consumer is later.
    return record(session,'lower-cell-closed',phase='LOWER_CLOSED',
                  lower=decoded.state,issue=issue)


def publish(session):
    if session.phase!='LOWER_CLOSED' or session.issue.closed_at>=len(session.events):
        raise ValueError('a previously executed and certified lower cell is required')
    issue=session.issue
    if (issue.decoded.state!=session.lower or issue.operation.cell.start!=issue.plan.lower_start
            or promote_word(issue.operation.cell)!=issue.operation
            or issue.operation.level!=session.original_trial.experiment.request.operation.level):
        raise ValueError('issue certificate or lineage does not match the producer')
    return record(session,'same-level-operation-published',phase='AVAILABLE',
                  stock=session.stock+(issue.operation,))


def require_available(session,operation):
    if operation.level!=session.original_trial.experiment.request.operation.level:
        raise ValueError('the consumer only accepts the same scale')
    if operation not in session.stock:
        raise ValueError('this operation has not been published to the consumer')


def consume(session):
    if session.phase!='AVAILABLE' or session.upper!=session.plan.upper_snapshot:
        raise ValueError('the fixed pending upper prefix must await the published correction')
    operation=session.issue.operation
    require_available(session,operation)
    upper=resume(session.upper,extra_word=(operation,))
    if len(upper.outputs)!=1 or upper.tail or upper.boundaries:
        raise ValueError('the upper compensation cell failed to close')
    request=generate_request(upper.outputs[0],session.original_trial.experiment.request.result)
    return record(session,'upper-cell-closed',phase='CLOSED',upper=upper,next_request=request)


def complete(trial):
    return consume(publish(execute_lower(plan_correction(open_session(trial)))))


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    ab,changed,first,second,zero_context=fixtures()
    trials=[start(ab,second),start(changed,first)]
    check('the original sealed-stock impossibility remains intact before stock extension',
          all(no_repair_certificate(trial)['kind']=='rational-valuation' for trial in trials)
          and all(append(trial,trial.experiment.stock*2).decoded.stop=='NoTerminalPrefix' for trial in trials))
    sessions=[];gate_rejections=[]
    for trial in trials:
        opened=open_session(trial)
        planned=plan_correction(opened)
        assert planned.lower==opened.lower and planned.upper==opened.upper and planned.stock==opened.stock
        try:
            require_available(planned,planned.plan.leaf)
        except ValueError:
            gate_rejections.append('planned-level-one-rejected')
        issued=execute_lower(planned)
        assert issued.upper==opened.upper and issued.stock==opened.stock
        try:
            require_available(issued,issued.issue.operation)
        except ValueError:
            gate_rejections.append('certified-unpublished-rejected')
        available=publish(issued)
        assert available.upper==opened.upper and available.lower==issued.lower
        require_available(available,available.issue.operation)
        sessions.append(consume(available))
    check('calculation, lower closure and publication are separate availability stages',
          len(gate_rejections)==4 and all(len(s.stock)==5 for s in sessions),rejections=gate_rejections,
          event_order=[e.kind for e in sessions[0].events])
    check('lower production extends the actual committed tape without consuming the upper tail',
          all(len(s.issue.decoded.state.executed_word)==len(s.original_trial.arrival.staged.executed_word)+1
              and s.issue.operation.cell.start==s.original_trial.arrival.staged
              and s.issue.operation.cell.beta==(s.plan.leaf,)
              and s.issue.operation.cell.endpoint==s.lower for s in sessions),
          private_lower_targets=[s.plan.lower_target for s in sessions],lower_letters_executed=1)
    check('both RR40 failures close through a newly certified same-level suffix after publication',
          [s.plan.wanted_action[0] for s in sessions]==[Q(-1,6),Q(-5,9)]
          and all(s.phase=='CLOSED' and s.upper.state.live.accumulated==tuple(NEG_ONE)
                  and len(s.upper.outputs[0].cell.beta)==2 and s.upper.outputs[0].level==3 for s in sessions),
          consumer_result=tuple(NEG_ONE),required_actions=[s.plan.wanted_action for s in sessions])
    check('compensation preserves fixed result, arrived context and original designated head',
          all(s.upper.outputs[0].cell.beta[0]==s.original_trial.experiment.request.operation
              and s.upper.state.live.context==s.original_trial.arrival.arrived_context
              and s.upper.outputs[0].cell.start==s.original_trial.arrival.staged
              and s.next_request.result==tuple(NEG_ONE) for s in sessions))
    for s in sessions:
        expected=decode(s.original_trial.arrival.staged,
                        s.original_trial.offered_word+(s.issue.operation,),(NEG_ONE,))
        assert expected==s.upper
        assert s.upper.state.executed_word==s.original_trial.arrival.staged.executed_word+(
            s.original_trial.experiment.request.operation,s.issue.operation)
    check('the original decoder exactly matches resumed same-level compensation',True,cases=2)
    check('publication history has strict logical ordering and keeps both actual clocks',
          all([e.index for e in s.events]==list(range(5))
              and all(e.upper_state==s.original_trial.arrival.staged for e in s.events[:-1])
              and s.events[2].lower_state==s.lower
              and s.events[2].stock==s.original_trial.experiment.stock
              and s.events[3].stock==s.stock for s in sessions),
          phases=['arrival','plan','lower execution and certification','publication','upper execution'])
    rejected=False
    try:
        plan_correction(open_session(start(ab,zero_context)))
    except ValueError:
        rejected=True
    check('the zero-absorbing boundary is not bypassed by the new lower producer',rejected)
    forbidden=0
    staged=execute_lower(plan_correction(open_session(trials[0])))
    for action in (lambda:consume(staged),lambda:publish(publish(staged)),
                   lambda:require_available(publish(staged),changed.request.operation)):
        try:
            action()
        except ValueError:
            forbidden+=1
    check('premature consumption, double publication and a different source branch are rejected',forbidden==3)
    # A scalar -1/3 action need not be promoted as a degenerate constant:
    # the full-frame null direction retains its response and adds activity.
    _,_,_,policy=primitive_fixture()
    matrix=action_matrix(policy.probe,ab.request.operation.leaves()[0].library)
    naive=AffineLetter(tuple(solve(matrix,[Q(1),Q(-1,3),0,0,0])),
                       ab.request.operation.leaves()[0].library)
    leaf=correction_leaf(policy.probe,ab.request.operation.leaves()[0].library,(Q(-1,3),0,0,0))
    check('a required scalar value can have an active certified-source candidate',
          not active_leaf(naive) and active_leaf(leaf) and leaf.kernel(policy.probe)==(Q(-1,3),0,0,0),
          reason='a normalization/action-null correction preserves the value but avoids a constant source')
    nonreal=complete(start(ab,policy.probe))
    check('the same certified publication process compensates a nonreal quaternion response',
          any(nonreal.plan.speculative_response[1:]) and any(nonreal.plan.wanted_action[1:])
          and nonreal.upper.state.live.accumulated==tuple(NEG_ONE),
          response=nonreal.plan.speculative_response,correction=nonreal.plan.wanted_action)
    check('a published correction retains its full source meaning at later contexts',
          all(s.issue.operation.kernel(first)==s.plan.leaf.kernel(first)
              and s.issue.operation.kernel(second)==s.plan.leaf.kernel(second)
              and s.issue.operation.cell.start.live.context==s.original_trial.arrival.arrived_context for s in sessions))
    root=Path(__file__).resolve().parent
    paths=['certified_correction_release.py','test_certified_correction_release.py',
           'same_level_continuation.py','test_same_level_continuation.py',
           'fixed_result_compatibility.py','test_fixed_result_compatibility.py',
           'closed_boundary_loop.py','test_closed_boundary_loop.py',
           'recursive_upper_decoder.py','test_recursive_upper_decoder.py',
           'certified_cell_bridge.py','test_certified_cell_bridge.py',
           'residual_extraction_transport.py','future_existence_residual.py',
           'vendor/two_flower_kernel_certificate.py','vendor/internal_port_certificate.py']
    return dict(note='RR42',passed=True,groups=len(checks),checks=checks,
                source_base_commit='9b447b96a7f287ca3b0c1254f351d54c1a136748',
                declared_extension='continued lower preparation lane and explicit same-level publication gate',
                supplied_resources=['six-generator affine frame','regular arrived context',
                                    'continued lower clock','private lower boundary','publication rule'],
                correction_status='executed one lower leaf, certified level-two operation, published, then consumed',
                fixed_consumer_result=tuple(NEG_ONE),old_stock_size=4,new_stock_size=5,
                limits=['RR41 stock obstruction is preserved for the original sealed stock',
                        'the producer resource and publication rule are not derived from v18 Gamma',
                        'no autonomous context source or future-origin C derived',
                        'zero remains uncompensable by all later left multipliers'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('certified_correction_release_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'])))
