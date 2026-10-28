import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import event_bridge as e4
import step_session as e2
import recollection as api

ROOT = Path(__file__).resolve().parents[2]
RAW = (ROOT / 'integrations/inquiry/E1-entry.record.json').read_bytes()
SHA = 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
DIGEST = '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'


class RecollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = e2.Session.receive(RAW, SHA, DIGEST).entry

    def fresh(self):
        return api.Recollection(e4.Episode(e2.Session(self.entry)))

    def seed(self):
        s = self.fresh()
        s.apply(dict(op='record', id='seed', origin='received',
                     source='fixed test report', text='にちゃにちゃ笑う、ゴビリン。'))
        s.apply(dict(op='goal', id='C', text='Use the received report in a later reply.',
                     events=['seed']))
        return s

    def registered(self):
        s = self.seed()
        s.apply(dict(op='register', id='gobirin', goal='C', cues=['ゴビリン'],
                     summary='台所の相談から共有された呼び名。これは呼出し側の要約。'))
        return s

    def reply(self, ticket, **changes):
        cmd = dict(op='record_reply', id='next', ticket=ticket,
                   text='あれなｗ　受け取った記録では、にちゃにちゃ笑っていたね。',
                   origin='reported_in_session', source='host AI output supplied by caller',
                   used_summary=True, used_sources=['seed'], other_context=['current_chat'])
        cmd.update(changes)
        return cmd

    def test_short_cue_returns_summary_and_refs_without_replaying_all_originals(self):
        s = self.registered(); before = s.snapshot()
        result = s.apply(dict(op='call', cue='あのときのゴビリン、面白かったなｗ'))
        self.assertEqual(result['packet']['status'], 'MATCH')
        self.assertEqual(result['packet']['memory']['id'], 'gobirin')
        self.assertEqual([r['id'] for r in result['packet']['references']], ['seed'])
        self.assertNotIn('にちゃにちゃ笑う', json.dumps(result['packet'], ensure_ascii=False))
        self.assertEqual(s.snapshot(), before)
        self.assertEqual(s.call('ゴブリン')['packet']['status'], 'NO_MATCH')

    def test_ambiguous_cue_keeps_current_choice_and_explicit_selection(self):
        s = self.registered()
        s.apply(dict(op='register', id='another', goal='C', cues=['ゴビリン'],
                     summary='同じ呼び名の別の読み方。'))
        result = s.call('ゴビリン')
        self.assertEqual(result['packet']['status'], 'AMBIGUOUS')
        self.assertIsNone(result['packet']['memory'])
        self.assertEqual(s.call('ゴビリン', 'another')['packet']['memory']['id'], 'another')
        with self.assertRaises(ValueError):
            s.call('別の語', 'gobirin')

    def test_read_returns_exact_report_and_rejects_outside_sources(self):
        s = self.registered()
        s.apply(dict(op='record', id='unrelated', origin='received',
                     source='other report', text='not in C'))
        ticket = s.call('ゴビリン')['ticket']
        result = s.apply(dict(op='read', ticket=ticket, event='seed'))
        self.assertEqual(result['text'], 'にちゃにちゃ笑う、ゴビリン。')
        self.assertEqual(result['event']['origin'], 'received')
        result['event']['text'] = 'edited display'
        self.assertEqual(s.read(ticket, 'seed')['text'], 'にちゃにちゃ笑う、ゴビリン。')
        with self.assertRaises(ValueError):
            s.read(ticket, 'unrelated')

    def test_reply_appends_new_history_preserving_old_horizon_and_prefix(self):
        s = self.registered()
        result = s.call('ゴビリン'); ticket = result['ticket']
        prior = s.episode.recall('C', ticket['as_of'])
        prefix = json.loads(s.snapshot()[0])['journal']
        answer = s.apply(self.reply(ticket))
        self.assertEqual(answer['receipt']['use_kind'], 'caller_declared_use')
        self.assertEqual(answer['receipt']['other_context'], ['current_chat'])
        self.assertFalse(answer['receipt']['semantic_certification'])
        self.assertEqual(s.episode.recall('C', ticket['as_of']), prior)
        self.assertEqual(json.loads(s.snapshot()[0])['journal'][:len(prefix)], prefix)
        self.assertEqual(s._verify(ticket), result['packet'])
        later = s.call('ゴビリン')['packet']
        self.assertIn(answer['receipt_event'], [r['id'] for r in later['references']])
        self.assertEqual(s.status()['engine']['phase'], 'UNBOUND')
        self.assertFalse(s.episode.status()['goals'][0]['semantic_certification'])

    def test_tampered_ticket_or_unavailable_declared_source_cannot_write(self):
        s = self.registered(); ticket = s.call('ゴビリン')['ticket']
        before = s.snapshot()
        wrong = dict(ticket, packet_sha256='0' * 64)
        for cmd in [self.reply(wrong), self.reply(ticket, used_sources=['not-delivered']),
                    self.reply(ticket, other_context=['invented_context'])]:
            with self.assertRaises(ValueError):
                s.apply(cmd)
            self.assertEqual(s.snapshot(), before)

    def test_missing_record_does_not_generate_a_memory_and_can_record_an_inquiry(self):
        s = self.fresh(); result = s.call('あのときのゴビリン')
        self.assertEqual(result['packet']['status'], 'NO_MATCH')
        self.assertEqual(result['packet']['references'], [])
        with self.assertRaises(ValueError):
            s.apply(self.reply(result['ticket']))
        response = s.apply(self.reply(result['ticket'], text='そのときの記録を渡してもらえる？',
                           used_sources=[], used_summary=False, other_context=['user_memory']))
        self.assertIsNone(response['receipt']['goal'])
        self.assertEqual(response['receipt']['other_context'], ['user_memory'])
        self.assertEqual(s.call('ゴビリン')['packet']['status'], 'NO_MATCH')

    def test_summary_only_and_other_context_are_separate_declarations(self):
        s = self.registered(); ticket = s.call('ゴビリン')['ticket']
        response = s.apply(self.reply(ticket, used_sources=[],
                           other_context=['user_memory', 'unknown']))
        self.assertTrue(response['receipt']['used_summary'])
        self.assertEqual(response['receipt']['used_sources'], [])
        self.assertEqual(response['receipt']['other_context'], ['user_memory', 'unknown'])

    def test_ordinary_e4_roundtrip_preserves_tickets_and_extended_records(self):
        s = self.registered(); ticket = s.call('ゴビリン')['ticket']
        s.apply(self.reply(ticket))
        raw, sha = s.snapshot()
        restored_episode = e4.Episode.restore(e2.Session(self.entry), raw, sha)
        restored = api.Recollection(restored_episode)
        self.assertEqual(restored.snapshot(), (raw, sha))
        self.assertEqual(restored._verify(ticket), s._verify(ticket))
        self.assertEqual(restored.call('ゴビリン'), s.call('ゴビリン'))
        self.assertTrue(restored_episode.recall('C')['events'])

    def test_reply_whitespace_unicode_and_crlf_are_lossless(self):
        s = self.registered(); ticket = s.call('ゴビリン')['ticket']
        body = '先頭' + ' ' * 298 + ('\r\n\t\u2003' * 75) + '末尾'
        result = s.apply(self.reply(ticket, text=body))
        current_ticket = s.call('ゴビリン')['ticket']
        joined = ''.join(s.read(current_ticket, k)['text'] for k in result['receipt']['parts'])
        self.assertEqual(joined, body)
        self.assertEqual(result['receipt']['text_sha256'], api.text_sha(body))
        raw, sha = s.snapshot()
        replay = api.Recollection(e4.Episode.restore(e2.Session(self.entry), raw, sha))
        self.assertEqual(replay.snapshot(), (raw, sha))

    def test_e4_budget_failure_leaves_no_partial_registration(self):
        s = self.seed(); before = s.snapshot()
        with patch.object(e4, 'MAX_COMMANDS', 3):
            with self.assertRaises(ValueError):
                s.apply(dict(op='register', id='gobirin', goal='C',
                             cues=['ゴビリン'], summary='要約'))
        self.assertEqual(s.snapshot(), before)
        self.assertEqual(s.status()['memories'], [])

    def test_mid_reply_failure_rolls_back_all_new_parts_and_allows_retry(self):
        s = self.registered(); ticket = s.call('ゴビリン')['ticket']; before = s.snapshot()
        original = e4.Episode.apply
        def fail_later(candidate, command):
            if command.get('id', '').endswith('-300'):
                raise ValueError('injected part failure')
            return original(candidate, command)
        with patch.object(e4.Episode, 'apply', fail_later):
            with self.assertRaises(ValueError):
                s.apply(self.reply(ticket, text='x' * 601))
        self.assertEqual(s.snapshot(), before)
        s.apply(self.reply(ticket, text='x' * 601))

    def test_snapshot_budget_failure_is_atomic(self):
        s = self.seed(); before = s.snapshot()
        with patch.object(e4, 'MAX_SNAPSHOT_BYTES', len(before[0]) + 10):
            with self.assertRaises(ValueError):
                s.apply(dict(op='register', id='gobirin', goal='C',
                             cues=['ゴビリン'], summary='要約'))
        self.assertEqual(s.snapshot(), before)

    def test_registered_summaries_cannot_be_overwritten(self):
        s = self.registered(); before = s.snapshot()
        for cmd in [dict(op='register', id='gobirin', goal='C', cues=['別名'], summary='書換え'),
                    dict(op='register', id='bad', goal='C', cues=[' '], summary='bad'),
                    dict(op='register', id='bad', goal='C', cues=['x', 'x'], summary='bad')]:
            with self.assertRaises(ValueError):
                s.apply(cmd)
            self.assertEqual(s.snapshot(), before)

    def test_original_monday_checkpoint_is_accepted_without_rewriting_it(self):
        case = json.loads((ROOT/'examples/recollection-gobirin.case.json').read_bytes())
        s = self.fresh()
        for record in case['records']:
            s.episode.apply(dict(op='record', **record))
        s.episode.apply(dict(op='goal', id=case['future_requirement']['id'],
                             text=case['future_requirement']['text'],
                             events=[r['id'] for r in case['records']]))
        s.episode.apply(dict(op='relate', goal=case['future_requirement']['id'],
                             events=case['interpretation']['events'],
                             note=case['interpretation']['note']))
        raw, sha = s.snapshot()
        self.assertEqual(sha, '570bd978e3e65c727ed2de4efeb5759c7864b06baf595f713778e190c4bf2434')
        restored = api.Recollection(e4.Episode.restore(e2.Session(self.entry), raw, sha))
        self.assertEqual(restored.snapshot(), (raw, sha))
        restored.apply(dict(op='register', id='gobirin', goal=case['future_requirement']['id'],
                            cues=['ゴビリン'], summary='既存の共有像への参照。'))
        self.assertEqual(len(restored.call('あのときのゴビリン')['packet']['references']), 7)

    def test_corrupted_e4_checkpoint_is_rejected(self):
        s = self.registered(); raw, sha = s.snapshot()
        altered = bytearray(raw); altered[len(altered)//2] ^= 1
        with self.assertRaises(ValueError):
            e4.Episode.restore(e2.Session(self.entry), bytes(altered), sha)

    def test_cli_resume_lookup_and_save_keeps_normal_e4_format(self):
        s = self.registered()
        work = ROOT / '.work'
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as temp:
            assert Path(temp).resolve().is_relative_to(work.resolve())
            raw, sha = s.snapshot()
            source, output = Path(temp)/'before.json', Path(temp)/'after.json'
            source.write_bytes(raw)
            commands = [dict(op='call', cue='あのときのゴビリン'),
                        dict(op='save', path=str(output)), dict(op='quit')]
            process = subprocess.run([sys.executable, '-I', '-B', str(ROOT/'run_recollection.py'),
                                      '--episode', str(source), '--trusted-episode-sha256', sha],
                                     input=b''.join(api.encode(c) for c in commands),
                                     capture_output=True, cwd=ROOT, timeout=120)
            self.assertEqual(process.returncode, 0, process.stderr)
            replies = [json.loads(line) for line in process.stdout.splitlines()]
            self.assertTrue(all(r['ok'] for r in replies), replies)
            self.assertEqual(replies[1]['packet']['status'], 'MATCH')
            self.assertEqual(output.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
