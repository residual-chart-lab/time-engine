"""RR60: connect an actual closed flower; inspect before constructing its port.

Only the first flower's local fixture and authenticated completed 3+1 inputs
are used before the notices are saved. No next-frame schedule is supplied.
"""
from dataclasses import asdict
from functools import lru_cache
from fractions import Fraction as Q
from pathlib import Path
import json

import internal_port as m
from internal_port import d,te
import rr59_study as prior

OUTPUT=d.ROOT/'.work/rr60-local'


def write(path,value):
    path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,
                                default=te.triple.encode)+'\n').encode())


@lru_cache(maxsize=3)
def flights(mode):return tuple(m.begin(mode,i,j) for i in range(4) for j in range(2))


def cases():
    rows=[]
    for mode in ('keep','erase','restore'):
        for i,flight in enumerate(flights(mode)):
            rows.append((f'{mode}-{i}-default',m.request_connection(flight)))
    for strength in (Q(0),Q(1,2048),Q(1,512)):
        for i,flight in enumerate(flights('keep')):
            rows.append((f'keep-{i}-strength-{strength}',m.request_connection(
                flight,te.pair.ConnectionSpec(strength=strength))))
    return tuple(rows)


def run():
    groups=[]
    def check(name,ok,**details):
        groups.append(dict(name=name,passed=bool(ok),**details))
        if not ok:raise AssertionError(name)
    requests=cases()
    # Persist starts before constructing ANY next context or second source.
    starts=[]
    for name,r in requests:
        receipt=r.flight.first.receipt
        starts.append(dict(name=name,mode=receipt.prepared.state.mode,contact=receipt.contact_index,
            petal=receipt.petal_choice,notice=asdict(r.notice),notice_digest=r.notice.digest,
            retained_shift=str(r.flight.pair.shift),waiting_phase=r.waiting.phase,
            last_actual_event=r.waiting.events[-1].kind,
            actual_event_index=r.waiting.events[-1].index,
            context_constructed=False,next_source_planned=False))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    write(OUTPUT/'starts.json',dict(schema='time-engine-rr60-internal-port-starts-v1',records=starts,
        source='actual local closure and current connection request, then unchanged RR53 readout obligation',
        new_future_context_supplied=False,global_future_requirement_used=False))
    starts_sha=d.fingerprint(starts)
    unique=tuple(f for mode in ('keep','erase','restore') for f in flights(mode))
    check('24_local_flowers_actually_close_before_any_next_context_is_constructed',
        len(unique)==24 and all(f.first.actual_endpoint==f.first.fixed_result and
            f.first.closed_engine.phase=='IDLE' and f.first.closed_engine.pending is None
            and f.local_certificate.status==d.SAFE for f in unique))
    check('48_current_connection_requests_automatically_create_bound_notices',
        len(requests)==48 and all(r.waiting.phase=='WAIT_CONTEXT' and
            r.waiting.events[-1].kind=='boundary-requested' for _,r in requests),notices=len(requests))
    check('the_actual_word_determines_the_transport_coefficient',
        {m.leaf_view(f)[2] for f in unique if f.first.receipt.petal_choice==0}=={Q(1,2)} and
        {m.leaf_view(f)[2] for f in unique if f.first.receipt.petal_choice==1}=={Q(11,21)},
        short='1/2',detour='11/21')

    deliveries={};rows=[];meter=d.Meter()
    for name,request in requests:
        delivered=m.emit(request);deliveries[name]=delivered
        flight=request.flight;first=flight.first;signal=request.notice
        _,reference=m.reference_context(flight,request.spec)
        delta_ok=all(delivered.context[i][j]-reference[i][j]==request.spec.strength*
            signal.source_mass*flight.pair.shift*signal.direction[i][j]
            for i in range(3) for j in range(3))
        assert delta_ok and signal.requested==(delivered.context!=reference)
        source_scope=delivered.exposure.scope
        recovered=d.read(flight.pair,source_scope,meter)
        assert recovered==flight.pair.original.kernel(delivered.context)
        before=first.closed_engine;after=delivered.arrived
        retained=(after.lower.live.accumulated==before.lower.live.accumulated and
            after.upper.live.accumulated==before.upper.live.accumulated and
            after.lower.executed_word==before.lower.executed_word and
            after.upper.executed_word==before.upper.executed_word and
            after.stock==before.stock and after.outputs==before.outputs and
            after.events[:len(before.events)]==before.events)
        assert retained and after.phase=='OPEN'
        rows.append(dict(name=name,requested=signal.requested,
            arrived_kernel_exposes_difference=delivered.exposure.requested,
            exact_transport_defect_identity=delta_ok,inheritance_and_stock_preserved=retained,
            context_digest=d.fingerprint(delivered.context),reference_context_digest=d.fingerprint(reference),
            arrived_factor=[str(x) for x in delivered.exposure.factor],
            recovered_response_digest=d.fingerprint(recovered),next_phase=after.phase))
    check('the_factorized_notice_exactly_detects_next_context_substitution',
        all(row['exact_transport_defect_identity'] for row in rows),cases=rows)
    zero=[row for row in rows if row['name'].endswith('strength-0')]
    check('cutting_the_existing_connection_prevents_the_onset',
        len(zero)==8 and not any(row['requested'] or row['arrived_kernel_exposes_difference'] for row in zero),
        contexts_equal_to_anchor=all(deliveries[name].context==te.pair.boundary_readout(
            r.flight.first.closed_engine.designated_head) for name,r in requests if r.spec.strength==0))
    default={mode:[row for row in rows if row['name'].startswith(mode+'-') and row['name'].endswith('-default')]
             for mode in ('keep','erase','restore')}
    check('erasure_and_restoration_change_the_internally_generated_inspection',
        sum(row['requested'] for row in default['keep'])==6 and
        not any(row['requested'] for row in default['erase']) and
        [r['context_digest'] for r in default['keep']]==[r['context_digest'] for r in default['restore']],
        notice_counts={mode:sum(row['requested'] for row in values) for mode,values in default.items()})
    check('all_declared_arrivals_reexpose_the_retained_response_without_rewriting_the_first_flower',
        all(row['requested']==row['arrived_kernel_exposes_difference'] and row['inheritance_and_stock_preserved']
            for row in rows),exact_preserved_response_reads=meter.exact_retained_responses,
        cost_scope='post-notice source-response reads only; excludes entry certification and exact port construction')

    controls=[]
    for petal in (0,1):
        flight=flights('keep')[2+petal];spec=te.pair.ConnectionSpec()
        pair,y,reference=m.cancellation_control(flight,spec)
        old=d.assess(pair,d.Scope((flight.first.residue.internal_context,),entry='RR60-control-current'))
        scope=d.Scope((y,),entry='RR60-control-self-generated-frame')
        signal=m.probe.initiate(pair,scope)
        assert pair.shift and y!=reference and old.status==d.SAFE and not signal.requested
        assert d.assess(pair,scope).status==d.SAFE
        assert pair.original.kernel(y)==pair.representative.kernel(y)
        controls.append(dict(petal=petal,shift=str(pair.shift),shift_approx=float(pair.shift),
            generated_context_changes=True,arrived_kernel_exposes_difference=False,
            current_response_unchanged=True,regular=d.regular(y,pair.original.library),
            scope='primitive source-line counterexample; not a new authenticated 3+1 contact or published stock'))
    check('pointwise_kernel_silence_is_not_a_next_context_replacement_certificate',
        len(controls)==2 and all(c['regular'] for c in controls),controls=controls)

    # The current branch/word choice is fixed, not selected by future success.
    chosen=deliveries['keep-2-default']
    if not chosen.notice.requested:raise AssertionError('the declared continuation starts after an inspection request')
    second,certificate=m.continue_one(chosen,branch=0,petal=0)
    before=chosen.flight.first.closed_engine;after=second.closed_engine
    exact_prefix=(after.events[:len(before.events)]==before.events and after.stock[:len(before.stock)]==before.stock)
    check('after_inspection_one_existing_legal_source_and_second_flower_actually_close',
        exact_prefix and len(after.stock)==len(before.stock)+1 and len(after.outputs)==len(before.outputs)+1
        and second.closure_error<second.tolerance/2 and after.phase=='IDLE' and after.pending is None,
        consumer_output_level=second.residue.terminal_operation.level,
        actual_new_published_sources=1,closure_error=str(second.closure_error),
        actual_endpoint=[str(x) for x in second.actual_endpoint],
        first_event_after_old_prefix=after.events[len(before.events)].kind,
        certificate=dict(branch=certificate.selected_branch,representative=str(certificate.representative),
                         polynomial_digest=d.fingerprint(certificate.polynomial)))
    archived=prior.retained.actuals()
    old=archived['keep-alternate'][0].actual_records
    check('the_first_and_second_actual_records_match_the_preexisting_RR57_witness',
        chosen.flight.first==old[0] and second==old[1],
        authenticated_record_sha256=archived['keep-alternate'][1],
        archived_upper_requirement_not_used_to_generate_the_notice=True)
    check('start_records_remain_unchanged_after_arrival_and_completion',
        d.fingerprint(json.loads((OUTPUT/'starts.json').read_bytes())['records'])==starts_sha,
        starts_digest=starts_sha)
    result=dict(date='2026-10-19',experiment='RR60 internally generated port-inspection obligation',
        parent_commit=m.PARENT,groups=groups,next_contexts_constructed_from_actual_closed_history=True,
        connection_law_and_gain_derived_from_first_principles=False,
        general_predictive_coding_or_attention_mechanism_derived=False,
        future_requirements_supply_a_new_driving_force=False,
        live_LLM_internal_telemetry_measured=False,full_128_family_reenumerated=False)
    write(OUTPUT/'result.json',result)
    print(json.dumps(dict(passed=True,groups=len(groups),local_flowers=24,current_requests=48,
        notices={mode:sum(row['requested'] for row in values) for mode,values in default.items()},
        post_notice_second_flower_closed=True,cancellation_controls=2)),flush=True)
    return result


if __name__=='__main__':run()
