"""RR35: future existence constrains residuals without a supplied future value.

Both local visible results are -1. The inherited RR31 join also must be -1.
Future boundaries range over the entire signed symmetric trace-one B2 fibre.
The content-blind feasibility check takes X only, never the future boundary.
"""
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
from two_flower_kernel_certificate import eye,plus,scale,mm,tr,outer,basis,qstate,join
from internal_port_certificate import rref

NEG_ONE=[Q(-1),Q(0),Q(0),Q(0)]


def zero():
    return [[Q(0)]*3 for _ in range(3)]


def residue(x):
    if x != [list(row) for row in zip(*x)] or tr(x)!=1:
        raise ValueError('symmetric trace-one B2 boundary required')
    return plus(x,scale(Q(-1,3),eye()))


def boundary(s):
    return plus(scale(Q(1,3),eye()),s)


def inner(s,t):
    return tr(mm(s,t))


def commutator(s,t):
    return plus(mm(s,t),scale(-1,mm(t,s)))


def future_exists(x):
    """No specific Y or direction is received or predicted here."""
    s=residue(x)
    return inner(s,s)>0


def one_existence_witness(x):
    """Construct ONE admissible continuation, not the actual unknown future."""
    s=residue(x)
    n=inner(s,s)
    if not n:
        raise ValueError('zero residue admits no equal-result continuation in this join')
    t=scale(-Q(1,3)/n,s)
    return boundary(t)


def five_basis():
    return [plus(basis(0,0),scale(-1,basis(1,1))),
            plus(basis(1,1),scale(-1,basis(2,2))),
            plus(basis(0,1),basis(1,0)),
            plus(basis(0,2),basis(2,0)),
            plus(basis(1,2),basis(2,1))]


def lincomb(c,bs):
    s=zero()
    for a,b in zip(c,bs):
        s=plus(s,scale(a,b))
    return s


def residual_relation(s,t):
    c=commutator(s,t)
    return inner(s,t)==-Q(1,3) and all(not z for row in c for z in row)


def future_flower_directions(x):
    """Compute the affine family of future residues; no future is selected."""
    if not future_exists(x):
        raise ValueError('no future family exists for zero residue')
    s=residue(x)
    bs=five_basis()
    a=[[inner(s,b) for b in bs]]
    cs=[commutator(s,b) for b in bs]
    for i,j in ((0,1),(0,2),(1,2)):
        a.append([c[i][j] for c in cs])
    reduced,pivots=rref(a)
    free=[j for j in range(5) if j not in pivots]
    directions=[]
    for f in free:
        v=[Q(0)]*5
        v[f]=Q(1)
        for row,p in zip(reduced,pivots):
            v[p]=-row[f]
        directions.append(lincomb(v,bs))
    return dict(rank=len(pivots),dimension=len(free),directions=directions)


