import unittest,hashlib,json
from unittest.mock import patch
from dataclasses import replace
from fractions import Fraction as Q
import mixed_action_sets as m
import mixed_execution as plant
import rr65_study as study
from mixed_action_sets import b,fn


class MixedActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry=m.register()
        cls.pure=m.Scope(cls.entry.digest,m.context(cls.entry,'mixed'),Q(0))
        cls.active=replace(cls.pure,strength=Q(1,1024))
        cls.main=replace(cls.active,diagonal=m.context(cls.entry,'main'))
        cls.full=m.action(cls.entry,cls.active,1,'HHHSUT')
        cls.joint=m.joint_action(cls.entry,cls.pure,1,'HHHSUT')
        cls.actual=plant.run(cls.entry,cls.active,cls.full)
        cls.joint_actual=plant.run(cls.entry,cls.pure,cls.joint)
        cls.erased=m.register(modes=('keep','erase'))

    def test_each_retained_coordinate_has_a_distinct_authenticated_origin(self):
        e=self.entry
        self.assertNotEqual(e.vault.reference('s').origin,e.vault.reference('t').origin)
        self.assertEqual(len(e.engine.stock),6)
        self.assertIn(e.U_operation,e.engine.stock)
        self.assertEqual(e.U_operation.leaves()[0],e.second.pair.original)
        self.assertEqual(e.engine.events[:len(e.first.flight.first.closed_engine.events)],e.first.flight.first.closed_engine.events)

    def test_copied_entry_digest_cannot_authorize_changed_lower_inheritance(self):
        e=self.entry
        lower=replace(e.engine.lower,live=replace(e.engine.lower.live,accumulated=b.ONE))
        forged=replace(e,engine=replace(e.engine,lower=lower))
        self.assertEqual(forged.digest,e.digest)
        with self.assertRaises(ValueError):m.compare(forged,self.active,('t',))
        with self.assertRaises(ValueError):plant.run(forged,self.active,self.full)

    def test_mixed_output_has_no_constant_or_individual_linear_term(self):
        p=m.build(self.entry,self.pure,1,'HHHSUT').polynomials['B1']
        self.assertEqual(set(p.terms),{('s','t')})
        self.assertTrue(any(p.terms['s','t']))

    def test_an_individual_jacobian_would_erase_the_whole_mixed_channel(self):
        p=m.build(self.entry,self.pure,1,'HHHSUT').polynomials['B1']
        linear={k:v for k,v in p.terms.items() if len(k)<=1}
        self.assertEqual(linear,{})
        values={k:self.entry.vault.exact(k,fn.Meter()) for k in ('s','t')}
        self.assertNotEqual(p.exact(values),(Q(0),)*4)

    def test_either_single_erasure_changes_the_nonempty_action_set(self):
        for omitted in (('s',),('t',),('s','t')):
            result=m.compare(self.entry,self.active,omitted)
            self.assertEqual(result.verdict,'DIFFERENT')
            self.assertTrue(any(x[2]=='DIFFERENT_EXISTENCE' for x in result.rows))
            self.assertEqual(result.reads[2],0)

    def test_matrix_oracle_matches_every_physical_action_in_the_fixed_grid(self):
        for scope in (self.pure,self.active,self.main):
            for v in scope.controls:
                for word in scope.words:
                    a=m.action(self.entry,scope,v,word)
                    expected=study.oracle(self.entry,scope,v,word)
                    self.assertEqual((a.status,a.T,a.R),expected)

    def test_comparison_uses_bounds_without_exact_values_or_completed_futures(self):
        with patch.object(self.entry.vault,'exact',side_effect=AssertionError('comparison must stay bounded')), \
             patch.object(plant,'run',side_effect=AssertionError('no future path')):
            result=m.compare(self.entry,self.active,('t',))
        self.assertEqual(result.verdict,'DIFFERENT');self.assertGreater(result.reads[1],0)

    def test_finite_budget_exhaustion_is_unknown_and_not_omission_permission(self):
        certificate=m.compare(self.entry,self.active,('t',),precisions=())
        self.assertEqual(certificate.verdict,'UNDETERMINED')
        with self.assertRaises(ValueError):m.action(self.entry,self.active,1,'HHHSUT',certificate)

    def test_zero_future_head_gives_equal_empty_sets_without_exact_reads(self):
        scope=replace(self.active,diagonal=m.context(self.entry,'zero_head'))
        c=m.compare(self.entry,scope,('s','t'))
        self.assertEqual(c.verdict,'SAME');self.assertEqual(c.reads[1:],(0,0))
        self.assertEqual(m.action(self.entry,scope,1,'HHHSUT',c).status,'EMPTY')

    def test_equal_empty_sets_do_not_require_symbolic_independence(self):
        scope=replace(self.active,entry_digest=self.erased.digest,diagonal=m.context(self.erased,'mixed'))
        c=m.compare(self.erased,scope,('s',))
        self.assertEqual(c.verdict,'SAME')
        self.assertTrue(any(not row[-1] for row in c.rows))

    def test_an_actually_zero_coordinate_can_be_omitted_in_a_nonempty_scope(self):
        scope=replace(self.main,entry_digest=self.erased.digest)
        c=m.compare(self.erased,scope,('t',))
        self.assertEqual(c.verdict,'SAME')
        full=m.action(self.erased,scope,1,'HHHSUT');meter=fn.Meter()
        omitted=m.action(self.erased,scope,1,'HHHSUT',c,meter)
        self.assertEqual((full.T,full.R),(omitted.T,omitted.R))
        self.assertEqual(omitted.read_keys,('s',));self.assertEqual(meter.exact_reads,1)

    def test_unknown_chart_does_not_become_equivalence(self):
        scope=replace(self.active,diagonal=m.context(self.entry,'outside_chart'))
        c=m.compare(self.entry,scope,('t',))
        self.assertEqual(c.verdict,'UNDETERMINED')
        with self.assertRaises(ValueError):m.action(self.entry,scope,1,'HHHSUT',c)

    def test_omission_certificate_is_bound_to_requirement_observation_and_entry(self):
        scope=replace(self.active,diagonal=m.context(self.entry,'zero_head'))
        c=m.compare(self.entry,scope,('t',))
        for changed in (replace(scope,domain=(Q(0),Q(8))),replace(scope,strength=0),self.main):
            with self.assertRaises(ValueError):m.action(self.entry,changed,1,'HHHSUT',c)
        # A wider omission in a blind empty scope would itself be valid. Use
        # a nonempty scope where only the actually-zero t can be omitted.
        nonempty=replace(self.main,entry_digest=self.erased.digest)
        safe=m.compare(self.erased,nonempty,('t',))
        with self.assertRaises(ValueError):m.action(self.erased,nonempty,1,'HHHSUT',replace(safe,omitted=('s','t')))

    def test_joint_observation_preserves_all_nonempty_physical_action_coefficients(self):
        for v in self.pure.controls:
            for word in self.pure.words:
                full=m.action(self.entry,self.pure,v,word)
                joint=m.joint_action(self.entry,self.pure,v,word)
                self.assertEqual((full.status,full.T,full.R),(joint.status,joint.T,joint.R))

    def test_joint_action_reads_no_individual_exact_coordinate(self):
        exact=self.entry.vault.exact;read=[]
        def guarded(key,meter):
            read.append(key)
            if key!='p':raise AssertionError('individual information was proved unnecessary')
            return exact(key,meter)
        with patch.object(self.entry.vault,'exact',side_effect=guarded):
            action=m.joint_action(self.entry,self.pure,1,'HHHSUT')
        self.assertEqual(read,['p']);self.assertEqual(action.R,self.joint.R)

    def test_new_scope_can_require_the_individual_information_again(self):
        self.assertIsNone(m.joint_polynomials(m.build(self.entry,self.active,1,'HHHSUT')))
        with self.assertRaises(ValueError):m.joint_action(self.entry,self.active,1,'HHHSUT')
        self.assertEqual(self.full.read_keys,('s','t'))

    def test_joint_planning_does_not_delete_or_rebind_originals(self):
        before=self.entry.vault._records()
        m.joint_action(self.entry,self.pure,1,'HHHSUT')
        self.assertEqual(before,self.entry.vault._records())
        values={r.key:v for r,v in before}
        self.assertEqual(set(values),{'s','t','p'});self.assertEqual(values['p'],values['s']*values['t'])

    def test_same_alpha_does_not_authorize_different_physical_R(self):
        forged=replace(self.full,R=(self.full.R[0]+1,self.full.R[1]-1,*self.full.R[2:]))
        with patch.object(plant.plant,'produce',side_effect=AssertionError('reject before actuation')):
            with self.assertRaises(ValueError):plant.run(self.entry,self.active,forged)

    def test_an_empty_action_cannot_be_relabeled_to_actuate(self):
        empty=m.action(self.entry,self.active,0,'HHHSUT')
        self.assertEqual(empty.status,'EMPTY')
        with patch.object(plant.plant,'produce',side_effect=AssertionError('reject before actuation')):
            with self.assertRaises(ValueError):plant.run(self.entry,self.active,replace(empty,status='ADMISSIBLE'))

    def test_fixed_target_and_inheritance_cannot_be_replaced(self):
        for kw in (dict(target=b.NEG),dict(inherited=b.ONE),dict(observation='alpha-only')):
            with self.assertRaises(ValueError):replace(self.active,**kw)

    def test_two_local_closures_and_upper_first_boundary_are_actual(self):
        for actual in (self.actual,self.joint_actual):
            self.assertEqual(actual.first.engine.upper.live.accumulated,b.NEG)
            self.assertEqual(actual.second.engine.upper.live.accumulated,b.NEG)
            self.assertEqual(actual.upper_start.live.accumulated,b.NEG)
            self.assertEqual(actual.upper_trial.live.accumulated,b.ONE)
            self.assertEqual(len(actual.upper_decoded.outputs[0].cell.beta),2)
            self.assertEqual([len(self.entry.engine.stock),len(actual.first.engine.stock),len(actual.second.engine.stock)],[6,7,8])

    def test_both_current_words_remain_and_retain_distinct_real_ports(self):
        a=m.action(self.entry,self.active,1,'HHHUST');other=plant.run(self.entry,self.active,a)
        self.assertTrue(other.certified)
        self.assertEqual(other.first.new_source.leaves()[0].weights,self.actual.first.new_source.leaves()[0].weights)
        self.assertNotEqual(other.port[1],self.actual.port[1])

    def test_wrong_omitted_correction_fails_only_at_bundle_and_cannot_be_saved(self):
        erased_scope=replace(self.main,entry_digest=self.erased.digest)
        wrong=m.action(self.erased,erased_scope,1,'HHHSUT')
        full=m.action(self.entry,self.main,1,'HHHSUT')
        actual=plant.run(self.entry,self.main,full,counterfactual_alpha=wrong.alpha)
        self.assertFalse(actual.certified)
        self.assertEqual(actual.first.engine.upper.live.accumulated,b.NEG)
        self.assertEqual(actual.second.engine.upper.live.accumulated,b.NEG)
        with self.assertRaises(ValueError):plant.dumps(self.entry,self.main,actual)

    def test_saved_joint_motion_replays_all_original_coordinates(self):
        raw,h=plant.dumps(self.entry,self.pure,self.joint_actual)
        self.assertEqual(plant.loads(raw,h,self.entry,self.pure,1,'HHHSUT'),self.joint_actual)
        before=json.loads(raw)
        self.assertTrue(before['joint'])
        with self.assertRaises(ValueError):plant.loads(raw+b' ',h,self.entry,self.pure,1,'HHHSUT')
        with self.assertRaises(ValueError):plant.loads(raw,h,self.entry,replace(self.pure,strength=Q(1,1024)),1,'HHHSUT')
        with self.assertRaises(ValueError):plant.loads(raw,h,self.entry,self.pure,64,'HHHSUT')
        with self.assertRaises(ValueError):plant.loads(raw,h,self.entry,self.pure,1,'HHHUST')

    def test_changed_actual_graph_is_rejected_even_with_new_outer_hash(self):
        raw,h=plant.dumps(self.entry,self.pure,self.joint_actual);value=json.loads(raw)
        def change(x):
            if isinstance(x,dict):
                if set(x)=={'q'} and x['q'][0]=='-1':x['q'][0]='0';return True
                return any(change(v) for v in x.values())
            if isinstance(x,list):return any(change(v) for v in x)
            return False
        self.assertTrue(change(value['graph']))
        changed=json.dumps(value).encode()
        with self.assertRaises(ValueError):plant.loads(changed,hashlib.sha256(changed).hexdigest(),self.entry,self.pure,1,'HHHSUT')

    def test_changed_number_archive_is_rejected_even_with_consistent_outer_hash(self):
        raw,h=plant.dumps(self.entry,self.pure,self.joint_actual);value=json.loads(raw)
        r=m.build(self.erased,replace(self.pure,entry_digest=self.erased.digest),1,'HHHSUT')
        from free_numbers.checkpoint import dumps
        numbers,digest=dumps(r.roots,self.erased.vault)
        value['numbers']=numbers.hex();value['number_sha256']=digest
        changed=json.dumps(value).encode()
        with self.assertRaises(ValueError):plant.loads(changed,hashlib.sha256(changed).hexdigest(),self.entry,self.pure,1,'HHHSUT')

    def test_invalid_offdiagonal_fixture_cannot_be_used_as_a_blind_residual(self):
        with self.assertRaisesRegex(ValueError,'source must close'):m.register('offdiagonal')


if __name__=='__main__':unittest.main()
