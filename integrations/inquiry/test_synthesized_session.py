import unittest,json,hashlib
from dataclasses import replace
from fractions import Fraction as Q
from unittest.mock import patch
import synthesized_resolution as a
import synthesized_session as live
import observation_synthesis as synth
import rr68_study as study


class AlgebraTests(unittest.TestCase):
    def test_product_is_discovered_when_both_linear_terms_vanish(self):
        x,y=synth.variable('x'),synth.variable('y');p=x.mul(y)
        proof=synth.discover({'first':p.scaled(3),'later':p.mul(p).add(synth.scalar(7))})
        self.assertEqual(proof.status,'AVAILABLE');self.assertEqual(len(proof.definitions),1)
        self.assertEqual(a.Polynomial(proof.definitions[0][1]).terms,p.terms)

    def test_unregistered_linear_and_quadratic_forms_are_synthesized(self):
        x,y=synth.variable('x'),synth.variable('y');z=x.scaled(3).add(y.scaled(5))
        q=x.mul(x).scaled(2).add(x.mul(y).scaled(-1)).add(y.mul(y).scaled(7))
        inputs={'a':z.add(z.mul(z)).add(q),'b':q.mul(q).add(z.mul(z).mul(z))}
        proof=synth.discover(inputs)
        self.assertEqual(proof.status,'AVAILABLE');self.assertEqual(len(proof.definitions),2)
        self.assertTrue(synth.verify(inputs,proof))

    def test_variable_names_do_not_select_a_catalogue(self):
        u,v=synth.variable('u'),synth.variable('v');p=u.mul(v)
        proof=synth.discover({'f':p,'g':p.mul(p)},variables=('u','v'))
        self.assertEqual(proof.status,'AVAILABLE');self.assertEqual(len(proof.definitions),1)

    def test_relabeling_a_whole_high_degree_output_is_not_an_allowed_escape(self):
        x=synth.variable('x');f=x.mul(x).mul(x)
        self.assertEqual(synth.discover({'f':f}).status,'UNDETERMINED_FEATURE_DEGREE_BUDGET')

    def test_a_graded_budget_failure_is_not_a_global_impossibility_claim(self):
        x,y=synth.variable('x'),synth.variable('y')
        proof=synth.discover({'a':x.mul(x),'b':x.mul(y),'c':y.mul(y)})
        self.assertEqual(proof.status,'UNDETERMINED_FEATURE_COUNT_BUDGET')

    def test_degree_one_budget_cannot_silently_drop_a_mixed_term(self):
        x,y=synth.variable('x'),synth.variable('y')
        proof=synth.discover({'f':x.mul(y)},budget=synth.Budget(max_feature_degree=1))
        self.assertEqual(proof.status,'UNDETERMINED_FEATURE_DEGREE_BUDGET')

    def test_work_budget_is_explicitly_unresolved(self):
        x,y=synth.variable('x'),synth.variable('y')
        self.assertEqual(synth.discover({'f':x.add(y)},budget=synth.Budget(max_terms=1)).status,'UNDETERMINED_TERM_BUDGET')

    def test_changed_identity_or_input_is_rejected(self):
        x,y=synth.variable('x'),synth.variable('y');inputs={'f':x.mul(y)};proof=synth.discover(inputs)
        with self.assertRaises(ValueError):synth.verify(inputs,replace(proof,outputs=(('f',()),)))
        with self.assertRaises(ValueError):synth.verify({'f':x.add(y)},proof)

    def test_renaming_an_inhomogeneous_demand_is_not_a_graded_certificate(self):
        x,y=synth.variable('x'),synth.variable('y');f=x.add(y.mul(y));inputs={'f':f}
        proof=synth.discover(inputs)
        forged=replace(proof,definitions=(('g0',synth.data(f)),),outputs=(('f',synth.data(synth.variable('g0'))),))
        with self.assertRaises(ValueError):synth.verify(inputs,forged)


class SynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry=a.register();cls.pure=study.scope(cls.entry,'mixed','0')
        cls.fine=study.scope(cls.entry,'mixed','1/1024');cls.split=study.scope(cls.entry,'mixed','1/1024','split')
        cls.ready=live.resolve(live.choose(live.start(cls.entry,cls.fine),1,'HHHSUT'))
        cls.complete=live.execute(cls.ready);cls.raw,cls.h=live.dumps(cls.complete)

    def test_compile_constructs_definitions_without_reading_values_or_catalogue(self):
        request=study.scope(self.entry,'main_perturbed','1/1024','shear')
        with (patch.object(self.entry.base.vault,'exact',side_effect=AssertionError('no exact value')),
              patch.object(self.entry.core.derived,'exact',side_effect=AssertionError('no old catalogue')),
              patch.object(a.core,'factor',side_effect=AssertionError('no old catalogue factorization'))):
            plan=a.compile(self.entry,request,64,'HHHUST')
        self.assertEqual(plan.status,'AVAILABLE');self.assertTrue(study.check_identity(self.entry,request,plan))

    def test_dynamic_observers_are_not_registered_before_resolution(self):
        entry=a.register();request=study.scope(entry,'mixed','0','split')
        plan=a.compile(entry,request,1,'HHHSUT')
        self.assertEqual(entry.derived._records(),());self.assertEqual(len(plan.features),1)

    def test_registration_source_reads_are_counted_in_addition_to_feature_query(self):
        entry=a.register();request=study.scope(entry,'mixed','0');meter=a.fn.Meter()
        ready=live.resolve(live.choose(live.start(entry,request),1,'HHHSUT'),meter)
        self.assertEqual(entry._work[-1]['source_reads_for_registration'],2)
        self.assertEqual(entry._work[-1]['new_feature_queries'],1);self.assertEqual(meter.exact_reads,3)
        self.assertEqual(ready.phase,'READY')

    def test_new_basis_produces_the_quadratic_difference_from_the_demand(self):
        request=study.scope(self.entry,'mixed','0','split');plan=a.compile(self.entry,request,1,'HHHSUT')
        x,y=synth.variable('x'),synth.variable('y')
        self.assertEqual(a.Polynomial(plan.proof.definitions[0][1]).terms,x.mul(x).add(y.mul(y).scaled(-1)).terms)

    def test_the_constructed_feature_can_merge_distinct_originals(self):
        p=a.compile(self.entry,self.pure,1,'HHHSUT');definition=a.Polynomial(p.definitions[0][1])
        self.assertEqual(definition.exact({'s':Q(1,3),'t':Q(1,7)}),definition.exact({'s':Q(1,7),'t':Q(1,3)}))

    def test_every_physical_action_coefficient_matches_across_frames(self):
        actions=[]
        for frame in study.FRAMES:
            request=study.scope(self.entry,'mixed','1/1024',frame);plan=a.compile(self.entry,request,1,'HHHSUT')
            self.assertTrue(study.check_identity(self.entry,request,plan));actions.append(study.physical(a.resolve(self.entry,request,a.Policy(),plan)[0]))
        self.assertEqual(actions,[actions[0]]*3)

    def test_a_new_feature_can_be_derived_from_previously_read_observations(self):
        exact=self.entry.base.vault.exact
        with patch.object(self.entry.base.vault,'exact',side_effect=AssertionError('derive from old feature values')):
            changed=live.resolve(live.choose(live.revise(self.ready,self.split),1,'HHHSUT'))
        self.assertFalse(live.history(changed)[-1]['new_keys']);self.assertTrue(live.history(changed)[-1]['derived_keys'])
        self.assertEqual(study.physical(changed.prepared.action),study.physical(self.ready.prepared.action))

    def test_new_scope_and_old_action_cannot_be_combined(self):
        changed=live.resolve(live.choose(live.revise(self.ready,self.split),1,'HHHSUT'))
        with patch.object(live,'actual_motion',side_effect=AssertionError('reject before motion')):
            with self.assertRaises(ValueError):live.execute(changed,self.ready.prepared)

    def test_a_plan_cannot_be_retargeted_to_a_new_frame(self):
        with self.assertRaises(ValueError):a.resolve(self.entry,self.split,a.Policy(),self.ready.prepared.plan)

    def test_budget_failure_keeps_values_and_can_be_revised(self):
        low=live.resolve(live.choose(live.start(self.entry,self.fine,a.Policy(max_features=1)),1,'HHHSUT'))
        self.assertEqual(low.phase,'BLOCKED');self.assertTrue(low.prepared.action.status.startswith('UNDETERMINED_'))
        self.assertEqual(low.cache,())
        with self.assertRaises(ValueError):live.execute(low)
        high=live.resolve(live.choose(live.revise(low,self.fine,a.Policy()),1,'HHHSUT'))
        self.assertEqual(high.phase,'READY')

    def test_a_copied_observation_cannot_replace_an_issued_definition(self):
        plan=a.compile(self.entry,self.fine,64,'HHHUST');key=plan.features[0];original=self.entry._observations[key]
        self.entry._observations[key]=replace(original)
        try:
            with self.assertRaises(ValueError):a.resolve(self.entry,self.fine,a.Policy(),plan)
        finally:self.entry._observations[key]=original

    def test_modified_feature_value_is_rejected(self):
        cache=dict(self.ready.cache);key=next(iter(cache));digest,value=cache[key];cache[key]=(digest,value+1)
        with self.assertRaises(ValueError):a.resolve(self.entry,self.fine,a.Policy(),self.ready.prepared.plan,tuple(cache.items()))

    def test_original_and_unused_legacy_values_remain_archived(self):
        before=live.archives(self.entry);after=live.archives(self.entry,self.ready.cache)
        self.assertEqual(before['base'],after['base']);self.assertEqual(before['legacy'],after['legacy'])
        self.assertEqual({r.key for r,v in self.entry.base.vault._records()},{'s','t','p'})

    def test_old_stage_archive_does_not_import_a_later_sessions_observations(self):
        early=live.resolve(live.choose(live.start(self.entry,self.pure),1,'HHHSUT'))
        later=live.resolve(live.choose(live.start(self.entry,study.scope(self.entry,'main','1/1024','shear')),1,'HHHSUT'))
        raw,h=live.dumps(early);fresh=a.register();restored=live.loads(raw,h,fresh,study.scope(fresh,'mixed','0'))
        self.assertEqual(restored.digest,early.digest);self.assertEqual(len(restored.cache),1)

    def test_ready_and_complete_records_replay_with_a_fresh_empty_registry(self):
        raw,h=live.dumps(self.ready);fresh=a.register()
        restored=live.loads(raw,h,fresh,study.scope(fresh,'mixed','1/1024'))
        self.assertEqual(live.execute(restored).digest,self.complete.digest)
        fresh=a.register();self.assertEqual(live.loads(self.raw,self.h,fresh,study.scope(fresh,'mixed','1/1024')).digest,self.complete.digest)

    def test_changed_frame_and_outer_hash_do_not_retarget_a_record(self):
        doc=json.loads(self.raw);doc['commands'][0]['scope']['frame']=[['1','1'],['1','1'],['1','1'],['-1','1']]
        raw=json.dumps(doc).encode()
        with self.assertRaises(ValueError):live.loads(raw,hashlib.sha256(raw).hexdigest(),self.entry,self.fine)

    def test_empty_and_unknown_do_not_become_discovery_permissions(self):
        for name,status in (('zero_head','EMPTY'),('outside_chart','UNKNOWN_CHART')):
            request=study.scope(self.entry,name,'0');meter=a.fn.Meter();p=a.compile(self.entry,request,1,'HHHSUT')
            action,cache,new,derived,used=a.resolve(self.entry,request,a.Policy(),p,meter=meter)
            self.assertEqual(action.status,status);self.assertEqual(meter.exact_reads,0)

    def test_both_current_words_remain_legal_and_completion_stops(self):
        for word in a.m.WORDS:self.assertEqual(live.choose(live.start(self.entry,self.fine),1,word).choice,(Q(1),word))
        self.assertEqual(self.complete.phase,'STOPPED')
        with self.assertRaises(ValueError):live.revise(self.complete,self.split)


if __name__=='__main__':unittest.main()
