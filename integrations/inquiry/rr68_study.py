"""Fixed catalogue-free discovery cases, physical controls and resumable use."""
from pathlib import Path
from dataclasses import replace
from fractions import Fraction as Q
import hashlib,json
import synthesized_resolution as a
import synthesized_session as live
import rr65_study as matrix
import rr67_study as previous

HERE=Path(__file__).resolve().parent;OUTPUT=HERE.parents[1]/'.work/rr68-local'
INPUT_COMMIT='78f1470cc1899e817e51afb909b3e09873013834'
INPUT_SHA='6f58ee64492612859ad58c6e418b459fb2dc51659dee331b6086e1903d9912b2'
FRAMES={'identity':(1,0,0,1),'split':(1,1,1,-1),'shear':(2,1,1,1)}


def write(path,value):path.write_bytes((json.dumps(value,indent=2,default=a.m.te.triple.encode)+'\n').encode())
def scope(entry,name,strength,frame='identity'):
    raw=previous.scope(entry.core,name,strength)
    return a.Scope(raw,FRAMES[frame] if type(frame) is str else frame)
def physical(action):return action.status,action.T,action.R,action.alpha
def before_values(entry,request,v,word,policy=a.Policy()):
    from unittest.mock import patch
    with patch.object(entry.base.vault,'exact',side_effect=AssertionError('no retained values during discovery')), \
         patch.object(entry.derived,'exact',side_effect=AssertionError('no dynamic values during discovery')), \
         patch.object(entry.core.derived,'exact',side_effect=AssertionError('no legacy catalogue')), \
         patch.object(a.core,'compile',side_effect=AssertionError('no catalogue planner')):
        return a.compile(entry,request,v,word,policy)


def check_identity(entry,request,plan):
    if plan.status!='AVAILABLE':return True
    original=a.m.build(entry.base,request.base_scope,plan.v,plan.word).polynomials
    definitions={key:a.Polynomial(coeff) for key,coeff in plan.definitions}
    assert all(a.synthesis.expand(plan.polynomials[label],definitions).terms==poly.terms for label,poly in original.items())
    return True


def sequence(spec,save=False):
    entry=a.register(tuple(spec['modes']));first=spec['requests'][0]
    initial=scope(entry,*first[:3]);session=live.start(entry,initial,a.Policy(max_features=first[4]));stages=[session];trace=[]
    original_archive=live.archives(entry)
    for i,(name,strength,frame,word,budget) in enumerate(spec['requests']):
        request=scope(entry,name,strength,frame);policy=a.Policy(max_features=budget)
        if i:session=live.revise(session,request,policy);stages.append(session)
        plan=before_values(entry,request,1,word,policy);check_identity(entry,request,plan)
        session=live.choose(session,1,word);stages.append(session);prior_work=len(entry._work);meter=a.fn.Meter()
        session=live.resolve(session,meter);stages.append(session)
        actual=matrix.oracle(entry.base,request.base_scope,Q(1),word)
        if plan.status=='AVAILABLE':assert (session.prepared.action.status,session.prepared.action.T,session.prepared.action.R)==actual
        cost=entry._work[-1] if len(entry._work)>prior_work else dict(new_feature_queries=0,source_reads_for_registration=0,derived_features=0)
        trace.append(dict(context=name,strength=strength,frame=frame,word=word,budget=budget,mode=plan.mode,
            status=session.prepared.action.status,frame_generators=plan.proof.definitions if plan.proof else (),
            physical_generators=plan.definitions,proof_digest=plan.proof.digest if plan.proof else None,
            reads=cost,total_exact_queries=meter.exact_reads,new_keys=live.history(session)[-1]['new_keys'],
            derived_keys=live.history(session)[-1]['derived_keys']))
    assert session.phase=='READY'
    done=live.execute(session);stages.append(done)
    now=live.archives(entry,done.cache)
    assert all(now[k]==original_archive[k] for k in ('base','base_sha256','legacy','legacy_sha256'))
    snapshots=[]
    if save:
        for index,stage in enumerate(stages):
            raw,h=live.dumps(stage);restored=live.loads(raw,h,entry,initial,stage.scope,stage.choice)
            assert restored.digest==stage.digest;snapshots.append(dict(index=index,phase=stage.phase,sha256=h,bytes=len(raw)))
        fresh=a.register(tuple(spec['modes']));restored=live.loads(raw,h,fresh,scope(fresh,*first[:3]))
        assert restored.digest==done.digest and restored.result.certified
        (OUTPUT/(spec['name']+'.record.json')).write_bytes(raw)
    return dict(name=spec['name'],trace=trace,certified=done.result.certified,checkpoints=snapshots,
        original_archives_unchanged=True,stock_counts=[len(entry.base.engine.stock),len(done.result.first.engine.stock),len(done.result.second.engine.stock)])


