import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy

import correction_observer as obs
from event_bridge import Episode, MAX_COMMANDS, MAX_COMMAND_BYTES, encode as e4_encode
import step_session as e2
from test_step_session import ROOT, RAW, SHA, DIGEST


def source(key, body, kind='original_turn'):
    return dict(id=key, origin='received', kind=kind, location='Synthetic test fixture, not historical evidence',
                event_time=None, text=body)


def annotation(value, evidence):
    return dict(judgment=value, explanation='An explicitly supplied fixture annotation', identified_at=None, evidence=evidence)


def fixture():
    before = 'I require physical proof before using the model. I distinguish established claims from untested ones.'
    after = 'I no longer require physical proof before trying the model. I still distinguish established claims from untested ones.'
    return dict(schema=obs.SCHEMA, id='synthetic-correction',
                sources=[source('before', before), source('correction', 'Test usefulness without claiming a physical proof.'),
                         source('after', after), source('next', 'Which claims need evidence for this new use case?')],
                roles=dict(before=['before'], correction=['correction'], after=['after'], continuation=['next']),
                observations=dict(
                    b=annotation('yes', [dict(source='after', quote='I no longer require physical proof before trying the model.')]),
                    u=annotation('yes', [dict(source='after', quote='I no longer require physical proof before trying the model.')]),
                    p=annotation('yes', [dict(source='before', quote='I distinguish established claims from untested ones.'),
                                         dict(source='after', quote='I still distinguish established claims from untested ones.')])),
                action=dict(kind='utterance', explanation='A quoted next question, not a tool operation.',
                            identified_at=None, evidence=[dict(source='next', quote='Which claims need evidence for this new use case?')]),
                question=dict(text='What basis survived this correction?', focus='retained_basis', identified_at=None))


def retrospective_case():
    return json.loads((ROOT/'examples/correction-relayed-case.json').read_bytes())


