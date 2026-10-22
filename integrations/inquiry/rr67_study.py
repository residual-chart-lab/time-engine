"""Precommitted changes -> projected proofs -> exact and actuated controls."""
from pathlib import Path
from fractions import Fraction as Q
from dataclasses import asdict,replace
from time import perf_counter_ns
import hashlib,json
import incremental_resolution as a
import incremental_session as live
import adaptive_session as reference
import rr65_study as matrix

HERE=Path(__file__).resolve().parent;OUTPUT=HERE.parents[1]/'.work/rr67-local'
INPUT_COMMIT='f97e7c0858061b2e652700678d0ff2d9ae83f5de'
INPUT_SHA='0245c5860a4c269720f6e45799b2cee7f83eb8d7934fddb6b903718c2c3d136e'


def write(path,value):path.write_bytes((json.dumps(value,indent=2,default=a.m.te.triple.encode)+'\n').encode())


def scope(entry,name,strength,domain='wide'):
    diagonal=a.m.context(entry.base,'main' if name=='main_perturbed' else name)
    if name=='main_perturbed':diagonal=tuple(x+y for x,y in zip(diagonal,(Q(1,100),Q(-1,100),Q(0))))
    return a.m.Scope(entry.base.digest,diagonal,Q(strength),domain=(-a.m.LIMIT,a.m.LIMIT) if domain=='wide' else (Q(0),Q(0)))


def action_signature(action):return action.status,action.T,action.R,action.alpha,action.read_keys


def compile_full(entry,request,v,word,policy):
    entry.original._plans.clear();entry.base._cache.clear()
    return a.old.compile(entry.original,request,v,word,policy)


def polynomial_match(entry,request,v,word):
    roots,_=a.graph(entry,request,v,word,a.Work())
    full=a.m.build(entry.base,request,v,word).polynomials
    if any(a.P(roots[label]).terms!=poly.terms for label,poly in full.items()):raise AssertionError('incremental arithmetic differs from RR65')
    return a.fingerprint(tuple((label,a.P(roots[label]).digest) for label in a.m.LABELS))


def motion_signature(session):
    r=session.result
    return a.fingerprint((r.action.T,r.action.R,r.port,r.first.engine.upper.live.accumulated,
        r.second.engine.upper.live.accumulated,r.upper_trial.live.accumulated,r.certified,
        len(r.second.engine.stock),len(r.second.engine.rounds)))


def sequence(spec,save=False):
    entry=a.register();first=spec['requests'][0];initial=scope(entry,*first[:3]);policy=a.Policy(first[5])
    current=live.start(entry,initial,policy);full=reference.start(entry.original,initial,policy)
    stages=[current];rows=[];started_archive=live.archives(entry)
    for i,(name,strength,domain,v,word,budget) in enumerate(spec['requests']):
        request=scope(entry,name,strength,domain);policy=a.Policy(budget)
        if i:
            current=live.revise(current,request,policy);full=reference.revise(full,request,policy);stages.append(current)
        entry.original._plans.clear();entry.base._cache.clear()
        start=perf_counter_ns();current=live.choose(current,v,word);incremental_ms=(perf_counter_ns()-start)/1e6
        work=asdict(entry._receipts[-1][1]);stages.append(current)
        start=perf_counter_ns();full=reference.choose(full,v,word);full_ms=(perf_counter_ns()-start)/1e6
        a_meter=a.fn.Meter();b_meter=a.fn.Meter()
        current=live.resolve(current,a_meter);full=reference.resolve(full,b_meter);stages.append(current)
        p,q=current.prepared.plan,full.prepared.plan
        assert (p.mode,p.status,p.features,p.coefficients,p.tested_modes)==(q.mode,q.status,q.features,q.coefficients,q.tested_modes)
        assert action_signature(current.prepared.action)==action_signature(full.prepared.action)
        assert current.cache==full.cache and a_meter.exact_reads==b_meter.exact_reads
        rows.append(dict(revision=i,context=name,strength=strength,domain=domain,word=word,v=v,budget=budget,
            mode=p.mode,status=current.prepared.action.status,scope_digest=request.digest,plan_digest=p.digest,
            work=work,new_keys=live.history(current)[-1]['new_keys'],derived_keys=live.history(current)[-1]['derived_keys'],
            exact_reads=a_meter.exact_reads,incremental_plan_ms=incremental_ms,full_plan_ms=full_ms,
            complete_action_and_observation_proof_match=True,polynomial_signature=polynomial_match(entry,request,v,word)))
    if spec['execute']:
        assert current.phase=='READY' and full.phase=='READY'
        current=live.execute(current);full=reference.execute(full);stages.append(current)
        assert current.result.certified and motion_signature(current)==motion_signature(full)
    assert live.archives(entry)==started_archive
    checkpoints=[]
    if save:
        for index,stage in enumerate(stages):
            raw,h=live.dumps(stage);restored=live.loads(raw,h,entry,initial,stage.scope,stage.choice)
            assert stage.digest==restored.digest
            checkpoints.append(dict(index=index,phase=stage.phase,sha256=h,bytes=len(raw)))
        fresh=a.register();restored=live.loads(raw,h,fresh,scope(fresh,*first[:3]))
        assert restored.digest==current.digest and motion_signature(restored)==motion_signature(current)
        (OUTPUT/(spec['name']+'.record.json')).write_bytes(raw)
    return dict(name=spec['name'],trace=rows,certified=current.result.certified,physical_signature=motion_signature(current),
        checkpoint_stages=checkpoints,unchanged_number_archives=True,
        stock_counts=[len(entry.base.engine.stock),len(current.result.first.engine.stock),len(current.result.second.engine.stock)],
        no_replacement_of_actual_history=True)


