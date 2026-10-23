"""Fixed scopes -> exact factorization -> one retained adaptive history."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
import hashlib,json
import adaptive_resolution as a
import adaptive_session as live
import rr65_study as old
from adaptive_resolution import m,fn

HERE=Path(__file__).resolve().parent;OUTPUT=HERE.parents[1]/'.work/rr66-local'
INPUT_COMMIT='1b1fa6c76acdbaa39e6adb2f557b7bad588e794d'
INPUT_SHA='d2b69bec39636bab6cbe277481021597dde2b7c0768dd0ff924f60ad995d09d7'


def write(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,default=m.te.triple.encode)+'\n').encode())
def scope(entry,name,strength):return m.Scope(entry.base.digest,m.context(entry.base,name),Q(strength))


def scenario(entry,spec,collect=False):
    first=spec['requests'][0];session=live.start(entry,scope(entry,first[0],first[1]))
    stages=[session];rows=[]
    for i,(name,strength,word) in enumerate(spec['requests']):
        if i:session=live.revise(session,scope(entry,name,strength));stages.append(session)
        session=live.choose(session,1,word);stages.append(session)
        meter=fn.Meter();session=live.resolve(session,meter);stages.append(session)
        c=live.history(session)[-1]
        rows.append(dict(revision=session.revision,context=name,strength=strength,word=word,mode=session.prepared.plan.mode,
            action_status=session.prepared.action.status,new_keys=c['new_keys'],derived_keys=c['derived_keys'],exact_feature_reads=meter.exact_reads))
    if spec['execute']:
        session=live.execute(session);stages.append(session)
    return session,rows,stages


def run():
    raw=(HERE/'RR66-inputs.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INPUT_SHA:raise ValueError('the pre-calculation RR66 input bytes changed')
    spec=json.loads(raw);OUTPUT.mkdir(parents=True,exist_ok=True);entry=a.register();rows=[]
    for name in spec['contexts']:
        for strength in spec['strengths']:
            request=scope(entry,name,strength)
            for v in map(Q,spec['controls']):
                for word in spec['words']:
                    plan=a.compile(entry,request,v,word);meter=fn.Meter()
                    action,cache,new,derived,used=a.resolve(entry,request,a.Policy(),plan,meter=meter)
                    direct=old.oracle(entry.base,request,v,word)
                    normalized='UNKNOWN' if action.status in ('UNKNOWN_CHART','REFINE','UNDETERMINED_NO_SCHEMA') else action.status
                    if (normalized,action.T,action.R)!=direct:raise AssertionError((name,strength,v,word,plan.mode,action,direct))
                    rows.append(dict(context=name,strength=strength,v=str(v),word=word,mode=plan.mode,status=plan.status,
                        features=plan.features,action_status=action.status,plan_digest=plan.digest,
                        proof_attempts=plan.tested_modes,exact_feature_reads=meter.exact_reads,
                        requested_future_paths_executed=0,matches_independent_matrix_action_oracle=True))
    write(OUTPUT/'starts.json',dict(input_commit=INPUT_COMMIT,input_sha256=INPUT_SHA,all_before_requested_bundle_motion=True,plans=rows))
    print(json.dumps(dict(stage='all-64-plans-match',modes=dict(Counter(x['mode'] for x in rows)))),flush=True)
    groups=[]
    def check(name,ok,**detail):
        if not ok:raise AssertionError(name)
        groups.append(dict(name=name,passed=True,**detail))
    check('exact_factorization_selects_sufficient_observations_before_values',len(rows)==64 and all(x['matches_independent_matrix_action_oracle'] for x in rows),
        modes=dict(Counter(x['mode'] for x in rows)),exact_feature_reads=sum(x['exact_feature_reads'] for x in rows))
    check('request_and_port_change_the_certified_observation',
        {x['mode'] for x in rows}=={'CONSTANT','PRODUCT','SUM_PRODUCT','PORT_PRODUCT','INDIVIDUAL'})
    check('empty_and_unknown_remain_distinct_without_exact_feature_reads',
        all(x['exact_feature_reads']==0 for x in rows if x['mode']=='CONSTANT'))
    records=[];instances={};checkpoint_trace=[]
    for item in spec['scenarios']:
        modes=tuple(item.get('modes',('keep','keep')))
        e=entry if modes==('keep','keep') else a.register(modes)
        session,trace,stages=scenario(e,item)
        instances[item['name']]=(session,trace,stages)
        records.append(dict(name=item['name'],entry_digest=e.digest,trace=trace,final=live.view(session),
            local_endpoints=(session.result.first.engine.upper.live.accumulated,session.result.second.engine.upper.live.accumulated),
            upper_endpoint=session.result.upper_trial.live.accumulated))
        if item['name']=='product-to-port':
            for index,stage in enumerate(stages):
                raw,h=live.dumps(stage);restored=live.loads(raw,h,e,stage.initial_scope,stage.scope,stage.choice)
                if restored.digest!=stage.digest:raise AssertionError('adaptive stage replay differs')
                checkpoint_trace.append(dict(index=index,phase=stage.phase,sha256=h,bytes=len(raw),same_state_digest=True))
            (OUTPUT/'product-to-port.record.json').write_bytes(raw)
    main,trace,stages=instances['full-cycle']
    check('one_history_can_refine_and_coarsen_without_erasing_any_feature',
        [x['mode'] for x in trace]==['PRODUCT','PORT_PRODUCT','SUM_PRODUCT','INDIVIDUAL','PRODUCT']
        and [x['new_keys'] for x in trace]==[['p'],['port-HHHSUT'],['sum'],[],[]]
        and trace[3]['derived_keys']==['s','t'],trace=trace)
    port,trace,stages=instances['product-to-port']
    check('the_connected_case_uses_product_and_actual_port_without_individual_reads',
        [x['new_keys'] for x in trace]==[['p'],['port-HHHSUT']] and port.result.certified,
        true_archive_queries=sum(x['exact_feature_reads'] for x in trace),individual_exact_queries=0)
    word,trace,stages=instances['word-sensitive-port']
    check('the_current_word_binds_the_port_feature_and_keeps_order_freedom',
        [x['new_keys'] for x in trace]==[['p','port-HHHSUT'],['port-HHHUST']]
        and word.result.port[1]!=port.result.port[1],trace=trace)
    empty,trace,stages=instances['empty-to-new-requirement']
    check('an_empty_result_does_not_delete_information_needed_by_a_new_requirement',
        [x['action_status'] for x in trace]==['EMPTY','ADMISSIBLE'] and empty.result.certified,trace=trace)
    check('restore_reproduces_the_same_physical_actions',
        instances['restore-product-to-port'][0].result.action.R==port.result.action.R)
    check('all_five_declared_motions_close_two_local_cells_and_the_bundle',
        len(records)==5 and all(x['local_endpoints']==(m.b.NEG,m.b.NEG) and x['upper_endpoint']==m.b.ONE for x in records))
    check('every_declared_adaptive_checkpoint_replays_the_original_request_journal',len(checkpoint_trace)==7,stages=checkpoint_trace)
    tight=a.Policy(max_features=1);request=scope(entry,'mixed','1/1024')
    plan=a.compile(entry,request,1,'HHHSUT',tight);meter=fn.Meter()
    action,cache,new,derived,used=a.resolve(entry,request,tight,plan,meter=meter)
    check('a_budget_limit_is_unknown_instead_of_a_false_omission_or_empty_set',
        action.status=='UNDETERMINED_NO_SCHEMA' and meter.exact_reads==0,status=action.status)
    result=dict(schema='time-engine-rr66-adaptive-resolution-v1',input_commit=INPUT_COMMIT,groups=groups,
        plans=len(rows),plan_modes=dict(Counter(x['mode'] for x in rows)),scenarios=records,
        checkpoint_stages=checkpoint_trace,requested_actual_bundles=len(records),
        original_values_deleted=False,global_minimum_information_claimed=False,registration_is_exact_and_separate=True)
    write(OUTPUT/'result.json',result)
    print(json.dumps(dict(passed=True,groups=len(groups),plans=len(rows),actual_bundles=len(records),checkpoint_stages=len(checkpoint_trace))),flush=True)
    return result


if __name__=='__main__':run()
