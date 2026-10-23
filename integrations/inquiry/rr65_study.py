"""Fixed-input omission proofs, an independent matrix oracle, actual motions."""
from pathlib import Path
from dataclasses import asdict,replace
from fractions import Fraction as Q
from collections import Counter
import hashlib,json
import mixed_action_sets as m
import mixed_execution as plant
from mixed_action_sets import b,d,te,prior,fn

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/'.work/rr65-local'
INPUT_COMMIT='a7ea44bf2e25915a54087f28cc76bf90f4e8b1df'
INPUT_SHA='4b738ebfc55046bef793ac4ed98947e372a438ef232f8b148b1f39f8ada08abd'
_ORACLE_VALUES={}


def write(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,default=te.triple.encode)+'\n').encode())


def oracle(entry,scope,v,word,omitted=()):
    """Direct matrix construction and affine solve; no symbolic pullback or path."""
    hc=prior.scalar(entry.head.kernel(scope.C))
    if not hc:return 'EMPTY',(),()
    if not te.port.regular(scope.C,entry.library):return 'UNKNOWN',(),()
    if entry.digest not in _ORACLE_VALUES:
        _ORACLE_VALUES[entry.digest]=(prior.data(entry.first.flight)[1].shift,prior.data(entry.second)[1].shift)
    actual_s,actual_t=_ORACLE_VALUES[entry.digest]
    s=Q(0) if 's' in omitted else actual_s
    t=Q(0) if 't' in omitted else actual_t
    base=entry.first.flight.pair.representative.weights
    S=d.AffineLetter(tuple(a+s*z for a,z in zip(base,entry.first.axis)),entry.library)
    U=d.AffineLetter(tuple(a+t*z for a,z in zip(base,entry.direction_U)),entry.library)
    T=d.AffineLetter(tuple(a+v*z for a,z in zip(base,entry.first.axis)),entry.library)
    H=tuple(d.tensor(x) for x in entry.head.leaves())
    maps={'H':H,'S':(d.tensor(S),),'U':(d.tensor(U),),'T':(d.tensor(T),)}
    leaves=tuple(x for k in word for x in maps[k]);den=Q(len(leaves)*(len(leaves)+1),2)
    raw=tuple(tuple(sum(Q(k)*x[i][j]/den for k,x in enumerate(leaves,1)) for j in range(3)) for i in range(3))
    anchor=te.pair.boundary_readout(entry.head)
    y=tuple(tuple(anchor[i][j]+scope.strength*(raw[i][j]-(Q(1,3) if i==j else 0)) for j in range(3)) for i in range(3))
    first=Q(1)
    for leaf in leaves:first*=prior.scalar(d.join(leaf,scope.C))
    if not first:return 'EMPTY',(),()
    if not te.port.regular(y,entry.library):return 'UNKNOWN',(),()
    h=prior.scalar(entry.head.kernel(y))
    if not h or abs(h-1)<=te.port.EPSILON or abs(-first-1)<=te.port.EPSILON:return 'UNKNOWN',(),()
    r0=prior.cycle.correction_leaf(y,entry.library,(1/h,0,0,0))
    axis=te.pair.null_direction(y,entry.library)
    g=prior.scalar(prior.direction_response(axis,entry.library,scope.C))
    k=-first*hc
    if not k or not g:return 'UNKNOWN',(),()
    alpha=(1/k-prior.scalar(r0.kernel(scope.C)))/g
    if not scope.domain[0]<=alpha<=scope.domain[1]:return 'EMPTY',(),()
    weights=tuple(a+alpha*z for a,z in zip(r0.weights,axis))
    if weights==(Q(1,3),Q(1,3),Q(1,3),Q(0),Q(0),Q(0)):return 'UNKNOWN',(),()
    return 'ADMISSIBLE',T.weights,weights


