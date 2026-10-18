import hashlib
import json
import unittest
from dataclasses import replace
from unittest.mock import patch

import three_flower as model
from three_flower import port, triple, Q


class EmbeddedThreeFlowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared={m:model.prepare(m) for m in ('keep','erase','restore')}
        cls.paths={m:model.finite_family(p) for m,p in cls.prepared.items()}
        cls.future=model.construct_requirement(cls.paths['keep'][0]).requirement
        cls.alternate=model.construct_requirement(cls.paths['keep'][32]).requirement
        cls.receipts={m:model.select(cls.prepared[m],cls.future,1) for m in ('keep','erase')}
        cls.actual={m:model.execute(r) for m,r in cls.receipts.items()}

    def test_completed_source_is_loaded_without_upstream_regeneration(self):
        model.prepare.cache_clear();model.published_record.cache_clear()
        with patch('outbound.source_course',side_effect=AssertionError('no SGD course')), \
             patch('outbound.carrier',side_effect=AssertionError('no carrier roots')), \
             patch('outbound.sample_transverse_matrix',side_effect=AssertionError('no Jacobian')):
            p=model.prepare('keep')
        self.assertEqual(p,self.prepared['keep'])
        self.assertEqual(len(p.state.course.checkpoints),9)
        self.assertTrue(all(len(s.network)==17 for s in p.state.course.checkpoints))

    def test_all_local_first_choices_have_identical_present_readout_and_exact_endpoint(self):
        self.assertEqual(len({p.state.phase for p in self.prepared.values()}),1)
        for p in self.prepared.values():
            firsts=model.first_options(p)
            self.assertEqual(len(firsts),8)
            self.assertTrue(all(r.actual_endpoint==port.FIXED_RESULT and r.closure_error==0 for r in firsts))
            self.assertTrue(all(c.leaf.kernel(p.receiver.anchor.current_context)==(-9,0,0,0) for c in p.candidates))
            self.assertEqual({r.receipt.petal_choice for r in firsts},{0,1})

    def test_first_retained_actions_differ_despite_equal_closure_and_preserve_full_history(self):
        firsts=model.first_options(self.prepared['keep'])
        self.assertEqual(len({r.residue.source.cell.beta[0].weights for r in firsts}),4)
        self.assertEqual(len({r.actual_endpoint for r in firsts}),1)
        self.assertNotEqual(firsts[0].residue.terminal_operation,firsts[1].residue.terminal_operation)
        self.assertNotEqual(firsts[0].closed_engine.upper.executed_word,firsts[1].closed_engine.upper.executed_word)

    def test_common_upper_condition_restricts_embedded_first_contact(self):
        self.assertEqual([p.choices for p in model.allowed(self.paths['keep'],self.future)],[(0,0,0,0,0,0)])
        self.assertEqual([p.choices for p in model.allowed(self.paths['erase'],self.future)],[(i,0,0,0,0,0) for i in range(4)])
        self.assertEqual(model.local_requirement(self.prepared['keep']),model.local_requirement(self.prepared['erase']))

    def test_every_excluded_first_choice_has_all_sixteen_suffixes_checked(self):
        for i in range(4):
            for j in range(2):
                group=[p for p in self.paths['keep'] if p.choices[:2]==(i,j)]
                self.assertEqual(len(group),16)
                if (i,j)!=(0,0):
                    self.assertTrue(all(not triple.admissible(p,self.future) for p in group))
        failures=[p for p in self.paths['keep'] if not triple.admissible(p,self.future)]
        self.assertGreater(min(triple.upper_preview(p.records,self.future)[-1][-1] for p in failures),port.EPSILON*1000)

    def test_restoration_and_zero_coupling_reproduce_the_two_controls(self):
        keep=[p.choices for p in model.allowed(self.paths['keep'],self.future)]
        self.assertEqual([p.choices for p in model.allowed(self.paths['restore'],self.future)],keep)
        zero=model.finite_family(model.prepare('keep',Q(0)))
        self.assertEqual([p.choices for p in model.allowed(zero,self.future)],
                         [p.choices for p in model.allowed(self.paths['erase'],self.future)])

    def test_changing_only_shared_future_changes_the_admitted_contact(self):
        self.assertEqual([p.choices for p in model.allowed(self.paths['keep'],self.alternate)],[(1,0,0,0,0,0)])
        self.assertEqual(model.allowed(self.paths['erase'],self.alternate),())
        # The common requirement excludes them; they are not intrinsically
        # incapable of any upper closure in the declared frame chart.
        for index in range(0,128,16):
            reference=self.paths['keep'][index]
            own=model.construct_requirement(reference).requirement
            self.assertTrue(triple.admissible(reference,own))

    def test_admissibility_uses_action_values_instead_of_path_names(self):
        p=self.paths['keep'][0]
        self.assertTrue(triple.admissible(replace(p,choices=(99,)*6),self.future))
        failed=self.paths['keep'][32]
        self.assertFalse(triple.admissible(replace(failed,choices=p.choices),self.future))

    def test_current_free_choice_remains_free_among_erased_allowed_contacts(self):
        self.assertEqual([model.select(self.prepared['erase'],self.future,i).chosen.choices[0] for i in range(4)],list(range(4)))
        self.assertEqual([model.select(self.prepared['keep'],self.future,i).chosen.choices[0] for i in range(4)],[0]*4)

    def test_changed_embedded_input_is_rejected_before_selection(self):
        p=self.prepared['keep']
        with self.assertRaises(ValueError):
            model.select(replace(p,candidates=tuple(reversed(p.candidates))),self.future)
        with self.assertRaises(ValueError):
            model.select(replace(p,state=replace(p.state,shape=(Q(0),)*4)),self.future)

    def test_frozen_execution_calls_no_candidate_or_root_solver(self):
        with patch('three_flower.finite_family',side_effect=AssertionError('no enumeration')), \
             patch('three_flower.select',side_effect=AssertionError('no selection')), \
             patch('three_flower.prepare',side_effect=AssertionError('no entry regeneration')), \
             patch('three_flower.construct_requirement',side_effect=AssertionError('no future fixture')), \
             patch('three_flower.preview_second',side_effect=AssertionError('no source search')), \
             patch('three_flower_constraint.source_witness',side_effect=AssertionError('no source roots')):
            self.assertEqual(model.execute(self.receipts['keep']),self.actual['keep'])

    def test_three_actual_sources_publish_at_same_scale_then_one_upper_closes(self):
        for actual in self.actual.values():
            self.assertEqual(len(actual.actual_records),3)
            end=actual.actual_records[-1].closed_engine
            self.assertEqual(len(end.stock),7)
            self.assertEqual(len(end.outputs),3)
            self.assertTrue(all(o.level==3 for o in end.outputs))
            self.assertEqual(actual.upper_decoded.outputs[0].level,4)
            self.assertTrue(all(x.level==2 for x in end.stock))
            for before,after in zip(actual.actual_records,actual.actual_records[1:]):
                self.assertEqual(after.closed_engine.stock[:len(before.closed_engine.stock)],before.closed_engine.stock)
                self.assertEqual(after.closed_engine.events[:len(before.closed_engine.events)],before.closed_engine.events)
                self.assertEqual(after.commitment.anchor.original,before.closed_engine)

    def test_actual_neural_contact_is_executed_and_retained_with_all_parameters(self):
        for actual in self.actual.values():
            contact=actual.neural_contact
            self.assertEqual(len(contact.before.network),17)
            self.assertEqual(len(contact.after.network),17)
            self.assertNotEqual(contact.after.network,contact.before.network)
            self.assertEqual(contact.contact_index,actual.commitment.chosen.choices[0])

    def test_coherent_record_substitutions_are_rejected_against_original_receipt(self):
        actual=self.actual['keep'];receipt=self.receipts['keep']
        first=actual.actual_records[0]
        for fakefirst in (replace(first,fixed_result=first.actual_endpoint[:-1]+(Q(1),)),
                          replace(first,actual_endpoint=(Q(0),)*4)):
            with self.assertRaises(ValueError):
                model.verify_occurrence(replace(actual,actual_records=(fakefirst,)+actual.actual_records[1:]),receipt)
        with self.assertRaises(ValueError):
            model.execute(replace(receipt,chosen=replace(receipt.chosen,choices=(99,)*6)))

    def test_authenticated_transport_preserves_bytes_without_learning_or_search(self):
        actual=self.actual['keep']
        raw=(json.dumps(model.export_record(actual),separators=(',',':'))+'\n').encode()
        sha=hashlib.sha256(raw).hexdigest()
        with patch('outbound.execute_contact',side_effect=AssertionError('no upstream contact regeneration')), \
             patch('three_flower.finite_family',side_effect=AssertionError('no enumeration')), \
             patch('three_flower_constraint.source_witness',side_effect=AssertionError('no roots')):
            restored=model.import_record(raw,self.future,free_choice=1,trusted_sha256=sha)
        self.assertEqual(restored,actual)
        self.assertEqual((json.dumps(model.export_record(restored),separators=(',',':'))+'\n').encode(),raw)

    def test_transport_binds_external_hash_requirement_mode_and_choice(self):
        raw=(json.dumps(model.export_record(self.actual['keep']),separators=(',',':'))+'\n').encode()
        sha=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError): model.import_record(raw+b' ',self.future,free_choice=1,trusted_sha256=sha)
        with self.assertRaises(ValueError): model.import_record(raw,self.alternate,free_choice=1,trusted_sha256=sha)
        with self.assertRaises(ValueError): model.import_record(raw,self.future,mode='erase',free_choice=1,trusted_sha256=sha)
        with self.assertRaises(ValueError): model.import_record(raw,self.future,free_choice=0,trusted_sha256=sha)


if __name__=='__main__':
    unittest.main()
