"""Fixed development demonstration, not an independent-AI behavior trial."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


class Client:
    def __init__(self, transcript, extra=()):
        self.transcript = transcript
        self.process = subprocess.Popen(
            [sys.executable, '-I', '-B', str(ROOT / 'run_recollection.py'), *extra],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.receive(None)

    def receive(self, command):
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError(self.process.stderr.read().decode('utf-8', 'replace'))
        response = json.loads(line)
        self.transcript.append(dict(command=command, response=response))
        if not response.get('ok'):
            raise RuntimeError(response)
        return response

    def send(self, command):
        self.process.stdin.write(json.dumps(command, ensure_ascii=True).encode() + b'\n')
        self.process.stdin.flush()
        return self.receive(command)

    def close(self):
        if self.process.poll() is None:
            self.send(dict(op='quit'))
            self.process.stdin.close()
        status = self.process.wait(timeout=30)
        if status:
            raise RuntimeError(self.process.stderr.read().decode('utf-8', 'replace'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=False, exist_ok=False)
    case = json.loads((ROOT / 'examples/recollection-gobirin.case.json').read_bytes())
    log = []
    client = Client(log)
    try:
        for record in case['records']:
            client.send(dict(op='record', **record))
        goal = case['future_requirement']
        client.send(dict(op='goal', id=goal['id'], text=goal['text'],
                         events=[r['id'] for r in case['records']]))
        client.send(dict(op='register', id='gobirin', goal=goal['id'], cues=['ゴビリン'],
                         summary='台所の相談へ転用され、共有幻想として語られたゴビリン。これは呼出し側の要約であり、元の発言は別に保持している。'))
        recalled = client.send(dict(op='call', cue='あのときのゴビリン、面白かったなｗ'))
        ticket = recalled['ticket']
        assert recalled['packet']['status'] == 'MATCH'
        assert len(recalled['packet']['references']) == 7
        seed = client.send(dict(op='read', ticket=ticket, event='seed'))
        witness = client.send(dict(op='read', ticket=ticket, event='witness'))
        saved = client.send(dict(op='save', path=str(out / 'ready-for-ai.episode.json')))
    finally:
        client.close()
    (out / 'packet.json').write_bytes(encode(recalled))
    (out / 'read-sources.json').write_bytes(encode([seed, witness]))
    ready = (out / 'ready-for-ai.episode.json').read_bytes()
    assert hashlib.sha256(ready).hexdigest() == saved['sha256']

    # A fixed driver supplies this sample text. A host AI supplies its own text
    # instead; the runtime never calls an LLM or claims that use was autonomous.
    body = ('あれなｗ　受け取った記録では「' + seed['text'] +
            '」という呼びかけから、台所にいる共有のゴビリンへ話が育っていたね。'
            '今の参照先は、その成立を語った発言の記録だよ。')
    client = Client(log, ['--episode', str(out / 'ready-for-ai.episode.json'),
                         '--trusted-episode-sha256', saved['sha256']])
    try:
        assert client.send(dict(op='call', cue='あのときのゴビリン、面白かったなｗ'))['ticket'] == ticket
        reply = client.send(dict(op='record_reply', id='example-next', ticket=ticket,
                            text=body, origin='reported_in_session',
                            source='fixed development driver; not an independent AI',
                            used_summary=True, used_sources=['seed', 'witness'],
                            other_context=['external']))
        later = client.send(dict(op='call', cue='ゴビリン'))
        after = client.send(dict(op='save', path=str(out / 'after-reply.episode.json')))
        assert client.send(dict(op='read', ticket=ticket, event='seed'))['text'] == seed['text']
    finally:
        client.close()
    cold = Client(log)
    try:
        no_match = cold.send(dict(op='call', cue='あのときのゴビリン、面白かったなｗ'))
        assert no_match['packet']['status'] == 'NO_MATCH'
    finally:
        cold.close()
    old = json.loads(ready)
    current = json.loads((out / 'after-reply.episode.json').read_bytes())
    assert current['journal'][:len(old['journal'])] == old['journal']
    assert reply['receipt_event'] in [r['id'] for r in later['packet']['references']]
    (out / 'sample-reply.txt').write_bytes((body + '\n').encode('utf-8'))
    (out / 'reply-receipt.json').write_bytes(encode(reply))
    (out / 'transcript.json').write_bytes(encode(log))
    result = dict(schema='recollection-first-use-result-v1', matched_sources=7,
                  ready_checkpoint_sha256=saved['sha256'],
                  after_reply_checkpoint_sha256=after['sha256'],
                  same_ticket_after_restart=True, old_journal_prefix_unchanged=True,
                  reply_linked_into_next_recall=True, missing_episode='NO_MATCH',
                  source_use='caller_declared_use', e1_math_phase='UNBOUND',
                  fixed_driver=True, independent_ai_behavior_test=False)
    (out / 'RESULT.json').write_bytes(encode(result))
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
