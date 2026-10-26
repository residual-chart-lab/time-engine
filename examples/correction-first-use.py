"""Try question-dependent observation and receive its records through E4.

The default input is synthetic. Supply --case for a caller-owned actual case.
No observation is bound to E1, and no AI behavior effect is claimed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
DIGEST = '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'


def encode(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,indent=2)+'\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, default=ROOT/'examples/correction-relayed-case.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=False,exist_ok=False)
    reports = {}
    for focus in ('current_response','retained_basis','next_action'):
        destination = out/focus
        result = subprocess.run(
            [sys.executable,'-I','-B',str(ROOT/'run_correction_observer.py'),'--case',str(args.case),
             '--output-dir',str(destination),'--focus',focus],capture_output=True,text=True,check=True,timeout=30)
        reply = json.loads(result.stdout)
        if not reply['ok']: raise ValueError(reply)
        reports[focus] = json.loads((destination/'observation.json').read_bytes())
    source_indices = [r['source_index'] for r in reports.values()]
    assert all(v == source_indices[0] for v in source_indices)
    assert reports['current_response']['reading_plan']['source_ids'] != reports['retained_basis']['reading_plan']['source_ids']
    commands = (out/'retained_basis/E4-commands.jsonl').read_bytes()
    checkpoint = out/'received.episode.json'
    commands += (json.dumps(dict(op='save',path=str(checkpoint)))+'\n{"op":"quit"}\n').encode()
    call = [sys.executable,'-I','-B',str(ROOT/'run_event_session.py'),
            '--entry',str(ROOT/'integrations/inquiry/E1-entry.record.json'),'--trusted-sha256',SHA,
            '--expected-entry-digest',DIGEST]
    result = subprocess.run(call,input=commands,capture_output=True,check=True,timeout=60)
    replies = [json.loads(line) for line in result.stdout.splitlines()]
    assert all(row['ok'] for row in replies)
    (out/'E4-receive.jsonl').write_bytes(result.stdout)
    saved = next(row for row in replies if 'saved' in row)
    trusted = saved['sha256']
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == trusted
    status = replies[-1]['status']
    goal = status['goals'][0]['id']
    assert status['engine']['phase'] == 'UNBOUND'
    assert status['reads']['combined_exact_queries'] == 0
    assert status['goals'][0]['model_status'] == 'UNMAPPED'
    recovered = subprocess.run(call+['--resume',str(checkpoint),'--trusted-resume-sha256',trusted],
                               input=(json.dumps(dict(op='recall',goal=goal))+'\n{"op":"quit"}\n').encode(),
                               capture_output=True,check=True,timeout=60)
    checks = [json.loads(line) for line in recovered.stdout.splitlines()]
    assert all(row['ok'] for row in checks)
    assert checks[0]['status'] == status
    (out/'E4-recall.jsonl').write_bytes(recovered.stdout)
    summary = dict(
        schema='time-engine-correction-first-use-v1',
        input_sha256=hashlib.sha256(args.case.read_bytes()).hexdigest(),
        question_views={focus:dict(report_id=report['report_id'],
                                  reading_plan=report['reading_plan'],
                                  continuity=report['observations']['p']['continuity_evidence'])
                        for focus,report in reports.items()},
        same_source_archive=True,
        observation_plan_changed=True,
        e4_received=True, e4_replay_exact=True,
        e4_accepted_commands=status['accepted_commands'], e4_checkpoint_sha256=trusted,
        e4_phase=status['engine']['phase'], numerical_model_bound=False,
        next_action=reports['retained_basis']['reading_plan']['next_operation'],
        ai_behavior_effect_measured=False, semantic_judgments_verified=False)
    (out/'RESULT.json').write_bytes(encode(summary))
    print(json.dumps(dict(ok=True,output_dir=str(out),next_action=summary['next_action'],
                          same_source_archive=True,e4_replay_exact=True,e4_phase=summary['e4_phase'],
                          ai_behavior_effect_measured=False)))


if __name__ == '__main__':
    main()

