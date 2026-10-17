"""RR39: a declared, forward boundary source coupled to the exact decoder.

SourcePolicy reads one certified closed operation, never an open input tail.
Its probe and readout are public model parameters, not future observations.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from recursive_upper_decoder import (
    AffineLetter, ExecutionState, UpperState, build_library, tuples, NEG_ONE,
    decode, certify_word, promote_word, kernel, qmul, inverse, encode,
)


@dataclass(frozen=True)
class SourceEvent:
    operation: object
    response: tuple
    signal: Q
    target: object


@dataclass(frozen=True)
class SourcePolicy:
    probe: tuple
    readout: tuple=(Q(0),Q(0),Q(1),Q(0))
    mode: str='polarity'

    def __post_init__(self):
        p=tuple(tuple(Q(x) for x in row) for row in self.probe)
        w=tuple(Q(x) for x in self.readout)
        if (len(p)!=3 or any(len(row)!=3 for row in p)
                or any(p[i][j]!=p[j][i] for i in range(3) for j in range(3))
                or sum(p[i][i] for i in range(3))!=1):
            raise ValueError('public probe must be a signed symmetric trace-one context')
        if len(w)!=4 or not any(w) or self.mode not in ('polarity','raw'):
            raise ValueError('nonzero readout and declared source mode required')
        object.__setattr__(self,'probe',p)
        object.__setattr__(self,'readout',w)

    def emit(self,operation):
        # Revalidate the full certificate; caller-supplied labels are insufficient.
        if promote_word(operation.cell)!=operation:
            raise ValueError('source requires a certified active closed operation')
        response=operation.kernel(self.probe)
        signal=sum(a*b for a,b in zip(self.readout,response))
        z=operation.cell.endpoint.live.accumulated
        if self.mode=='polarity':
            target=None if signal==0 else tuple((1 if signal>0 else -1)*x for x in z)
        else:
            target=tuple(qmul(response,z)) if any(response) else None
        return SourceEvent(operation,response,signal,target)


@dataclass(frozen=True)
class ClosedLoop:
    state: ExecutionState
    outputs: tuple
    tail: tuple
    pending: tuple
    issued: tuple
    events: tuple
    policy: SourcePolicy
    stop: str


def _drive(state,outputs,tail,pending,issued,events,policy):
    while True:
        if not tail:
            stop='InputExhausted'
            break
        if not pending:
            stop='SourceUndecided'
            break
        part=decode(state,tail,pending)
        if not part.outputs:
            stop=part.stop
            break
        assert len(part.outputs)==1 and not part.boundaries
        operation=part.outputs[0]
        state=part.state;tail=part.tail
        outputs=outputs+(operation,)
        event=policy.emit(operation)
        events=events+(event,)
        pending=() if event.target is None else (event.target,)
        if pending:
            issued=issued+pending
    return ClosedLoop(state,outputs,tail,pending,issued,events,policy,stop)


def start_loop(state,word,bootstrap,policy):
    target=tuple(Q(x) for x in bootstrap)
    inverse(target)
    return _drive(state,(),tuple(word),(target,),(target,),(),policy)


def extend_loop(result,extra_word=()):
    # Fixed source parameters; no reissuing old events or rewriting boundaries.
    return _drive(result.state,result.outputs,result.tail+tuple(extra_word),
                  result.pending,result.issued,result.events,result.policy)


def fixture():
    library=build_library()
    a=AffineLetter((1,0,0,0,0,0),library)
    b=AffineLetter((0,1,0,0,0,0),library)
    y=tuples([[Q(3,2),0,0],[0,Q(1,4),0],[0,0,Q(-3,4)]])
    probe=tuples([[Q(3,2),1,0],[1,Q(1,4),1],[0,1,Q(-3,4)]])
    return ExecutionState(UpperState(y)),a,b,SourcePolicy(probe)


def replay_matches(initial,result):
    old=initial.executed_word
    assert result.state.executed_word[:len(old)]==old
    fresh_word=result.state.executed_word[len(old):]+result.tail
    fixed=decode(initial,fresh_word,result.issued)
    return (fixed.state==result.state and fixed.outputs==result.outputs
            and fixed.tail==result.tail and fixed.boundaries==result.pending
            and fixed.stop==('BoundaryExhausted' if result.stop=='SourceUndecided' else result.stop))


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    initial,a,b,policy=fixture()
    word=(a,b)*8
    result=start_loop(initial,word,NEG_ONE,policy)
    lengths=[len(op.cell.beta) for op in result.outputs]
    check('closed exact residue generates the next boundary and continues the decoder',
          lengths==[2]*8 and len(result.events)==8 and len(result.issued)==9
          and result.stop=='InputExhausted' and len(result.pending)==1,
          lengths=lengths,issued_targets=result.issued,signals=[e.signal for e in result.events])
    check('generated-boundary execution exactly replays through the unchanged RR38 decoder',
          replay_matches(initial,result))
    fixed=decode(initial,word,[NEG_ONE]*9)
    check('the generation law changes real factorization without resetting the state',
          [len(op.cell.beta) for op in fixed.outputs]==[2,4,4,4]
          and len(result.state.executed_word)==16 and len(fixed.tail)==2,
          fixed_lengths=[len(op.cell.beta) for op in fixed.outputs])
    ab=promote_word(certify_word(initial,(a,b),NEG_ONE))
    ba=promote_word(certify_word(initial,(b,a),NEG_ONE))
    eab=policy.emit(ab);eba=policy.emit(ba)
    same_tail=(a,b)*2
    after_ab=start_loop(ab.cell.endpoint,same_tail,eab.target,policy)
    after_ba=start_loop(ba.cell.endpoint,same_tail,eba.target,policy)
    check('same visible result and live endpoint can generate different next requirements',
          ab.visible==ba.visible and ab.cell.endpoint.live==ba.cell.endpoint.live
          and eab.signal==-4 and eba.signal==4 and eab.target!=eba.target
          and len(after_ab.outputs[0].cell.beta)==2 and len(after_ba.outputs[0].cell.beta)==4,
          responses=[eab.response,eba.response],targets=[eab.target,eba.target],next_lengths=[2,4])
    near_cases=0
    for epsilon in (Q(-1,100),Q(1,100)):
        rows=[list(row) for row in policy.probe]
        rows[0][1]+=epsilon;rows[1][0]+=epsilon
        near=SourcePolicy(tuples(rows))
        for op,event in ((ab,eab),(ba,eba)):
            assert near.emit(op).target==event.target
            near_cases+=1
    check('strict nonzero source readouts persist under small public calibration changes',True,
          cases=near_cases,scope='local source sign, not a global derivation of the source law')
    rejected=False
    try:
        policy.emit(replace(ab,visible=(Q(1),Q(0),Q(0),Q(0))))
    except ValueError:
        rejected=True
    check('forged promoted labels cannot trigger a source event',rejected)
    splits=0
    for i in range(17):
        partial=start_loop(initial,word[:i],NEG_ONE,policy)
        complete=extend_loop(partial,word[i:])
        assert complete==result
        assert complete.events[:len(partial.events)]==partial.events
        splits+=1
    short=(a,b)*3
    expected=start_loop(initial,short,NEG_ONE,policy)
    partitions=0
    for mask in range(1<<(len(short)-1)):
        cuts=[0]+[i for i in range(1,len(short)) if mask&(1<<(i-1))]+[len(short)]
        partial=start_loop(initial,(),NEG_ONE,policy)
        for lo,hi in zip(cuts,cuts[1:]):
            partial=extend_loop(partial,short[lo:hi])
        assert partial==expected
        partitions+=1
    check('append schedule cannot change the boundary journal or old certificates',True,
          single_splits=splits,all_six_letter_partitions=partitions)
    open_result=start_loop(initial,(a,),NEG_ONE,policy)
    check('an open prefix issues no boundary event and is not committed',
          open_result.state==initial and not open_result.events
          and open_result.tail==(a,) and open_result.stop=='NoTerminalPrefix'
          and extend_loop(open_result,(b,)).outputs==(ab,))
    raw=SourcePolicy(policy.probe,mode='raw')
    failed=start_loop(initial,word,NEG_ONE,raw)
    check('a generated requirement can genuinely fail without editing the open tail',
          len(failed.outputs)==1 and failed.stop=='NoTerminalPrefix'
          and failed.state==ab.cell.endpoint and failed.tail==word[2:]
          and len(failed.events)==1 and replay_matches(initial,failed),
          impossible_generated_target=failed.pending[0],unconsumed_letters=len(failed.tail))
    undecided=start_loop(initial,word,NEG_ONE,SourcePolicy(initial.live.context))
    check('zero readout suspends the source instead of fabricating a successful boundary',
          len(undecided.outputs)==1 and undecided.stop=='SourceUndecided'
          and not undecided.pending and undecided.events[-1].target is None
          and replay_matches(initial,undecided)
          and extend_loop(undecided).events==undecided.events)
    macro=ab
    higher=start_loop(ab.cell.endpoint,(macro,)*6,NEG_ONE,policy)
    check('the same source and scheduler operate on nested upper letters',
          len(higher.outputs)==5 and all(op.level==3 for op in higher.outputs)
          and higher.stop=='InputExhausted' and len(higher.events)==5
          and replay_matches(ab.cell.endpoint,higher),
          terminal_lengths=[len(op.cell.beta) for op in higher.outputs],output_level=3)
    check('next requirements are issued even when input is empty, then await new input',
          len(result.issued)==len(result.outputs)+1
          and extend_loop(result,(a,b)).events[:8]==result.events
          and len(extend_loop(result,(a,b)).outputs)==9)
    root=Path(__file__).resolve().parent
    paths=['closed_boundary_loop.py','test_closed_boundary_loop.py','recursive_upper_decoder.py',
           'test_recursive_upper_decoder.py','certified_cell_bridge.py','test_certified_cell_bridge.py',
           'residual_extraction_transport.py','future_existence_residual.py',
           'vendor/two_flower_kernel_certificate.py','vendor/internal_port_certificate.py']
    return dict(note='RR39',passed=True,groups=len(checks),checks=checks,
                source_base_commit='fb492d93daf8b0788d212caf3e39931e8a6efbe3',
                law='public probe/readout -> sign -> next endpoint target; explicitly postulated forward source',
                probe=policy.probe,readout=policy.readout,levels_reached=[1,2,3],
                limits=['bootstrap, live context, input word, and source calibration remain supplied',
                        'no derivation of v18 future-origin C or general Gamma',
                        'source readout does not replace the exact residual payload'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('closed_boundary_loop_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'])))
