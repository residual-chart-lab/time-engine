"""A real E4 CLI round trip; the E1 correspondence is explicitly supplied.

No persona or natural-language feature is numerically encoded by this example.
The broad conversational goal stays UNMAPPED. The numeric question is real.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT/'integrations/inquiry/E1-entry.record.json'
SHA = 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
DIGEST = '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'
ARGS = [sys.executable, '-I', '-B', str(ROOT/'run_event_session.py'),
        '--entry', str(ENTRY), '--trusted-sha256', SHA, '--expected-entry-digest', DIGEST]


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='new output directory')
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=False, exist_ok=False)
    transcript = []
    process = None

    def start(extra=()):
        nonlocal process
        process = subprocess.Popen(ARGS+list(extra), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding='utf-8')
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(process.stderr.read())
        result = json.loads(line)
        transcript.append(dict(response=result))
        if not result['ok']:
            raise RuntimeError(result)
        return result

    def send(command, ok=True):
        process.stdin.write(json.dumps(command)+'\n'); process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(process.stderr.read())
        result = json.loads(line)
        transcript.append(dict(command=command, response=result))
        if result['ok'] is not ok:
            raise RuntimeError(result)
        return result

    def stop():
        send(dict(op='quit'))
        _, error = process.communicate(timeout=30)
        if process.returncode:
            raise RuntimeError(error)

    try:
        start()
        send(dict(op='record', id='prior', origin='received', source='illustrative imported report, not an original transcript',
                  text='An earlier participant revised a mistaken question while retaining the reason for asking.'))
        send(dict(op='record', id='question', origin='reported_in_session', source='this demonstration caller',
                  text='May the fixed E1 coordinate s be omitted while preserving this continuation?'))
        send(dict(op='goal', id='continuation', text='Preserve the declared model continuation construction', events=['question']))
        initial = send(dict(op='goal', id='commitment', text='Carry the adopted commitment into later dialogue',
                            events=['prior', 'question']))
        horizon = initial['status']['accepted_commands']
        then = send(dict(op='recall', goal='commitment', as_of=horizon))['recall']
        send(dict(op='bind', goal='continuation',
                  requirement=dict(context='mixed', strengths=['0','0'], frame='identity'),
                  coordinates={'s': ['question']},
                  correspondence='This question explicitly refers to the already authenticated E1 coordinate s. '
                                 'The event text supplies no numerical values and is not a personality measurement.'))
        send(dict(op='choose', v='1', u='0', word='HHHSUT'))
        inspection = send(dict(op='inspect', omitted=['s']))
        diagnostic = inspection['outcome']['report']
        assert diagnostic['current']['equal']
        assert diagnostic['requested']['relation'] == 'DIFFERENT_EXISTENCE'
        send(dict(op='resolve', inspection=inspection['outcome']['id'], retention='erase'), ok=False)
        r = send(dict(op='resolve', inspection=inspection['outcome']['id'], retention='preserve'))
        r = send(dict(op='advance', permit=r['status']['permit']))
        assert r['status']['engine']['phase'] == 'CLOSED1'
        saved = send(dict(op='save', path=str(out/'closed1.episode.json')))
        assert hashlib.sha256((out/'closed1.episode.json').read_bytes()).hexdigest() == saved['sha256']
        stop()

        r = start(['--resume', str(out/'closed1.episode.json'), '--trusted-resume-sha256', saved['sha256']])
        for _ in range(3):
            r = send(dict(op='advance', permit=r['status']['permit']))
        assert r['status']['engine']['certified'] and r['status']['engine']['phase'] == 'STOPPED'
        send(dict(op='record', id='reflection', origin='reported_in_session', source='this demonstration caller',
                  text='The numerical omission was refused for a scoped reason, not merely because preserving everything is good.'))
        send(dict(op='relate', goal='commitment', events=['question','reflection'],
                  note='This later observation may inform a later question. It does not certify understanding or identity.'))
        later = send(dict(op='recall', goal='commitment'))['recall']
        then_again = send(dict(op='recall', goal='commitment', as_of=horizon))['recall']
        assert then_again == then
        final_save = send(dict(op='save', path=str(out/'final.episode.json')))
        final = final_save['status']
        assert final['episode'] == 'OPEN'
        assert all(g['status'] == 'OPEN' and not g['semantic_certification'] for g in final['goals'])
        assert next(g for g in final['goals'] if g['id'] == 'commitment')['model_status'] == 'UNMAPPED'
        stop()
        assert hashlib.sha256(ENTRY.read_bytes()).hexdigest() == SHA
        with (out/'transcript.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
            for row in transcript:
                stream.write(json.dumps(row, ensure_ascii=True, separators=(',',':'))+'\n')
        write(out/'then-known.json', then)
        write(out/'later-recall.json', later)
        summary = dict(schema='time-engine-event-bridge-example-v1',
                       current_endpoints_equal=diagnostic['current']['equal'],
                       original_status=diagnostic['requested']['original_status'],
                       projected_status=diagnostic['requested']['projected_status'],
                       relation=diagnostic['requested']['relation'],
                       actual_engine=final['engine'], exact_queries=final['reads'],
                       outer_episode=final['episode'], goals=final['goals'],
                       then_known_view_unchanged=True, checkpoint_sha256=final_save['sha256'],
                       intermediate_checkpoint_sha256=saved['sha256'],
                       mapping='caller-declared reference to existing E1 s; no text/persona encoding',
                       semantic_goal_certified=False)
        write(out/'RESULT.json', summary)
        print(json.dumps(summary, ensure_ascii=True, separators=(',',':')))
    finally:
        if process is not None and process.poll() is None:
            process.kill(); process.communicate()


if __name__ == '__main__':
    main()

