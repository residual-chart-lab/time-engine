import unittest
from dataclasses import replace
from fractions import Fraction as Q
from unittest.mock import patch
import demand_filter as f
import retained_execution as plant
from demand_filter import prior,te,d

class DemandFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive=f.Archive();cls.hist=prior.previous.begin('keep');cls.erase=prior.previous.begin('erase')
        cls.entry=cls.archive.register(cls.hist);cls.erased=cls.archive.register(cls.erase)
        cls.c=prior.Requirement(prior.diagonal(-1))
        cls.scope=f.Scope(cls.entry.digest,cls.c);cls.demand=f.assess(cls.archive,cls.entry,cls.scope)
        cls.res=f.resolve(cls.archive,cls.entry,cls.scope,cls.demand,f.Meter())
        cls.actual=plant.execute(cls.archive,cls.entry,cls.scope,cls.demand,cls.res,'HHST')

    def test_archive_requires_a_true_exact_envelope_and_binds_its_reference(self):
        with self.assertRaises(ValueError):self.archive.register(self.hist,(0,0))
        with self.assertRaises(ValueError):self.archive.verify(replace(self.entry,envelope=(-64,64)))
        self.assertEqual(self.archive.history(self.entry),self.hist)

    def test_assessment_uses_no_retained_value_response_or_future_paths(self):
        original=d.AffineLetter.kernel
        def guard(leaf,y):
            if leaf==self.hist.pair.original:raise AssertionError('no retained response')
            return original(leaf,y)
        with patch.object(self.archive,'read_shift',side_effect=AssertionError('no exact shift')), \
             patch.object(self.archive,'history',side_effect=AssertionError('no archive expansion')), \
             patch.object(d.AffineLetter,'kernel',guard), \
             patch.object(te,'construct_requirement',side_effect=AssertionError('no C fixture')), \
             patch.object(te,'finite_family',side_effect=AssertionError('no completed path enumeration')):
            self.assertTrue(f.assess(self.archive,self.entry,self.scope).needs_exact_shift)

    def test_same_C_skips_existence_but_requests_exact_information_for_action(self):
        scope=replace(self.scope,observation=f.EXISTS)
        proof=f.assess(self.archive,self.entry,scope);meter=f.Meter()
        with patch.object(self.archive,'read_shift',side_effect=AssertionError('must omit')):
            result=f.resolve(self.archive,self.entry,scope,proof,meter)
        self.assertTrue(result.feasible);self.assertIsNone(result.control)
        self.assertEqual(meter.exact_shift_reads,0);self.assertTrue(self.demand.needs_exact_shift)

    def test_refinement_reads_shift_but_never_expands_retained_future_response(self):
        meter=f.Meter();original=d.AffineLetter.kernel
        def guard(leaf,y):
            if leaf==self.hist.pair.original:raise AssertionError('factorization avoids retained leaf response')
            return original(leaf,y)
        with patch.object(d.AffineLetter,'kernel',guard):result=f.resolve(self.archive,self.entry,self.scope,self.demand,meter)
        self.assertEqual(meter.exact_shift_reads,1);self.assertEqual(result,self.res)

    def test_strict_control_difference_has_exact_necessary_information_formula(self):
        scope=f.Scope(self.erased.digest,self.c);proof=f.assess(self.archive,self.erased,scope)
        erase=f.resolve(self.archive,self.erased,scope,proof,f.Meter())
        h,a,g=self.demand.h,self.demand.a,self.demand.g;s=self.hist.pair.shift
        self.assertEqual(self.res.control-erase.control,s/(h*h*a*(a+s*g)))
        self.assertGreater(self.res.control,erase.control)

    def test_domain_exclusion_is_scoped_and_needs_no_inspection(self):
        scope=replace(self.scope,domain=(0,1));proof=f.assess(self.archive,self.entry,scope)
        self.assertEqual(proof.status,'EMPTY_DOMAIN_FOR_ENVELOPE')
        meter=f.Meter();result=f.resolve(self.archive,self.entry,scope,proof,meter)
        self.assertFalse(result.feasible);self.assertEqual(meter.exact_shift_reads,0)

    def test_boundary_straddling_stays_unresolved_until_refined(self):
        lo,hi=self.demand.control_interval
        scope=replace(self.scope,domain=((lo+hi)/2,hi),observation=f.EXISTS)
        proof=f.assess(self.archive,self.entry,scope)
        self.assertEqual(proof.status,'EXISTENCE_NEEDS_REFINEMENT')
        self.assertIsNone(proof.verdict)
        meter=f.Meter();r=f.resolve(self.archive,self.entry,scope,proof,meter)
        self.assertEqual((r.feasible,r.control),f.exact_oracle(self.archive,self.entry,scope))
        self.assertEqual(meter.exact_shift_reads,1)

    def test_pole_in_a_wide_envelope_never_gets_silent_omission_permission(self):
        archive=f.Archive();entry=archive.register(self.hist,(-64,64));scope=f.Scope(entry.digest,self.c)
        proof=f.assess(archive,entry,scope)
        self.assertEqual(proof.status,'ENVELOPE_CROSSES_ZERO_SOURCE');self.assertIsNone(proof.verdict)
        r=f.resolve(archive,entry,scope,proof,f.Meter())
        self.assertEqual((r.feasible,r.control),f.exact_oracle(archive,entry,scope))

    def test_zero_head_and_zero_difference_channel_return_empty_without_read(self):
        for x,status in ((Q(1,2),'EMPTY_ZERO_HEAD'),(Q(1,3),'EMPTY_BLIND')):
            scope=replace(self.scope,requirement=prior.Requirement(prior.diagonal(x)))
            proof=f.assess(self.archive,self.entry,scope);self.assertEqual(proof.status,status)
            with patch.object(self.archive,'read_shift',side_effect=AssertionError('no need')):
                self.assertFalse(f.resolve(self.archive,self.entry,scope,proof,f.Meter()).feasible)

    def test_chart_failure_stays_unknown_and_cannot_execute(self):
        scope=replace(self.scope,requirement=prior.Requirement(prior.diagonal(0)))
        proof=f.assess(self.archive,self.entry,scope);result=f.resolve(self.archive,self.entry,scope,proof,f.Meter())
        self.assertEqual(proof.status,'OUTSIDE_CERTIFIED_CHART');self.assertIsNone(result.feasible)
        with self.assertRaises(ValueError):plant.execute(self.archive,self.entry,scope,proof,result,'HHST')

    def test_scope_or_demand_substitution_is_rejected(self):
        for scope in (replace(self.scope,domain=(0,4)),replace(self.scope,observation=f.EXISTS),
                      replace(self.scope,entry_digest=self.erased.digest),
                      replace(self.scope,requirement=prior.Requirement(prior.diagonal(Q(1,4))))):
            with self.assertRaises(ValueError):f.verify_demand(self.archive,self.entry,scope,self.demand)
        with self.assertRaises(ValueError):f.verify_demand(self.archive,self.entry,self.scope,replace(self.demand,needs_exact_shift=False))

    def test_feasibility_proof_cannot_authorize_an_actual_source(self):
        scope=replace(self.scope,observation=f.EXISTS);proof=f.assess(self.archive,self.entry,scope)
        result=f.resolve(self.archive,self.entry,scope,proof,f.Meter())
        with self.assertRaises(ValueError):plant.execute(self.archive,self.entry,scope,proof,result,'HHST')

    def test_resolution_or_occurrence_substitution_is_rejected(self):
        with self.assertRaises(ValueError):plant.execute(self.archive,self.entry,self.scope,self.demand,
            replace(self.res,control=self.res.control+1),'HHST')
        for record in (replace(self.actual,scope_digest='bad'),replace(self.actual,word='HHTS'),
                replace(self.actual,closed_engine=replace(self.actual.closed_engine,result=prior.ONE))):
            with self.assertRaises(ValueError):plant.future(self.archive,self.entry,self.scope,self.demand,record)

    def test_current_uses_actual_published_retained_source_and_produces_new_one(self):
        r=self.actual;e=r.closed_engine;before=self.hist.first.closed_engine
        self.assertEqual(r.retained_source,self.hist.first.residue.source)
        self.assertIn(r.retained_source,r.terminal.cell.beta)
        self.assertEqual(e.stock,before.stock+(r.new_source,));self.assertEqual(e.rounds[:-1],before.rounds)
        self.assertEqual(e.events[:len(before.events)],before.events)
        self.assertEqual(r.new_source.cell.start,before.lower)
        kinds=[x.kind for x in e.events[len(before.events):]]
        self.assertLess(kinds.index('lower-cell-closed'),kinds.index('same-level-operation-published'))
        self.assertLess(kinds.index('same-level-operation-published'),kinds.index('rr62-current-action-executed'))

    def test_same_C_leaves_two_different_actual_word_choices(self):
        for word in f.WORDS:
            r=plant.execute(self.archive,self.entry,self.scope,self.demand,self.res,word)
            trial,decoded,ok=plant.future(self.archive,self.entry,self.scope,self.demand,r)
            self.assertTrue(ok);self.assertEqual(trial.live.accumulated,prior.ONE)
            self.assertEqual((r.new_source.level,r.terminal.level,decoded.outputs[0].level),(2,3,4))

    def test_undeclared_words_are_not_silently_promoted(self):
        for word in ('HS','HSH T','HHSS','HTHS','HHSTST'):
            with self.assertRaises(ValueError):plant.execute(self.archive,self.entry,self.scope,self.demand,self.res,word)

    def test_retention_changes_actual_new_source_even_when_current_observation_agrees(self):
        scope=f.Scope(self.erased.digest,self.c);proof=f.assess(self.archive,self.erased,scope)
        res=f.resolve(self.archive,self.erased,scope,proof,f.Meter());r=plant.execute(self.archive,self.erased,scope,proof,res,'HHST')
        self.assertNotEqual(r.new_source.leaves()[0].weights,self.actual.new_source.leaves()[0].weights)
        self.assertNotEqual(r.new_source.kernel(self.c.context),self.actual.new_source.kernel(self.c.context))
        y=self.hist.first.residue.internal_context
        self.assertEqual(r.new_source.kernel(y),self.actual.new_source.kernel(y))

    def test_erased_actuator_closes_current_but_fails_the_same_future(self):
        scope=f.Scope(self.erased.digest,self.c);proof=f.assess(self.archive,self.erased,scope)
        res=f.resolve(self.archive,self.erased,scope,proof,f.Meter())
        r=plant.execute(self.archive,self.entry,self.scope,self.demand,self.res,'HHST',res.control)
        trial,_,ok=plant.future(self.archive,self.entry,self.scope,self.demand,r,res.control)
        self.assertFalse(ok);self.assertEqual(r.closed_engine.upper.live.accumulated,prior.NEG)
        self.assertEqual(trial.live.accumulated[0]-1,self.hist.pair.shift*self.demand.g/self.demand.a)

    def test_same_current_and_future_results_still_have_different_ordered_ports(self):
        alt=plant.execute(self.archive,self.entry,self.scope,self.demand,self.res,'HHTS')
        a=te.pair.ordered_terminal_readout(self.actual.terminal);b=te.pair.ordered_terminal_readout(alt.terminal)
        old=d.tensor(self.actual.retained_source.leaves()[0]);new=d.tensor(self.actual.new_source.leaves()[0])
        self.assertNotEqual(a,b)
        self.assertTrue(all(a[i][j]-b[i][j]==(new[i][j]-old[i][j])/21 for i in range(3) for j in range(3)))

    def test_omission_preserves_the_full_original_and_later_scope_can_inspect_it(self):
        before=self.archive.history(self.entry)
        scope=replace(self.scope,observation=f.EXISTS);proof=f.assess(self.archive,self.entry,scope)
        f.resolve(self.archive,self.entry,scope,proof,f.Meter())
        self.assertEqual(before,self.archive.history(self.entry))
        result=f.resolve(self.archive,self.entry,self.scope,self.demand,f.Meter())
        self.assertTrue(result.exact_shift_used);self.assertTrue(prior.previous.verify_flight(before))

if __name__=='__main__':unittest.main()
