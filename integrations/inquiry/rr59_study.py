"""Information available at an inspection trigger, and later validation.

Archived frames are supplied as simulated arrivals. All initiation records are
written before evaluating any closure outcome. No live LLM telemetry is used.
"""
from dataclasses import asdict
from fractions import Fraction as Q
from pathlib import Path
import json

import inquiry_probe as p
from inquiry_probe import d
import experiment as retained

HERE=Path(__file__).resolve().parent
OUTPUT=d.ROOT/'.work/rr59-local'
PARENT='ee74a88412b266900118e7927bfd3799b0404b75'


def write(path,value):
    path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,
                                default=d.embedded.triple.encode)+'\n').encode())


def perturbed_frame(future):
    y=[list(row) for row in future]
    y[0][0]+=Q(1,1024);y[1][1]-=Q(1,1024)
    return d.embedded.port.single.context(y)


def pair_with_shift(reference,shift,origin):
    leaf=d.AffineLetter(tuple(w+shift*v for w,v in zip(reference.representative.weights,
        reference.direction)),reference.original.library)
    return d.RetainedPair(leaf,reference.representative,shift,reference.direction,origin)


def representative_query(first,y,representative,origin):
    word=first.residue.terminal_operation.cell.beta
    source_leaves=first.residue.source.leaves()
    if len(source_leaves)!=1:
        raise ValueError('this declared source intervention requires one primitive leaf')
    source=source_leaves[0]
    groups=tuple(tuple(representative if leaf==source else leaf
                       for leaf in action.leaves()) for action in word)
    return d.WordQuery(groups,y,first.residue.terminal_operation.cell.start.live.accumulated,
        first.fixed_result,first.tolerance,origin)


