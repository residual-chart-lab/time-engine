"""RR38: stateful upper first-boundary decoding and recursive exact promotion.

The regular affine action chart is declared explicitly. Higher residues retain
ordered nested words; they are not forced into the lower B2 five-coordinate type.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
from functools import lru_cache
import hashlib
import json

from certified_cell_bridge import CellWitness,certify,promotion,UpperState,tuples,dot
from future_existence_residual import boundary,five_basis,zero,NEG_ONE
from two_flower_kernel_certificate import eye,plus,scale,join
from internal_port_certificate import qmul,solve,rref


def inverse(q):
    if len(q)!=4:
        raise ValueError('four-component quaternion required')
    n=sum(x*x for x in q)
    if not n:
        raise ValueError('nonzero quaternion required')
    return [q[0]/n,*[-x/n for x in q[1:]]]


def build_library():
    axes=[tuple(r) for r in eye()]
    wanted=axes+[(Q(3,5),Q(4,5),Q(0)),(Q(3,5),Q(0),Q(4,5)),(Q(0),Q(3,5),Q(4,5))]
    path=[wanted[0],wanted[1],wanted[2],wanted[3],axes[2],axes[1],wanted[4],axes[1],axes[0],wanted[5]]
    selected={0:0,1:1,2:2,3:3,6:4,9:5}
    p=axes[2];past=(p,p);ops=[None]*6
    for i,u in enumerate(path):
        cell=certify(CellWitness(past,(u,u)))
        op=promotion(cell)
        if i in selected:
            ops[selected[i]]=op
        past=past+(u,u)
    return tuple(ops)


@lru_cache(maxsize=16)
def verify_library(library):
    if len(library)!=6:
        raise ValueError('six committed generating operations required')
    histories=[]
    for op in library:
        if op.source is None or promotion(op.source)!=op:
            raise ValueError('library operation has no verified lower origin')
        w=op.source.witness
        histories.append(w.committed_past+w.beta)
    whole=max(histories,key=len)
    if any(h!=whole[:len(h)] for h in histories):
        raise ValueError('the declared library must come from one committed lower path')
    return True


@dataclass(frozen=True)
class AffineLetter:
    weights: tuple
    library: tuple
    level: int=1

    def __post_init__(self):
        object.__setattr__(self,'weights',tuple(Q(x) for x in self.weights))
        object.__setattr__(self,'library',tuple(self.library))
        verify_library(self.library)
        if len(self.weights)!=len(self.library) or sum(self.weights)!=1:
            raise ValueError('a normalized signed affine action is required')
        if self.level!=1:
            raise ValueError('primitive affine letters live at level one')

    @property
    def visible(self):
        return tuple(NEG_ONE)

    def kernel(self,y):
        values=[op.apply(y) for op in self.library]
        return tuple(sum(w*v[j] for w,v in zip(self.weights,values)) for j in range(4))

    def leaves(self):
        return (self,)

    def execute(self,state):
        return UpperState(state.context,tuple(qmul(self.kernel(state.context),state.accumulated)))


@dataclass(frozen=True)
class ExecutionState:
    live: UpperState
    executed_word: tuple=()


def step(letter,state):
    return ExecutionState(letter.execute(state.live),state.executed_word+(letter,))


def kernel(word,y):
    q=(Q(1),Q(0),Q(0),Q(0))
    for a in word:
        q=tuple(qmul(a.kernel(y),q))
    return q


def flattened(word):
    return tuple(leaf for a in word for leaf in a.leaves())


def action_matrix(y,library):
    return [[Q(1)]*len(library)]+[list(row) for row in zip(*(op.apply(y) for op in library))]


def regular(y,library):
    return len(rref(action_matrix(y,library))[1])==5


@dataclass(frozen=True)
class WordCell:
    start: ExecutionState
    beta: tuple
    target: tuple
    endpoint: ExecutionState
    chart: str='regular-affine-final-leaf'


def certify_word(start,word,target):
    word=tuple(word);target=tuple(Q(x) for x in target)
    if not word or len({a.level for a in word})!=1:
        raise ValueError('a nonempty word of one scale is required')
    for a in word:
        if isinstance(a,RecursiveLetter):
            expected=tuple(qmul(a.cell.target,inverse(a.cell.start.live.accumulated)))
            if (certify_word(a.cell.start,a.cell.beta,a.cell.target)!=a.cell
                    or a.visible!=expected or a.level!=a.cell.beta[0].level+1
                    or activity_witness(a.cell) is None):
                raise ValueError('a nested letter has no valid source-cell certificate')
        elif not isinstance(a,AffineLetter):
            raise ValueError('unsupported exact operation type')
    leaves=flattened(word)
    library=leaves[-1].library
    if any(a.library!=library for a in leaves) or not regular(start.live.context,library):
        raise ValueError('one declared regular affine action chart is required')
    inverse(start.live.accumulated);inverse(target)
    current=start
    for i,a in enumerate(word):
        current=step(a,current)
        if current.live.accumulated==target and i<len(word)-1:
            raise ValueError('the proposed terminal block crossed an earlier boundary')
    if current.live.accumulated!=target:
        raise ValueError('result closure failed')
    # In this regular chart, a near final-leaf coefficient correction exists.
    # Prefix inequalities and nonzero accumulated state persist locally.
    return WordCell(start,word,target,current)


@dataclass(frozen=True)
class RecursiveLetter:
    cell: WordCell
    visible: tuple
    level: int

    def leaves(self):
        return flattened(self.cell.beta)

    def kernel(self,y):
        return kernel(self.cell.beta,y)

    def execute(self,state):
        return UpperState(state.context,tuple(qmul(self.kernel(state.context),state.accumulated)))


def activity_witness(cell):
    leaves=flattened(cell.beta)
    q=tuple(qmul(cell.target,inverse(cell.start.live.accumulated)))
    y0=[list(r) for r in cell.start.live.context]
    library=leaves[-1].library
    h=None
    for b in five_basis():
        for leaf in leaves:
            x=[[sum(w*op.source.endpoint[i][j] for w,op in zip(leaf.weights,leaf.library)) for j in range(3)] for i in range(3)]
            if any(join(x,b)):
                h=b
                break
        if h is not None:
            break
    if h is None:
        return None
    # Norm squared of the word kernel along the line has degree <=2n.
    # A nonzero 5x5 regular-chart minor adds at most four exceptional roots.
    for t in range(2*len(leaves)+7):
        y=plus(y0,scale(Q(t),h))
        if regular(y,library) and kernel(cell.beta,y)!=q:
            return dict(context=tuples(y),actual=kernel(cell.beta,y),zero_residue_reference=q)
    raise AssertionError('a nonconstant regular word must have an activity witness')


def promote_word(cell):
    if not isinstance(cell,WordCell) or certify_word(cell.start,cell.beta,cell.target)!=cell:
        raise ValueError('verified upper terminal cell required')
    if activity_witness(cell) is None:
        raise ValueError('constant-action cell is degenerate, not an active phase closure')
    q=tuple(qmul(cell.target,inverse(cell.start.live.accumulated)))
    # The complete nested word and certificate survive in the exact payload.
    return RecursiveLetter(cell,q,cell.beta[0].level+1)


def replace_last_leaf(letter,new_leaf,new_context):
    if isinstance(letter,AffineLetter):
        return new_leaf
    beta=letter.cell.beta[:-1]+(replace_last_leaf(letter.cell.beta[-1],new_leaf,new_context),)
    start=ExecutionState(UpperState(new_context,letter.cell.start.live.accumulated),letter.cell.start.executed_word)
    target=tuple(qmul(kernel(beta,new_context),start.live.accumulated))
    return promote_word(certify_word(start,beta,target))


def retarget_near(cell,new_start,new_target):
    leaves=flattened(cell.beta)
    last=leaves[-1]
    y=new_start.live.context
    before=tuple(qmul(kernel(leaves[:-1],y),new_start.live.accumulated))
    wanted=qmul(new_target,inverse(before))
    previous=last.kernel(y)
    delta=[Q(0),*[a-b for a,b in zip(wanted,previous)]]
    correction=solve(action_matrix(y,last.library),delta)
    adjusted=AffineLetter(tuple(a+b for a,b in zip(last.weights,correction)),last.library)
    beta=cell.beta[:-1]+(replace_last_leaf(cell.beta[-1],adjusted,y),)
    return certify_word(new_start,beta,new_target)


@dataclass(frozen=True)
class DecodeResult:
    state: ExecutionState
    outputs: tuple
    tail: tuple
    boundaries: tuple
    stop: str


def decode(state,word,boundaries):
    tail=tuple(word);pending=tuple(tuple(Q(x) for x in b) for b in boundaries);out=[]
    if len({a.level for a in tail})>1:
        raise ValueError('decoder input must belong to one scale')
    for target in pending:
        inverse(target)
    while True:
        if not tail:
            return DecodeResult(state,tuple(out),tail,pending,'InputExhausted')
        if not pending:
            return DecodeResult(state,tuple(out),tail,pending,'BoundaryExhausted')
        current=state;found=None
        for i,a in enumerate(tail):
            current=step(a,current)
            if current.live.accumulated==pending[0]:
                found=i+1
                break
        if found is None:
            return DecodeResult(state,tuple(out),tail,pending,'NoTerminalPrefix')
        cell=certify_word(state,tail[:found],pending[0])
        out.append(promote_word(cell))
        state=cell.endpoint;tail=tail[found:];pending=pending[1:]


def resume(result,extra_word=(),extra_boundaries=()):
    fresh=decode(result.state,result.tail+tuple(extra_word),result.boundaries+tuple(extra_boundaries))
    return DecodeResult(fresh.state,result.outputs+fresh.outputs,fresh.tail,fresh.boundaries,fresh.stop)


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    library=build_library()
    leaves=tuple(AffineLetter(tuple(Q(i==j) for i in range(6)),library) for j in range(6))
    y=tuples([[Q(3,2),0,0],[0,Q(1,4),0],[0,0,Q(-3,4)]])
    initial=ExecutionState(UpperState(y))
    a,b=leaves[:2]
    cell=certify_word(initial,(a,b),NEG_ONE)
    m=promote_word(cell)
    check('exact upper actions close at the second prefix although the visible first letter is already minus one',
          a.visible==tuple(NEG_ONE) and a.kernel(y)==(2,0,0,0)
          and cell.endpoint.live.accumulated==tuple(NEG_ONE),terminal_length=2,
          prefix_actual_values=[a.kernel(y),cell.endpoint.live.accumulated])
    bad=False
    try:
        certify_word(initial,(a,b,a,b,a,b),NEG_ONE)
    except ValueError:
        bad=True
    check('a later matching endpoint cannot hide the earlier first boundary',bad)
    result=decode(initial,(a,b)*8,[NEG_ONE]*8)
    lengths=[len(op.cell.beta) for op in result.outputs]
    check('greedy factorization keeps the consumed state rather than resetting at each closure',
          lengths==[2,4,4,4] and len(result.tail)==2 and result.stop=='NoTerminalPrefix'
          and len(result.state.executed_word)==14,terminal_lengths=lengths,unconsumed_letters=2)
    joined=resume(result,(a,b))
    full=decode(initial,(a,b)*9,[NEG_ONE]*8)
    check('append-and-resume agrees exactly with one-shot decoding and leaves old certified outputs intact',joined==full)
    wait=decode(initial,(a,b)*3,[NEG_ONE])
    after=resume(wait,extra_boundaries=[NEG_ONE])
    check('boundary exhaustion preserves the tail and resumes from the consumed state',
          wait.stop=='BoundaryExhausted' and len(wait.tail)==4 and after.stop=='InputExhausted'
          and after==decode(initial,(a,b)*3,[NEG_ONE,NEG_ONE]))
    open_result=decode(initial,(a,),[NEG_ONE])
    check('no terminal prefix leaves the open suffix unexecuted in the returned state',
          open_result.stop=='NoTerminalPrefix' and open_result.state==initial
          and resume(open_result,(b,)).outputs==(m,))
    check('input exhaustion has the documented stop-priority',decode(initial,(),()).stop=='InputExhausted')
    returning=certify_word(cell.endpoint,(m,m),NEG_ONE)
    higher=promote_word(returning)
    witness=activity_witness(returning)
    check('a visible return still carries exact history and a nonconstant next-scale action',
          returning.start.live==returning.endpoint.live
          and returning.start.executed_word!=returning.endpoint.executed_word
          and higher.visible==(1,0,0,0) and witness['actual']!=witness['zero_residue_reference'],
          level=higher.level,visible_net_action=higher.visible,activity=witness)
    for context in [y,witness['context'],tuples(boundary(zero()))]:
        state=UpperState(context,(Q(1),Q(2),Q(0),Q(0)))
        direct=state
        for child in returning.beta:
            direct=child.execute(direct)
        assert higher.execute(state)==direct
    check('nested promotion preserves the original ordered operation exactly at later contexts',True,contexts=3)
    noncommuting=tuples(plus(plus([list(r) for r in y],five_basis()[2]),five_basis()[4]))
    check('the higher residue must preserve operation order beyond the certifying context',
          kernel((a,b),noncommuting)!=kernel((b,a),noncommuting)
          and m.kernel(noncommuting)==kernel((a,b),noncommuting),
          forward=kernel((a,b),noncommuting),reversed=kernel((b,a),noncommuting))
    h=five_basis()[0]
    vals=[kernel((a,b),tuples(plus([list(r) for r in y],scale(Q(t),h))))[0] for t in (0,1,2)]
    second=vals[2]-2*vals[1]+vals[0]
    check('the promoted word cannot be forced back into a single five-component B2 action',
          second==-8,second_difference=second,
          reason='single B2 action is affine in the context; this two-letter kernel has a nonzero quadratic term')
    stable=0
    for source in (cell,returning):
        for sign in (-1,1):
            new_y=tuples(plus([list(r) for r in source.start.live.context],scale(Q(sign,100),five_basis()[2])))
            z=tuple(x+Q(sign,100)*Q(i==1) for i,x in enumerate(source.start.live.accumulated))
            target=tuple(x+Q(sign,200)*Q(i==2) for i,x in enumerate(source.target))
            near=retarget_near(source,ExecutionState(UpperState(new_y,z),source.start.executed_word),target)
            assert near.endpoint.live.accumulated==target and len(near.beta)==len(source.beta)
            assert source.endpoint.live.accumulated==source.target
            stable+=1
    check('regular first-boundary modes have fresh near-cell certificates without rewriting old cells',True,
          cases=stable,levels=[1,2],scope='declared signed affine action chart with rank-five context matrix')
    root=Path(__file__).resolve().parent
    paths=[Path(__file__),root/'test_recursive_upper_decoder.py',root/'certified_cell_bridge.py',
           root/'test_certified_cell_bridge.py',
           root/'residual_extraction_transport.py',root/'future_existence_residual.py',
           root/'vendor/two_flower_kernel_certificate.py',root/'vendor/internal_port_certificate.py']
    return dict(note='RR38',passed=True,groups=len(checks),checks=checks,
                source_base_commit='3b2fc8e0c3980a82c91f27b7b07ebdeddfbf9ceb',
                upper_chart='base promoted actions and explicitly admitted normalized signed affine action constructors',
                residue_type='complete ordered nested operation word and certified source context; not a fixed B2 S',
                status='local recursive upper decoder and active promotion; no self-generated future-causal law derived',
                canonical_terminal_lengths=lengths,stop_modes=['InputExhausted','BoundaryExhausted','NoTerminalPrefix'],
                levels_reached=[1,2,3],activity_witness=witness,
                source_sha256={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def encode(x):
    if isinstance(x,Q):
        return str(x)
    raise TypeError(type(x))


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('recursive_upper_decoder_result.json').write_text(json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'groups':data['groups'],'terminal_lengths':data['canonical_terminal_lengths'],
                      'levels':data['levels_reached']}))
