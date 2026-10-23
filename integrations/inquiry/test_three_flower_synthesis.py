import unittest,json,hashlib
from dataclasses import replace
from fractions import Fraction as Q
from unittest.mock import patch
import three_flower_synthesis as n
import three_flower_session as live
import rr69_study as study
from three_flower_synthesis import synthesis as synth


def recipe_from(g,output):
    needed=set();todo=[output.index]+list(g.divisors)
    while todo:
        i=todo.pop()
        if i in needed:continue
        needed.add(i)
        if g.nodes[i].kind!='poly':todo.extend(g.nodes[i].children)
    islands=tuple(('p'+str(i),i) for i in sorted(needed) if g.nodes[i].kind=='poly')
    return n.Recipe(tuple(g.nodes),(('result',output.index),),tuple(g.divisors),islands)


class RationalAdapterTests(unittest.TestCase):
    def test_zero_multiplication_does_not_erase_a_denominator_guard(self):
        g=n.Arithmetic();s=g.poly(synth.variable('s'));out=g.scalar(0)*(g.scalar(1)/s)
        recipe=recipe_from(g,out);self.assertTrue(n.verify_graph(recipe))
        values={name:p.exact({'s':Q(0)})[0] for name,p in recipe.polynomials.items()}
        with self.assertRaises(n.Singular):n.Values(recipe,values).all()

    def test_canceled_division_is_not_legal_at_a_zero_denominator(self):
        g=n.Arithmetic();s=g.poly(synth.variable('s'));recipe=recipe_from(g,s/s)
        values={name:p.exact({'s':Q(0)})[0] for name,p in recipe.polynomials.items()}
        with self.assertRaises(n.Singular):n.Values(recipe,values).guard_all_divisions()

    def test_an_unlisted_divisor_is_rejected(self):
        g=n.Arithmetic();s=g.poly(synth.variable('s'));recipe=recipe_from(g,1/s)
        with self.assertRaises(ValueError):n.verify_graph(replace(recipe,divisors=()))

    def test_a_missing_polynomial_island_is_rejected(self):
        g=n.Arithmetic();s=g.poly(synth.variable('s'));recipe=recipe_from(g,1/s)
        with self.assertRaises(ValueError):n.verify_graph(replace(recipe,islands=recipe.islands[:-1]))

    def test_cyclic_graph_is_rejected(self):
        g=n.Arithmetic();s=g.poly(synth.variable('s'));recipe=recipe_from(g,1/s)
        bad=list(recipe.nodes);bad[-1]=n.Node('div',(len(bad)-1,0))
        with self.assertRaises(ValueError):n.verify_graph(replace(recipe,nodes=tuple(bad)))

    def test_finite_arithmetic_graph_budget_is_enforced(self):
        g=n.Arithmetic()
        for i in range(n.MAX_NODES):g.scalar(i)
        with self.assertRaises(ValueError):g.scalar(n.MAX_NODES)

    def test_adapter_does_not_override_the_frozen_input_degree_budget(self):
        x=synth.variable('x');p=synth.scalar(1)
        for _ in range(17):p=p.mul(x)
        self.assertEqual(synth.discover({'too-large-island':p}).status,'UNDETERMINED_INPUT_DEGREE_BUDGET')


class ThreeFlowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry=n.a.register();cls.request=study.scope(cls.entry)
        cls.bound=live.start(cls.entry,cls.request)
        cls.chosen=live.choose(cls.bound,1,0,'HHHSUT')
        cls.ready,cls.work=live.resolve(cls.chosen)
        cls.first=live.advance(cls.ready);cls.second=live.advance(cls.first);cls.third=live.advance(cls.second)
        cls.done=live.advance(cls.third);cls.raw,cls.sha=live.dumps(cls.done)

    def test_three_flower_plan_does_not_use_two_flower_planner_or_values(self):
        request=study.scope(self.entry,'main',('0','1/1024'),'split')
        plan=study.before_values(self.entry,request,1,-1,'HHHUST')
        self.assertEqual(plan.status,'AVAILABLE');self.assertTrue(n.verify_plan(self.entry,request,plan))

    def test_plan_construction_does_not_register_numeric_observations(self):
        entry=n.a.register();request=study.scope(entry);study.before_values(entry,request,1,1,'HHHUST')
        self.assertEqual(entry.derived._records(),())

    def test_pure_joint_requirement_constructs_one_mixed_observation(self):
        request=study.scope(self.entry,'mixed',('0','0'),'split');p=n.compile(self.entry,request,1,0,'HHHSUT')
        x,y=synth.variable('x'),synth.variable('y')
        self.assertEqual(len(p.features),1)
        self.assertEqual(n.Polynomial(p.proof.definitions[0][1]).terms,x.mul(x).add(y.mul(y).scaled(-1)).terms)

    def test_nonzero_ports_keep_both_required_generators(self):
        self.assertEqual(sorted(synth.degree(n.Polynomial(c)) for k,c in self.ready.plan.proof.definitions),[1,2])

    def test_all_three_generated_sources_match_independent_matrix_solve(self):
        direct=study.oracle(self.entry,self.request,1,0,'HHHSUT')
        self.assertEqual(study.physical(self.ready.action),direct[:5])

    def test_same_action_is_reconstructed_in_a_different_frame(self):
        request=study.scope(self.entry,frame='split');plan=n.compile(self.entry,request,1,0,'HHHSUT')
        action=n.resolve(self.entry,request,plan)[0]
        self.assertEqual(study.physical(action),study.physical(self.ready.action))

    def test_two_flower_observations_can_be_reused_by_three_flower_consumer(self):
        request=n.a.Scope(self.request.base_scope)
        plan=n.a.compile(self.entry,request,1,'HHHSUT')
        action,cache,*_=n.a.resolve(self.entry,request,n.a.Policy(),plan)
        with patch.object(self.entry.base.vault,'exact',side_effect=AssertionError('already read observers suffice')):
            actual,new_cache,work=n.resolve(self.entry,self.request,self.ready.plan,cache)
        self.assertEqual(study.physical(actual),study.physical(self.ready.action));self.assertEqual(work['source_reads_for_registration'],0)

    def test_registration_cost_includes_original_source_reads(self):
        entry=n.a.register();request=study.scope(entry,'mixed',('0','0'));plan=n.compile(entry,request,1,0,'HHHSUT')
        meter=n.fn.Meter();action,cache,work=n.resolve(entry,request,plan,meter=meter)
        self.assertEqual(action.status,'ADMISSIBLE');self.assertEqual(work['source_reads_for_registration'],2)
        self.assertEqual(work['new_feature_queries'],1);self.assertEqual(meter.exact_reads,3)

    def test_changed_cached_value_is_rejected_before_motion(self):
        cache=dict(self.ready.cache);key=next(iter(cache));digest,value=cache[key];cache[key]=(digest,value+1)
        with self.assertRaises(ValueError):n.resolve(self.entry,self.request,self.ready.plan,tuple(cache.items()))

    def test_copied_or_retargeted_plan_is_rejected(self):
        with self.assertRaises(ValueError):n.resolve(self.entry,self.request,replace(self.ready.plan))
        with self.assertRaises(ValueError):n.resolve(self.entry,replace(self.request,last_strength=Q(0)),self.ready.plan)

    def test_changed_reconstruction_certificate_is_rejected(self):
        proof=self.ready.plan.proof;bad=replace(proof,outputs=proof.outputs[:-1])
        demands=n.a.in_frame(self.ready.plan.recipe.polynomials,self.request.frame)
        with self.assertRaises(ValueError):synth.verify(demands,bad)

    def test_unknown_chart_is_not_an_execution_permission(self):
        request=study.scope(self.entry,'outside_chart');state=live.choose(live.start(self.entry,request),1,0,'HHHSUT')
        state,_=live.resolve(state);self.assertEqual(state.phase,'REJECTED')
        with self.assertRaises(ValueError):live.advance(state)

    def test_upper_zero_obstruction_is_not_repaired_by_rewriting_past(self):
        request=study.scope(self.entry,'mixed',('0','0'));plan=n.compile(self.entry,request,0,0,'HHHSUT')
        self.assertEqual(n.resolve(self.entry,request,plan)[0].status,'EMPTY')
        self.assertEqual(self.entry.base.engine,self.bound.engine)

    def test_restricted_final_resource_interval_is_rechecked(self):
        request=study.scope(self.entry,domain=('0','0'));plan=n.compile(self.entry,request,1,0,'HHHSUT')
        self.assertEqual(n.resolve(self.entry,request,plan)[0].status,'EMPTY')

    def test_each_real_flower_closes_and_inherits_the_previous_history(self):
        before=self.entry.base.engine
        for state in (self.first,self.second,self.third):
            self.assertEqual(state.engine.upper.live.accumulated,n.b.NEG)
            self.assertEqual(state.engine.stock[:-1],before.stock)
            self.assertEqual(state.engine.events[:len(before.events)],before.events)
            self.assertEqual(state.engine.rounds[:-1],before.rounds)
            before=state.engine
        self.assertEqual(len(self.third.engine.stock),9)

    def test_three_outputs_form_one_first_boundary_upper_cell(self):
        self.assertTrue(self.done.certified);self.assertEqual(self.done.phase,'STOPPED')
        start,current,decoded,errors=self.done.upper
        self.assertEqual(current.live.accumulated,n.b.ONE)
        self.assertTrue(all(x>n.te.port.EPSILON for x in errors[:2]));self.assertEqual(errors[2],0)
        self.assertEqual(len(decoded.outputs[0].cell.beta),3);self.assertEqual(decoded.outputs[0].level,4)

    def test_closed_past_cannot_be_reselected(self):
        for state in (self.first,self.second,self.third,self.done):
            with self.assertRaises(ValueError):live.choose(state,1,1,'HHHUST')
        with self.assertRaises(ValueError):live.advance(self.done)

    def test_forged_state_is_rejected(self):
        with self.assertRaises(ValueError):live.advance(replace(self.ready,action=replace(self.ready.action,R3=self.ready.action.R2)))

    def test_the_entire_original_archive_is_preserved(self):
        before=live.old.archives(self.entry);after=live.old.archives(self.entry,self.ready.cache)
        self.assertEqual(before['base'],after['base']);self.assertEqual(before['legacy'],after['legacy'])

    def test_completed_record_replays_from_a_fresh_issued_entry(self):
        entry=n.a.register();request=study.scope(entry);actual=live.loads(self.raw,self.sha,entry,request,(Q(1),Q(0),'HHHSUT'))
        self.assertEqual(live.dumps(actual)[0],self.raw)

    def test_hash_request_and_current_choice_substitution_are_rejected(self):
        with self.assertRaises(ValueError):live.loads(self.raw,'0'*64,self.entry,self.request)
        with self.assertRaises(ValueError):live.loads(self.raw,self.sha,self.entry,replace(self.request,last_strength=Q(0)))
        with self.assertRaises(ValueError):live.loads(self.raw,self.sha,self.entry,self.request,(Q(1),Q(1),'HHHSUT'))

    def test_forged_actual_endpoint_is_rejected_even_with_rehashed_bytes(self):
        value=json.loads(self.raw);value['graph']['root']=None
        raw=(json.dumps(value,separators=(',',':'))+'\n').encode()
        with self.assertRaises(ValueError):live.loads(raw,hashlib.sha256(raw).hexdigest(),self.entry,self.request)

    def test_forged_observation_archive_is_rejected(self):
        value=json.loads(self.raw);value['numbers']['base']='00'
        raw=(json.dumps(value,separators=(',',':'))+'\n').encode()
        with self.assertRaises(ValueError):live.loads(raw,hashlib.sha256(raw).hexdigest(),self.entry,self.request)

    def test_command_save_and_load_bounds_are_consistent(self):
        state=self.bound
        for _ in range(live.MAX_COMMANDS-1):state=live.choose(state,1,0,'HHHSUT')
        raw,h=live.dumps(state);actual=live.loads(raw,h,self.entry,self.request,state.choice)
        self.assertEqual(actual.phase,'CHOSEN')
        with self.assertRaises(ValueError):live.choose(state,1,0,'HHHSUT')

if __name__=='__main__':unittest.main()
