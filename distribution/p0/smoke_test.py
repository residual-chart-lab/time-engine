"""Run the candidate's thin CLI, save after one flower and resume to upper closure."""
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from verify_package import verify

SHA = 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
DIGEST = '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'


def run():
    integrity = verify()
    engine = ROOT/'engine'
    args = [sys.executable, '-I', str(engine/'run_time_engine.py'), '--entry',
            str(engine/'integrations/inquiry/E1-entry.record.json'),
            '--trusted-sha256', SHA, '--expected-entry-digest', DIGEST]
    def command_stream(commands, extra=()):
        result = subprocess.run([*args, *extra], input='\n'.join(json.dumps(x) for x in commands)+'\n',
                                cwd=ROOT, text=True, capture_output=True, check=True)
        rows = [json.loads(x) for x in result.stdout.splitlines()]
        if not rows or not all(x.get('ok') is True for x in rows):
            raise AssertionError('candidate CLI rejected its acceptance commands')
        return rows
    work = ROOT/'.work'; work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as temp:
        if not Path(temp).resolve().is_relative_to(work.resolve()):
            raise ValueError('temporary checkpoint outside candidate workspace')
        checkpoint = Path(temp)/'closed-first.json'
        block = [dict(op='bind', requirement=dict(context='mixed', strengths=['1/1024','1/1024'], frame='split')),
                 dict(op='choose', v='1', u='0', word='HHHSUT'), dict(op='resolve')]
        first = command_stream(block+block+[dict(op='advance'), dict(op='save',path=str(checkpoint)), dict(op='quit')])
        if first[0]['status']['phase'] != 'UNBOUND' or first[7]['status']['phase'] != 'CLOSED1':
            raise AssertionError('candidate did not stop after its first flower')
        first_reads = first[3]['status']['last_resolution_work']['total_exact_queries']
        repeated_reads = first[6]['status']['last_resolution_work']['total_exact_queries']
        if first_reads <= 0 or repeated_reads != 0:
            raise AssertionError('expected positive initial reads and zero extra reads on reuse')
        saved = next(x for x in first if 'saved' in x)
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != saved['sha256']:
            raise AssertionError('checkpoint bytes and external save response disagree')
        second = command_stream([dict(op='advance')]*3+[dict(op='quit')],
                                ['--resume', str(checkpoint), '--trusted-resume-sha256', saved['sha256']])
        if (second[0]['status']['phase'] != 'CLOSED1'
                or [x['status']['phase'] for x in second[1:4]] != ['CLOSED2','CLOSED3','STOPPED']
                or not second[-1]['status']['certified'] or second[-1]['status']['stock'] != 9):
            raise AssertionError('candidate recovery or upper closure failed')
    report = dict(schema='time-engine-p0-acceptance-v1', passed=True, integrity=integrity,
                  runtime=dict(python=platform.python_version(),system=platform.system(),platform=platform.platform()),
                  source_commit='1c185365bfcb2ea9f6c52c73ba263cf48c356d32',
                  initial_resolution_exact_reads=first_reads, repeated_resolution_exact_reads=repeated_reads,
                  saved_after='CLOSED1', resumed=True, phase='STOPPED', certified=True, stock=9,
                  executed_from_unpacked_candidate=True)
    (work/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2))
    return report


if __name__ == '__main__':
    run()
