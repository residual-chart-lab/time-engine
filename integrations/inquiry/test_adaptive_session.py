import unittest,json,hashlib
from unittest.mock import patch
from dataclasses import replace
from fractions import Fraction as Q
import adaptive_resolution as a
import adaptive_session as live
import resolution_algebra as alg
import rr66_study as study
import rr65_study as oracle
from adaptive_resolution import m,fn


class AdaptiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry=a.register()
        cls.pure=study.scope(cls.entry,'mixed','0');cls.fine=study.scope(cls.entry,'mixed','1/1024')
        cls.main=study.scope(cls.entry,'main','1/1024');cls.sum_scope=study.scope(cls.entry,'main','0')
        cls.coarse=live.resolve(live.choose(live.start(cls.entry,cls.pure),1,'HHHSUT'))
        cls.ready=live.resolve(live.choose(live.revise(cls.coarse,cls.fine),1,'HHHSUT'))
        cls.complete=live.execute(cls.ready)
        cls.raw,cls.sha=live.dumps(cls.complete)

    def test_exact_linear_feature_reduction_and_reexpansion(self):
        s,t=alg.variable('s'),alg.variable('t');z=s.scaled(7).add(t.scaled(8));p=s.mul(t)
        original=alg.power(z,3).add(p.mul(alg.power(z,2))).add(p.mul(p).scaled(-3))
        reduced=alg.linear_product(original,'port',7,8)
        self.assertIsNotNone(reduced)
        self.assertEqual(alg.expand(reduced,{'p':p,'port':z}).terms,original.terms)
        for x,y in ((Q(1,3),Q(-2,5)),(Q(0),Q(1)),(Q(1,10**20),Q(-7,11))):
            self.assertEqual(reduced.exact({'p':x*y,'port':7*x+8*y}),original.exact({'s':x,'t':y}))

    def test_symmetric_polynomial_reduces_but_a_single_coordinate_does_not(self):
        s,t=alg.variable('s'),alg.variable('t')
        original=s.mul(s).add(t.mul(t))
        reduced=alg.linear_product(original,'sum',1,1)
        expected=alg.variable('sum').mul(alg.variable('sum')).add(alg.variable('p').scaled(-2))
        self.assertEqual(reduced.terms,expected.terms)
        self.assertIsNone(alg.linear_product(s,'sum',1,1))

    def test_schema_selection_does_not_read_exact_values(self):
        scope=replace(self.main,domain=(-m.LIMIT,m.LIMIT-1))
        with patch.object(self.entry.base.vault,'exact',side_effect=AssertionError('no exact source read')), \
             patch.object(self.entry.derived,'exact',side_effect=AssertionError('no exact derived read')):
            plan=a.compile(self.entry,scope,64,'HHHUST')
        self.assertEqual(plan.mode,'INDIVIDUAL')

    def test_requests_select_four_different_sufficient_observations(self):
        scopes=(self.pure,self.fine,self.sum_scope,self.main)
        self.assertEqual([a.compile(self.entry,s,1,'HHHSUT').mode for s in scopes],
            ['PRODUCT','PORT_PRODUCT','SUM_PRODUCT','INDIVIDUAL'])

    def test_port_weights_are_bound_to_real_primitive_positions(self):
        self.assertEqual(a.port_weights(self.entry.base,'HHHSUT'),(7,8))
        self.assertEqual(a.port_weights(self.entry.base,'HHHUST'),(8,7))
        plan=a.compile(self.entry,self.fine,1,'HHHUST')
        self.assertEqual(plan.features,('p','port-HHHUST'))

    def test_all_physical_coefficients_match_independent_matrix_solutions(self):
        for scope in (self.pure,self.fine,self.sum_scope,self.main):
            for word in m.WORDS:
                plan=a.compile(self.entry,scope,1,word)
                action,cache,new,derived,used=a.resolve(self.entry,scope,a.Policy(),plan)
                self.assertEqual((action.status,action.T,action.R),oracle.oracle(self.entry.base,scope,Q(1),word))

    def test_product_to_port_reads_only_the_new_port_observation(self):
        self.assertEqual(live.history(self.coarse)[-1]['new_keys'],['p'])
        self.assertEqual(live.history(self.ready)[-1]['new_keys'],['port-HHHSUT'])
        self.assertEqual(set(dict(self.ready.cache)),{'p','port-HHHSUT'})

    def test_connected_actuation_and_its_verification_do_not_expand_originals(self):
        exact=self.entry.base.vault.exact
        def guard(key,meter):
            if key in ('s','t'):raise AssertionError('the sufficient port map must not be bypassed')
            return exact(key,meter)
        with patch.object(self.entry.base.vault,'exact',side_effect=guard):
            ready=live.resolve(live.choose(live.revise(self.coarse,self.fine),1,'HHHSUT'))
            complete=live.execute(ready)
        self.assertTrue(complete.result.certified)

    def test_a_real_full_fallback_reads_individuals_when_joint_cache_is_ambiguous(self):
        self.assertIsNone(a.derive_cached(self.entry,'s',dict(self.ready.cache)))
        meter=fn.Meter();session=live.resolve(live.choose(live.revise(self.ready,self.main),1,'HHHSUT'),meter)
        self.assertEqual(session.prepared.plan.mode,'INDIVIDUAL')
        self.assertEqual(live.history(session)[-1]['new_keys'],['s','t']);self.assertEqual(meter.exact_reads,2)

    def test_cached_sum_and_port_recover_originals_without_another_archive_query(self):
        session=live.resolve(live.choose(live.revise(self.ready,self.sum_scope),1,'HHHSUT'))
        meter=fn.Meter();session=live.resolve(live.choose(live.revise(session,self.main),1,'HHHSUT'),meter)
        self.assertEqual(live.history(session)[-1]['new_keys'],[])
        self.assertEqual(live.history(session)[-1]['derived_keys'],['s','t']);self.assertEqual(meter.exact_reads,0)

    def test_coarsening_reuses_product_and_keeps_every_finer_cached_value(self):
        full=live.resolve(live.choose(live.revise(self.ready,self.main),1,'HHHSUT'))
        down=live.resolve(live.choose(live.revise(full,self.pure),1,'HHHUST'))
        self.assertEqual(down.prepared.plan.mode,'PRODUCT')
        self.assertEqual(live.history(down)[-1]['new_keys'],[])
        self.assertTrue(set(dict(full.cache))<=set(dict(down.cache)))

    def test_word_change_cannot_reuse_the_wrong_port_as_if_identical(self):
        other=live.resolve(live.choose(self.ready,1,'HHHUST'))
        self.assertEqual(live.history(other)[-1]['new_keys'],['port-HHHUST'])
        self.assertNotEqual(other.prepared.action.R,self.ready.prepared.action.R)

    def test_feature_budget_is_unknown_and_can_be_revised_without_retargeting(self):
        low=live.start(self.entry,self.fine,a.Policy(max_features=1))
        low=live.resolve(live.choose(low,1,'HHHSUT'))
        self.assertEqual(low.phase,'BLOCKED');self.assertEqual(low.prepared.action.status,'UNDETERMINED_NO_SCHEMA')
        self.assertEqual(low.cache,())
        with self.assertRaises(ValueError):live.execute(low)
        high=live.resolve(live.choose(live.revise(low,self.fine,a.Policy()),1,'HHHSUT'))
        self.assertEqual(high.phase,'READY');self.assertEqual(high.scope,low.scope)

    def test_empty_and_unknown_requirements_neither_actuate_nor_erase(self):
        for name,status in (('zero_head','EMPTY'),('outside_chart','UNKNOWN_CHART')):
            session=live.resolve(live.choose(live.start(self.entry,study.scope(self.entry,name,'0')),1,'HHHSUT'))
            self.assertEqual(session.prepared.action.status,status);self.assertEqual(session.cache,())
            with self.assertRaises(ValueError):live.execute(session)

    def test_current_must_choose_and_both_words_remain_available(self):
        session=live.start(self.entry,self.fine)
        with self.assertRaises(ValueError):live.resolve(session)
        for word in m.WORDS:self.assertEqual(live.choose(session,1,word).choice,(Q(1),word))

    def test_old_action_is_invalidated_on_request_revision_before_any_actuation(self):
        changed=live.resolve(live.choose(live.revise(self.coarse,self.fine),1,'HHHSUT'))
        with patch.object(live,'actual_motion',side_effect=AssertionError('reject before motion')):
            with self.assertRaises(ValueError):live.execute(changed,self.coarse.prepared)

    def test_reselection_invalidates_the_old_prepared_action(self):
        changed=live.choose(self.ready,64,'HHHUST')
        self.assertIsNone(changed.prepared)
        with self.assertRaises(ValueError):live.execute(changed,self.ready.prepared)

    def test_plan_scope_and_coefficient_substitution_are_rejected(self):
        p=a.compile(self.entry,self.fine,1,'HHHSUT')
        for changed in (replace(p,features=('p',)),replace(p,coefficients=()),replace(p,word='HHHUST')):
            with self.assertRaises(ValueError):a.resolve(self.entry,self.fine,a.Policy(),changed)

    def test_forged_cached_numeric_value_is_rejected_by_its_commitment(self):
        cache=dict(self.coarse.cache);digest,value=cache['p'];cache['p']=(digest,value+1)
        p=a.compile(self.entry,self.pure,1,'HHHSUT')
        with self.assertRaises(ValueError):a.resolve(self.entry,self.pure,a.Policy(),p,tuple(cache.items()))

    def test_cached_features_cannot_cross_to_another_retained_entry(self):
        other=a.register(('restore','restore'));scope=study.scope(other,'mixed','0')
        p=a.compile(other,scope,1,'HHHSUT')
        with self.assertRaises(ValueError):a.resolve(other,scope,a.Policy(),p,self.coarse.cache)

    def test_copied_session_cannot_change_lower_inheritance(self):
        engine=self.ready.waiting
        lower=replace(engine.lower,live=replace(engine.lower.live,accumulated=m.b.ONE))
        forged=replace(self.ready,waiting=replace(engine,lower=lower))
        with self.assertRaises(ValueError):live.execute(forged)

    def test_public_history_copies_cannot_mutate_the_issued_request(self):
        original=live.history(self.ready);copy=live.history(self.ready)
        copy[0]['scope']['diagonal'][0]=['999','1']
        self.assertEqual(live.history(self.ready),original)

    def test_decision_revisions_survive_in_the_actual_TE_event_history(self):
        before=self.entry.base.engine;done=self.complete.result.second.engine
        self.assertEqual(done.events[:len(before.events)],before.events)
        names=[e.kind for e in done.events[len(before.events):]]
        self.assertTrue(any(x.startswith('rr66-request-revised:') for x in names))
        self.assertTrue(any(x.startswith('rr66-demand-and-current-committed:') for x in names))
        self.assertEqual([len(before.stock),len(self.complete.result.first.engine.stock),len(done.stock)],[6,7,8])

    def test_actual_cells_close_and_the_bundle_normally_stops(self):
        r=self.complete.result
        self.assertEqual((r.first.engine.upper.live.accumulated,r.second.engine.upper.live.accumulated),(m.b.NEG,m.b.NEG))
        self.assertEqual(r.upper_start.live.accumulated,m.b.NEG);self.assertEqual(r.upper_trial.live.accumulated,m.b.ONE)
        self.assertEqual(self.complete.phase,'STOPPED')
        for step in (lambda:live.revise(self.complete,self.pure),lambda:live.choose(self.complete,1,'HHHSUT'),lambda:live.resolve(self.complete),lambda:live.execute(self.complete)):
            with self.assertRaises(ValueError):step()

    def test_partial_resume_reproduces_the_same_next_motion(self):
        raw,h=live.dumps(self.ready)
        restored=live.loads(raw,h,self.entry,self.pure,self.fine,self.ready.choice)
        self.assertEqual(live.execute(restored).digest,self.complete.digest)

    def test_complete_snapshot_replays_originals_and_all_derived_observations(self):
        restored=live.loads(self.raw,self.sha,self.entry,self.pure,self.fine,self.complete.choice)
        self.assertEqual(restored.digest,self.complete.digest)
        self.assertEqual({r.key for r,v in self.entry.base.vault._records()},{'s','t','p'})
        self.assertEqual({r.key for r,v in self.entry.derived._records()},{'sum','port-HHHSUT','port-HHHUST'})

    def test_changed_bytes_or_original_request_or_current_choice_are_rejected(self):
        with self.assertRaises(ValueError):live.loads(self.raw+b' ',self.sha,self.entry,self.pure)
        with self.assertRaises(ValueError):live.loads(self.raw,self.sha,self.entry,self.fine)
        with self.assertRaises(ValueError):live.loads(self.raw,self.sha,self.entry,self.pure,self.pure)
        with self.assertRaises(ValueError):live.loads(self.raw,self.sha,self.entry,self.pure,self.fine,(Q(64),'HHHSUT'))

    def test_changed_resolution_claim_fails_even_with_new_outer_hash(self):
        doc=json.loads(self.raw)
        resolve=next(x for x in doc['commands'] if x['kind']=='resolve');resolve['mode']='INDIVIDUAL'
        changed=json.dumps(doc).encode()
        with self.assertRaises(ValueError):live.loads(changed,hashlib.sha256(changed).hexdigest(),self.entry,self.pure)

    def test_a_post_execution_retarget_is_rejected_during_replay(self):
        doc=json.loads(self.raw)
        doc['commands'].append(dict(kind='revise',scope=live.scope_data(self.main),policy=live.policy_data(a.Policy())))
        changed=json.dumps(doc).encode()
        with self.assertRaises(ValueError):live.loads(changed,hashlib.sha256(changed).hexdigest(),self.entry,self.pure)


if __name__=='__main__':unittest.main()
