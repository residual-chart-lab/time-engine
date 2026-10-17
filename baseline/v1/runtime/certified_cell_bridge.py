"""RR37: a local certified-cell -> residue -> active-upper-operation bridge.

Local chart: equal unit-vector two-letter histories, a committed inherited
unit direction, fixed visible result -1, and the RR31 inherited connection.
T3 has an analytic transport witness within this declared unit-vector chart.
Actual future contents are not passed to certification or extraction.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json

from residual_extraction_transport import extract,coordinates,transpose,matvec
from future_existence_residual import residue,boundary,five_basis,lincomb,one_existence_witness,NEG_ONE
from two_flower_kernel_certificate import eye,outer,join,qstate,mm,plus,scale
from internal_port_certificate import qmul,solve,rank


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def unit(v):
    return len(v)==3 and dot(v,v)==1


def tuples(x):
    return tuple(tuple(Q(z) for z in row) for row in x)


@dataclass(frozen=True)
class CellWitness:
    committed_past: tuple
    beta: tuple
    required_result: tuple=tuple(NEG_ONE)
    connection: str='RR31-fixed-join'

    def __post_init__(self):
        object.__setattr__(self,'committed_past',tuples(self.committed_past))
        object.__setattr__(self,'beta',tuples(self.beta))
        object.__setattr__(self,'required_result',tuple(Q(x) for x in self.required_result))


@dataclass(frozen=True)
class CertifiedCell:
    witness: CellWitness
    endpoint: tuple
    certification: str='unit-chart-T1-T2-T3'


def certify(w):
    """Check local T1/T2; attach the proved local T3 mode, never a supplied flag."""
    if w.required_result!=tuple(NEG_ONE) or w.connection!='RR31-fixed-join':
        raise ValueError('unsupported boundary or connection in this local chart')
    pfx=w.committed_past
    if len(pfx)<2 or len(pfx)%2:
        raise ValueError('committed past must consist of complete equal-unit blocks')
    for i in range(0,len(pfx),2):
        if pfx[i]!=pfx[i+1] or not unit(pfx[i]):
            raise ValueError('invalid committed past block')
        if i and dot(pfx[i-2],pfx[i])!=0:
            raise ValueError('committed past adjacency is incompatible')
    if len(w.beta)!=2 or w.beta[0]!=w.beta[1] or not unit(w.beta[0]):
        raise ValueError('local mode requires two equal unit letters')
    p,u=pfx[-1],w.beta[0]
    if dot(p,u)!=0:
        raise ValueError('history is outside inherited reachability')
    first=[Q(0),*u]
    last=qmul(first,first)
    if last!=NEG_ONE or first==NEG_ONE:
        raise ValueError('first-boundary proof failed')
    x=outer(u)
    if join(outer(p),x)!=NEG_ONE or qstate(x)!=NEG_ONE:
        raise ValueError('future-result and causal-adjacency checks failed')
    # T3 mode: for nearby unit p', the proper rotation mapping p to p'
    # gives u'=R u. Unit length, orthogonality and two-letter first closure
    # are preserved. The sole future-result value in this chart remains -1.
    return CertifiedCell(w,tuples(x))


def near_rotation(p,p_new):
    if not unit(p) or not unit(p_new):
        raise ValueError('unit inherited states required')
    c=dot(p,p_new)
    if c<=-1:
        raise ValueError('antipodal state is outside the local stability neighbourhood')
    v=[p[1]*p_new[2]-p[2]*p_new[1],p[2]*p_new[0]-p[0]*p_new[2],p[0]*p_new[1]-p[1]*p_new[0]]
    k=[[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]
    r=plus(plus(eye(),k),scale(1/(1+c),mm(k,k)))
    assert mm(transpose(r),r)==eye() and matvec(r,p)==list(p_new)
    return r


@dataclass(frozen=True)
class FullTerminalResidue:
    active: tuple
    ordered_cell_record: tuple


def transport_residue(r):
    if not isinstance(r,FullTerminalResidue):
        raise ValueError('typed full terminal residue required')
    return FullTerminalResidue(r.active,r.ordered_cell_record)


@dataclass(frozen=True)
class UpperState:
    context: tuple
    accumulated: tuple=(Q(1),Q(0),Q(0),Q(0))


@dataclass(frozen=True)
class UpperOperation:
    visible: tuple
    full_residue: FullTerminalResidue
    active_carrier: object
    source: CertifiedCell | None

    def apply(self,context):
        return self.active_carrier.connect([list(row) for row in context])

    def execute(self,state):
        if not isinstance(state,UpperState):
            raise ValueError('typed upper state required')
        value=self.apply(state.context)
        return UpperState(state.context,tuple(qmul(value,state.accumulated)))


def promotion(cell):
    if not isinstance(cell,CertifiedCell) or certify(cell.witness)!=cell:
        raise ValueError('a verified local terminal witness is required')
    carrier=extract([list(row) for row in cell.endpoint])
    w=cell.witness
    record=(w.committed_past,w.required_result,w.beta,w.connection)
    r=FullTerminalResidue(carrier.exact,record)
    # J is the identity on this exact typed residue. iota bundles q,J(r),action.
    return UpperOperation(w.required_result,transport_residue(r),carrier,cell)


def seed_cells():
    axes=[tuple(row) for row in eye()]
    directions=axes+[(Q(3,5),Q(4,5),Q(0)),(Q(3,5),Q(0),Q(4,5)),(Q(0),Q(3,5),Q(4,5))]
    parents=[axes[1],axes[2],axes[0],axes[2],axes[1],axes[0]]
    return [certify(CellWitness((p,p),(u,u))) for p,u in zip(parents,directions)]


def symmetric_coordinates(x):
    return [x[0][0],x[1][1],x[2][2],x[0][1],x[0][2],x[1][2]]


def construct_upper_boundary(y,operations):
    """Declared free-number chart rule: a signed affine combination is one state.

