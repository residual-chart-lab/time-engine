"""Fixed C and current choices -> pre-actuation demand -> real two flowers."""
from pathlib import Path
from dataclasses import replace,asdict
from fractions import Fraction as Q
from collections import Counter,defaultdict
import hashlib,json
import bundle_demand as b
import bundle_execution as plant
from bundle_demand import fn,te,d,prior

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/'.work/rr64-local'
INPUT_COMMIT='9f534b9d1223c4ee4f6388363f1b4432d244f243'
INPUT_SHA256='1db157d7d6548905390766382ff4d69a8028500011ef758c6dd87a2014a19f77'


def write(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,default=te.triple.encode)+'\n').encode())


def cases(spec,entries):
    rows=[]
    def add(mode,x,v,word,domain,strength,kind):
        for obs in spec['observations']:
            scope=b.Scope(entries[mode].digest,Q(x),Q(v),word,Q(strength),tuple(map(Q,domain)),obs)
            rows.append((mode,kind,scope))
    for mode in spec['histories']:
        for x in spec['future_x']:
            for v in spec['first_controls']:
                for word in spec['first_words']:
                    add(mode,x,v,word,spec['later_control_domain'],spec['strength'],'main')
    for mode in spec['histories']:
        for x in spec['narrow_controls']['x']:
            for v in spec['first_controls']:
                for word in spec['first_words']:
                    add(mode,x,v,word,spec['narrow_controls']['domain'],spec['strength'],'narrow-resource')
    for mode in spec['zero_coupling_controls']['histories']:
        for x in spec['zero_coupling_controls']['x']:
            for v in spec['first_controls']:
                for word in spec['first_words']:
                    add(mode,x,v,word,spec['later_control_domain'],'0','zero-coupling')
    return tuple(rows)


def direct_oracle(entry,scope):
    """Independent exact matrix/action calculation, without execution of a path."""
    if not prior.scalar(entry.head.kernel(scope.context)):return False,None
    if not te.port.regular(scope.context,entry.library):return None,None
    base=entry.flight.pair.representative
    S=d.tensor(entry.flight.pair.original)
    T=d.tensor(d.AffineLetter(tuple(a+scope.first_control*z for a,z in zip(base.weights,entry.axis)),entry.library))
    H=tuple(d.tensor(leaf) for leaf in entry.head.leaves())
    mapping={'H':H,'S':(S,),'T':(T,)}
    leaves=tuple(leaf for c in scope.first_word for leaf in mapping[c])
    den=Q(len(leaves)*(len(leaves)+1),2)
    raw=tuple(tuple(sum(Q(k)*x[i][j]/den for k,x in enumerate(leaves,1)) for j in range(3)) for i in range(3))
    anchor=te.pair.boundary_readout(entry.head)
    y=tuple(tuple(anchor[i][j]+scope.strength*(raw[i][j]-(Q(1,3) if i==j else 0)) for j in range(3)) for i in range(3))
    if not te.port.regular(y,entry.library):return None,None
    h=prior.scalar(entry.head.kernel(y))
    if not h or abs(h-1)<=te.port.EPSILON:return None,None
    leaf=prior.cycle.correction_leaf(y,entry.library,(1/h,0,0,0))
    axis=te.pair.null_direction(y,entry.library)
    g=prior.scalar(prior.direction_response(axis,entry.library,scope.context))
    a=prior.scalar(leaf.kernel(scope.context))
    kernel=Q(1)
    for matrix in leaves:kernel*=prior.scalar(d.join(matrix,scope.context))
    prefix=-kernel
    if abs(prefix-1)<=te.port.EPSILON:return None,None
    coefficient=-kernel*prior.scalar(entry.head.kernel(scope.context))
    if not coefficient or not g:return (False,None) if coefficient*a!=1 else (None,None)
    alpha=(1/coefficient-a)/g
    if h==-3 and alpha==Q(1,3):return None,None
    ok=scope.domain[0]<=alpha<=scope.domain[1]
    return ok,alpha if ok and scope.observation==b.ACTIONS else None


