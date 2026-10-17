"""RR36: content-blind extraction and preservation of successful future sets.

Preserving which futures succeed does not require every future to succeed.
Extraction receives one committed current boundary, never the actual future.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
from itertools import product
import hashlib
import json

from future_existence_residual import residue,boundary,five_basis,lincomb,inner,one_existence_witness,future_exists,NEG_ONE
from two_flower_kernel_certificate import eye,outer,join,mm,tr,plus,scale
from internal_port_certificate import rref


def coordinates(s):
    return (s[0][0],s[1][1],s[0][1],s[0][2],s[1][2])


def from_coordinates(v):
    a,b,c,d,e=v
    return [[a,c,d],[c,b,e],[d,e,-a-b]]


def transpose(a):
    return [list(row) for row in zip(*a)]


def matvec(a,v):
    return [sum(x*y for x,y in zip(row,v)) for row in a]


def zero():
    return [[Q(0)]*3 for _ in range(3)]


@dataclass(frozen=True)
class ResidualCarrier:
    exact: tuple
    # Frame is an explicit chart parameter, not a guessed future direction.
    frame: tuple
    operation: str='RR31-fixed-join'

    def original_residue(self):
        o=[list(row) for row in self.frame]
        return mm(mm(o,from_coordinates(self.exact)),transpose(o))

    def connect(self,y):
        residue(y)  # Check the declared same-result future type on arrival.
        o=[list(row) for row in self.frame]
        y_chart=mm(mm(transpose(o),y),o)
        value=join(boundary(from_coordinates(self.exact)),y_chart)
        # Return the quaternion response in the original semantic frame.
        return [value[0],*matvec(o,value[1:])]


def extract(x,frame=None):
    """Future-blind: only the current boundary and a declared chart are read."""
    o=eye() if frame is None else [[Q(z) for z in row] for row in frame]
    if mm(transpose(o),o)!=eye():
        raise ValueError('orthogonal chart required')
    determinant=(o[0][0]*(o[1][1]*o[2][2]-o[1][2]*o[2][1])
                 -o[0][1]*(o[1][0]*o[2][2]-o[1][2]*o[2][0])
                 +o[0][2]*(o[1][0]*o[2][1]-o[1][1]*o[2][0]))
    if determinant!=1:
        raise ValueError('proper oriented chart required for quaternion response')
    s_chart=mm(mm(transpose(o),residue(x)),o)
    return ResidualCarrier(tuple(coordinates(s_chart)),tuple(tuple(row) for row in o))


def distinguishing_future(x,z):
    """Audit witness: distinguish two already collided extraction inputs.

