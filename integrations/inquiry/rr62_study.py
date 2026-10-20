"""C -> requested observation -> inspection -> current actuation -> closure."""
from dataclasses import asdict
from fractions import Fraction as Q
from pathlib import Path
from collections import Counter
import hashlib,json
import demand_filter as f
import retained_execution as plant
from demand_filter import prior,d,te

HERE=Path(__file__).resolve().parent
OUTPUT=d.ROOT/'.work/rr62-local'
INPUT_SHA='5aea8291c577aa257e7a795ca8ba7b168bb1c17cee67256dfef0703bfc8d4e1f'
INPUT_COMMIT='5cace65874ef7334154b1b7e51bf77b04ba3b8ed'

def write(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,default=te.triple.encode)+'\n').encode())
def inputs():
    raw=(HERE/'RR62-inputs.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INPUT_SHA:raise ValueError('fixed inputs changed')
    return json.loads(raw)

def run():
    spec=inputs();archive=f.Archive();entries={};groups=[]
    def check(name,ok,**kw):
        groups.append(dict(name=name,passed=bool(ok),**kw))
        if not ok:raise AssertionError(name)
    for h in spec['histories']:
        history=prior.previous.begin(h['mode'],h['contact'],gain=Q(h['gain']))
        entries[h['name']]=archive.register(history,tuple(map(Q,spec['envelope'])))
    before={n:archive.history(e).digest for n,e in entries.items()}
    tasks=[];starts=[]
    for name,e in entries.items():
        for c in spec['future_frames']:
            req=prior.Requirement(prior.diagonal(Q(c['x'])))
            for domain in spec['domains']:
                for obs in spec['observations']:
                    scope=f.Scope(e.digest,req,tuple(map(Q,domain['interval'])),obs)
                    demand=f.assess(archive,e,scope)
                    tasks.append((name,c['name'],domain['name'],e,scope,demand))
                    starts.append(dict(history=name,C_name=c['name'],domain_name=domain['name'],
                        scope=asdict(scope),demand=asdict(demand),demand_digest=demand.digest,
                        exact_shift_read=False,new_source_produced=False,new_word_executed=False))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    write(OUTPUT/'starts.json',dict(input_sha256=INPUT_SHA,input_commit=INPUT_COMMIT,
        assessments=starts,assessments_count=len(starts),exact_shift_reads_in_assessment=0,
        envelope_authentication_is_a_separate_prior_exact_stage=True))
    check('all_168_scope_assessments_saved_before_inspection_or_execution',len(tasks)==168)
    meters={f.EXISTS:f.Meter(),f.ACTIONS:f.Meter()};resolved=[];rows=[]
    for name,cname,dname,e,scope,demand in tasks:
        r=f.resolve(archive,e,scope,demand,meters[scope.observation])
        oracle=f.exact_oracle(archive,e,scope)
        if (r.feasible,r.control)!=oracle:raise AssertionError('filtered result differs from exact retained-response oracle')
        resolved.append((name,cname,dname,e,scope,demand,r))
        rows.append(dict(history=name,C_name=cname,domain_name=dname,observation=scope.observation,
            status=demand.status,resolution=asdict(r),matches_exact_oracle=True))
    check('all_168_queries_match_full_exact_response_oracle',len(rows)==168)
    check('all_84_existence_queries_omit_exact_shift_read',meters[f.EXISTS].exact_shift_reads==0)
    action_reads=meters[f.ACTIONS].exact_shift_reads
    check('action_queries_inspect_only_when_the_scoped_result_requires_it',
          action_reads==sum(x[5].needs_exact_shift for x in resolved if x[4].observation==f.ACTIONS) and 0<action_reads<84,
          action_exact_shift_reads=action_reads)
    check('same_C_and_entry_can_skip_for_existence_but_inspect_for_actuation',all(
        f.assess(archive,e,f.Scope(e.digest,prior.Requirement(prior.diagonal(-1)),observation=f.EXISTS)).verdict is True
        and f.assess(archive,e,f.Scope(e.digest,prior.Requirement(prior.diagonal(-1)),observation=f.ACTIONS)).needs_exact_shift
        for e in entries.values()))
    print(json.dumps(dict(stage='assessments-and-resolution-complete',queries=168,
        shift_reads={k:v.exact_shift_reads for k,v in meters.items()})),flush=True)
    records=[];executed={}
    def do(name,e,scope,demand,r,word,kind,override=None):
        actual=plant.execute(archive,e,scope,demand,r,word,override)
        trial,decoded,ok=plant.future(archive,e,scope,demand,actual,override)
        row=dict(history=name,scope_digest=scope.digest,word=word,kind=kind,
            control=r.control if override is None else override,
            old_weights=actual.retained_source.leaves()[0].weights,
            new_weights=actual.new_source.leaves()[0].weights,
            current_endpoint=actual.closed_engine.upper.live.accumulated,
            future_actual=trial.live.accumulated,future_certified=ok,
            future_level=decoded.outputs[0].level if ok else None,
            retained_source_in_actual_word=actual.retained_source in actual.terminal.cell.beta,
            lower_before=actual.new_source.cell.start.live.accumulated,
            lower_after=actual.closed_engine.lower.live.accumulated,
            stock_count=len(actual.closed_engine.stock),event_kinds=[x.kind for x in actual.closed_engine.events])
        records.append(row);return actual,trial,ok
    full=[x for x in resolved if x[2]=='full' and x[4].observation==f.ACTIONS and x[6].feasible]
    for name,cname,dname,e,scope,demand,r in full:
        actual,trial,ok=do(name,e,scope,demand,r,'HHST','full-grid-realization')
        if not ok:raise AssertionError('predicted current action did not certify at C')
        executed[name,cname]=(e,scope,demand,r,actual)
    check('30_predicted_full_domain_realizations_certify_at_C',len(full)==30)
    first_name=spec['future_frames'][0]['name'];alternate={}
    for name in entries:
        e,scope,demand,r,actual=executed[name,first_name]
        alternate[name],_,ok=do(name,e,scope,demand,r,'HHTS','free-second-word')
        if not ok:raise AssertionError('second free word did not certify')
    check('same_C_preserves_two_current_word_choices',len(records)==33)
    e,scope,demand,r,keep=executed['keep',first_name]
    _,_,_,erased,erase=executed['erase',first_name]
    check('retained_difference_changes_the_actual_new_source_not_only_control_coordinates',
        r.control!=erased.control and keep.new_source.leaves()[0].weights!=erase.new_source.leaves()[0].weights
        and keep.new_source.kernel(scope.requirement.context)!=erase.new_source.kernel(scope.requirement.context))
    wrong,trial,ok=do('keep',e,scope,demand,r,'HHST','erased-control-used-with-retained-S',erased.control)
    s=archive.history(e).pair.shift
    check('erased_control_closes_current_but_fails_future_with_exact_predicted_defect',
        not ok and wrong.closed_engine.upper.live.accumulated==prior.NEG
        and trial.live.accumulated[0]-1==s*demand.g/demand.a,
        future_defect=trial.live.accumulated[0]-1)
    raw=te.pair.ordered_terminal_readout(keep.terminal)
    alt=te.pair.ordered_terminal_readout(alternate['keep'].terminal)
    new_tensor=d.tensor(keep.new_source.leaves()[0]);old_tensor=d.tensor(keep.retained_source.leaves()[0])
    check('equal_current_and_future_results_do_not_erase_ordered_connection_difference',
        raw!=alt and all(raw[i][j]-alt[i][j]==(new_tensor[i][j]-old_tensor[i][j])/21
                        for i in range(3) for j in range(3)))
    check('earlier_histories_and_actual_published_sources_remain_unchanged',
        all(archive.history(e).digest==before[n] and prior.previous.verify_flight(archive.history(e)) for n,e in entries.items()))
    counts=Counter(x['status'] for x in rows)
    result=dict(schema='time-engine-rr62-demand-directed-residue-v1',groups=groups,
        input_commit=INPUT_COMMIT,input_sha256=INPUT_SHA,
        starts_sha256=hashlib.sha256((OUTPUT/'starts.json').read_bytes()).hexdigest(),
        query_count=168,queries_by_observation={f.EXISTS:84,f.ACTIONS:84},status_counts=dict(counts),
        exact_shift_reads={k:v.exact_shift_reads for k,v in meters.items()},
        exact_retained_future_leaf_responses_in_assessment_and_resolution=0,
        full_response_oracle_calls=168,queries=rows,actual_executions=len(records),
        certified_future_closures=sum(r['future_certified'] for r in records),records=records,
        archive_authentication_and_execution_revalidation_excluded_from_omission_counts=True,
        full_TE_speedup_or_storage_reduction_measured=False,
        TE_exclusive_computational_principle_claimed=False,
        fixed_current_chart_and_two_word_family=True)
    write(OUTPUT/'result.json',result)
    print(json.dumps(dict(groups=len(groups),queries=168,statuses=dict(counts),executions=len(records),
        certified=result['certified_future_closures'],shift_reads=result['exact_shift_reads'])),flush=True)
    return result

if __name__=='__main__':run()