def run():
    prepared,firsts,pairs,current,future,_=retained.fixtures()
    groups=[]
    def check(name,ok,**details):
        groups.append(dict(name=name,passed=bool(ok),**details))
        if not ok:raise AssertionError(name)
    local=d.Scope((current,),entry='RR59-arrival-current')
    later=d.Scope((future,),entry='RR59-arrival-later')
    shifted=d.Scope((perturbed_frame(future),),entry='RR59-arrival-perturbed-control')
    # This is a specified projection, not every datum currently accessible to
    # TE. The obstruction below applies only to detectors limited to it.
    # Persist the information used and decisions BEFORE computing any closure
    # verdict below. An external trusted digest is needed to authenticate a
    # saved log; the local digest by itself is not a wall-clock attestation.
    starts=[]
    for scope in (local,later,shifted):
        for i,pair in enumerate(pairs):
            signal=p.initiate(pair,scope)
            starts.append(dict(sequence=len(starts),contact=i,signal=asdict(signal),
                signal_digest=signal.digest,frame_arrival='simulated from archived data'))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    write(OUTPUT/'starts.json',dict(schema='time-engine-rr59-inspection-starts-v1',
        records=starts,rule='nonzero retained shift and nonzero arrived projected response',
        target_available_to_trigger=False,later_frames_available_to_trigger=False))
    start_digest=d.fingerprint(starts)
    features=tuple((pair.value,pair.original.kernel(current)) for pair in pairs)
    future_difference=tuple(pair.original.kernel(future)!=pair.representative.kernel(future)
                            for pair in pairs)
    check('same_projected_present_cannot_separate_later_relevance',
        len(set(features))==1 and future_difference==(False,True,True,True),
        identical_projected_features=4,later_kernel_difference=list(future_difference))
    local_signals=tuple(p.initiate(pair,local).requested for pair in pairs)
    later_signals=tuple(p.initiate(pair,later).requested for pair in pairs)
    check('an_arrived_projection_can_request_inspection_without_original_leaf_expansion',
        local_signals==(False,)*4 and later_signals==future_difference,
        current_requests=list(local_signals),later_requests=list(later_signals),
        exact_retained_leaf_calls_at_initiation=0,
        cost_scope='small-library responses, exact nonzero tests, input binding and hashing are still required')
    check('absence_of_a_current_signal_does_not_clear_future_scope',
        not any(local_signals) and sum(later_signals)==3,
        old_local_certificates_remain_valid=all(d.assess(pair,local).status==d.SAFE for pair in pairs))

    outcomes=[];meter=d.Meter()
    # Read all cases, including untriggered cases. This audit measures what the
    # trigger misses and over-selects; it is not a speedup experiment.
    for label,scope in (('later',later),('perturbed-control',shifted)):
        for i,first in enumerate(firsts):
            contact=first.receipt.contact_index
            pair=pairs[contact]
            original=d.query_from_first(first,scope.contexts[0],f'RR59-{label}-{i}-original')
            reference=representative_query(first,scope.contexts[0],pair.representative,
                                           f'RR59-{label}-{i}-representative')
            before=d.exact_preview(original,meter)[0]
            after=d.exact_preview(reference,meter)[0]
            # Also validate original RR58 bounded readout after the initiation.
            bounded=d.adaptive_preview(original,d.Meter())
            assert bounded.verdict==before
            outcomes.append(dict(frame=label,first=i,contact=contact,
                requested=p.initiate(pair,scope).requested,original_closes=before,
                representative_closes=after,closure_verdict_changes=before!=after,
                original_query_digest=original.digest,representative_query_digest=reference.digest))
    ordinary=[x for x in outcomes if x['frame']=='later']
    control=[x for x in outcomes if x['frame']=='perturbed-control']
    check('later_kernel_trigger_and_fixed_result_are_separately_audited',
        len(ordinary)==8 and any(x['closure_verdict_changes'] for x in ordinary),cases=ordinary)
    check('a_signal_need_not_change_the_requested_closure_verdict',
        sum(x['requested'] and not x['closure_verdict_changes'] for x in control)==6
        and not any(x['original_closes'] or x['representative_closes'] for x in control),cases=control)
    check('initiation_evidence_precedes_and_binds_the_outcome_stage',
        d.fingerprint(json.loads((OUTPUT/'starts.json').read_bytes())['records'])==start_digest,
        starts_digest=start_digest,initiation_records=12,outcome_queries=16,
        oracle_leaf_response_calls=meter.exact_retained_responses)

    controls=[]
    for shift in (Q(1,10**20),Q(10**50)):
        pair=pair_with_shift(pairs[0],shift,'RR59-declared-primitive-size-control-'+str(shift))
        origin_weights=pair.original.weights
        controls.append(dict(shift=str(shift),current=p.initiate(pair,local).requested,
            later=p.initiate(pair,later).requested,original_retained=pair.original.weights==origin_weights,
            scope='declared primitive chart control, not new certified stock'))
    check('size_is_not_the_initiation_rule_and_payloads_are_retained',
        all(not row['current'] and row['later'] and row['original_retained'] for row in controls),controls=controls)
    check('authenticated_original_records_remain_accessible',len(retained.actuals())==3,
        records={name:sha for name,(_,sha) in retained.actuals().items()})
    result=dict(date='2026-10-18',experiment='RR59 inspection initiation and later validation',
        parent_commit=PARENT,groups=groups,
        live_LLM_internal_state_measured=False,predictive_coding_mechanism_identified=False,
        trigger_rule_derived_from_TE_motion=False,actual_stock_or_closure_changed=False,
        speedup_or_unknown_future_recall_claimed=False,full_RR57_family_reenumerated=False)
    write(OUTPUT/'result.json',result)
    print(json.dumps(dict(passed=True,groups=len(groups),initiation_records=12,
        outcome_queries=16,later_requests=list(later_signals),
        signalled_without_closure_verdict_change=sum(x['requested'] and not x['closure_verdict_changes']
                                                   for x in control))),flush=True)
    return result


if __name__=='__main__':run()