This constructs a possible test future AFTER comparing the records. It is not
an actual future value secretly passed to either extractor.
"""
    if x==z:
        raise ValueError('distinct boundaries required')
    if future_exists(x):
        y=one_existence_witness(x)
        if join(z,y)!=NEG_ONE:
            return dict(future=y,success_x=True,success_z=False)
    if future_exists(z):
        y=one_existence_witness(z)
        if join(x,y)!=NEG_ONE:
            return dict(future=y,success_x=False,success_z=True)
    raise AssertionError('distinct future-success families must be distinguishable')


def null_vector(a):
    reduced,piv=rref(a)
    free=next(j for j in range(5) if j not in piv)
    v=[Q(0)]*5
    v[free]=Q(1)
    for row,p in zip(reduced,piv):
        v[p]=-row[free]
    return v


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    bs=five_basis()
    states=[boundary(lincomb(c,bs)) for c in product((-1,0,1),repeat=5)]
    # A finite test of the analytic two-witness separation lemma.
    pairs=0
    for idx in range(len(states)):
        x,z=states[idx],states[(idx*37+11)%len(states)]
        if x==z:
            continue
        d=distinguishing_future(x,z)
        assert (join(x,d['future'])==NEG_ONE)==d['success_x']
        assert (join(z,d['future'])==NEG_ONE)==d['success_z']
        pairs+=1
    check('two canonical possible-future witnesses separate distinct current success families',True,pairs=pairs)
    axes=[outer(e) for e in eye()]
    x,z=axes[0],axes[1]
    feature_examples=[]
    for name,fn in [
        ('existence_flag',lambda a:future_exists(a)),
        ('residue_norm_squared',lambda a:inner(residue(a),residue(a))),
        ('spectral_invariants',lambda a:(inner(residue(a),residue(a)),tr(mm(mm(residue(a),residue(a)),residue(a))))),
        ('one_declared_future_response_plus_flag',lambda a:(future_exists(a),tuple(join(a,axes[2]))))]:
        assert fn(x)==fn(z)
        d=distinguishing_future(x,z)
        feature_examples.append(dict(extractor=name,current_x=x,current_z=z,
                                     same_extraction=True,same_existence_flag=True,witness=d))
    check('existence, magnitude, spectrum, and one response can all hide different successful futures',True,examples=feature_examples)
    dropped=[]
    for omitted in range(5):
        a=[[Q(j==i) for j in range(5)] for i in range(5) if i!=omitted]
        h=null_vector(a)
        base=[Q(0)]*5
        base[(omitted+1)%5]=Q(1)
        other=[v+w for v,w in zip(base,h)]
        x,z=boundary(from_coordinates(base)),boundary(from_coordinates(other))
        assert matvec(a,base)==matvec(a,other) and future_exists(x) and future_exists(z)
        d=distinguishing_future(x,z)
        dropped.append(dict(omitted_coordinate=omitted,projection=a,current_x=x,current_z=z,witness=d,
                            existence_flag_equal=True))
    check('each one-coordinate deletion loses a future-success distinction even with the existence flag retained',True,projections=5)
    # Test arbitrary rational rank-four maps rather than only coordinate deletion.
    arbitrary=[]
    for n in range(1,6):
        a=[[Q(i==j) if j<4 else Q((i+1)*n-2) for j in range(5)] for i in range(4)]
        h=null_vector(a)
        base=[Q(1),Q(0),Q(0),Q(0),Q(0)]
        other=[v+w for v,w in zip(base,h)]
        x,z=boundary(from_coordinates(base)),boundary(from_coordinates(other))
        assert matvec(a,base)==matvec(a,other) and future_exists(x) and future_exists(z)
        arbitrary.append(dict(map=a,kernel_direction=h,witness=distinguishing_future(x,z)))
    check('non-coordinate rank-four linear extractions have the same obstruction',True,maps=5)
    # Fixed rational proper rotation: future is transformed only when it arrives.
    o=[[Q(3,5),Q(-4,5),Q(0)],[Q(4,5),Q(3,5),Q(0)],[Q(0),Q(0),Q(1)]]
    futures=axes+[boundary(zero())]+[boundary(s) for s in bs]
    faithful=0
    rotated=0
    for x in states:
        plain,charted=extract(x),extract(x,o)
        assert plain.original_residue()==charted.original_residue()==residue(x)
        for y in futures:
            expected=join(x,y)
            assert plain.connect(y)==expected
            assert charted.connect(y)==expected
            faithful+=1
            rotated+=1
    check('five exact coordinates give a future-blind extractor with faithful later connections',True,cases=faithful)
    check('a declared chart change preserves exact operation semantics including the returned quaternion frame',True,cases=rotated)
    current_rank=[]
    for y in [axes[0],boundary([[Q(1,6),0,0],[0,0,0],[0,0,Q(-1,6)]])]:
        rows=[list(row) for row in zip(*(join(s,y) for s in bs))]
        _,piv=rref(rows)
        current_rank.append(dict(future=y,response_rank=len(piv),currently_invisible_dimensions=5-len(piv)))
    check('a single realized future allows a shallower response quotient than the whole possible-future family',
          [z['response_rank'] for z in current_rank]==[3,4],examples=current_rank)
    # Revealing a new future after a shallow read makes that lost difference matter.
    a,z=axes[1],axes[2]
    check('a difference invisible to one future is needed by another future',
          join(a,axes[0])==join(z,axes[0]) and join(a,axes[1])!=join(z,axes[1]),
          caution='one-response quotient is not automatically safe for later contexts')
    carrier=extract(axes[0])
    before=carrier.exact
    for y in futures:
        carrier.connect(y)
    check('later contexts never alter the already extracted single record',carrier.exact==before)
    root=Path(__file__).resolve().parent
    paths=[Path(__file__),root/'test_residual_extraction_transport.py',root/'future_existence_residual.py',
           root/'vendor/two_flower_kernel_certificate.py',root/'vendor/internal_port_certificate.py']
    return dict(note='RR36',passed=True,groups=len(checks),checks=checks,
                source_base_commit='e4fc0b5d562a35fcc44fa7bfac033ae942a05b4a',
                preservation_target='which permitted futures satisfy Omega(X,Y)=-1, not success against every future',
                scope='full signed symmetric trace-one B2 fibre; inherited RR31 join',
                conclusion='success-family preservation implies an injective extraction; a linear extraction has rank five',
                witness_pairs=pairs,feature_collisions=feature_examples,coordinate_deletions=dropped,
                arbitrary_linear_collisions=arbitrary,single_future_response_ranks=current_rank,
                faithful_connections=faithful,charted_connections=rotated,
                status='safe exact extraction implemented; future-specific selective deletion before the future is known not derived',
                source_sha256={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def encode(x):
    if isinstance(x,Q):
        return str(x)
    raise TypeError(type(x))


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('residual_extraction_transport_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'groups':data['groups'],'faithful_connections':data['faithful_connections'],
                      'charted_connections':data['charted_connections'],'compression_collision_maps':10}))
