"""The readout is detached; state transfer requires a complete verified record."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
import step_session as api
from test_step_session import RAW, SHA, DIGEST, ROOT, REQUEST, receive, ready, encoded


class StateViewTests(unittest.TestCase):
    def test_mutating_nested_readouts_cannot_mutate_request_journal_or_work(self):
        s = receive()
        request = dict(REQUEST, domain=['-2', '2'])
        s.apply(dict(op='bind', requirement=request))
        s.apply(dict(op='choose', v='1', u='0', word='HHHSUT'))
        returned = s.apply(dict(op='resolve'))
        before = s.snapshot()
        baseline = copy.deepcopy(s.status())
        returned['requirement']['strengths'][0] = '0'
        returned['requirement']['domain'][0] = '-999'
        returned['last_resolution_work'].clear()
        returned['phase_operations'].clear()
        with patch.object(s.entry.base.vault, 'exact', side_effect=AssertionError('view must not read source values')), \
             patch.object(s.entry.derived, 'exact', side_effect=AssertionError('view must not read observations')):
            other = s.status()
            other['requirement']['strengths'].clear()
            other['last_resolution_work']['total_exact_queries'] = -1
            self.assertEqual(s.status(), baseline)
        self.assertEqual(baseline['schema'], api.VIEW_SCHEMA)
        self.assertEqual(s.snapshot(), before)
        restored = api.Session.restore(api.wire.loads(RAW, SHA, DIGEST), *before)
        self.assertEqual(restored.snapshot(), before)
        self.assertEqual(restored.status(), baseline)
        type(self).isolation = dict(nested_views_detached=True, checkpoint_bytes_unchanged=True,
                                    view_exact_reads=0, restore_after_view_edits=True)

    def test_status_or_numeric_summary_cannot_replace_entry_or_checkpoint(self):
        s = receive(); ready(s)
        raw, _ = s.snapshot()
        view = s.status()
        summary = dict(entry=view['entry'], phase=view['phase'], certified=view['certified'],
                       stock=view['stock'], values=[['-1', '0', '0', '0']])
        forged_current = json.loads(raw)
        forged_current['current'] = view
        # Even a matching hash supplied for a replacement is not a state certificate.
        for value in (view, summary, forged_current):
            reduced, reduced_sha = encoded(value)
            with self.assertRaises(ValueError):
                api.Session.restore(api.wire.loads(RAW, SHA, DIGEST), reduced, reduced_sha)
        reduced, reduced_sha = encoded(view)
        with self.assertRaises(ValueError):
            api.Session.receive(reduced, reduced_sha, DIGEST)
        type(self).rejection = dict(status_as_entry_rejected=True, status_as_checkpoint_rejected=True,
            numeric_summary_as_checkpoint_rejected=True, summary_inside_checkpoint_rejected=True)

    def test_same_values_do_not_make_replaced_provenance_an_original_state(self):
        raw = (ROOT/'integrations/inquiry/fixtures/P0-first-use-CLOSED1.record.json').read_bytes()
        document = json.loads(raw)
        archive = json.loads(bytes.fromhex(document['current']['numbers']['base']))
        original_records = copy.deepcopy(archive['retained'])
        # Preserve every numeric value, bound, node and current physical graph;
        # replace only one source origin reference in the held-number archive.
        archive['retained'][0][3] = '0'*64
        self.assertNotEqual(archive['retained'], original_records)
        self.assertEqual([x[:3] for x in archive['retained']], [x[:3] for x in original_records])
        document['current']['numbers']['base'] = json.dumps(archive, separators=(',', ':')).encode().hex()
        forged, forged_sha = encoded(document)
        with self.assertRaisesRegex(ValueError, 'history or command chronology changed'):
            api.Session.restore(api.wire.loads(RAW, SHA, DIGEST), forged, forged_sha)
        # The untouched old record still restores and keeps its exact bytes.
        sha = hashlib.sha256(raw).hexdigest()
        restored = api.Session.restore(api.wire.loads(RAW, SHA, DIGEST), raw, sha)
        self.assertEqual(restored.snapshot(), (raw, sha))
        self.assertEqual(restored.status()['phase'], 'CLOSED1')
        type(self).provenance = dict(same_values_replaced_origin_rejected=True,
            physical_graph_preserved_in_counterfeit=True, original_record_restored=True,
            legacy_checkpoint_sha256=sha)


if __name__ == '__main__':
    unittest.main()
