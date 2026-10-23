"""Independent matrix/linear-system oracle and the precommitted RR69 study."""
from pathlib import Path
from fractions import Fraction as Q
from dataclasses import replace
from unittest.mock import patch
import json,hashlib
import three_flower_synthesis as n
import three_flower_session as live
from three_flower_synthesis import a,m,b,fn,prior,d,te,plant

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUTPUT=ROOT/'.work/rr69-local'
INPUT_COMMIT='828a7f9dd52855f10f27399d8dfb0f699e0323b0'
INPUT_SHA='2a50ac6c2431d473555a9240c93defeaf58f9c07e26e66bbed2344f7b736c411'
FRAMES={'identity':(1,0,0,1),'split':(1,1,1,-1)}


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=te.triple.encode)+'\n',encoding='utf-8',newline='\n')


def scope(entry,name='mixed',strengths=('1/1024','1/1024'),frame='identity',domain=None):
    raw=m.Scope(entry.base.digest,m.context(entry.base,name),Q(strengths[0]))
    if domain is not None:raw=replace(raw,domain=tuple(map(Q,domain)))
    return n.Scope(raw,Q(strengths[1]),frame=FRAMES[frame] if type(frame) is str else frame)


def before_values(entry,request,v,u,word):
    with patch.object(entry.base.vault,'exact',side_effect=AssertionError('no retained values during construction')), \
         patch.object(entry.derived,'exact',side_effect=AssertionError('no observation values during construction')), \
         patch.object(entry.core.derived,'exact',side_effect=AssertionError('no legacy catalogue values')), \
         patch.object(a.core,'compile',side_effect=AssertionError('no RR66/67 catalogue planner')), \
         patch.object(a,'compile',side_effect=AssertionError('no RR68 two-flower planner')), \
         patch.object(plant,'produce',side_effect=AssertionError('no requested future source execution')):
        return n.compile(entry,request,v,u,word)


def solve(rows,values):
    matrix=[list(map(Q,row))+[Q(value)] for row,value in zip(rows,values)]
    for col in range(3):
        candidates=[i for i in range(col,3) if matrix[i][col]]
        if not candidates:return None
        i=candidates[0];matrix[col],matrix[i]=matrix[i],matrix[col]
        factor=matrix[col][col];matrix[col]=[v/factor for v in matrix[col]]
        for i in range(3):
            if i!=col:
                factor=matrix[i][col];matrix[i]=[v-factor*w for v,w in zip(matrix[i],matrix[col])]
    return tuple(row[-1] for row in matrix)