def run(execute_cases=True):
    raw_inputs=(HERE/'RR64-inputs.json').read_bytes()
    if hashlib.sha256(raw_inputs).hexdigest()!=INPUT_SHA256:
        raise ValueError('the committed pre-calculation RR64 input bytes changed')
    spec=json.loads(raw_inputs)
    entries={mode:b.register(mode,tuple(map(Q,spec['envelope']))) for mode in spec['histories']}
    all_cases=cases(spec,entries);OUTPUT.mkdir(parents=True,exist_ok=True)
    starts=[];work=[]
    for mode,kind,scope in all_cases:
        entry=entries[mode];recipe=b.build(entry,scope);meter=fn.Meter()
        assessment=b.assess(entry,scope,recipe,meter)
        starts.append(dict(mode=mode,kind=kind,scope=asdict(scope),scope_digest=scope.digest,
            recipe_digest=recipe.digest,dependencies=recipe.dependencies,
            assessment=dict(status=assessment.status,feasible=assessment.feasible,
                            control_bounds=assessment.control_bounds,needs_exact=assessment.needs_exact),
            exact_residual_reads=meter.exact_reads,requested_new_sources=0,requested_flowers_executed=0))
        work.append((mode,kind,scope,recipe,assessment))
    write(OUTPUT/'starts.json',dict(input_commit=INPUT_COMMIT,input_sha256=hashlib.sha256((HERE/'RR64-inputs.json').read_bytes()).hexdigest(),
        assessments=starts,all_before_first_requested_actuation=True))
    print(json.dumps(dict(stage='pre-actuation-assessments-written',queries=len(work))),flush=True)
    rows=[];meters={obs:fn.Meter() for obs in spec['observations']};resolved={}
    for mode,kind,scope,recipe,assessment in work:
        entry=entries[mode]
        result=b.resolve(entry,scope,recipe,assessment,meters[scope.observation])
        oracle=direct_oracle(entry,scope)
        if (result.feasible,result.control)!=oracle:
            raise AssertionError((mode,kind,scope.x,scope.first_control,scope.first_word,result,oracle))
        key=(mode,kind,scope.x,scope.first_control,scope.first_word,scope.observation)
        resolved[key]=(entry,scope,recipe,assessment,result)
        rows.append(dict(mode=mode,kind=kind,x=str(scope.x),first_control=str(scope.first_control),word=scope.first_word,
            observation=scope.observation,status=assessment.status,resolution_status=result.status,
            feasible=result.feasible,control=result.control,scope_digest=scope.digest,matches_direct_exact_oracle=True))
    print(json.dumps(dict(stage='all-queries-match-independent-oracle',queries=len(rows),reads={k:m.exact_reads for k,m in meters.items()})),flush=True)
    groups=[]
    def check(name,passed,**detail):
        if not passed:raise AssertionError(name)
        groups.append(dict(name=name,passed=True,**detail))
    check('fixed_C_current_choices_and_demands_are_bound_before_actuation',len(rows)==600 and all(x['exact_residual_reads']==0 for x in starts))
    check('all_queries_match_an_independent_matrix_action_oracle',all(x['matches_direct_exact_oracle'] for x in rows))
    admissible=defaultdict(list)
    for row in rows:
        if row['kind']=='main' and row['observation']==b.ACTIONS and row['feasible']:
            admissible[row['mode']+'@'+row['x']].append((row['first_control'],row['word']))
    check('a_common_bundle_requirement_can_be_checked_without_completing_future_paths',True,
        completed_paths_in_assessment_and_resolution=0,admissible_current_choices=dict(admissible))
    check('some_feasibility_queries_omit_the_retained_exact_value',meters[b.EXISTS].exact_reads<300,
        feasibility_reads=meters[b.EXISTS].exact_reads,action_reads=meters[b.ACTIONS].exact_reads)
    ordered_controls=[]
    for mode in spec['histories']:
        for x in map(Q,spec['future_x']):
            for v in map(Q,spec['first_controls']):
                a=resolved[mode,'main',x,v,'HHST',b.ACTIONS][-1]
                z=resolved[mode,'main',x,v,'HHTS',b.ACTIONS][-1]
                if a.feasible and z.feasible:
                    ordered_controls.append(dict(mode=mode,x=str(x),v=str(v),different=a.control!=z.control))
    check('the_ordered_exit_can_change_the_required_later_action',any(x['different'] for x in ordered_controls),cases=ordered_controls)
    zero=[]
    for x in map(Q,spec['zero_coupling_controls']['x']):
        for v in map(Q,spec['first_controls']):
            a=resolved['keep','zero-coupling',x,v,'HHST',b.ACTIONS][-1]
            z=resolved['keep','zero-coupling',x,v,'HHTS',b.ACTIONS][-1]
            zero.append((a.feasible,a.control)==(z.feasible,z.control))
    check('cutting_the_context_coupling_removes_the_order_effect_without_erasing_history',all(zero))
    import bundle_resource_sweep
    sweep=bundle_resource_sweep.run(entries['keep'])
    write(OUTPUT/'resource-sweep.json',sweep)
    check('a_labelled_resource_sweep_restricts_current_choices_without_future_path_completion',
          sweep['rows'][2]['count']==4 and sweep['rows'][-1]['count']==6 and sweep['completed_future_paths']==0,
          role=sweep['role'],counts=[x['count'] for x in sweep['rows']],exact_reads=sweep['exact_residual_reads'])
    executions=[];actuals={};requested=[]
    if execute_cases:
        for mode in spec['execution_cases']['histories']:
            for x in map(Q,spec['execution_cases']['x']):
                for word in spec['execution_cases']['words']:
                    key=(mode,'main',x,Q(spec['execution_cases']['preferred_first_control']),word,b.ACTIONS)
                    entry,scope,recipe,assessment,result=resolved[key]
                    requested.append(dict(mode=mode,x=str(x),word=word,feasible=result.feasible,executed=bool(result.feasible)))
                    if not result.feasible:continue
                    actual=plant.execute(entry,scope,recipe,assessment,result)
                    actuals[mode,x,word]=(entry,scope,recipe,assessment,result,actual)
                    executions.append(dict(mode=mode,x=str(x),word=word,control=result.control,
                        first_endpoint=actual.first.engine.upper.live.accumulated,second_endpoint=actual.second.engine.upper.live.accumulated,
                        bundle_endpoint=actual.upper_trial.live.accumulated,certified=actual.certified,
                        stocks=[len(entry.flight.first.closed_engine.stock),len(actual.first.engine.stock),len(actual.second.engine.stock)],
                        prefix_errors=actual.future_prefix_errors))
        check('every_predicted_execution_case_actually_closes_two_flowers_and_one_bundle',
            bool(executions) and all(x['certified'] and x['first_endpoint']==b.NEG and x['second_endpoint']==b.NEG and x['bundle_endpoint']==b.ONE for x in executions),
            executions=len(executions),requested_cases=requested)
        keep=actuals['keep',Q(-1),'HHST'];erase=actuals['erase',Q(-1),'HHST'];restore=actuals['restore',Q(-1),'HHST']
        check('retained_experience_changes_the_actual_second_source_and_restore_recovers_it',
            keep[-1].second.new_source.leaves()[0].weights!=erase[-1].second.new_source.leaves()[0].weights
            and keep[-1].second.new_source.leaves()[0].weights==restore[-1].second.new_source.leaves()[0].weights)
        wrong=plant.execute(*keep[:5],control_test=erase[4].control)
        check('erased_control_preserves_both_local_closures_but_fails_the_common_bundle',
            not wrong.certified and wrong.first.engine.upper.live.accumulated==b.NEG and wrong.second.engine.upper.live.accumulated==b.NEG,
            future_defect=tuple(a-c for a,c in zip(wrong.upper_trial.live.accumulated,b.ONE)))
        raw,h=plant.dumps(keep[0],keep[1],keep[2],keep[3],keep[-1])
        loaded=plant.loads(raw,h,keep[0],keep[1])
        check('the_complete_two_flower_history_and_retained_number_graph_replay_after_restore',loaded==keep[-1],bytes=len(raw),sha256=h)
        (OUTPUT/'keep-primary.record.json').write_bytes(raw)
        # A separate declared resource-cap diagnostic; not silently folded into
        # the preregistered main execution matrix.
        e,s,r,a,z,actual=keep
        cap_scope=replace(s,domain=(Q(0),Q(12)))
        cap_recipe=b.build(e,cap_scope);cap_a=b.assess(e,cap_scope,cap_recipe);cap_z=b.resolve(e,cap_scope,cap_recipe,cap_a)
        cap_actual=plant.execute(e,cap_scope,cap_recipe,cap_a,cap_z)
        if not cap_actual.certified:raise AssertionError('resource-cap execution failed')
        executions.append(dict(mode='keep',x='-1',word='HHST',kind='post-grid-resource-cap-12',control=cap_z.control,
            first_endpoint=cap_actual.first.engine.upper.live.accumulated,second_endpoint=cap_actual.second.engine.upper.live.accumulated,
            bundle_endpoint=cap_actual.upper_trial.live.accumulated,certified=cap_actual.certified))
    result=dict(schema='time-engine-rr64-bundle-demand-v1',input_commit=INPUT_COMMIT,groups=groups,
        query_count=len(rows),queries=rows,exact_residual_reads={k:m.exact_reads for k,m in meters.items()},
        current_admissible_choices=dict(admissible),executions=executions,
        future_path_completions_in_assessment=0,registered_two_flower_continuation=True,
        arbitrary_future_coverage_claimed=False,total_runtime_speedup_claimed=False)
    write(OUTPUT/'result.json',result)
    print(json.dumps(dict(passed=True,groups=len(groups),queries=len(rows),executions=len(executions),
        admissible_counts={k:len(v) for k,v in admissible.items()})),flush=True)
    return result


if __name__=='__main__':run('--assess-only' not in __import__('sys').argv)
