"""RR52 v002: apply an actual, saved one-flower operation to a reference state.

The completed record is loaded/validated against an externally supplied entry
configuration first. Reading then uses its trusted immutable commitment receipt;
it neither searches possible histories nor produces another flower. Visible
normalization is a diagnostic convention, not an edit to the actual endpoint.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json

from completed_single_flower import (
    Configuration, Commitment, FlowerRecord, FlowerMachine, import_record,
    expected_execution, close, context, UpperState, encode,
)
from recursive_upper_decoder import qmul, inverse, regular
from robust_flower_geometry import Interval, diagonal


@dataclass(frozen=True)
class ReferenceInput:
    live: UpperState
    level: int=3

    def __post_init__(self):
        if type(self.level) is not int or self.level<1:
            raise ValueError('a declared positive reference level is required')
        if not isinstance(self.live,UpperState) or len(self.live.accumulated)!=4:
            raise ValueError('a four-component typed reference state is required')
        y=context(self.live.context)
        q=tuple(Q(x) for x in self.live.accumulated)
        object.__setattr__(self,'live',UpperState(y,q))


@dataclass(frozen=True)
class ReferenceResponse:
    before: ReferenceInput
    after: UpperState
    visible_only_after: UpperState
    residue_effect: tuple
    visible_normalized_after: UpperState


def verify_completed_against_receipt(record,receipt):
    """Recheck actual completion only, against an already trusted receipt.

    Canonical entry/selection validation is performed by import_record, once.
    This smaller replay checks actual prefix/inheritance, fixed request, exact
    certificate and retained payload. No root solving or candidate enumeration.
    A caller changing both receipt and record is changing the external trust
    anchor; this is not cryptographic authentication of an author.
    """
    if type(record) is not FlowerRecord or type(receipt) is not Commitment:
        raise ValueError('an actual completed record and trusted receipt are required')
    engine=expected_execution(receipt,len(receipt.word))
    machine=FlowerMachine(receipt.anchor,'EXECUTED',engine,receipt.problem.representative,
        receipt.problem,(),receipt,len(receipt.word))
    if record!=close(machine,receipt).record:
        raise ValueError('the actual completed occurrence differs from its trusted receipt')
    return True


def read_retained(record,receipt,reference):
    """The retained nested operation actually updates a current reference state."""
    verify_completed_against_receipt(record,receipt)
    if not isinstance(reference,ReferenceInput):
        raise ValueError('a typed reference input is required')
    operation=record.residue.terminal_operation
    if operation.level!=reference.level:
        raise ValueError('reference and retained operation must have the same level')
    leaves=operation.leaves();library=leaves[-1].library
    if any(a.library!=library for a in leaves) or not regular(reference.live.context,library):
        raise ValueError('the reference must stay in the declared regular chart')
    after=operation.execute(reference.live)
    visible=UpperState(reference.live.context,tuple(qmul(operation.visible,reference.live.accumulated)))
    normalized=UpperState(reference.live.context,tuple(qmul(inverse(operation.visible),after.accumulated)))
    return ReferenceResponse(reference,after,visible,
        tuple(a-b for a,b in zip(after.accumulated,visible.accumulated)),normalized)


def load_published(branch,choice):
    root=Path(__file__).resolve().parent
    path=root/f'examples/{branch}-choice-{choice}.record.json'
    payload=json.loads(path.read_text(encoding='utf-8'))
    return import_record(payload,Configuration(source_branch=branch,petal_choice=choice))


def diagonal_kernel_interval(operation,coordinates):
    """Independent scalar product formula for the saved baseline leaves.

    Each used affine leaf has weights only on the first three axis sources.
    For diagonal trace-one Y, their joins are 2*y_i-1. This validates that
    representation before using 2*sum(w_i*y_i)-1, not merely fitting samples.
    """
    value=Interval.cast(1)
    for leaf in operation.leaves():
        if any(leaf.weights[3:]):
            raise ValueError('the diagonal scalar interval formula has a restricted domain')
        for index,source in enumerate(leaf.library[:3]):
            endpoint=source.source.endpoint
            expected=tuple(tuple(Q(i==j==index) for j in range(3)) for i in range(3))
            if endpoint!=expected: raise ValueError('the first three certified sources must be axis projectors')
        factor=2*sum(w*y for w,y in zip(leaf.weights[:3],coordinates))-1
        value=factor*value
    return value


def reference_neighborhood(short,long,radius=Q(1,10**6)):
    """Rational interval proof on a two-dimensional box of reference contexts.

    Not a theorem for arbitrary quaternion model perturbations. The saved
    sources, histories and actual endpoints are held fixed in this comparison.
    """
    radius=Q(radius)
    if radius<=0: raise ValueError('a positive reference radius is required')
    y0=short.commitment.anchor.original.designated_head.cell.start.live.context
    if y0!=long.commitment.anchor.original.designated_head.cell.start.live.context:
        raise ValueError('a common reference center is required')
    center=tuple(y0[i][i] for i in range(3))
    coordinates=(Interval(center[0]-radius,center[0]+radius),
                 Interval(center[1]-radius,center[1]+radius),
                 Interval(center[2]-2*radius,center[2]+2*radius))
    # This bounding box encloses all y=(c1+d1,c2+d2,c3-d1-d2).
    # Distinct diagonal entries imply rank five for the original six-generator
    # affine chart (RR48). Test this criterion uniformly, not just at corners.
    gaps=[coordinates[i]-coordinates[j] for i,j in ((0,1),(0,2),(1,2))]
    if not all(g.excludes_zero() for g in gaps):
        raise AssertionError('the entire reference box must stay regular')
    operations=(short.residue.terminal_operation,long.residue.terminal_operation)
    values=[diagonal_kernel_interval(op,coordinates) for op in operations]
    for op in operations:
        if any(op.visible[1:]) or op.visible[0]==0:
            raise ValueError('the interval proof is for nonzero scalar visible responses')
    raw=values[1]-values[0]
    normalized=values[1]/operations[1].visible[0]-values[0]/operations[0].visible[0]
    if not raw.excludes_zero() or not normalized.excludes_zero():
        raise AssertionError('the retained distinction must survive throughout the reference box')
    return dict(radius=radius,center=center,coordinates=[a.as_pair() for a in coordinates],
        parametrization='diag(c1+d1,c2+d2,c3-d1-d2), |d1|,|d2| <= radius',
        raw_long_minus_short=raw.as_pair(),raw_abs_lower=raw.min_abs(),
        visible_normalized_long_minus_short=normalized.as_pair(),normalized_abs_lower=normalized.min_abs(),
        chart_gaps=[g.as_pair() for g in gaps],
        scope='all real references in this two-dimensional box; same saved baseline records; q=1')


def run():
    checks=[];comparisons=[];neighborhoods=[];records={}
    def check(name,ok,**details):
        if not ok: raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    for branch in ('first','second'):
        short=load_published(branch,0);long=load_published(branch,1)
        records[branch]=(short,long)
        check(branch+': saved actual histories share F and epsilon, not clamped endpoints',
            short.fixed_result==long.fixed_result and short.tolerance==long.tolerance
            and short.actual_endpoint!=long.actual_endpoint
            and short.residue!=long.residue and len(short.commitment.word)==2 and len(long.commitment.word)==4,
            fixed_result=short.fixed_result,tolerance=short.tolerance,
            short_actual=short.actual_endpoint,long_actual=long.actual_endpoint)
        current=short.commitment.anchor.current_context
        origin=short.commitment.anchor.original.designated_head.cell.start.live.context
        views={}
        for name,y in (('current_correction',current),('closing',short.residue.internal_context),('changed_reference',origin)):
            pair=[read_retained(r,r.commitment,ReferenceInput(UpperState(y))) for r in (short,long)]
            views[name]=[dict(raw=p.after.accumulated,visible_only=p.visible_only_after.accumulated,
                residue_effect=p.residue_effect,normalized=p.visible_normalized_after.accumulated) for p in pair]
        comparisons.append(dict(branch=branch,reference_views=views))
        check(branch+': the raw current correction reference is exactly blind',
              views['current_correction'][0]['raw']==views['current_correction'][1]['raw']==(1,0,0,0))
        check(branch+': visible normalization removes the actual endpoint gain at closure',
              all(v['normalized']==(1,0,0,0) for v in views['closing']),
              normalization='left multiply by inverse of each retained actual visible multiplier; no record edit')
        check(branch+': a changed present reference reads a retained distinction beyond visible gain',
              views['changed_reference'][0]['raw']!=views['changed_reference'][1]['raw']
              and views['changed_reference'][0]['normalized']!=views['changed_reference'][1]['normalized'])
        proof=reference_neighborhood(short,long);neighborhoods.append(dict(branch=branch,certificate=proof))
    check('the distinction survives a continuous box of changed references on both branches',
          all(p['certificate']['normalized_abs_lower']>0 for p in neighborhoods),certificates=neighborhoods)
    extended=[]
    for branch,(short,long) in records.items():
        proof=next(p['certificate'] for p in neighborhoods if p['branch']==branch)
        center=proof['center'];radius=proof['radius']
        for signs in product((-1,1),repeat=2):
            y=diagonal((center[0]+signs[0]*radius,center[1]+signs[1]*radius,
                        center[2]-(signs[0]+signs[1])*radius))
            reference=ReferenceInput(UpperState(y,(Q(1),Q(2),Q(-1),Q(3))))
            pair=[read_retained(r,r.commitment,reference) for r in (short,long)]
            if pair[0].after==pair[1].after or pair[0].visible_normalized_after==pair[1].visible_normalized_after:
                raise AssertionError('the difference must act on the new nontrivial quaternion state')
            for r,p in zip((short,long),pair):
                scalar=diagonal_kernel_interval(r.residue.terminal_operation,tuple(Interval(y[i][i],y[i][i]) for i in range(3)))
                if r.residue.terminal_operation.kernel(y)!=(scalar.lo,0,0,0) or scalar.lo!=scalar.hi:
                    raise AssertionError('independent formula disagrees with actual retained execution')
            extended.append(dict(branch=branch,signs=signs,before=reference.live.accumulated,
                short_after=pair[0].after.accumulated,long_after=pair[1].after.accumulated))
    check('eight perturbed references change a nontrivial present quaternion through actual saved operations',
          len(extended)==8,readings=extended)
    root=Path(__file__).resolve().parent
    old=json.loads((root/'completed_single_flower_result.json').read_text(encoding='utf-8'))
    paths=['retrospective_residue_readout.py','test_retrospective_residue_readout.py',*old['source_sha256']]
    return dict(note='RR52',version='002',passed=True,groups=len(checks),checks=checks,
        comparisons=comparisons,new_flower_generated=False,subjective_experience_claimed=False,
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in paths},
        input_record_sha256={f'examples/{branch}-choice-{choice}.record.json':
            hashlib.sha256((root/f'examples/{branch}-choice-{choice}.record.json').read_bytes()).hexdigest()
            for branch in ('first','second') for choice in (0,1)})


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('retrospective_residue_readout_result.json').write_text(
        json.dumps(result,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=result['groups'],saved_records=4,uniform_reference_boxes=2)))
