import hashlib
import json
import math
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import outbound as port
import validate as driver


class PortabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.here = Path(__file__).resolve().parent
        cls.manifest = json.loads((cls.here/'records/manifest.json').read_bytes())
        cls.items = cls.manifest['records']
        cls.original_course = port.source_course
        cls.primary = port.primary_requirement()
        cls.raw = (cls.here/cls.items[0]['path']).read_bytes()
        cls.digest = cls.items[0]['sha256']
        cls.original = port.import_occurrence(cls.raw, cls.primary, mode='keep', free_choice=1)

    @staticmethod
    def future(item):
        data = item['requirement']
        return port.FutureRequirement(tuple(tuple(port.Q(v) for v in row) for row in data['context']),
                                      tuple(port.Q(v) for v in data['result']), port.Q(data['tolerance']))

    @classmethod
    def drifted_course(cls, config=port.CourseConfig()):
        course = cls.original_course(config)
        last = course.checkpoints[-1]
        weights = (port.Q(math.nextafter(float(last.network[0]), math.inf)), *last.network[1:])
        tangent = (port.Q(math.nextafter(float(last.tangent[0]), math.inf)), *last.tangent[1:])
        return replace(course, checkpoints=(*course.checkpoints[:-1], replace(last, network=weights, tangent=tangent)))

    @staticmethod
    def serialized(record):
        return (json.dumps(port.export_occurrence(record), ensure_ascii=False, indent=2)+'\n').encode('utf-8')

    def transport(self, raw=None, digest=None, future=None, **kwargs):
        return port.import_occurrence(self.raw if raw is None else raw,
            self.primary if future is None else future, mode=kwargs.pop('mode', 'keep'),
            free_choice=kwargs.pop('free_choice', 1), verification='transport',
            trusted_sha256=self.digest if digest is None else digest, **kwargs)

    def test_one_ulp_environment_proxy_keeps_decisions_but_rejects_exact_local_reproduction(self):
        with patch('outbound.source_course', side_effect=self.drifted_course):
            self.assertEqual(port.allowed_indices(port.prepare(), self.primary), (0,))
            self.assertEqual(port.allowed_indices(port.prepare(mode='erase'), self.primary), (0, 1, 2, 3))
            with self.assertRaises(port.LocalReproductionMismatch):
                port.import_occurrence(self.raw, self.primary, mode='keep', free_choice=1)

    def test_trusted_transport_preserves_old_data_under_the_same_one_ulp_proxy(self):
        with patch('outbound.source_course', side_effect=self.drifted_course):
            for item in self.items:
                raw = (self.here/item['path']).read_bytes()
                restored = self.transport(raw, item['sha256'], self.future(item), mode=item['mode'])
                self.assertEqual(self.serialized(restored), raw)

    def test_all_published_records_transport_with_neural_regeneration_and_roots_forbidden(self):
        with patch('outbound.source_course', side_effect=AssertionError('no SGD trajectory regeneration')), \
             patch('outbound.port_state', side_effect=AssertionError('no floating-point profile regeneration')), \
             patch('outbound.prepare', side_effect=AssertionError('no local entry regeneration')), \
             patch('outbound.carrier', side_effect=AssertionError('no fixture regeneration')), \
             patch('outbound.execute_contact', side_effect=AssertionError('no floating-point contact regeneration')), \
             patch('outbound.sample_transverse_matrix', side_effect=AssertionError('no local K regeneration')), \
             patch('outbound.epoch_transverse_matrix', side_effect=AssertionError('no local J regeneration')), \
             patch('outbound.single.isolate', side_effect=AssertionError('no root solving')):
            report = driver.transport_published()
        self.assertTrue(report['passed'])
        self.assertEqual(report['published_records'], 3)
        self.assertFalse(report['upstream_floating_point_regenerated'])
        self.assertFalse(report['independent_upstream_dynamics_verified'])
        self.assertTrue(report['exact_port_and_receiver_verified'])

    def test_default_verification_never_falls_back_to_transport_after_a_reproduction_mismatch(self):
        with patch('outbound.source_course', side_effect=self.drifted_course), \
             patch('outbound.verify_transported_occurrence', side_effect=AssertionError('no silent fallback')):
            with self.assertRaises(port.LocalReproductionMismatch):
                port.import_occurrence(self.raw, self.primary, mode='keep', free_choice=1)

    def test_transport_requires_original_bytes_and_an_external_well_formed_digest(self):
        for payload, digest in ((json.loads(self.raw), self.digest), (self.raw, None),
                                (self.raw, 'not-a-hash'), (self.raw, 'G'*64)):
            with self.assertRaises(ValueError):
                port.import_occurrence(payload, self.primary, mode='keep', free_choice=1,
                                       verification='transport', trusted_sha256=digest)

    def test_even_tiny_or_semantically_equivalent_byte_changes_fail_the_original_digest(self):
        altered = replace(self.original.neural_contact.after,
                          network=(self.original.neural_contact.after.network[0]+port.Q(1, 2**80),
                                   *self.original.neural_contact.after.network[1:]))
        fake = replace(self.original, neural_contact=replace(self.original.neural_contact, after=altered))
        for raw in (self.raw+b' ', self.serialized(fake)):
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                self.transport(raw)

    def test_external_entry_mode_c_and_choice_are_still_required_after_a_valid_hash(self):
        alternate = self.future(self.items[-1])
        variants = ({'mode': 'erase'}, {'free_choice': 0}, {'config': port.CourseConfig(start_epoch=100)},
                    {'spec': port.PortSpec(gain=2)}, {'future': alternate})
        for kwargs in variants:
            with self.assertRaisesRegex(ValueError, 'external entry'):
                self.transport(**kwargs)

    def test_invalid_exact_receiver_or_shape_is_rejected_even_with_a_new_explicitly_trusted_digest(self):
        o = self.original
        wrong_state = replace(o.commitment.state, shape=(port.Q(0),)*4)
        variants = (replace(o, actual_endpoint=o.commitment.requirement.result, closure_error=port.Q(0)),
                    replace(o, commitment=replace(o.commitment, state=wrong_state)))
        for fake in variants:
            raw = self.serialized(fake)
            with self.assertRaises(ValueError):
                self.transport(raw, hashlib.sha256(raw).hexdigest())

    def test_transport_does_not_relax_unknown_type_cycle_or_schema_guards(self):
        payload = json.loads(self.raw)
        payload['nodes'][0]['type'] = 'untrusted.Type'
        variants = (payload,
                    {'schema': 'time-engine-3plus1-outbound-occurrence-v1', 'root': {'ref': 0},
                     'nodes': [{'tuple': [{'ref': 0}]}]},
                    {'schema': 'invented'})
        for payload in variants:
            raw = json.dumps(payload).encode('utf-8')
            with self.assertRaises(ValueError):
                self.transport(raw, hashlib.sha256(raw).hexdigest())

    def test_complete_payload_graph_and_all_frozen_source_checkpoints_round_trip_unchanged(self):
        restored = self.transport()
        self.assertEqual(restored, self.original)
        self.assertEqual(port.export_occurrence(restored), json.loads(self.raw))
        self.assertEqual(restored.commitment.state.course.checkpoints,
                         self.original.commitment.state.course.checkpoints)
        self.assertEqual(restored.neural_contact.after, self.original.neural_contact.after)
        self.assertEqual(self.serialized(restored), self.raw)


if __name__ == '__main__':
    unittest.main()
