"""Evaluate EVERY precommitted independent C; save decisions before execution."""
from dataclasses import asdict
from fractions import Fraction as Q
from pathlib import Path
from collections import Counter
import hashlib,json

import future_pullback as m
from future_pullback import d,te

HERE=Path(__file__).resolve().parent
OUTPUT=d.ROOT/'.work/rr61-local'
INPUT_SHA='4656807bc1229acd8318ee372303f744eadd877c25be6987359b06b9845f40f5'
INPUT_COMMIT='93004cf57e5286a927e7a0e07d4c07ef142f883d'

def write(path,value):
    path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,default=te.triple.encode)+'\n').encode())

def load_inputs():
    raw=(HERE/'RR61-inputs.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INPUT_SHA:raise ValueError('the precommitted inputs changed')
    return json.loads(raw)

def projection(f):
    e=f.first.closed_engine;y=f.first.residue.internal_context
    return (y,e.lower.live.accumulated,e.upper.live.accumulated,
            e.designated_head.kernel(y),f.pair.original.kernel(y),f.first.actual_endpoint)

def record_row(name,decision,execution,trial,decoded,ok,kind):
    e=execution.closed_engine
    return dict(history=name,requirement_digest=decision.requirement.digest,
        context=decision.requirement.context,target=decision.requirement.target,
        decision_digest=decision.digest,control=execution.control,word=execution.word,kind=kind,
        source_weights=execution.source.leaves()[0].weights,
        current_endpoint=e.upper.live.accumulated,future_actual=trial.live.accumulated,
        future_certified=ok,future_output_level=decoded.outputs[0].level if ok else None,
        source_level=execution.source.level,current_output_level=execution.terminal.level,
        actual_source_start=execution.source.cell.start.live.accumulated,
        lower_endpoint=e.lower.live.accumulated,stock_count=len(e.stock),
        rounds=len(e.rounds),events=len(e.events),prefix_errors=execution.prefix_errors,
        event_kinds=tuple(x.kind for x in e.events),
        replay_protocol='recreate authenticated history, decision and selected current word; exact decoder again')

def run():
    inputs=load_inputs();groups=[]
    def check(name,ok,**kw):
        groups.append(dict(name=name,passed=bool(ok),**kw))
        if not ok:raise AssertionError(name)
    histories={};rejections=[]
    for spec in inputs['histories']:
        try:histories[spec['name']]=m.previous.begin(spec['mode'],spec['contact'],gain=Q(spec['gain']))
        except ValueError as exc:
            rejections.append(dict(history=spec['name'],declared=spec,status='REJECTED_INPUT',reason=str(exc),
                C_cases_not_evaluated=len(inputs['future_frames']),success_outcome_not_observed=True))
    check('all_preregistered_inputs_accounted_for_including_invalid_large_gain',
          len(histories)==3 and len(rejections)==1 and rejections[0]['history']=='large-history-control')
    check('same_current_observables_but_retained_histories_differ',
          len({projection(f) for f in histories.values()})==1 and
          histories['erase'].pair.original!=histories['keep'].pair.original and
          histories['keep'].pair.original==histories['restore'].pair.original)
    decisions=[];starts=[]
    for name,f in histories.items():
        for spec in inputs['future_frames']:
            req=m.Requirement(m.diagonal(Q(spec['x'])))
            decision=m.derive(f,req,tuple(map(Q,inputs['control_domain'])))
            forward=m.forward_reachability(f,req,decision.domain)
            same=(decision.control,decision.all_controls,decision.algebraically_feasible,decision.chart_regular)==(
                forward.control,forward.all_controls,forward.algebraically_feasible,forward.chart_regular)
            if not same:raise AssertionError('backward/forward disagreement')
            decisions.append((name,spec,f,decision,forward))
            starts.append(dict(history=name,C_name=spec['name'],x=spec['x'],decision=asdict(decision),
                decision_digest=decision.digest,forward=asdict(forward),same_admissible_set=same,
                actual_history_events=len(f.first.closed_engine.events),
                new_current_source_produced=False,new_current_word_executed=False,future_word_executed=False))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    write(OUTPUT/'starts.json',dict(input_sha256=INPUT_SHA,input_commit=INPUT_COMMIT,
        decisions=starts,rejected_inputs=rejections,decision_count=len(starts),
        future_path_enumerations=0,all_decisions_saved_before_any_new_current_or_future_execution=True))
    starts_sha=hashlib.sha256((OUTPUT/'starts.json').read_bytes()).hexdigest()
    check('42_independent_C_decisions_before_new_execution_and_forward_equivalence',len(starts)==42)
    counts=Counter(row['decision']['status'] for row in starts)
    check('success_failure_blind_and_nonregular_cases_all_retained',counts=={
        'ADMISSIBLE':30,'ALGEBRAIC_ONLY':6,'EMPTY_ZERO_HEAD':3,'EMPTY_BLIND':3},counts=dict(counts))
    check('every_visible_retained_shift_changes_current_control_exactly',all(
        m.derive(histories['erase'],v.requirement).control-v.control==histories['keep'].pair.shift
        for name,_,_,v,_ in decisions if name=='keep' and v.control is not None))
    records=[]
    for name,spec,f,v,forward in decisions:
        if v.status!='ADMISSIBLE':continue
        run=m.execute_current(f,v,'HS');trial,decoded,ok=m.read_future(f,v,run)
        if not ok:raise AssertionError('predicted certified realization failed')
        records.append(record_row(name,v,run,trial,decoded,ok,'independent-grid-execution'))
    check('all_30_regular_predicted_HS_realizations_certify_exactly',len(records)==30 and all(
        r['current_endpoint']==m.NEG and r['future_actual']==m.ONE and r['future_output_level']==4 for r in records))
    # Choice tests use the FIRST grid input, not a retrospectively selected C.
    c=m.Requirement(m.diagonal(Q(inputs['future_frames'][0]['x'])))
    for name,f in histories.items():
        v=m.derive(f,c)
        for word in inputs['free_execution_words'][1:]:
            run=m.execute_current(f,v,word);trial,decoded,ok=m.read_future(f,v,run)
            if not ok:raise AssertionError('the additional free word failed')
            records.append(record_row(name,v,run,trial,decoded,ok,'current-free-word-execution'))
    check('one_C_leaves_three_distinct_current_words_with_actual_certificates',len(records)==36)
    f=histories['keep'];v=m.derive(f,c);erased=m.derive(histories['erase'],c)
    wrong=m.execute_current(f,v,'HS',erased.control,allow_control_test=True)
    trial,decoded,ok=m.read_future(f,v,wrong,allow_control_test=True)
    defect=trial.live.accumulated[0]-1
    check('reusing_erased_control_preserves_current_but_changes_future_exactly',
        wrong.closed_engine.upper.live.accumulated==m.NEG and not ok and defect==-v.h*v.g*v.retained_shift,
        exact_future_defect=defect)
    records.append(record_row('keep',v,wrong,trial,decoded,ok,'wrong-history-control'))
    even=m.execute_current(f,v,inputs['negative_even_word'],allow_control_test=True)
    trial,decoded,ok=m.read_future(f,v,even,allow_control_test=True)
    check('even_pair_count_is_locally_valid_but_future_requirement_rejects_it',
        even.closed_engine.upper.live.accumulated==m.NEG and trial.live.accumulated==m.NEG and not ok)
    records.append(record_row('keep',v,even,trial,decoded,ok,'even-parity-control'))
    check('needed_retained_channel_is_present_iff_h_times_g_is_nonzero',
          all((forward.slope!=0)==bool(v.h*v.g) for _,_,_,v,forward in decisions))
    check('the_geometric_axis_matches_but_does_not_use_the_old_pivot_axis',all(
        tuple(m.geom.geometry(f.first.residue.internal_context,f.pair.original.library).coefficient_axis)==f.pair.direction
        for f in histories.values()))
    check('original_histories_remain_exactly_replayable_after_all_current_and_future_runs',
          all(m.previous.verify_flight(f) for f in histories.values()))
    result=dict(schema='time-engine-rr61-independent-C-pullback-v1',input_commit=INPUT_COMMIT,
        input_sha256=INPUT_SHA,starts_sha256=starts_sha,groups=groups,decisions=len(starts),
        counts=dict(counts),rejected_inputs=rejections,current_and_future_executions=len(records),
        certified_future_closures=sum(r['future_certified'] for r in records),records=records,
        forward_and_pullback_mathematically_equivalent_in_declared_class=True,
        TE_exclusive_property_demonstrated=False,physical_retrocausal_force_demonstrated=False,
        independent_C_derived_from_success_path=False,future_path_enumerations_in_decision=0,
        general_nondiagonal_or_arbitrary_stock_theorem=False,old_RR53_port_claimed_for_new_C=False)
    write(OUTPUT/'result.json',result)
    print(json.dumps(dict(groups=len(groups),decisions=len(starts),statuses=dict(counts),
        executions=len(records),certified=result['certified_future_closures'],forward_equivalent=True)),flush=True)
    return result

if __name__=='__main__':run()