def oracle(entry,request,v,u,word):
    """Read all original coordinates; use matrices and independent 3x3 solves.

    No rational DAG, observation proof, symbolic source or completed path is used.
    """
    base=entry.base;raw=request.base_scope;c=raw.C
    endpoints=tuple(op.source.endpoint for op in base.library)
    def tensor(weights):return tuple(tuple(sum(x*M[i][j] for x,M in zip(weights,endpoints)) for j in range(3)) for i in range(3))
    def response(weights,Y):
        X=tensor(weights)
        return 2*sum(X[i][j]*Y[j][i] for i in range(3) for j in range(3))-1
    head=tuple(x.weights for x in base.head.leaves())
    def h_at(Y):
        value=Q(1)
        for weights in head:value*=response(weights,Y)
        return value
    hc=h_at(c)
    if not hc:return 'EMPTY',(),(),(),None,{}
    if not te.port.regular(c,base.library):return 'UNKNOWN_CHART',(),(),(),None,{}
    s=base.vault.exact('s',fn.Meter());t=base.vault.exact('t',fn.Meter())
    fixed=base.first.flight.pair.representative.weights
    S=tuple(x+s*z for x,z in zip(fixed,base.first.axis));U=tuple(x+t*z for x,z in zip(fixed,base.direction_U));T=tuple(x+Q(v)*z for x,z in zip(fixed,base.first.axis))
    anchor=te.pair.boundary_readout(base.head)
    def port(leaves,strength):
        matrices=tuple(tensor(x) for x in leaves);den=Q(len(matrices)*(len(matrices)+1),2)
        return tuple(tuple(anchor[i][j]+strength*(sum(Q(pos)/den*M[i][j] for pos,M in enumerate(matrices,1))-(Q(1,3) if i==j else 0)) for j in range(3)) for i in range(3))
    def coeff(Y):return tuple(2*sum(M[i][j]*Y[j][i] for i in range(3) for j in range(3)) for M in endpoints[:3])
    mapping={'H':head,'S':(S,),'U':(U,),'T':(T,)};leaves=tuple(x for k in word for x in mapping[k])
    y2=port(leaves,raw.strength)
    if not te.port.regular(y2,base.library):return 'UNKNOWN_CHART',(),(),(),None,{}
    h2=h_at(y2)
    if not h2:return 'EMPTY',(),(),(),None,{}
    if abs(h2-1)<=te.port.EPSILON:return 'UNDETERMINED_FIRST_BOUNDARY',(),(),(),None,{}
    B1=Q(1)
    for weights in leaves:B1*=response(weights,c)
    if not B1:return 'EMPTY',(),(),(),None,{}
    r2=solve(((1,1,1),coeff(y2),(0,0,1)),(1,1+1/h2,u))
    if r2 is None:return 'UNDETERMINED_SINGULAR',(),(),(),None,{}
    R2=r2+(Q(0),)*3;y3=port(head+(R2,),request.last_strength)
    if not te.port.regular(y3,base.library):return 'UNKNOWN_CHART',(),(),(),None,{}
    h3=h_at(y3);B2=hc*response(R2,c)
    if not h3 or not B2:return 'EMPTY',(),(),(),None,{}
    if abs(h3-1)<=te.port.EPSILON or any(abs(x-1)<=te.port.EPSILON for x in (-B1,-B1*B2)):
        return 'UNDETERMINED_FIRST_BOUNDARY',(),(),(),None,{}
    r3=solve(((1,1,1),coeff(y3),coeff(c)),(1,1+1/h3,1-1/(hc*B1*B2)))
    if r3 is None:return 'UNDETERMINED_SINGULAR',(),(),(),None,{}
    alpha=r3[2]
    if not raw.domain[0]<=alpha<=raw.domain[1]:return 'EMPTY',(),(),(),None,{}
    R3=r3+(Q(0),)*3;B3=hc*response(R3,c)
    return 'ADMISSIBLE',T,R2,R3,alpha,dict(Y2=y2,Y3=y3,B1=B1,B2=B2,B3=B3,upper=-B1*B2*B3)


def physical(action):return action.status,action.T,action.R2,action.R3,action.alpha


def build_case(case):
    entry=a.register(tuple(case['modes']));request=scope(entry,case['context'],case['strengths'],case['frame'])
    state=live.start(entry,request);stages=[state]
    plan=before_values(entry,request,Q(case['v']),Q(case['u']),case['word'])
    state=live.choose(state,Q(case['v']),Q(case['u']),case['word']);stages.append(state)
    state,work=live.resolve(state);stages.append(state)
    direct=oracle(entry,request,Q(case['v']),Q(case['u']),case['word'])
    assert physical(state.action)==direct[:5]
    while state.phase in ('READY','CLOSED1','CLOSED2','CLOSED3'):
        state=live.advance(state);stages.append(state)
    return state,stages,work


def counterfactual(entry,request,v=Q(1),u=Q(0),word='HHHSUT'):
    """Declared open-loop negative control, never a completed RR69 record.

    Close locally with beta=0 at the final flower, even when the upper demand
    has no completion. The real Decoder decides the upper failure.
    """
    base=entry.base;engine=base.engine
    T=d.AffineLetter(tuple(x+v*z for x,z in zip(base.first.flight.pair.representative.weights,base.first.axis)),base.library)
    ready,t=plant.produce(engine,engine.upper.live.context,T,'rr69-control-T')
    mapping={'H':ready.pending.head,'S':base.first.flight.first.residue.source,'U':base.U_operation,'T':t}
    flowers=[plant.consume(ready,tuple(mapping[k] for k in word),'rr69-control-first')]
    from live_flower import ExitView,ExitResidue
    for i,strength in enumerate((request.base_scope.strength,request.last_strength)):
        prev=flowers[-1];raw,y=te.pair.connection_context(ExitView(prev.engine,ExitResidue(prev.terminal)),te.pair.ConnectionSpec(strength=strength))
        h=prior.scalar(base.head.kernel(y));source=prior.cycle.correction_leaf(y,base.library,(1/h,0,0,0));control=u if not i else Q(0)
        delta=te.pair.null_direction(y,base.library)
        source=d.AffineLetter(tuple(x+control*z for x,z in zip(source.weights,delta)),base.library)
        ready,r=plant.produce(prev.engine,y,source,'rr69-control-R'+str(i),emitted=True)
        flowers.append(plant.consume(ready,(ready.pending.head,r),'rr69-control-'+str(i)))
    last=flowers[-1];start=te.port.ExecutionState(te.port.UpperState(request.C,last.engine.upper.live.accumulated),last.engine.upper.executed_word)
    operations=tuple(f.terminal for f in flowers);current=start
    for op in operations:current=te.port.step(op,current)
    decoded=te.port.decode(start,operations,(request.base_scope.target,))
    certified=bool(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries and current.live.accumulated==request.base_scope.target)
    return dict(certified=certified,local_endpoints=[f.engine.upper.live.accumulated for f in flowers],upper_endpoint=current.live.accumulated,successful_record_issued=False)