This linear envelope is not silently inferred from v18's im(PCl) alphabet.
"""
    residue(y)  # Require the declared normalized symmetric B2 future type.
    columns=[symmetric_coordinates(op.source.endpoint) for op in operations]
    a=[list(row) for row in zip(*columns)]
    coefficients=solve(a,symmetric_coordinates(y))
    if sum(coefficients)!=1:
        raise AssertionError('visible-result normalization changed')
    rebuilt=[[sum(c*op.source.endpoint[i][j] for c,op in zip(coefficients,operations)) for j in range(3)] for i in range(3)]
    if rebuilt!=y:
        raise AssertionError('generated upper-boundary reconstruction failed')
    return dict(coefficients=coefficients,boundary=tuples(rebuilt))


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    cells=seed_cells()
    ops=[promotion(c) for c in cells]
    check('six concrete ordered lower cells satisfy the declared local T1/T2 mode',
          all(c.certification=='unit-chart-T1-T2-T3' and qstate(c.endpoint)==NEG_ONE for c in cells),cells=6)
    # Rational nearby variations plus the analytic Rodrigues witness.
    co,si=Q(99,101),Q(20,101)
    rotations=[[[co,-si,0],[si,co,0],[0,0,1]],[[co,0,si],[0,1,0],[-si,0,co]],[[1,0,0],[0,co,-si],[0,si,co]]]
    stability_cases=0
    for c,o in product(cells,rotations):
        p,u=c.witness.committed_past[-1],c.witness.beta[0]
        p_new=tuple(matvec(o,p))
        assert sum((a-b)**2 for a,b in zip(p,p_new))<Q(1,4)
        r=near_rotation(p,p_new)
        u_new=tuple(matvec(r,u))
        certify(CellWitness((p_new,p_new),(u_new,u_new)))
        stability_cases+=1
    check('the local T3 mode has an explicit nearby inherited-state transport',True,cases=stability_cases,
          analytic_scope='unit-state chart and singleton fixed future-result requirement; not arbitrary v18 perturbations')
    u=cells[0].witness.beta[0]
    opposite=certify(CellWitness(cells[0].witness.committed_past,(tuple(-z for z in u),)*2))
    opposite_op=promotion(opposite)
    check('the active S is not silently equated with the entire ordered terminal record',
          ops[0].active_carrier.exact==opposite_op.active_carrier.exact
          and ops[0].full_residue!=opposite_op.full_residue,
          example='u|u and (-u)|(-u) share the B2 action but preserve different exact word records')
    check('q, extracted active residue, full-record transport and constructor are one typed bridge',
          all(op.visible==tuple(NEG_ONE) and op.full_residue.active==op.active_carrier.exact for op in ops))
    formal_zero=FullTerminalResidue((Q(0),)*5,())
    check('J preserves the formal zero and every exact cell record',
          transport_residue(formal_zero)==formal_zero
          and all(transport_residue(op.full_residue)==op.full_residue for op in ops))
    a=[list(row) for row in zip(*(symmetric_coordinates(c.endpoint) for c in cells))]
    check('the promoted generators span the full symmetric B2 space',rank(a)==6,rank=6,
          allowance='signed affine linear-envelope rule declared separately from direct generated letters')
    families=[]
    for coeff in product((-1,0,1),repeat=5):
        y=boundary(lincomb(coeff,five_basis()))
        built=construct_upper_boundary(y,ops)
        assert qstate(built['boundary'])==NEG_ONE
        for op in ops:
            assert op.apply(y)==join(op.source.endpoint,y)
        families.append(dict(residue_coordinates=list(coeff),coefficients=built['coefficients']))
    check('the allowed upper linear envelope generates the declared future class, preserving actual action',True,
          future_states=len(families),connections=len(families)*len(ops))
    for op in ops:
        y=one_existence_witness([list(row) for row in op.source.endpoint])
        assert op.apply(y)==NEG_ONE
        assert join(boundary([[Q(0)]*3 for _ in range(3)]),y)!=NEG_ONE
        state=UpperState(tuples(y))
        changed=op.execute(state)
        baseline=UpperOperation(tuple(NEG_ONE),formal_zero,
                                extract(boundary([[Q(0)]*3 for _ in range(3)])),None)
        assert changed!=baseline.execute(state)
        assert changed.accumulated==tuple(NEG_ONE)
        assert changed.context==state.context
        assert op.execute(changed).accumulated==(1,0,0,0)
    check('each admitted active S changes an upper state through a composable actual operation',True,operations=6,
          state_type='fixed boundary context plus accumulated quaternion; visible observation is the quaternion')
    try:
        promotion(cells[0].witness)
    except ValueError:
        rejected=True
    else:
        rejected=False
    check('an unverified witness cannot be promoted as a certified cell',rejected)
    try:
        certify(CellWitness(cells[0].witness.committed_past,(cells[0].witness.committed_past[-1],)*2))
    except ValueError:
        rejected=True
    else:
        rejected=False
    check('a history that violates inherited causal adjacency is rejected',rejected)
    # One lower exact process becomes one active upper letter each iteration.
    p=tuple(eye()[1]);past=(p,p);records=[]
    for n in range(24):
        axes=[tuple(row) for row in eye()]
        u=next(v for v in axes if dot(v,p)==0)
        c=certify(CellWitness(past,(u,u)))
        op=promotion(c)
        context=one_existence_witness([list(row) for row in c.endpoint])
        assert op.apply(context)==NEG_ONE
        records.append(dict(step=n,beta=c.witness.beta,past_word_length=len(past),
                            active_residue=op.full_residue.active,visible=op.visible,
                            upper_result=op.apply(context)))
        past=past+c.witness.beta
        p=u
    check('twenty-four certified processes promote to active operations with all committed prefixes retained',
          len(records)==24 and records[-1]['past_word_length']==48,cells=24,
          scope='one lower-to-upper bridge repeated; upper-level terminal cells are not yet constructed')
    root=Path(__file__).resolve().parent
    paths=[Path(__file__),root/'test_certified_cell_bridge.py',root/'residual_extraction_transport.py',
           root/'test_residual_extraction_transport.py',root/'future_existence_residual.py',
           root/'test_future_existence_residual.py',root/'vendor/two_flower_kernel_certificate.py',root/'vendor/internal_port_certificate.py']
    return dict(note='RR37',passed=True,groups=len(checks),checks=checks,
                source_base_commit='6de9a46ffa2871e067d3ba9a4807c181cdb7448a',
                accepted_policy='faithful transport of the specified allowed connection; deletion is optional, not required',
                local_chart='unit-vector equal-letter words, orthogonal inherited reachability, fixed future result -1',
                residual_type='active S coordinates plus exact ordered cell record',
                upper_direct_image='rank-one projector actions from locally certified unit words',
                upper_linear_envelope='full signed symmetric trace-one B2 under an explicitly declared free-number affine combination rule',
                limitations=['The local realization is not asserted to be the unique v18 chart.',
                             'The affine-envelope permission is not inferred from v18 alone.',
                             'Actual future origin and recursive upper terminality remain unresolved.'],
                generated_future_examples=families,bridge_trace=records,
                source_sha256={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def encode(x):
    if isinstance(x,Q):
        return str(x)
    raise TypeError(type(x))


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('certified_cell_bridge_result.json').write_text(json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'groups':data['groups'],'local_certificates':6,'stability_cases':18,
                      'generated_future_states':243,'connections':1458,'promoted_cells':24}))