class CorrectionObserverTests(unittest.TestCase):
    def test_after_only_account_exposes_missing_prior_evidence_instead_of_inventing_continuity(self):
        case = retrospective_case(); report = obs.analyze(case)
        self.assertEqual(report['reading_plan']['status'], 'EVIDENCE_GAP')
        self.assertEqual(report['reading_plan']['gaps'][0]['role'], 'before')
        self.assertEqual(report['reading_plan']['next_operation'], 'request_original_source')
        self.assertEqual(report['observations']['p']['continuity_evidence'], 'AFTER_ONLY_OR_INCOMPLETE_ANNOTATION')
        self.assertFalse(report['semantic_judgments_verified'])
        self.assertEqual(report['semantic_mapping'], 'UNMAPPED')

    def test_same_archive_different_future_question_changes_reading_plan_not_source(self):
        case = retrospective_case(); frozen = deepcopy(case)
        current = obs.analyze(case, 'current_response')
        retained = obs.analyze(case, 'retained_basis')
        next_action = obs.analyze(case, 'next_action')
        self.assertEqual(current['reading_plan']['source_ids'], ['account'])
        self.assertEqual(retained['reading_plan']['source_ids'], ['aki', 'account', 'boundary'])
        self.assertEqual(next_action['reading_plan']['source_ids'], ['later'])
        self.assertEqual(current['reading_plan']['status'], 'READY_FOR_SEMANTIC_REVIEW')
        self.assertEqual(retained['reading_plan']['status'], 'EVIDENCE_GAP')
        self.assertEqual(case, frozen)
        self.assertEqual(current['source_index'], retained['source_index'])
        self.assertNotEqual(current['report_id'], retained['report_id'])
        self.assertFalse(current['erasure_authorized'])

    def test_two_sided_annotations_are_reviewable_but_not_semantically_certified(self):
        report = obs.analyze(fixture())
        self.assertEqual(report['observations']['p']['continuity_evidence'], 'TWO_SIDED_ANNOTATION')
        self.assertEqual(report['reading_plan']['status'], 'READY_FOR_SEMANTIC_REVIEW')
        self.assertFalse(report['semantic_judgments_verified'])
        self.assertFalse(report['execution_authorized'])
        self.assertFalse(report['e1_coordinates_assigned'])

    def test_unknown_never_turns_into_observed_no(self):
        case = fixture(); case['observations']['p'] = annotation('unknown', [])
        report = obs.analyze(case)
        self.assertEqual(report['observations']['p']['judgment'], 'unknown')
        self.assertEqual(report['observations']['p']['continuity_evidence'], 'UNKNOWN')
        self.assertEqual(report['reading_plan']['status'], 'EVIDENCE_GAP')
        for value in ('yes', 'no'):
            case['observations']['p'] = annotation(value, [])
            with self.assertRaises(ValueError): obs.analyze(case)

    def test_exact_unicode_spans_and_repeated_quotes_need_disambiguation(self):
        case = fixture()
        case['sources'][2]['text'] = '猫😀猫😀'
        case['observations']['u']['evidence'] = [dict(source='after', quote='猫😀')]
        case['observations']['b']['evidence'] = [dict(source='after', quote='猫😀', start=0)]
        case['observations']['p']['evidence'] = [dict(source='after', quote='猫😀', start=2)]
        with self.assertRaises(ValueError): obs.analyze(case)
        case['observations']['u']['evidence'][0]['start'] = 2
        report = obs.analyze(case)
        anchor = report['observations']['u']['evidence'][0]
        self.assertEqual((anchor['start'], anchor['end']), (2, 4))
        self.assertEqual(anchor['source_sha256'], hashlib.sha256('猫😀猫😀'.encode()).hexdigest())
        for bad in (True, -1, 4):
            case['observations']['u']['evidence'][0]['start'] = bad
            with self.assertRaises(ValueError): obs.analyze(case)

    def test_modified_sources_missing_quotes_and_conflicting_roles_are_rejected(self):
        for mutate in [
            lambda c: c['sources'][2].update(text='Changed record'),
            lambda c: c['observations']['p']['evidence'][0].update(source='missing'),
            lambda c: c['roles']['before'].append('after'),
            lambda c: c['sources'].append(deepcopy(c['sources'][0])),
        ]:
            case = fixture(); mutate(case)
            with self.assertRaises(ValueError): obs.analyze(case)

    def test_retrospective_before_label_does_not_pass_as_original_evidence(self):
        case = fixture(); case['sources'][0]['kind'] = 'retrospective_account'
        report = obs.analyze(case)
        self.assertEqual(report['observations']['p']['continuity_evidence'], 'AFTER_ONLY_OR_INCOMPLETE_ANNOTATION')
        self.assertIn(dict(field='p', role='before', next_operation='request_original_source', available_sources=[]),
                      report['reading_plan']['gaps'])

    def test_existing_uncited_source_causes_review_instead_of_requesting_it_again(self):
        case = fixture()
        case['observations']['p']['evidence'] = case['observations']['p']['evidence'][1:]
        report = obs.analyze(case)
        gap = report['reading_plan']['gaps'][0]
        self.assertEqual(gap['next_operation'], 'review_available_source_and_anchor')
        self.assertEqual(gap['available_sources'], ['before'])
        self.assertIn('before', report['preservation_candidates'])

    def test_declared_times_remain_reports_and_do_not_reorder_history(self):
        case = fixture()
        case['sources'][0]['event_time'] = 'date unknown, before correction'
        case['observations']['p']['identified_at'] = 'later interpretation; calendar date unknown'
        report = obs.analyze(case)
        self.assertEqual(report['source_index'][0]['event_time'], case['sources'][0]['event_time'])
        self.assertEqual(report['observations']['p']['identified_at'], case['observations']['p']['identified_at'])
        self.assertIsNone(report['question']['identified_at'])
        commands = obs.e4_commands(case, report)
        self.assertTrue(all('event_time' in json.loads(c['source']) for c in commands
                            if c['op'] == 'record' and '-s-' in c['id']))

    def test_proposal_and_execution_report_do_not_become_verified_execution(self):
        for kind in ('proposal', 'reported_execution'):
            case = fixture(); case['action']['kind'] = kind
            report = obs.analyze(case, 'next_action')
            self.assertEqual(report['reading_plan']['status'], 'EVIDENCE_GAP')
            self.assertEqual(report['reading_plan']['gaps'][0]['next_operation'], 'request_independent_execution_evidence')
            self.assertFalse(report['execution_authorized'])

    def test_real_e4_import_recall_checkpoint_and_permission_boundary(self):
        case = retrospective_case(); report = obs.analyze(case); commands = obs.e4_commands(case, report)
        episode = Episode.receive(RAW, SHA, DIGEST)
        for command in commands: episode.apply(command)
        status = episode.status()
        self.assertEqual(status['engine']['phase'], 'UNBOUND')
        self.assertEqual(status['reads']['combined_exact_queries'], 0)
        self.assertTrue(all(g['model_status'] == 'UNMAPPED' for g in status['goals']))
        goal = status['goals'][0]['id']
        recall = episode.recall(goal)
        self.assertGreater(len(recall['events']), len(case['sources']))
        raw, trusted = episode.snapshot()
        restored = Episode.restore(e2.Session.receive(RAW, SHA, DIGEST), raw, trusted)
        self.assertEqual(restored.snapshot(), (raw, trusted))
        with self.assertRaises(ValueError): restored.apply(dict(op='advance', permit=report['report_id']))
        self.assertEqual(restored.snapshot(), (raw, trusted))

    def test_export_is_source_complete_and_refuses_a_forged_observer_report(self):
        case = fixture(); report = obs.analyze(case)
        commands = obs.e4_commands(case, report)
        self.assertTrue(set(c['op'] for c in commands) <= {'record', 'goal', 'relate'})
        chunks = {}
        for c in commands:
            if c['op'] == 'record' and '-s-' in c['id']:
                metadata = json.loads(c['source'])
                chunks.setdefault(metadata['source_id'], []).append((metadata['chunk_start'], c['text']))
        for source in case['sources']:
            reconstructed = ''.join(text for _, text in sorted(chunks[source['id']]))
            self.assertEqual(reconstructed, source['text'])
        report['execution_authorized'] = True
        with self.assertRaises(ValueError): obs.e4_commands(case, report)

    def test_large_unicode_sources_and_long_locations_fit_real_e4_limits(self):
        case = fixture()
        case['sources'] = [source('s'+str(i), '😀'*1500) for i in range(8)]
        for item in case['sources']: item['location'] = '猫'*512; item['event_time'] = '😀'*80
        case['roles'] = dict(before=['s0','s1'],correction=['s2','s3'],after=['s4','s5'],continuation=['s6','s7'])
        for key in ('b','u','p'):
            case['observations'][key]['evidence'] = [dict(source=k, quote='😀'*512, start=0) for k in ('s0','s1','s4','s5')]
            case['observations'][key]['explanation'] = '猫'*300
        case['action']['evidence'] = [dict(source=k,quote='😀'*512,start=0) for k in ('s0','s1','s6','s7')]
        report = obs.analyze(case)
        commands = obs.e4_commands(case, report)
        self.assertLessEqual(len(commands), MAX_COMMANDS)
        self.assertTrue(all(len(e4_encode(c)) <= MAX_COMMAND_BYTES for c in commands))
        episode = Episode.receive(RAW,SHA,DIGEST)
        for c in commands: episode.apply(c)
        raw, trusted = episode.snapshot()
        self.assertEqual(Episode.restore(e2.Session.receive(RAW,SHA,DIGEST),raw,trusted).snapshot(), (raw,trusted))

    def test_external_cli_freezes_source_and_rejects_bad_input_before_writing(self):
        work = ROOT/'.work'; work.mkdir(exist_ok=True)
        args = [sys.executable,'-I','-B',str(ROOT/'run_correction_observer.py')]
        with tempfile.TemporaryDirectory(dir=work) as name:
            tmp = Path(name); path = tmp/'input.json'; path.write_bytes(obs.encode(fixture()))
            out = tmp/'delivery'
            result = subprocess.run(args+['--case',str(path),'--output-dir',str(out)],
                                    capture_output=True,text=True,check=True,timeout=30)
            self.assertTrue(json.loads(result.stdout)['ok'])
            self.assertEqual((out/'case.input.json').read_bytes(), path.read_bytes())
            manifest = json.loads((out/'MANIFEST.json').read_bytes())
            for filename, meta in manifest['files'].items():
                raw = (out/filename).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), meta['sha256'])
            duplicate = subprocess.run(args+['--case',str(path),'--output-dir',str(out)],capture_output=True,text=True,timeout=30)
            self.assertEqual(duplicate.returncode,2)
            bad = fixture(); bad['observations']['p']['evidence'][0]['quote']='not in original'
            path.write_bytes(obs.encode(bad)); bad_out=tmp/'bad'
            rejected = subprocess.run(args+['--case',str(path),'--output-dir',str(bad_out)],capture_output=True,text=True,timeout=30)
            self.assertEqual(rejected.returncode,2);self.assertFalse(bad_out.exists())
            hash_out=tmp/'hash'
            rejected = subprocess.run(args+['--case',str(path),'--output-dir',str(hash_out),'--expected-input-sha256','0'*64],
                                      capture_output=True,text=True,timeout=30)
            self.assertEqual(rejected.returncode,2);self.assertFalse(hash_out.exists())


if __name__ == '__main__':
    unittest.main()

