import unittest,json,hashlib
from unittest.mock import patch
from dataclasses import replace,asdict
from fractions import Fraction as Q
import incremental_resolution as a
import incremental_session as live
import adaptive_session as reference
import rr67_study as study


class IncrementalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry=a.register();cls.fine=study.scope(cls.entry,'mixed','1/1024');cls.main=study.scope(cls.entry,'main','1/1024')
        cls.ready=live.resolve(live.choose(live.start(cls.entry,cls.fine),1,'HHHSUT'))
        cls.complete=live.execute(cls.ready);cls.raw,cls.h=live.dumps(cls.complete)

    def fresh(self):
        return a.Entry(self.entry.original,self.entry.basis,self.entry.digest)

    def test_scope_changes_do_not_borrow_an_old_plan(self):
        p=a.compile(self.entry,self.fine,1,'HHHSUT')
        with self.assertRaises(ValueError):a.resolve(self.entry,self.main,a.Policy(),p)

    def test_an_unissued_entry_copy_is_rejected(self):
        with self.assertRaises(ValueError):a.compile(self.fresh(),self.fine,1,'HHHSUT')

    def test_no_exact_read_or_old_full_build_during_new_compilation(self):
        changed=replace(self.main,diagonal=(Q(-99,100),Q(199,100),Q(0)))
        with patch.object(self.entry.base.vault,'exact',side_effect=AssertionError('no source query')), \
             patch.object(self.entry.derived,'exact',side_effect=AssertionError('no derived query')), \
             patch.object(a.m,'build',side_effect=AssertionError('no full build')), \
             patch.object(live,'actual_motion',side_effect=AssertionError('no future path')):
            plan=a.compile(self.entry,changed,64,'HHHUST')
        self.assertEqual(plan.status,'AVAILABLE')

    def test_domain_only_reuses_arithmetic_but_rechecks_feasibility(self):
        entry=a.register();wide=study.scope(entry,'main','1/1024');zero=replace(wide,domain=(Q(0),Q(0)))
        a.compile(entry,wide,1,'HHHSUT');p=a.compile(entry,zero,1,'HHHSUT');work=entry._receipts[-1][1]
        self.assertEqual(work.nodes_new,[]);self.assertEqual(len(work.nodes_reused),32)
        self.assertEqual(work.bounds_new,[]);self.assertEqual(p.status,'EMPTY')
        self.assertEqual(a.resolve(entry,wide,a.Policy(),a.compile(entry,wide,1,'HHHSUT'))[0].status,'ADMISSIBLE')

    def test_C_change_preserves_Y_but_recomputes_future_dependent_roots(self):
        entry=a.register();fine=study.scope(entry,'mixed','1/1024');main=study.scope(entry,'main','1/1024')
        a.compile(entry,fine,1,'HHHSUT');a.compile(entry,main,1,'HHHSUT');work=entry._receipts[-1][1]
        self.assertTrue({'Y0','Y1','Y2','h','dy'}<=set(work.nodes_reused))
        self.assertTrue({'SC','UC','TC','N','D','L'}<=set(work.nodes_new));self.assertTrue(work.factors_reused)

    def test_zero_connection_removes_raw_dependency_exactly(self):
        request=study.scope(self.entry,'main','0')
        first,_=a.graph(self.entry,request,1,'HHHSUT',a.Work());work=a.Work()
        second,_=a.graph(self.entry,request,1,'HHHUST',work)
        self.assertEqual({k:x.coefficients for k,x in first.items()},{k:x.coefficients for k,x in second.items()})
        self.assertFalse(work.nodes_new);self.assertFalse(any(x.startswith('raw') for x in work.nodes_reused))

    def test_nonzero_connection_word_change_invalidates_ordered_context(self):
        first=a.compile(self.entry,self.fine,1,'HHHSUT');second=a.compile(self.entry,self.fine,1,'HHHUST')
        self.assertNotEqual(first.polynomials['Y0'].terms,second.polynomials['Y0'].terms)
        x=a.resolve(self.entry,self.fine,a.Policy(),first)[0];y=a.resolve(self.entry,self.fine,a.Policy(),second)[0]
        self.assertNotEqual(x.R,y.R)

    def test_feature_budget_is_separately_bound_from_reusable_algebra(self):
        entry=a.register();request=study.scope(entry,'mixed','1/1024')
        low=a.compile(entry,request,1,'HHHSUT',a.Policy(1));high=a.compile(entry,request,1,'HHHSUT')
        work=entry._receipts[-1][1]
        self.assertEqual(low.status,'UNDETERMINED_NO_SCHEMA');self.assertEqual(high.mode,'PORT_PRODUCT')
        self.assertFalse(work.factors_new);self.assertTrue(work.factors_reused)

    def test_exact_plan_return_is_cache_independent(self):
        entry=a.register();request=study.scope(entry,'mixed','1/1024')
        p=a.compile(entry,request,1,'HHHSUT');entry._plans.clear()
        q=a.compile(entry,request,1,'HHHSUT')
        self.assertEqual(p.digest,q.digest);self.assertFalse(entry._receipts[-1][1].nodes_new)
        self.assertFalse(entry._receipts[-1][1].factors_new)

    def test_factor_identity_is_bound_to_the_complete_observation_definition(self):
        s,t=a.algebra.variable('s'),a.algebra.variable('t');poly=s.scaled(7).add(t.scaled(8))
        first=a.factor(self.entry,'PORT_PRODUCT','z',(Q(7),Q(8)),poly,a.Work(),'test')
        second=a.factor(self.entry,'PORT_PRODUCT','z',(Q(8),Q(7)),poly,a.Work(),'test')
        self.assertIsNotNone(first);self.assertIsNone(second)

    def test_interval_cache_requires_the_current_dependency_intervals(self):
        roots,_=a.graph(self.entry,self.fine,1,'HHHSUT',a.Work());polys={k:a.P(x) for k,x in roots.items()}
        coarse={k:self.entry.base.vault.reference(k).envelope for k in a.m.KEYS}
        a.assessed(self.entry,self.fine,polys,coarse,a.Work())
        exact={r.key:(v,v) for r,v in self.entry.base.vault._records() if r.key in a.m.KEYS};work=a.Work()
        actual=a.assessed(self.entry,self.fine,polys,exact,work)
        self.assertTrue(work.bounds_new)
        self.assertEqual(actual,a.m.status(self.entry.base,self.fine,polys,exact)[0])

    def test_forged_arithmetic_cache_entry_is_rejected(self):
        entry=a.register();request=study.scope(entry,'main','0');a.compile(entry,request,1,'HHHSUT')
        key=next(iter(entry._nodes));entry._nodes[key]=replace(entry._nodes[key],coefficients=())
        with self.assertRaises(ValueError):a.graph(entry,request,1,'HHHSUT',a.Work())

    def test_forged_factor_cache_entry_is_rejected(self):
        entry=a.register();poly=a.C(1);a.factor(entry,'CONSTANT',None,(),poly,a.Work(),'x')
        key=next(iter(entry._factors));entry._factors[key]=replace(entry._factors[key],coefficients=())
        with self.assertRaises(ValueError):a.factor(entry,'CONSTANT',None,(),poly,a.Work(),'x')

    def test_forged_interval_cache_entry_is_rejected(self):
        entry=a.register();request=study.scope(entry,'main','0');polys={'B1':a.C(1)}
        # Populate and reuse all guard bounds on a normal plan.
        a.compile(entry,request,1,'HHHSUT');key=next(iter(entry._bounds))
        entry._bounds[key]=replace(entry._bounds[key],interval=(Q(0),Q(0)))
        roots,_=a.graph(entry,request,1,'HHHSUT',a.Work())
        with self.assertRaises(ValueError):a.assessed(entry,request,{k:a.P(x) for k,x in roots.items()},
            {k:entry.base.vault.reference(k).envelope for k in a.m.KEYS},a.Work())

    def test_forged_plan_copy_cannot_authorize_an_action(self):
        p=self.ready.prepared.plan
        with self.assertRaises(ValueError):a.resolve(self.entry,self.fine,a.Policy(),replace(p))

    def test_original_source_and_derived_archives_remain_complete(self):
        self.assertEqual({r.key for r,v in self.entry.base.vault._records()},{'s','t','p'})
        self.assertEqual({r.key for r,v in self.entry.derived._records()},{'sum','port-HHHSUT','port-HHHUST'})
        self.assertEqual(live.archives(self.entry),reference.archives(self.entry.original))

    def test_changed_request_invalidates_prepared_action_before_motion(self):
        changed=live.resolve(live.choose(live.revise(self.ready,self.main),1,'HHHSUT'))
        with patch.object(live,'actual_motion',side_effect=AssertionError('reject before motion')):
            with self.assertRaises(ValueError):live.execute(changed,self.ready.prepared)

    def test_fresh_entry_can_resume_and_reconstruct_mathematical_proofs(self):
        raw,h=live.dumps(self.ready);fresh=a.register()
        restored=live.loads(raw,h,fresh,study.scope(fresh,'mixed','1/1024'))
        self.assertEqual(live.execute(restored).digest,self.complete.digest)

    def test_complete_record_replays_with_fresh_cache(self):
        fresh=a.register();restored=live.loads(self.raw,self.h,fresh,study.scope(fresh,'mixed','1/1024'))
        self.assertEqual(restored.digest,self.complete.digest)

    def test_changed_new_scope_is_rejected_with_recomputed_outer_hash(self):
        doc=json.loads(self.raw);doc['commands'][0]['scope']['strength']=['0','1']
        raw=json.dumps(doc).encode()
        with self.assertRaises(ValueError):live.loads(raw,hashlib.sha256(raw).hexdigest(),self.entry,self.fine)

    def test_empty_and_unknown_remain_separate_and_keep_originals(self):
        for name,status in (('zero_head','EMPTY'),('outside_chart','UNKNOWN_CHART')):
            request=study.scope(self.entry,name,'0');meter=a.fn.Meter()
            state=live.resolve(live.choose(live.start(self.entry,request),1,'HHHSUT'),meter)
            self.assertEqual(state.prepared.action.status,status);self.assertEqual(meter.exact_reads,0)
            with self.assertRaises(ValueError):live.execute(state)

    def test_current_keeps_both_word_choices_and_completed_bundle_stops(self):
        for word in a.m.WORDS:self.assertEqual(live.choose(live.start(self.entry,self.fine),1,word).choice,(Q(1),word))
        self.assertEqual(self.complete.phase,'STOPPED')
        with self.assertRaises(ValueError):live.revise(self.complete,self.main)


if __name__=='__main__':unittest.main()
