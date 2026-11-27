"""Create a new, entirely synthetic continuity notebook; never overwrite one."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if workspace.exists():
        raise SystemExit('Choose a new workspace; existing notes will not be overwritten.')
    workspace.parent.mkdir(parents=True, exist_ok=True)
    trace = []

    def call(*command):
        p = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(HERE / 'continuity.py'),
            '--workspace', str(workspace), *command], capture_output=True, text=True, encoding='utf-8', timeout=90)
        trace.append(dict(args=list(command), returncode=p.returncode, stdout=p.stdout, stderr=p.stderr))
        if p.returncode:
            raise RuntimeError(p.stdout + p.stderr)
        return json.loads(p.stdout)['result']

    call('init', '--backend', str(HERE / 'open_use/te_use.py'), '--work', 'Synthetic continuity demonstration')
    source = workspace.parent / ('synthetic-input-' + uuid.uuid4().hex + '.jsonl')
    messages = ['DEMO START: invented observations, no real conversation data.']
    messages.extend('Synthetic observation ' + str(i) for i in range(2, 29))
    messages[23:26] = [
        '舞台係「入口の札は『合図をお待ちください』でどうでしょう」',
        '受付係「『合図があるまで、ここでお待ちください』にしましょう」',
        '進行係「受付係の文に決めます。札はすりガラスの手前に置きます」',
    ]
    messages.append('Synthetic scene.\n僕は黙って手帳を閉じた。案内係は入口を指し、同行者は椅子を寄せている。\nEnd of synthetic scene.')
    with source.open('x', encoding='utf-8', newline='\n') as stream:
        for text in messages:
            row = dict(type='response_item', timestamp='2026-11-19T00:00:00Z',
                payload=dict(type='message', role='user', content=[dict(type='input_text', text=text)]))
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    call('capture', '--session', str(source), '--start-marker', 'DEMO START')
    definitions = [
        ('continuity-choice-01', 'choice', 'current-work', ['s000001'], dict(reading='Initial synthetic work choice.')),
        ('demo-reading', 'reading', 'reading', ['s000029'], dict(reading='A fictional narrator closes a notebook while two others move near a doorway. This is a paraphrase, not a direct quotation.')),
        ('demo-memory', 'flower', 'memory', ['s000029'], dict(memory_owner='fictional narrator', reading='An invented room and three figures; not an AI subjective-memory claim.')),
        ('demo-candidate', 'candidate', 'candidate', ['s000001'], dict(status='unclassified', reason=None)),
        ('demo-outcome', 'outcome', 'last-outcome', ['s000025', 's000026'], dict(reading='The team chose the wording for the entrance sign.')),
        ('demo-next', 'choice', 'current-work', ['s000001'], dict(reading='Continue from the current packet and retrieve exact originals only as needed.')),
    ]
    for identifier, kind, slot, sources, payload in definitions:
        value = dict(id=identifier, kind=kind, actor='synthetic-author', actor_role='main',
            reading_time='current', sources=sources, links=['continuity-choice-01'] if identifier == 'demo-next' else [],
            slot=slot, adoption='adopt', payload=payload)
        if identifier == 'demo-outcome':
            value['decision_bookmark'] = dict(state='adopted', proposal='s000025', decision='s000026')
        file = workspace / (identifier + '.request.json')
        file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        call('note', '--file', str(file))
    packet = call('resume')
    original = call('source', '--id', 's000029')
    assert original['text'] == messages[-1]
    (workspace / 'DEMO_TRACE.json').write_text(json.dumps(trace, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(created=True, synthetic=True, sources=packet['inventory']['sources'],
        current_records=len(packet['records']), raw_id=original['id'], raw_sha256=original['sha256'],
        pending=packet['inventory']['pending'], workspace=str(workspace)), ensure_ascii=False))


if __name__ == '__main__':
    main()
