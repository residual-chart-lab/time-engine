import unittest,copy
from dataclasses import replace
from unittest.mock import patch
from three_flower_constraint import *


class ThreeFlowerConstraintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths=finite_family();cls.fixture=construct_test_requirement()
        cls.requirement=cls.fixture.requirement;cls.receipt=select_macro(cls.requirement)
        cls.actual=execute_macro(cls.receipt)
        cls.alternate=construct_test_requirement(63).requirement

    def test_all_declared_three_flower_continuations_are_locally_closed(self):
        self.assertEqual(len(self.paths),64)
        for path in self.paths:
            self.assertEqual(len(path.records[-1].closed_engine.rounds),3)
            self.assertTrue(all(r.closure_error<TOLERANCE/2 for r in path.records))

    def test_common_future_reduces_four_first_choices_to_one(self):
        before={p.choices[:2] for p in self.paths}
        after={p.choices[:2] for p in self.paths if admissible(p,self.requirement)}
        self.assertEqual(len(before),4);self.assertEqual(after,{('first',0)})
        self.assertEqual(self.receipt.admissible_count,1)

    def test_later_source_and_petal_reselection_cannot_rescue_excluded_first_choices(self):
        for first in (('first',1),('second',0),('second',1)):
            later=[p for p in self.paths if p.choices[:2]==first]
            self.assertEqual(len(later),16)
            errors=[upper_preview(p.records,self.requirement)[-1][-1] for p in later]
            self.assertGreater(min(errors),TOLERANCE*10**6)

    def test_changing_future_frame_changes_which_first_history_is_selected(self):
        other=select_macro(self.alternate)
        self.assertNotEqual(other.chosen.choices[:2],self.receipt.chosen.choices[:2])
        self.assertEqual(other.requirement.result,self.requirement.result)
        self.assertEqual(other.requirement.tolerance,self.requirement.tolerance)
        self.assertTrue(verify_occurrence(execute_macro(other),other))

    def test_predicate_uses_actual_actions_rather_than_history_labels(self):
        chosen=self.receipt.chosen
        self.assertTrue(admissible(replace(chosen,choices=('unread-label',)*6),self.requirement))
        rejected=next(p for p in self.paths if not admissible(p,self.requirement))
        self.assertFalse(admissible(replace(rejected,choices=chosen.choices),self.requirement))

    def test_unbound_future_frame_restores_all_first_choices(self):
        firsts=set()
        for i in range(0,64,16):
            own=construct_test_requirement(i).requirement
            self.assertTrue(admissible(self.paths[i],own));firsts.add(self.paths[i].choices[:2])
        self.assertEqual(len(firsts),4)

    def test_committed_execution_never_searches_or_resolves_future_roots(self):
        with patch('three_flower_constraint.finite_family',side_effect=AssertionError('no candidate search')), \
             patch('three_flower_constraint.source_witness',side_effect=AssertionError('no source solving')), \
             patch('three_flower_constraint.isolated',side_effect=AssertionError('no root isolation')), \
             patch('completed_single_flower.candidates',side_effect=AssertionError('no word search')), \
             patch('two_flower_connection.resolve_open',side_effect=AssertionError('no replanning')):
            actual=execute_macro(self.receipt)
        self.assertEqual(actual,self.actual)

    def test_actual_inventory_contains_only_three_published_new_sources(self):
        e=self.actual.actual_records[-1].closed_engine
        self.assertEqual(len(e.stock),7);self.assertEqual(len(e.outputs),3)
        self.assertTrue(all(op.level==2 for op in e.stock))
        self.assertTrue(all(op.level==3 for op in e.outputs))

    def test_every_connection_inherits_actual_states_and_keeps_prefixes(self):
        records=self.actual.actual_records
        for a,b in zip(records,records[1:]):
            self.assertEqual(b.commitment.anchor.original,a.closed_engine)
            self.assertEqual(b.commitment.problem.start.live.accumulated,a.actual_endpoint)
            self.assertEqual(b.closed_engine.outputs[:len(a.closed_engine.outputs)],a.closed_engine.outputs)
            self.assertEqual(b.closed_engine.events[:len(a.closed_engine.events)],a.closed_engine.events)

    def test_shared_boundary_actually_closes_after_three_upper_operations(self):
        a=self.actual;_,_,_,errors=upper_preview(a.actual_records,self.requirement)
        self.assertTrue(all(e>TOLERANCE for e in errors[:-1]))
        self.assertLess(errors[-1],TOLERANCE/2)
        self.assertEqual(len(a.upper_decoded.outputs[0].cell.beta),3)
        self.assertEqual(a.upper_decoded.outputs[0].level,4)
        self.assertEqual(promote_word(a.upper_decoded.outputs[0].cell),a.upper_decoded.outputs[0])

    def test_actual_upper_endpoint_is_retained_separately_from_fixed_requirement(self):
        self.assertNotEqual(self.actual.upper_decoded.state.live.accumulated,self.requirement.result)
        self.assertTrue(all(r.actual_endpoint!=r.fixed_result for r in self.actual.actual_records))

    def test_terminal_polynomial_matches_the_actual_nested_kernel(self):
        from recursive_upper_decoder import qmul
        records=self.receipt.chosen.records;p=terminal_polynomial(records)
        for x in (Q(3,10),Q(7,20),self.requirement.x):
            y=context([[x,0,0],[0,1-x,0],[0,0,0]])
            state=records[-1].actual_endpoint
            for record in records:state=tuple(qmul(record.residue.terminal_operation.kernel(y),state))
            self.assertEqual(evaluate(p,x),state[0]+1)
            self.assertEqual(state[1:],(0,0,0))

    def test_simple_terminal_frame_root_has_sign_change_and_nonzero_derivative(self):
        f=self.fixture
        self.assertLess(evaluate(f.polynomial,f.bracket[0])*evaluate(f.polynomial,f.bracket[1]),0)
        self.assertFalse(f.derivative_range[0]<=0<=f.derivative_range[1])

    def test_different_future_requirement_cannot_certify_the_same_occurrence(self):
        other=replace(self.receipt,requirement=self.alternate)
        with self.assertRaises(ValueError):verify_occurrence(self.actual,other)

    def test_replaced_first_occurrence_is_rejected_against_frozen_macro_receipt(self):
        other=next(p for p in self.paths if p.choices[:2]!=self.receipt.chosen.choices[:2])
        fake=replace(self.actual,actual_records=(other.records[0],*self.actual.actual_records[1:]))
        with self.assertRaises(ValueError):verify_occurrence(fake,self.receipt)

    def test_replaced_inherited_state_is_rejected_before_executing_the_next_flower(self):
        first,second,*_=self.actual.actual_records
        fake=replace(first,closed_engine=replace(first.closed_engine,upper=replace(first.closed_engine.upper,
            live=UpperState(first.closed_engine.upper.live.context,(-1,0,0,0)))))
        with self.assertRaisesRegex(ValueError,'previous exit'):replay_frozen(second,fake)

    def test_exact_json_round_trip_keeps_the_actual_macro_history(self):
        saved=json.loads(json.dumps(export_macro(self.actual)))
        self.assertEqual(import_macro(saved,self.requirement),self.actual)

    def test_unknown_or_cyclic_json_types_are_rejected(self):
        payload=export_macro(self.actual);payload['nodes'][0]['type']='untrusted.Type'
        with self.assertRaises(ValueError):import_macro(payload,self.requirement)
        payload={'schema':'time-engine-three-flower-upper-occurrence-v1','root':{'ref':0},'nodes':[{'tuple':[{'ref':0}]}]}
        with self.assertRaisesRegex(ValueError,'cyclic'):import_macro(payload,self.requirement)

    def test_invalid_terminal_request_cannot_loosen_tolerance_or_replace_fixed_result(self):
        for args in ({'x':0},{'x':Q(1,3),'tolerance':TOLERANCE*10},{'x':Q(1,3),'result':(1,0,0,0)}):
            with self.assertRaises(ValueError):TerminalRequirement(**args)

    def test_exact_rational_io_exceeds_the_default_decimal_digit_limit_without_rounding(self):
        value=Q(10**5000+7,10**5011+9)
        encoded=encode(value);numerator,denominator=encoded.split('/')
        self.assertGreater(len(numerator),4300)
        self.assertEqual(Q(parse_integer(numerator),parse_integer(denominator)),value)
        self.assertEqual(parse_integer(decimal_integer(-value.numerator)),-value.numerator)


if __name__=='__main__':unittest.main()