def run():
    raw=(HERE/'RR68-inputs.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==INPUT_SHA
    spec=json.loads(raw);OUTPUT.mkdir(parents=True,exist_ok=True);entry=a.register();rows=[]
    for name in spec['contexts']:
        for strength in spec['strengths']:
            for v in map(Q,spec['controls']):
                for word in spec['words']:
                    for frame in spec['frames']:
                        request=scope(entry,name,strength,frame);plan=before_values(entry,request,v,word)
                        assert check_identity(entry,request,plan)
                        action=a.resolve(entry,request,a.Policy(),plan)[0]
                        status='UNKNOWN' if action.status in ('UNKNOWN_CHART','REFINE') else action.status
                        direct=matrix.oracle(entry.base,request.base_scope,v,word)
                        assert (status,action.T,action.R)==direct,(name,strength,v,word,frame,plan.status,direct)
                        rows.append(dict(context=name,strength=strength,v=str(v),word=word,frame=frame,status=action.status,
                            feature_count=len(plan.features),frame_generators=plan.proof.definitions if plan.proof else (),
                            physical_generators=plan.definitions,proof_digest=plan.proof.digest if plan.proof else None,
                            all_13_identities_and_matrix_action_match=True,exact_queries_during_discovery=0,
                            requested_future_paths_executed=0))
    write(OUTPUT/'starts.json',dict(input_commit=INPUT_COMMIT,input_sha256=INPUT_SHA,rows=rows,all_before_requested_motion=True))
    print(json.dumps(dict(stage='all-plans-match',plans=len(rows))),flush=True)
    cases=[]
    for item in spec['sequences']:
        case=sequence(item,save=item['name'] in ('unregistered-split','word-and-frame'))
        cases.append(case);print(json.dumps(dict(stage=item['name'],certified=case['certified'],checkpoints=len(case['checkpoints']))),flush=True)
    retention=[]
    for modes in map(tuple,spec['retention_controls']):
        e=a.register(modes);request=scope(e,'mixed','0','split');p=before_values(e,request,1,'HHHSUT')
        current=live.resolve(live.choose(live.start(e,request),1,'HHHSUT'))
        direct=matrix.oracle(e.base,request.base_scope,Q(1),'HHHSUT')
        assert (current.prepared.action.status,current.prepared.action.T,current.prepared.action.R)==direct
        if current.phase=='READY':actual=live.execute(current).result
        else:
            # A separate declared negative control; never a successful record.
            original=a.m.action(e.base,request.base_scope,1,'HHHSUT')
            import mixed_execution
            actual=mixed_execution.run(e.base,request.base_scope,original,counterfactual_alpha=0)
        retention.append(dict(modes=modes,status=current.prepared.action.status,certified=actual.certified,
            local_endpoints=[actual.first.engine.upper.live.accumulated,actual.second.engine.upper.live.accumulated],
            upper_endpoint=actual.upper_trial.live.accumulated))
    groups=[]
    def check(name,ok,**detail):
        if not ok:raise AssertionError(name)
        groups.append(dict(name=name,passed=True,**detail))
    check('all_precommitted_frames_and_demands_match_complete_physical_action',len(rows)==240)
    check('all_synthesis_runs_precede_value_queries_and_requested_motion',all(x['exact_queries_during_discovery']==0 and x['requested_future_paths_executed']==0 for x in rows))
    pure=[x for x in rows if x['context']=='mixed' and x['strength']=='0' and x['v']=='1']
    check('a_joint_quadratic_is_constructed_without_a_product_catalogue',all(x['feature_count']==1 for x in pure))
    split=next(x for x in pure if x['frame']=='split' and x['word']=='HHHSUT')
    quad=a.Polynomial(split['frame_generators'][0][1])
    x,y=a.synthesis.variable('x'),a.synthesis.variable('y')
    check('changed_coordinates_produce_an_unregistered_quadratic_form',quad.terms==x.mul(x).add(y.mul(y).scaled(-1)).terms)
    request=scope(entry,'mixed','1/1024');plan=before_values(entry,request,1,'HHHSUT')
    check('connected_requirement_constructs_both_linear_and_quadratic_generators',
        sorted(a.synthesis.degree(a.Polynomial(coeff)) for name,coeff in plan.proof.definitions)==[1,2])
    small=a.Policy(max_features=1);blocked=before_values(entry,request,1,'HHHSUT',small)
    check('insufficient_synthesis_budget_is_unresolved_not_empty',blocked.status.startswith('UNDETERMINED_'))
    # Demonstrate actual information reduction on a certified polynomial fibre.
    s0,t0=Q(1,1024),Q(1,2048);s1,t1=Q(4,7)*Q(1,1024),Q(7,8)*Q(1,1024)
    definitions=[a.Polynomial(c) for _,c in plan.definitions]
    values0=[p.exact({'s':s0,'t':t0}) for p in definitions];values1=[p.exact({'s':s1,'t':t1}) for p in definitions]
    check('the_constructed_observation_need_not_encode_the_whole_original_state',
        (s0,t0)!=(s1,t1) and values0==values1,role='algebraic witness inside source envelopes, not a newly issued TE history')
    check('all_five_declared_synthesis_sequences_actuate_and_close',len(cases)==5 and all(x['certified'] for x in cases))
    check('erasure_is_distinguished_from_retention_in_real_motion',
        [x['certified'] for x in retention]==[True,False,False,False,True] and all(x['local_endpoints']==[a.b.NEG,a.b.NEG] for x in retention),controls=retention)
    check('original_archives_and_prior_stock_survive',all(x['original_archives_unchanged'] and x['stock_counts']==[6,7,8] for x in cases))
    count=sum(len(x['checkpoints']) for x in cases)
    check('dynamic_observations_replay_from_fresh_entries',count==14,checkpoints=count)
    result=dict(schema='time-engine-rr68-synthesis-result-v1',input_commit=INPUT_COMMIT,groups=groups,plans=len(rows),
        sequences=cases,retention_controls=retention,declared_actual_bundles=5,retention_control_motions=5,
        checkpoint_stages=count,catalogue_supplied_to_discovery=False,registration_costs_accounted=True,
        universal_minimal_observation_claimed=False,new_physical_connection_law_claimed=False)
    write(OUTPUT/'result.json',result);print(json.dumps(dict(passed=True,groups=len(groups),plans=len(rows),checkpoints=count)),flush=True);return result


if __name__=='__main__':run()
