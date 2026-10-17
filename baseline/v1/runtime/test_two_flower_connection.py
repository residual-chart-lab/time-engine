import copy
import unittest
from dataclasses import replace
from unittest.mock import patch

from two_flower_connection import *


class TwoFlowerConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=load_published('first',0)
        cls.record=connect_two(cls.first)
        cls.long=connect_two(cls.first,ConnectionSpec(petal_choice=1))

    def test_two_actual_consumer_closures_are_certified_and_keep_both_outputs(self):
        r=self.record
        self.assertTrue(verify_connection(r,self.first,ConnectionSpec()))
        self.assertEqual(len(r.second.closed_engine.rounds),2)
        self.assertEqual(len(r.second.closed_engine.outputs),2)
        self.assertEqual(r.second.closed_engine.outputs[0],r.first.residue.terminal_operation)
        self.assertEqual(promote_word(r.second.residue.terminal_operation.cell),r.second.residue.terminal_operation)

    def test_second_inherits_both_actual_tapes_accumulators_and_stock_without_reset(self):
        a=self.first.closed_engine;b=self.record.second.commitment.anchor.original
        self.assertEqual(a,b)
        self.assertNotEqual(a.upper.live.accumulated,a.result)
        start=self.record.second.commitment.problem.start
        self.assertEqual(start.live.accumulated,a.upper.live.accumulated)
        self.assertEqual(start.executed_word,a.upper.executed_word)
        producer=self.record.second.commitment.anchor.producer_plan
        self.assertEqual(producer.lower.live.accumulated,a.lower.live.accumulated)
        self.assertEqual(producer.lower.executed_word,a.lower.executed_word)
        self.assertEqual(producer.stock,a.stock)

    def test_higher_outputs_do_not_enter_lower_stock(self):
        r=self.record
        self.assertTrue(all(op.level==2 for op in r.second.closed_engine.stock))
        self.assertTrue(all(op.level==3 for op in r.second.closed_engine.outputs))
        self.assertEqual(len(r.second.closed_engine.stock),len(r.first.closed_engine.stock)+1)

    def test_internal_future_constraint_selects_from_a_currently_indistinguishable_source_line(self):
        _,_,anchor=prepare_connection(self.first,ConnectionSpec())
        leaf=anchor.producer_plan.pending.plan.leaf
        delta=null_direction(anchor.current_context,anchor.producer_plan.library)
        from recursive_upper_decoder import AffineLetter
        other=AffineLetter(tuple(a+b for a,b in zip(leaf.weights,delta)),leaf.library)
        self.assertEqual(leaf.kernel(anchor.current_context),other.kernel(anchor.current_context))
        p=compatibility_polynomial(anchor)
        self.assertGreater(abs(evaluate(p,0)),TOLERANCE)
        self.assertLess(abs(evaluate(p,self.record.source_certificate.representative)),TOLERANCE/64)

    def test_changed_first_history_changes_the_next_port_and_the_actual_second_source(self):
        other=connect_two(load_published('first',1))
        self.assertNotEqual(self.record.arrived_port,other.arrived_port)
        self.assertNotEqual(self.record.second.residue.source,other.second.residue.source)
        self.assertNotEqual(self.record.source_certificate.representative,other.source_certificate.representative)

    def test_direct_port_obstruction_is_global_for_the_declared_source_line(self):
        for branch,choice in product(('first','second'),(0,1)):
            first=load_published(branch,choice)
            _,_,anchor=prepare_connection(first,ConnectionSpec(mode='direct'))
            p=compatibility_polynomial(anchor)
            self.assertEqual(count_roots(sturm(p)),0)
            with self.assertRaisesRegex(ValueError,'no requested source branch'):
                source_certificate(anchor,0)

    def test_sturm_counts_real_roots_including_a_repeated_root_and_no_root_control(self):
        p=(Q(1),)
        for root in (-3,-1,2,4):p=mul(p,(-root,1))
        self.assertEqual(count_roots(sturm(p)),4)
        self.assertEqual(count_roots(sturm(p),Q(0),Q(5)),2)
        self.assertEqual(count_roots(sturm((1,0,1))),0)
        self.assertEqual(count_roots(sturm(mul((-2,1),(-2,1)))),1)

    def test_quartic_formula_matches_the_existing_quaternion_kernel_independently(self):
        from recursive_upper_decoder import AffineLetter,qmul
        for mode in ('direct','anchored'):
            _,_,anchor=prepare_connection(self.first,ConnectionSpec(mode=mode))
            plan=anchor.producer_plan;base=plan.pending.plan.leaf
            delta=null_direction(anchor.current_context,plan.library)
            p=compatibility_polynomial(anchor)
            for t in (Q(0),Q(1),Q(7),Q(14)):
                leaf=AffineLetter(tuple(a+t*b for a,b in zip(base.weights,delta)),base.library)
                y=context([[leaf.weights[i] if i==j else 0 for j in range(3)] for i in range(3)])
                head_response=qmul(plan.pending.head.kernel(y),plan.upper.live.accumulated)
                endpoint=qmul(leaf.kernel(y),head_response)
                self.assertEqual(endpoint[1:],[0,0,0])
                self.assertEqual(evaluate(p,t),endpoint[0]+1)

    def test_second_root_has_a_sign_change_and_nonzero_slope(self):
        c=self.record.source_certificate
        self.assertLess(evaluate(c.polynomial,c.bracket[0])*evaluate(c.polynomial,c.bracket[1]),0)
        self.assertFalse(c.derivative_range[0]<=0<=c.derivative_range[1])
        self.assertEqual(c.real_roots,2)

    def test_committed_second_execution_never_re_solves_a_root_or_searches(self):
        receipt=self.record.second.commitment
        machine=FlowerMachine(receipt.anchor,'COMMITTED',receipt.committed_engine,
            receipt.problem.representative,receipt.problem,(),receipt,0)
        with patch('two_flower_connection.source_certificate',side_effect=AssertionError('no root solving')), \
             patch('two_flower_connection.isolating_brackets',side_effect=AssertionError('no branch search')), \
             patch('completed_single_flower.candidates',side_effect=AssertionError('no word search')):
            while machine.cursor<len(receipt.word):machine=advance(machine,receipt)
            second=close(machine,receipt).record
        self.assertEqual(second,self.record.second)

    def test_replacing_the_second_fixed_request_is_rejected(self):
        fake=replace(self.record.second,fixed_result=self.record.second.actual_endpoint,closure_error=Q(0))
        with self.assertRaises(ValueError):verify_connection(replace(self.record,second=fake),self.first,ConnectionSpec())

    def test_second_consumer_inheritance_cannot_be_replaced(self):
        r=self.record.second;receipt=r.commitment
        original=receipt.anchor.original
        fake=replace(original,upper=replace(original.upper,live=UpperState(original.upper.live.context,(-1,0,0,0))))
        fake_anchor=replace(receipt.anchor,original=fake)
        fake_receipt=replace(receipt,anchor=fake_anchor)
        with self.assertRaises(ValueError):
            verify_connection(replace(self.record,second=replace(r,commitment=fake_receipt)),self.first,ConnectionSpec())

    def test_connection_context_and_first_occurrence_cannot_be_swapped(self):
        with self.assertRaises(ValueError):
            verify_connection(replace(self.record,arrived_port=self.record.raw_port),self.first,ConnectionSpec())
        with self.assertRaises(ValueError):
            verify_connection(self.record,load_published('first',1),ConnectionSpec())

    def test_source_representative_or_branch_cannot_be_changed_after_execution(self):
        c=self.record.source_certificate
        with self.assertRaises(ValueError):
            verify_connection(replace(self.record,source_certificate=replace(c,representative=Q(0))),self.first,ConnectionSpec())
        with self.assertRaises(ValueError):
            verify_connection(self.record,self.first,ConnectionSpec(source_branch=1))

    def test_another_legal_second_path_does_not_pass_the_original_free_choice(self):
        with self.assertRaises(ValueError):
            verify_connection(replace(self.record,second=self.long.second),self.first,ConnectionSpec())

    def test_past_rounds_events_and_stock_are_not_deleted_by_connection(self):
        a=self.first.closed_engine;b=self.record.second.closed_engine
        self.assertEqual(b.events[:len(a.events)],a.events)
        self.assertEqual(b.rounds[:len(a.rounds)],a.rounds)
        self.assertEqual(b.stock[:len(a.stock)],a.stock)
        self.assertEqual(b.upper.executed_word[:len(a.upper.executed_word)],a.upper.executed_word)

    def test_second_closure_is_a_stop_without_a_third_request(self):
        e=self.record.second.closed_engine
        self.assertEqual(e.phase,'IDLE');self.assertIsNone(e.pending)
        self.assertEqual(sum(v.kind=='boundary-requested' for v in e.events),2)
        self.assertLess(self.record.second.closure_error,TOLERANCE/2)
        self.assertNotEqual(self.record.second.actual_endpoint,self.record.second.fixed_result)

    def test_exact_json_round_trip_keeps_the_complete_two_flower_occurrence(self):
        before=copy.deepcopy(self.record)
        loaded=import_connected(json.loads(json.dumps(export_connected(self.record))),self.first,ConnectionSpec())
        self.assertEqual(loaded,before)

    def test_unknown_json_type_and_cyclic_reference_are_rejected(self):
        payload=export_connected(self.record);payload['nodes'][0]['type']='untrusted.SomeClass'
        with self.assertRaises(ValueError):import_connected(payload,self.first,ConnectionSpec())
        payload={'schema':'time-engine-two-flower-record-v1','root':{'ref':0},'nodes':[{'tuple':[{'ref':0}]}]}
        with self.assertRaisesRegex(ValueError,'cyclic'):import_connected(payload,self.first,ConnectionSpec())

    def test_zero_port_strength_is_an_explicit_residue_readout_ablation(self):
        left=connection_context(self.first,ConnectionSpec(strength=0))[1]
        right=connection_context(load_published('first',1),ConnectionSpec(strength=0))[1]
        self.assertEqual(left,right)
        self.assertEqual(left,boundary_readout(self.first.closed_engine.designated_head))
        self.assertNotEqual(self.record.arrived_port,left)

    def test_invalid_connection_conditions_are_rejected(self):
        for args in ({'mode':'automatic-fallback'},{'strength':-1},{'source_branch':2},{'petal_choice':-1}):
            with self.assertRaises(ValueError):ConnectionSpec(**args)


if __name__=='__main__':unittest.main()