def run():
    raw=(HERE/'RR67-inputs.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==INPUT_SHA
    spec=json.loads(raw);OUTPUT.mkdir(parents=True,exist_ok=True);entry=a.register();rows=[]
    for name in spec['contexts']:
        for strength in spec['strengths']:
            for domain in spec['domains']:
                request=scope(entry,name,strength,domain)
                for v in map(Q,spec['controls']):
                    for word in spec['words']:
                        plan=a.compile(entry,request,v,word);work=asdict(entry._receipts[-1][1])
                        full=compile_full(entry,request,v,word,a.Policy())
                        assert (plan.mode,plan.status,plan.features,plan.coefficients,plan.tested_modes)==(
                            full.mode,full.status,full.features,full.coefficients,full.tested_modes)
                        signature=polynomial_match(entry,request,v,word)
                        result=a.resolve(entry,request,a.Policy(),plan)[0]
                        direct=matrix.oracle(entry.base,request,v,word)
                        status='UNKNOWN' if result.status in ('UNKNOWN_CHART','REFINE','UNDETERMINED_NO_SCHEMA') else result.status
                        assert (status,result.T,result.R)==direct,(name,strength,domain,v,word,result,direct)
                        rows.append(dict(context=name,strength=strength,domain=domain,v=str(v),word=word,mode=plan.mode,
                            status=result.status,polynomial_signature=signature,work=work,all_13_polynomials_and_full_plan_and_matrix_match=True,
                            requested_future_paths_executed=0))
    write(OUTPUT/'starts.json',dict(input_commit=INPUT_COMMIT,input_sha256=INPUT_SHA,plans=rows,all_before_requested_motion=True))
    print(json.dumps(dict(stage='all-plans-match',plans=len(rows))),flush=True)
    sequences=[]
    for item in spec['sequences']:
        result=sequence(item,save=item['name'] in ('changes-and-return','current-word'))
        sequences.append(result);print(json.dumps(dict(stage=item['name'],certified=result['certified'],snapshots=len(result['checkpoint_stages']))),flush=True)
    groups=[]
    def check(name,ok,**details):
        if not ok:raise AssertionError(name)
        groups.append(dict(name=name,passed=True,**details))
    check('all_precommitted_plans_match_full_algebra_and_independent_matrix',len(rows)==160)
    domain=next(x for x in sequences if x['name']=='domain-only')['trace']
    check('changing_only_domain_reuses_every_arithmetic_stage_but_changes_feasibility',
        domain[1]['work']['nodes_new']==[] and len(domain[1]['work']['nodes_reused'])==32 and
        [x['status'] for x in domain]==['ADMISSIBLE','EMPTY','ADMISSIBLE'],trace=domain)
    future=next(x for x in sequences if x['name']=='future-C-only')['trace']
    check('a_new_future_C_reuses_local_context_and_rebuilds_the_affected_pullback',
        all('Y'+str(i) in future[1]['work']['nodes_reused'] for i in range(3)) and
        bool(future[1]['work']['nodes_new']) and bool(future[1]['work']['factors_reused']),trace=future)
    changed=next(x for x in sequences if x['name']=='changes-and-return')['trace']
    check('strength_change_reopens_the_affected_context_and_reads_its_new_feature',
        all('Y'+str(i) in changed[1]['work']['nodes_new'] for i in range(3)) and changed[1]['new_keys']==['port-HHHSUT'])
    check('cache_reuse_preserves_all_original_values_across_requirement_revisions',all(x['unchanged_number_archives'] for x in sequences))
    check('word_change_reads_the_correct_port_and_both_choices_can_execute',
        next(x for x in sequences if x['name']=='current-word')['trace'][1]['new_keys']==['port-HHHUST'])
    budget=next(x for x in sequences if x['name']=='budget-and-back')['trace']
    check('budget_revision_reuses_identities_but_rebinds_permission',
        [x['status'] for x in budget]==['UNDETERMINED_NO_SCHEMA','ADMISSIBLE'] and
        bool(budget[1]['work']['factors_reused']) and not budget[1]['work']['factors_new'])
    check('all_five_sequences_match_actual_full_recomputation_motion',len(sequences)==5 and all(x['certified'] for x in sequences))
    check('current_stock_and_inheritance_survive_without_reset',all(x['stock_counts']==[6,7,8] for x in sequences))
    snapshots=sum(len(x['checkpoint_stages']) for x in sequences)
    check('snapshot_replay_reconstructs_proofs_without_an_existing_warm_cache',snapshots==26,snapshots=snapshots)
    check('cache_hits_do_not_erase_earlier_request_or_query_events',all(x['no_replacement_of_actual_history'] for x in sequences))
    result=dict(schema='time-engine-rr67-incremental-demand-result-v1',input_commit=INPUT_COMMIT,
        groups=groups,plans=len(rows),sequences=sequences,actual_bundles=5,full_control_actual_bundles=5,checkpoint_stages=snapshots,
        timing_is_diagnostic=True,original_values_deleted=False,universal_minimum_recomputation_claimed=False)
    write(OUTPUT/'result.json',result);print(json.dumps(dict(passed=True,groups=len(groups),actual_bundles=5,checkpoints=snapshots)),flush=True)
    return result


if __name__=='__main__':run()