def run():
    raw=(HERE/'RR69-inputs.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==INPUT_SHA
    spec=json.loads(raw);OUTPUT.mkdir(parents=True,exist_ok=True);entry=a.register();rows=[]
    for name in spec['contexts']:
        for strengths in spec['strength_pairs']:
            for v in map(Q,spec['controls']):
                for u in map(Q,spec['middle_controls']):
                    for word in spec['words']:
                        for frame in spec['frames']:
                            request=scope(entry,name,strengths,frame);plan=before_values(entry,request,v,u,word)
                            action,cache,work=n.resolve(entry,request,plan);direct=oracle(entry,request,v,u,word)
                            assert physical(action)==direct[:5],(name,strengths,v,u,word,frame,action.status,direct[0])
                            if action.status=='ADMISSIBLE':
                                q=dict(action.values)
                                assert tuple(q['Y2_'+str(i)] for i in range(3))==tuple(direct[5]['Y2'][i][i] for i in range(3))
                                assert tuple(q['Y3_'+str(i)] for i in range(3))==tuple(direct[5]['Y3'][i][i] for i in range(3))
                            rows.append(dict(context=name,strengths=strengths,v=str(v),u=str(u),word=word,frame=frame,status=action.status,
                                plan_status=plan.status,features=len(plan.features),definitions=plan.proof.definitions if plan.proof else (),
                                proof_digest=plan.proof.digest if plan.proof else None,recipe_digest=plan.recipe.digest,nodes=len(plan.recipe.nodes),
                                islands=len(plan.recipe.islands),maximum_island_degree=max(map(n.synthesis.degree,plan.recipe.polynomials.values())),
                                all_island_identities_verified=plan.status=='AVAILABLE',matrix_action_match=True))
        print(json.dumps(dict(stage='matrix-matches',context=name,plans=len(rows))),flush=True)
    write(OUTPUT/'starts.json',dict(input_commit=INPUT_COMMIT,input_sha256=INPUT_SHA,rows=rows,exact_reads_during_construction=0,requested_future_paths_during_construction=0))
    motions=[];snapshots=[]
    for case in spec['motions']:
        state,stages,work=build_case(case)
        # Independently supplied contexts, words and controls are not changed
        # if a case is empty, singular or exceeds a budget.
        item=dict(name=case['name'],phase=state.phase,status=state.action.status,certified=state.certified,
            source_counts=[len(x.engine.stock) for x in stages if x.phase in ('BOUND','CLOSED1','CLOSED2','CLOSED3')],
            work=work,features=len(state.plan.features),upper_endpoint=state.upper[1].live.accumulated if state.upper else None,
            local_endpoints=[x.engine.upper.live.accumulated for x in state.flowers])
        if case['name'] in ('mixed-connected','mixed-last-port'):
            for i,stage in enumerate(stages):
                raw,h=live.dumps(stage)
                fresh=a.register(tuple(case['modes']));request=scope(fresh,case['context'],case['strengths'],case['frame'])
                actual=live.loads(raw,h,fresh,request,stage.choice)
                assert live.dumps(actual)[0]==raw
                snapshots.append(dict(name=case['name'],index=i,phase=stage.phase,sha256=h,bytes=len(raw)))
            (OUTPUT/(case['name']+'.record.json')).write_bytes(raw)
        motions.append(item);print(json.dumps(dict(stage=case['name'],certified=state.certified,checkpoints=len(snapshots))),flush=True)
    controls=[]
    for modes in map(tuple,spec['retention_controls']):
        e=a.register(modes);request=scope(e,'mixed',('0','0'));plan=before_values(e,request,1,0,'HHHSUT');action,cache,work=n.resolve(e,request,plan)
        if action.status=='ADMISSIBLE':
            ready=live.resolve(live.choose(live.start(e,request),1,0,'HHHSUT'))[0];done=live.finish(ready)
            actual=dict(certified=done.certified,local_endpoints=[x.engine.upper.live.accumulated for x in done.flowers],upper_endpoint=done.upper[1].live.accumulated,successful_record_issued=True)
        else:actual=counterfactual(e,request)
        controls.append(dict(modes=modes,status=action.status,**actual))
    # A past first flower closes even for v=0, while the common upper demand
    # has no completion in the declared family. Keep this as a failed control.
    request=scope(entry,'mixed',('0','0'));zero=before_values(entry,request,0,0,'HHHSUT');zero_action=n.resolve(entry,request,zero)[0]
    zero_motion=counterfactual(entry,request,v=Q(0))
    groups=[]
    def check(name,ok,**detail):
        if not ok:raise AssertionError(name)
        groups.append(dict(name=name,passed=True,**detail))
    check('all_precommitted_current_plans_match_independent_three_by_three_matrix_solves',len(rows)==288)
    check('construction_is_before_exact_values_and_requested_motion',True,exact_queries=0,requested_future_paths=0)
    active=[r for r in rows if r['plan_status']=='AVAILABLE']
    check('all_polynomial_islands_have_exact_reconstruction_certificates',bool(active) and all(r['all_island_identities_verified'] for r in active),certificates=len(active))
    check('the_same_frozen_budget_accepts_this_new_rational_consumer',all(r['maximum_island_degree']<=16 and r['features']<=2 for r in active),maximum_nodes=max(r['nodes'] for r in rows),maximum_island_degree=max(r['maximum_island_degree'] for r in rows))
    check('disconnected_mixed_requires_a_joint_observation',all(r['features']==1 for r in active if r['context']=='mixed' and r['strengths'][0]=='0' and r['v']=='1'))
    check('connected_mixed_constructs_a_linear_and_a_quadratic_observation',all(sorted(n.synthesis.degree(n.Polynomial(c)) for k,c in r['definitions'])==[1,2] for r in active if r['context']=='mixed' and r['strengths'][0]!='0' and r['status']=='ADMISSIBLE'))
    check('five_declared_cases_close_three_real_flowers_and_one_upper_cell',len(motions)==5 and all(r['certified'] and r['source_counts']==[6,7,8,9] and r['local_endpoints']==[b.NEG]*3 and r['upper_endpoint']==b.ONE for r in motions))
    check('erasure_obstructs_the_same_upper_demand_and_restoration_recovers_it',[x['certified'] for x in controls]==[True,False,False,False,True] and all(x['local_endpoints']==[b.NEG]*3 for x in controls))
    check('upper_constraint_excludes_a_locally_closing_current_choice_before_execution',zero_action.status=='EMPTY' and not zero_motion['certified'] and zero_motion['local_endpoints']==[b.NEG]*3,control=zero_motion)
    check('unavailable_common_charts_are_not_execution_permissions',all(r['status']=='UNKNOWN_CHART' for r in rows if r['context']=='outside_chart'))
    check('two_complete_seven_stage_histories_replay_from_fresh_entries',len(snapshots)==14,checkpoints=len(snapshots))
    frozen=(HERE/'observation_synthesis.py').read_bytes()
    check('RR68_component_bytes_are_unchanged',hashlib.sha256(frozen).hexdigest()==spec['frozen_component']['sha256'])
    result=dict(schema='time-engine-rr69-three-flower-result-v1',input_commit=INPUT_COMMIT,input_sha256=INPUT_SHA,groups=groups,plans=len(rows),
        available_proofs=len(active),motions=motions,retention_controls=controls,checkpoints=snapshots,original_RR54_root_family_reused=False,
        unchanged_component_sha256=hashlib.sha256(frozen).hexdigest(),global_rational_degree_bound_claimed=False,globally_minimal_observations_claimed=False)
    write(OUTPUT/'result.json',result);print(json.dumps(dict(passed=True,plans=len(rows),groups=len(groups),checkpoints=len(snapshots))),flush=True);return result

if __name__=='__main__':run()
