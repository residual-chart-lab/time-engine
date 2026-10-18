import unittest
from dataclasses import replace
from fractions import Fraction as Q
from itertools import product
from unittest.mock import patch

import deferred as d
import experiment as e


class DeferredTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared,cls.firsts,cls.pairs,cls.current,cls.future,cls.queries=e.fixtures()
        cls.local=d.Scope((cls.current,),entry='first')
        cls.later=d.Scope((cls.future,),entry='later')
        cls.oracle={name:d.exact_preview(query,d.Meter()) for name,query in cls.queries}

    def test_free_value_and_published_action_are_distinct_observations(self):
        pair=self.pairs[1]
        self.assertEqual(pair.value,(-1,0,0,0))
        self.assertEqual(pair.original.kernel(self.current),(-9,0,0,0))
        x=d.tensor(pair.original)
        q,s=d.split_tensor(x)
        self.assertEqual(q,pair.value)
        self.assertTrue(any(v for row in s for v in row))
        for k in range(3):self.assertEqual(tuple(d.probe(s,d.eye()[k])),(0,*(-2*s[i][k] for i in range(3))))

    def test_same_compression_does_not_justify_kernel_replacement(self):
        compressed=d.Scope((self.future,),observation='compression',entry='later')
        self.assertEqual(d.assess(self.pairs[1],compressed).status,d.SAFE)
        self.assertEqual(d.assess(self.pairs[1],self.later).status,d.DIFFERENT)

    def test_safe_local_read_keeps_original_coefficients_and_payload(self):
        pair=self.pairs[1];original=pair.original;weights=original.weights
        meter=d.Meter();c=d.assess(pair,self.local)
        self.assertEqual(d.read(pair,self.local,meter,c),original.kernel(self.current))
        self.assertIs(pair.original,original)
        self.assertEqual(pair.original.weights,weights)
        self.assertNotEqual(pair.original.weights,pair.representative.weights)
        self.assertEqual(meter.exact_retained_responses,0)
        self.assertEqual(meter.exact_tensor_expansions,0)

    def test_broader_scope_requires_a_new_certificate(self):
        pair=self.pairs[1];c=d.assess(pair,self.local)
        enlarged=d.Scope((self.current,self.future),entry='two flowers')
        with self.assertRaises(ValueError):d.verify_certificate(pair,enlarged,c)
        self.assertEqual(d.assess(pair,enlarged,budget=1).status,d.UNKNOWN)
        self.assertEqual(d.assess(pair,enlarged,budget=2).status,d.DIFFERENT)
        self.assertEqual(c.status,d.SAFE)

    def test_entry_and_observation_are_bound_even_at_the_same_frame(self):
        pair=self.pairs[1];c=d.assess(pair,self.local)
        for scope in (replace(self.local,entry='other entry'),replace(self.local,observation='boundary_tensor')):
            with self.assertRaises(ValueError):d.verify_certificate(pair,scope,c)
        self.assertEqual(d.assess(pair,replace(self.local,observation='boundary_tensor')).status,d.DIFFERENT)

    def test_a_forged_safe_certificate_is_rejected(self):
        pair=self.pairs[1];c=d.assess(pair,self.later)
        with self.assertRaises(ValueError):d.verify_certificate(pair,self.later,replace(c,status=d.SAFE))
        with self.assertRaises(ValueError):d.verify_certificate(pair,self.later,replace(c,factors=((Q(0),)*4,)))

    def test_a_certificate_cannot_be_reused_for_another_origin_or_pair(self):
        pair=self.pairs[1];c=d.assess(pair,self.local)
        for changed in (self.pairs[2],replace(pair,origin='another retained occurrence')):
            with self.assertRaises(ValueError):d.verify_certificate(changed,self.local,c)

    def test_undetermined_is_not_permission_to_read_a_representative(self):
        pair=self.pairs[1];c=d.assess(pair,self.local,budget=0)
        self.assertEqual(c.status,d.UNKNOWN)
        with self.assertRaises(ValueError):d.read(pair,self.local,d.Meter(),c)
        self.assertNotEqual(pair.original.weights,pair.representative.weights)

    def test_later_read_reexpands_original_difference(self):
        pair=self.pairs[1];meter=d.Meter()
        original=d.read(pair,self.later,meter)
        self.assertEqual(original,pair.original.kernel(self.future))
        self.assertNotEqual(original,pair.representative.kernel(self.future))
        self.assertEqual(meter.exact_retained_responses,1)
        residual=pair.residual_tensor(meter)
        self.assertEqual(tuple(d.qstate(residual)),(0,0,0,0))
        self.assertTrue(any(x for row in residual for x in row))

    def test_deferred_tail_preserves_noncommutative_order(self):
        y=[list(r) for r in self.future]
        y[0][1]+=1;y[1][0]+=1;y[1][2]+=1;y[2][1]+=1
        scope=d.Scope((y,),entry='noncommuting later read')
        pair=self.pairs[1];word=d.DeferredWord(pair)
        head=self.prepared.receiver.anchor.original.designated_head
        for leaf in head.leaves():word=word.append(leaf)
        original=pair.original.kernel(scope.contexts[0]);h=head.kernel(scope.contexts[0])
        self.assertEqual(word.read(scope,d.Meter()),tuple(d.qmul(h,original)))
        self.assertNotEqual(tuple(d.qmul(h,original)),tuple(d.qmul(original,h)))
        self.assertIs(word.pair,pair)
        self.assertEqual(d.DeferredWord(pair).tail,())

    def test_large_difference_can_stay_invisible_in_a_declared_scope(self):
        reference=self.pairs[0].representative;direction=self.pairs[0].direction
        shift=Q(10**50)
        leaf=d.AffineLetter(tuple(w+shift*v for w,v in zip(reference.weights,direction)),reference.library)
        pair=d.RetainedPair(leaf,reference,shift,direction,'large primitive control')
        meter=d.Meter()
        self.assertEqual(d.assess(pair,self.local).status,d.SAFE)
        self.assertEqual(d.read(pair,self.local,meter),reference.kernel(self.current))
        self.assertEqual(meter.exact_retained_responses,0)

    def test_tiny_difference_is_not_discarded_by_a_size_threshold(self):
        reference=self.pairs[0].representative;direction=self.pairs[0].direction;shift=Q(1,10**20)
        leaf=d.AffineLetter(tuple(w+shift*v for w,v in zip(reference.weights,direction)),reference.library)
        pair=d.RetainedPair(leaf,reference,shift,direction,'tiny primitive control')
        y=d.embedded.port.single.context(((Q(10**20),0,0),(0,Q(1-10**20),0),(0,0,0)))
        scope=d.Scope((y,),entry='large but regular primitive frame')
        self.assertEqual(d.assess(pair,scope).status,d.DIFFERENT)
        self.assertGreater(sum(abs(x-y) for x,y in zip(leaf.kernel(scope.contexts[0]),reference.kernel(scope.contexts[0]))),1)

    def test_integer_bounds_enclose_negative_and_positive_rational_arithmetic(self):
        values=(Q(-3,5),Q(-1,10**20),Q(0),Q(1,3),Q(8,3),Q(10**20))
        for bits,a,b in product((8,24),values,values):
            meter=d.Meter();x=d.Grid.enclose(a,bits);y=d.Grid.enclose(b,bits)
            self.assertTrue(x.contains(a))
            self.assertTrue(x.add(y,meter).contains(a+b))
            self.assertTrue(x.mul(y,meter).contains(a*b))

    def test_noncommuting_quaternion_products_have_outward_bounds(self):
        a=(Q(1,3),Q(-2,7),Q(1,10**20),Q(5))
        b=(Q(-3,11),Q(7),Q(2,5),Q(-1))
        actual=d.qmul(a,b)
        for bits in (8,24,80):
            result=d.grid_qmul(tuple(d.Grid.enclose(x,bits) for x in a),
                              tuple(d.Grid.enclose(x,bits) for x in b),d.Meter())
            self.assertTrue(all(x.contains(y) for x,y in zip(result,actual)))

    def test_all_twenty_two_query_error_traces_are_enclosed(self):
        for name,query in self.queries:
            expected,errors,_=self.oracle[name]
            for bits in (24,48,80):
                c=d.preview(query,bits,d.Meter())
                self.assertTrue(all(lo<=e<=hi for e,(lo,hi) in zip(errors,c.error_bounds)),name)
                if c.verdict is not None:self.assertEqual(c.verdict,expected,name)

    def test_adaptive_filter_agrees_and_uses_different_precisions(self):
        meter=d.Meter();bits=set()
        for name,query in self.queries:
            c=d.adaptive_preview(query,meter)
            self.assertEqual(c.verdict,self.oracle[name][0],name)
            bits.add(c.bits)
        self.assertGreaterEqual(len(bits),2)
        self.assertEqual(meter.exact_retained_responses,0)

    def test_low_precision_ambiguity_stays_unresolved(self):
        query=next(q for name,q in self.queries if name=='keep-primary@primary')
        c=d.adaptive_preview(query,d.Meter(),precisions=(8,))
        self.assertIsNone(c.verdict)
        self.assertIsNotNone(d.adaptive_preview(query,d.Meter()).verdict)

    def test_strict_terminal_threshold_cannot_be_accepted_by_rounding(self):
        from recursive_upper_decoder import action_matrix
        from internal_port_certificate import solve
        library=self.pairs[0].original.library;epsilon=Q(1,1024)
        wanted=(Q(-1)+epsilon/2,Q(0),Q(0),Q(0))
        weights=solve(action_matrix(self.current,library),(Q(1),*wanted))
        leaf=d.AffineLetter(tuple(weights),library)
        query=d.WordQuery(((leaf,),),self.current,(Q(1),0,0,0),(-1,0,0,0),epsilon,'terminal threshold control')
        self.assertFalse(d.exact_preview(query,d.Meter())[0])
        for bits in (8,24,80):self.assertIsNot(d.preview(query,bits,d.Meter()).verdict,True)

    def test_query_certificate_binds_frame_inheritance_policy_and_grouped_prefixes(self):
        query=self.queries[0][1];c=d.adaptive_preview(query,d.Meter())
        variants=(replace(query,context=self.future),replace(query,inherited=(Q(2),0,0,0)),
            replace(query,tolerance=query.tolerance*2),replace(query,origin='other original'),
            replace(query,groups=(tuple(a for g in query.groups for a in g),)))
        for other in variants:
            with self.assertRaises(ValueError):d.verify_preview(other,c,d.Meter())
        from recursive_upper_decoder import promote_word
        with self.assertRaises(ValueError):promote_word(c)

    def test_interval_proof_tampering_is_rejected(self):
        query=self.queries[0][1];c=d.adaptive_preview(query,d.Meter())
        with self.assertRaises(ValueError):d.verify_preview(query,replace(c,verdict=not c.verdict),d.Meter())
        with self.assertRaises(ValueError):d.verify_preview(query,replace(c,error_bounds=((Q(0),Q(0)),)),d.Meter())

    def test_mutable_input_containers_are_frozen_and_bad_precision_is_rejected(self):
        query=self.queries[0][1];groups=[list(g) for g in query.groups]
        copy=replace(query,groups=groups);groups[0].clear()
        self.assertEqual(copy.groups,query.groups)
        for precision in ((),(0,),(1.5,),(True,)):
            with self.assertRaises(ValueError):d.adaptive_preview(query,d.Meter(),precision)

    def test_authenticated_inputs_need_no_upstream_regeneration_or_macro_search(self):
        e.actuals.cache_clear()
        with patch('outbound.execute_contact',side_effect=AssertionError('no SGD regeneration')), \
             patch('outbound.source_course',side_effect=AssertionError('no training course')), \
             patch('three_flower.finite_family',side_effect=AssertionError('no 128-family enumeration')), \
             patch('three_flower_constraint.source_witness',side_effect=AssertionError('no source roots')):
            self.assertEqual(len(e.actuals()),3)


if __name__=='__main__':unittest.main()