def relation_output(s,t):
    c=commutator(s,t)
    return [-Q(1,3)+2*inner(s,t),2*c[1][2],2*c[2][0],2*c[0][1]]


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    bs=five_basis()
    # Test the residual join formula independently in the inherited quaternion
    # implementation on a basis of the affine current/future fibres.
    states=[boundary(zero())]+[boundary(s) for s in bs]
    for x,y in product(states,repeat=2):
        assert join(x,y)==relation_output(residue(x),residue(y))
    check('the fixed-result join is a residual pairing plus a commutator',True,basis_pairs=36)
    samples=[]
    for c in product((-1,0,1),repeat=5):
        x=boundary(lincomb(c,bs))
        assert qstate(x)==NEG_ONE
        feasible=future_exists(x)
        item=dict(coordinates=list(c),future_exists=feasible)
        if feasible:
            y=one_existence_witness(x)
            s,t=residue(x),residue(y)
            assert qstate(y)==NEG_ONE and join(x,y)==NEG_ONE and residual_relation(s,t)
            assert inner(s,s)*inner(t,t)==Q(1,9)
            family=future_flower_directions(x)
            assert family['dimension']>=1
            for k in family['directions']:
                candidate=boundary(plus(t,k))
                assert qstate(candidate)==NEG_ONE and join(x,candidate)==NEG_ONE
                assert inner(s,s)*inner(residue(candidate),residue(candidate))>=Q(1,9)
            item.update(residue_norm_squared=inner(s,s),future_family_dimension=family['dimension'])
        samples.append(item)
    check('future existence rejects only zero residue on the full signed fixed-result fibre',
          sum(z['future_exists'] for z in samples)==242,len_samples=len(samples),feasible=242,infeasible=1)
    x0=boundary(zero())
    # For every symmetric trace-one Y, tr((I/3)Y)=1/3 and the commutator is zero.
    check('erasing residue preserves the local result but destroys every same-result continuation in this join',
          qstate(x0)==NEG_ONE and all(join(x0,y)==[-Q(1,3),0,0,0] for y in states),
          erased_join_result=[-Q(1,3),0,0,0],general_identity='Omega(I/3,Y)=-1/3 for tr(Y)=1')
    full=[[Q(1,2),0,0],[0,Q(1,3),0],[0,0,Q(1,6)]]
    signed=one_existence_witness(full)
    check('a full-rank current boundary still admits a signed future boundary',
          signed==[[Q(-2,3),0,0],[0,Q(1,3),0],[0,0,Q(4,3)]] and join(full,signed)==NEG_ONE,
          current=full,future_witness=signed)
    check('restricting the future to a pure direction would incorrectly reject that full-rank example',
          all(join(full,outer(e))!=NEG_ONE for e in eye()),
          scope='full-rank X has no pure-direction witness; signed B2 continuations are allowed')
    # The pairing condition alone is insufficient: the imaginary join must also vanish.
    s=[[Q(1,2),0,0],[0,Q(-1,2),0],[0,0,0]]
    t=residue(one_existence_witness(boundary(s)))
    t_bad=plus(t,scale(Q(1,2),bs[2]))
    check('the real residual pairing alone does not certify the future unit',
          inner(s,t_bad)==-Q(1,3) and not residual_relation(s,t_bad)
          and join(boundary(s),boundary(t_bad))==[-1,0,0,1],failure_result=[-1,0,0,1])
    examples=[]
    for name,x in [('axis_i',outer(eye()[0])),('full_rank_diagonal',full)]:
        family=future_flower_directions(x)
        y=one_existence_witness(x)
        examples.append(dict(name=name,current=x,future_family_dimension=family['dimension'],
                             witness=y,future_family_directions=family['directions']))
    check('existence constrains the future while leaving its content open',
          [z['future_family_dimension'] for z in examples]==[2,1],examples=examples)
    axes=[outer(e) for e in eye()]
    later=[]
    for u,y in enumerate(axes):
        values=[join(x,y) for x in axes]
        later.append(dict(future_axis=u,visible_future=qstate(y),current_candidates_results=values))
    check('later future boundaries with the same visible result change which current differences are replaceable',
          later[2]['current_candidates_results'][0]==later[2]['current_candidates_results'][1]
          and later[0]['current_candidates_results'][0]!=later[0]['current_candidates_results'][1],later_partitions=later)
    rows=[]
    for y in axes:
        columns=[join(s,y) for s in bs]
        rows.extend([list(row) for row in zip(*columns)])
    _,piv=rref(rows)
    check('preserving every admissible future response is stronger than preserving the existence flag',
          len(piv)==5,common_future_response_rank=5,existence_flag='nonzero residue only')
    # A canonicalized nonzero residue preserves existence but breaks a later
    # response. This is a compression counterexample, not a permitted rewrite.
    check('collapsing all feasible histories to one prototype loses future-relative residuals',
          future_exists(axes[0]) and future_exists(axes[1])
          and join(axes[0],axes[0])!=join(axes[1],axes[0]),
          restriction='diagnostic compression counterexample; closed histories are not rewritten')
    chain=[]
    x=full
    for tick in range(24):
        # The record is committed before constructing the possible witness.
        snapshot=[row[:] for row in x]
        y=one_existence_witness(snapshot)
        assert join(snapshot,y)==NEG_ONE
        chain.append(dict(tick=tick,current=snapshot,visible_current=qstate(snapshot),
                          residue=residue(snapshot),generated_witness=y,
                          connection=join(snapshot,y),squared_norm_product=inner(residue(snapshot),residue(snapshot))*inner(residue(y),residue(y))))
        x=y
    check('one explicit forward witness generator realizes 24 equal-result links without a supplied future value',
          len(chain)==24 and chain[0]['current']==chain[2]['current'],links=24,
          role='existence witness and valid forward comparator; not the derived actual Time Engine future')
    check('a generated witness is not asserted to succeed against every independently chosen future',
          future_exists(axes[0]) and join(axes[0],axes[0])!=NEG_ONE)
    root=Path(__file__).resolve().parent
    paths=[Path(__file__),root/'test_future_existence_residual.py',
           root/'vendor/two_flower_kernel_certificate.py',root/'vendor/internal_port_certificate.py']
    return dict(note='RR35',passed=True,groups=len(checks),checks=checks,
                source_base_commit='b5886842a5b3baf36d59b75263ca8c687b4eecc5',
                premise='same local and joined visible result F=-1; actual future content unspecified',
                future_domain='all symmetric trace-one signed real B2 boundaries, not only pure directions',
                content_blind_condition='S != 0',
                residual_relation='tr(S T)=-1/3 and [S,T]=0',
                norm_constraint='||S||_F^2 ||T||_F^2 >= 1/9',
                status='conditional residual constraint and future-relative preservation; no backward causal mechanism derived',
                samples=samples,later_partitions=later,examples=examples,witness_chain=chain,
                source_sha256={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def encode(x):
    if isinstance(x,Q):
        return str(x)
    raise TypeError(type(x))


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('future_existence_residual_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'groups':data['groups'],'samples':243,'feasible':242,
                      'content_blind_condition':'S != 0','future_response_rank':5,'witness_links':24}))