def run():
    raw=(HERE/'RR65-inputs.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INPUT_SHA:raise ValueError('the pre-calculation RR65 input bytes changed')
    spec=json.loads(raw);OUTPUT.mkdir(parents=True,exist_ok=True)
    entry=m.register();entries={('keep','keep'):entry};rows=[];rejections=[]
    for cfg in spec['cases']:
        if cfg['family']=='offdiagonal':
            try:m.register('offdiagonal')
            except ValueError as err:
                rejections.append(dict(configuration=cfg,stage='entry-source-current-closure',reason=str(err),
                    planned_scope_comparisons=12,planned_additional_execution_pairs=2,
                    inference='this proposed blind-direction fixture is invalid; no omission permission'))
            else:raise AssertionError('the non-null offdiagonal source must not be accepted')
            continue
        for name in spec['contexts']:
            scope=m.Scope(entry.digest,m.context(entry,name),Q(cfg['strength']))
            for omitted in spec['omitted_subsets']:
                result=m.compare(entry,scope,omitted,tuple(spec['precisions']))
                full=[];reduced=[]
                for v in scope.controls:
                    for word in scope.words:
                        full.append(oracle(entry,scope,v,word));reduced.append(oracle(entry,scope,v,word,omitted))
                expected=('DIFFERENT' if any(a!=z and a[0]!='UNKNOWN' and z[0]!='UNKNOWN' for a,z in zip(full,reduced))
                    else 'SAME' if all(a==z and a[0]!='UNKNOWN' for a,z in zip(full,reduced)) else 'UNDETERMINED')
                if result.verdict!=expected:raise AssertionError((cfg,name,omitted,result,expected))
                rows.append(dict(context=name,strength=cfg['strength'],omitted=omitted,
                    certificate=asdict(result),matches_independent_physical_action_oracle=True))
    write(OUTPUT/'starts.json',dict(input_commit=INPUT_COMMIT,input_sha256=INPUT_SHA,
        comparisons=rows,rejected_input_configurations=rejections,all_before_requested_bundle_actuation=True,
        prior_U_bootstrap_is_part_of_entry_authentication=True))
    print(json.dumps(dict(stage='all-pre-actuation-comparisons-match',scopes=len(rows),verdicts=dict(Counter(x['certificate']['verdict'] for x in rows)))),flush=True)
    groups=[]
    def check(name,ok,**details):
        if not ok:raise AssertionError(name)
        groups.append(dict(name=name,passed=True,**details))
    check('physical_action_set_comparisons_match_independent_matrix_oracle',all(x['matches_independent_physical_action_oracle'] for x in rows),scopes=len(rows),candidate_comparisons=8*len(rows))
    check('comparison_never_reads_exact_retained_coordinates',all(x['certificate']['reads'][2]==0 for x in rows),
        coarse_reads=sum(x['certificate']['reads'][0] for x in rows),refinement_reads=sum(x['certificate']['reads'][1] for x in rows))
    check('unknown_charts_do_not_become_omission_permissions',all(x['certificate']['verdict']=='UNDETERMINED' for x in rows if x['context']=='outside_chart'))
    check('an_invalid_blind_direction_is_rejected_at_entry',len(rejections)==1,rejected=rejections)
    pure=m.Scope(entry.digest,m.context(entry,'mixed'),Q(0))
    recipe=m.build(entry,pure,1,'HHHSUT');poly=recipe.polynomials['B1']
    check('the_mixed_channel_survives_when_both_first_order_terms_vanish',
        set(poly.terms)=={('s','t')} and any(poly.terms[('s','t')]),terms=tuple(poly.terms.items()),
        first_order_control='constant and both single-coordinate terms of B1 are exactly zero')
    joint_rows=[];joint_meters=[]
    for v in pure.controls:
        for word in pure.words:
            full_meter=fn.Meter();joint_meter=fn.Meter()
            full=m.action(entry,pure,v,word,meter=full_meter);joint=m.joint_action(entry,pure,v,word,meter=joint_meter)
            if (full.status,full.T,full.R)!=(joint.status,joint.T,joint.R):raise AssertionError('joint observation changed a physical action')
            joint_rows.append(dict(v=str(v),word=word,status=full.status,full_keys=full.read_keys,joint_keys=joint.read_keys,
                full_exact_reads=full_meter.exact_reads,joint_exact_reads=joint_meter.exact_reads))
            joint_meters.append(joint_meter)
    write(OUTPUT/'joint-observation.json',dict(role='follow-up quotient diagnostic after rejecting the offdiagonal fixture; not a preregistered discovery',
        context='mixed',strength='0',proof='every monomial in every action and guard polynomial is s^n t^n; map it exactly to p^n',
        registration_cost='p=s*t is authenticated exactly once; full s and t remain in the archive',rows=joint_rows))
    check('a_scoped_mixed_observation_preserves_the_whole_nonempty_physical_action_set',
        sum(x['status']=='ADMISSIBLE' for x in joint_rows)==6 and all(set(x['joint_keys'])<= {'p'} for x in joint_rows),
        exact_reads_individual=sum(x['full_exact_reads'] for x in joint_rows),exact_reads_joint=sum(x['joint_exact_reads'] for x in joint_rows),
        not_a_total_runtime_speedup_claim=True)
    active=m.Scope(entry.digest,m.context(entry,'mixed'),Q(1,1024))
    check('the_next_scope_can_require_individual_information_again',m.joint_polynomials(m.build(entry,active,1,'HHHSUT')) is None)
    executions=[];saved=None
    for modes in map(tuple,spec['execution_histories']):
        e=entries.get(modes)
        if e is None:e=m.register(modes=modes);entries[modes]=e
        scope=m.Scope(e.digest,m.context(e,'mixed'),Q(1,1024));action=m.action(e,scope,1,'HHHSUT')
        actual=plant.run(e,scope,action,counterfactual_alpha=0 if action.status!='ADMISSIBLE' else None)
        if modes==('keep','keep'):primary_kept=actual
        executions.append(dict(kind='declared-retention-control',modes=modes,predicted=action.status,
            certified=actual.certified,counterfactual=actual.counterfactual,
            endpoints=(actual.first.engine.upper.live.accumulated,actual.second.engine.upper.live.accumulated,actual.upper_trial.live.accumulated)))
    check('retention_and_restore_close_the_bundle_while_either_erasure_does_not',
        [x['certified'] for x in executions]==[True,False,False,False,True]
        and all(x['endpoints'][:2]==(b.NEG,b.NEG) for x in executions),cases=executions.copy())
    joint_action=m.joint_action(entry,pure,1,'HHHSUT');joint_actual=plant.run(entry,pure,joint_action)
    executions.append(dict(kind='follow-up-joint-observation',certified=joint_actual.certified,counterfactual=False))
    raw,h=plant.dumps(entry,pure,joint_actual);loaded=plant.loads(raw,h,entry,pure,1,'HHHSUT')
    (OUTPUT/'joint-complete.record.json').write_bytes(raw)
    check('joint_omission_preserves_the_actual_motion_and_full_original_archive',loaded==joint_actual,
        original_keys=tuple(ref.key for ref,value in entry.vault._records()),bytes=len(raw),sha256=h)
    main=m.Scope(entry.digest,m.context(entry,'main'),Q(1,1024));a=m.action(entry,main,1,'HHHSUT')
    full=plant.run(entry,main,a)
    # Counterfactual coefficients are computed from the t-erased matrix model,
    # then applied as alpha to the original actual port, preserving local work.
    erased=entries[('keep','erase')];es=m.Scope(erased.digest,m.context(erased,'main'),Q(1,1024))
    ea=m.action(erased,es,1,'HHHSUT');wrong=plant.run(entry,main,a,counterfactual_alpha=ea.alpha)
    executions.extend((dict(kind='main-kept',certified=full.certified,counterfactual=False),dict(kind='main-erased-correction-on-kept-plant',certified=wrong.certified,counterfactual=True)))
    check('wrong_omission_can_keep_both_local_closures_but_fail_the_bundle',not wrong.certified
        and wrong.first.engine.upper.live.accumulated==b.NEG and wrong.second.engine.upper.live.accumulated==b.NEG)
    other=m.action(entry,active,1,'HHHUST');other_actual=plant.run(entry,active,other)
    executions.append(dict(kind='other-current-word',certified=other_actual.certified,counterfactual=False))
    check('the_current_keeps_two_real_order_choices',other_actual.certified and other_actual.port[1]!=primary_kept.port[1]
        and other_actual.first.new_source.leaves()[0].weights==primary_kept.first.new_source.leaves()[0].weights,
        selected_words=list(m.WORDS))
    result=dict(schema='time-engine-rr65-mixed-action-set-v1',input_commit=INPUT_COMMIT,groups=groups,
        scope_comparisons=len(rows),candidate_comparisons=8*len(rows),verdict_counts=dict(Counter(x['certificate']['verdict'] for x in rows)),
        rejected_input_configurations=rejections,joint_observation=joint_rows,executions=executions,
        future_path_completions_for_set_comparison=0,original_differences_deleted=False,
        retained_product_is_a_derived_authenticated_observation=True)
    write(OUTPUT/'result.json',result)
    print(json.dumps(dict(passed=True,groups=len(groups),scopes=len(rows),executions=len(executions),
        certified=sum(x['certified'] for x in executions))),flush=True)
    return result


if __name__=='__main__':run()
