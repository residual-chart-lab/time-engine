import unittest
from unittest.mock import patch
from dataclasses import replace
from fractions import Fraction as Q
import hashlib,json
import bundle_demand as b
import bundle_execution as plant
import rr64_study as study


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries={m:b.register(m) for m in ('keep','erase','restore')}
        cls.resolved={};cls.actuals={}
        for mode,entry in cls.entries.items():
            for word in ('HHST','HHTS'):
                scope=b.Scope(entry.digest,Q(-1),Q(64),word)
                recipe=b.build(entry,scope);assessment=b.assess(entry,scope,recipe)
                resolution=b.resolve(entry,scope,recipe,assessment)
                cls.resolved[mode,word]=(entry,scope,recipe,assessment,resolution)
                cls.actuals[mode,word]=plant.execute(entry,scope,recipe,assessment,resolution)

    def test_assessment_uses_no_retained_exact_read_or_completed_future_path(self):
        e,s,r,a,z=self.resolved['keep','HHST']
        s=replace(s,x=Q(-1,2),first_control=Q(0))
        original=b.d.AffineLetter.kernel
        def guard(leaf,y):
            if leaf==e.flight.pair.original:raise AssertionError('retained source response must stay latent')
            return original(leaf,y)
        with patch.object(e.vault,'exact',side_effect=AssertionError('no exact read')), \
             patch.object(plant,'execute',side_effect=AssertionError('no completed future path')), \
             patch.object(type(e.flight),'digest',property(lambda _: (_ for _ in ()).throw(AssertionError('no full-history rehash')))), \
             patch.object(b.d.AffineLetter,'kernel',guard):
            recipe=b.build(e,s)
            self.assertTrue(b.assess(e,s,recipe).needs_exact)

    def test_existence_needs_no_exact_value_or_action_permission(self):
        e,s,r,a,z=self.resolved['keep','HHST']
        exists=replace(s,observation=b.EXISTS);recipe=b.build(e,exists);meter=b.fn.Meter()
        with patch.object(e.vault,'exact',side_effect=AssertionError('not needed')):
            assessment=b.assess(e,exists,recipe)
            result=b.resolve(e,exists,recipe,assessment,meter)
        self.assertTrue(result.feasible);self.assertIsNone(result.control)
        self.assertEqual(meter.exact_reads,0)
        with self.assertRaises(ValueError):plant.execute(e,exists,recipe,assessment,result)

    def test_exact_action_reads_only_one_retained_coordinate(self):
        e,s,r,a,z=self.resolved['keep','HHST'];meter=b.fn.Meter()
        self.assertEqual(b.resolve(e,s,r,a,meter),z)
        self.assertEqual(meter.exact_reads,1)
        self.assertEqual(r.dependencies,('retained-s',))

    def test_source_domain_exclusion_can_be_proved_without_exact_read(self):
        e,s,r,a,z=self.resolved['keep','HHST']
        narrow=replace(s,domain=(0,8));recipe=b.build(e,narrow);meter=b.fn.Meter()
        assessment=b.assess(e,narrow,recipe)
        self.assertEqual(assessment.status,'EMPTY_RESOURCE_DOMAIN')
        self.assertFalse(b.resolve(e,narrow,recipe,assessment,meter).feasible)
        self.assertEqual(meter.exact_reads,0)

    def test_resource_sweep_can_restrict_first_choices_before_execution(self):
        import bundle_resource_sweep
        result=bundle_resource_sweep.run(self.entries['keep'])
        counts=[x['count'] for x in result['rows']]
        self.assertEqual(counts,sorted(counts))
        self.assertTrue(0<result['rows'][2]['count']<6)
        self.assertEqual(result['rows'][-1]['count'],6)
        self.assertEqual(result['completed_future_paths'],0)

    def test_resource_boundary_stays_unresolved_until_exact_refinement(self):
        e,s,r,a,z=self.resolved['keep','HHST'];lo,hi=a.control_bounds
        edge=replace(s,domain=((lo+hi)/2,hi),observation=b.EXISTS)
        recipe=b.build(e,edge);assessment=b.assess(e,edge,recipe)
        self.assertTrue(assessment.needs_exact);self.assertIsNone(assessment.feasible)
        result=b.resolve(e,edge,recipe,assessment)
        self.assertEqual((result.feasible,result.control),study.direct_oracle(e,edge))

    def test_future_chart_failure_remains_unknown(self):
        e,s,r,a,z=self.resolved['keep','HHST'];s=replace(s,x=Q(0))
        r=b.build(e,s);a=b.assess(e,s,r);z=b.resolve(e,s,r,a)
        self.assertEqual(a.status,'OUTSIDE_FUTURE_CHART');self.assertIsNone(z.feasible)
        with self.assertRaises(ValueError):plant.execute(e,s,r,a,z)

    def test_zero_future_head_cannot_close_at_nonzero_target(self):
        e,s,r,a,z=self.resolved['keep','HHST'];s=replace(s,x=Q(1,2))
        r=b.build(e,s);a=b.assess(e,s,r);meter=b.fn.Meter()
        self.assertFalse(b.resolve(e,s,r,a,meter).feasible);self.assertEqual(meter.exact_reads,0)

    def test_scope_changes_cannot_reuse_dependency_proofs(self):
        e,s,r,a,z=self.resolved['keep','HHST']
        for changed in (replace(s,x=Q(-3,4)),replace(s,first_word='HHTS'),
                        replace(s,first_control=0),replace(s,strength=0),replace(s,domain=(0,8)),
                        replace(s,observation=b.EXISTS)):
            with self.assertRaises(ValueError):b.resolve(e,changed,r,a)

    def test_arbitrary_polynomial_witness_cannot_replace_the_issued_recipe(self):
        e,s,r,a,z=self.resolved['keep','HHST']
        forged=replace(r,plans=r.plans[:-1]+(replace(r.plans[-1],coefficients=()),))
        with self.assertRaises(ValueError):b.assess(e,s,forged)

    def test_fixed_result_and_inheritance_are_not_substitutable(self):
        e,s,r,a,z=self.resolved['keep','HHST']
        for kw in (dict(target=b.NEG),dict(inherited=b.ONE),dict(next_word='RH')):
            with self.assertRaises(ValueError):replace(s,**kw)

    def test_independent_matrix_oracle_matches_the_exact_control(self):
        for e,s,r,a,z in self.resolved.values():
            self.assertEqual((z.feasible,z.control),study.direct_oracle(e,s))

    def test_different_future_contexts_can_require_different_actions(self):
        e,s,r,a,z=self.resolved['keep','HHST'];s=replace(s,x=Q(-3,4))
        r=b.build(e,s);a=b.assess(e,s,r);other=b.resolve(e,s,r,a)
        self.assertTrue(other.feasible);self.assertNotEqual(other.control,z.control)

    def test_current_keeps_both_order_choices(self):
        a,c=self.actuals['keep','HHST'],self.actuals['keep','HHTS']
        self.assertTrue(a.certified and c.certified)
        self.assertEqual(a.first.engine.upper.live.accumulated,b.NEG)
        self.assertEqual(c.first.engine.upper.live.accumulated,b.NEG)
        self.assertEqual(a.first.new_source.leaves()[0].weights,c.first.new_source.leaves()[0].weights)
        self.assertNotEqual(a.port[1],c.port[1])
        self.assertNotEqual(a.control,c.control)

    def test_two_actual_cells_form_one_first_boundary_upper_cell(self):
        for actual in self.actuals.values():
            self.assertEqual(actual.second.engine.upper.live.accumulated,b.NEG)
            self.assertEqual(actual.upper_start.live.accumulated,b.NEG)
            self.assertEqual(actual.upper_trial.live.accumulated,b.ONE)
            self.assertEqual(len(actual.upper_decoded.outputs[0].cell.beta),2)
            self.assertGreater(actual.future_prefix_errors[0],b.te.port.EPSILON)

    def test_stock_publication_clocks_and_old_history_are_inherited(self):
        for key,actual in self.actuals.items():
            e=self.entries[key[0]];before=e.flight.first.closed_engine
            self.assertEqual([len(before.stock),len(actual.first.engine.stock),len(actual.second.engine.stock)],[5,6,7])
            self.assertEqual(actual.second.engine.events[:len(before.events)],before.events)
            self.assertEqual(actual.second.engine.rounds[:len(before.rounds)],before.rounds)
            self.assertTrue(all(x.level==2 for x in actual.second.engine.stock))
            self.assertTrue(all(x.level==3 for x in actual.second.engine.outputs))
            self.assertEqual(actual.second.new_source.cell.start,actual.first.engine.lower.__class__(
                b.te.port.UpperState(actual.second.context,actual.first.engine.lower.live.accumulated),
                actual.first.engine.lower.executed_word))

    def test_erasure_and_restore_affect_the_actual_later_source(self):
        a,z,r=(self.actuals[m,'HHST'] for m in ('keep','erase','restore'))
        self.assertNotEqual(a.second.new_source.leaves()[0].weights,z.second.new_source.leaves()[0].weights)
        self.assertEqual(a.second.new_source.leaves()[0].weights,r.second.new_source.leaves()[0].weights)

    def test_cutting_only_port_coupling_removes_order_dependence(self):
        e=self.entries['keep'];controls=[]
        for word in ('HHST','HHTS'):
            s=b.Scope(e.digest,-1,64,word,strength=0);r=b.build(e,s);a=b.assess(e,s,r)
            controls.append(b.resolve(e,s,r,a).control)
        self.assertEqual(controls[0],controls[1])

    def test_wrong_erased_control_closes_locally_but_fails_the_bundle(self):
        args=self.resolved['keep','HHST'];wrong=self.resolved['erase','HHST'][-1].control
        actual=plant.execute(*args,control_test=wrong)
        self.assertFalse(actual.certified)
        self.assertEqual(actual.first.engine.upper.live.accumulated,b.NEG)
        self.assertEqual(actual.second.engine.upper.live.accumulated,b.NEG)
        with self.assertRaises(ValueError):plant.dumps(*args[:4],actual)

    def test_an_action_resolution_cannot_be_forged(self):
        e,s,r,a,z=self.resolved['keep','HHST']
        with self.assertRaises(ValueError):plant.execute(e,s,r,a,replace(z,control=z.control+1))

    def test_completed_bundle_roundtrip_replays_all_actual_state(self):
        args=self.resolved['keep','HHST'];actual=self.actuals['keep','HHST']
        raw,h=plant.dumps(*args[:4],actual)
        loaded=plant.loads(raw,h,args[0],args[1])
        self.assertEqual(loaded,actual)

    def test_saved_scope_or_hash_substitution_is_rejected(self):
        args=self.resolved['keep','HHST'];actual=self.actuals['keep','HHST']
        raw,h=plant.dumps(*args[:4],actual)
        with self.assertRaises(ValueError):plant.loads(raw,h,args[0],replace(args[1],x=Q(-3,4)))
        with self.assertRaises(ValueError):plant.loads(raw+' '.encode(),h,args[0],args[1])
        changed=json.loads(raw);changed['scope_digest']='0'*64
        encoded=json.dumps(changed).encode()
        with self.assertRaises(ValueError):plant.loads(encoded,hashlib.sha256(encoded).hexdigest(),args[0],args[1])


if __name__=='__main__':unittest.main()
