"""Run route -> finite choice -> request -> original arrival -> revised choice.

This is a fixed development driver. No independent AI is launched or simulated.
All response execution uses the unchanged source-reply-v1 action generator.
"""
import argparse
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import woven_action as wa

REQ = dict(target='retained_basis', question='訂正後も保持されたという根拠を、前後の原文と訂正箇所で示してください。')
NOW = dict(target='current_response', question='What does the current record answer?')


def fixture(env):
    case = json.loads(Path(__file__).with_name('case.json').read_bytes())
    model = env.api.compile_model(case)
    memory = wa.fresh_memory(env)
    mapping = {}
    for source in case['sources']:
        key = 'src-' + source['id']
        memory.apply(dict(op='record', id=key, origin=source['origin'], source=source['location'], text=source['text']))
        mapping[key] = source['id']
    memory.apply(dict(op='goal', id='C-basis', text=REQ['question'], events=list(mapping)))
    for event in mapping:
        env.weave.passage(memory, 'mark-' + event, event, 'Synthetic fixture; original event time unknown.')
    env.weave.step(memory, 'source-link-1', 'C-basis', 'src-before', 'src-correction', 'Supplied correction-case chronology.')
    env.weave.step(memory, 'source-link-2', 'C-basis', 'src-correction', 'src-after', 'Supplied correction-case chronology.')
    env.weave.thread(memory, 'full-route', 'C-basis', 'src-before', 'src-after', 'Retain before, correction, after.')
    env.weave.thread(memory, 'short-route', 'C-basis', 'src-correction', 'src-after', 'Recipient omits the before source.')
    memory.apply(dict(op='register', id='basis', goal='C-basis', cues=['保持根拠'],
                      summary='固定された出典契約について、訂正前・訂正・訂正後の原文を辿る。開発用作例。'))
    return wa.Bridge(env, memory, model, mapping, 'C-basis', REQ)


def send(receiver, command, trace):
    value = receiver.apply(command)
    trace.append(dict(command=deepcopy(command), response=deepcopy(value)))
    return value


def execute(receiver, kind, trace, role=None):
    options = [p for p in receiver.status()['plans'] if p['kind'] == kind]
    if role is not None:
        options = [p for p in options if p.get('role') == role]
    if kind == 'answer':
        options = [p for p in options if p['style'] == 'account_first']
    if not options:
        raise ValueError('no requested enabled action; do not repair the condition')
    send(receiver, dict(op='choose', plan=options[0]['id']), trace)
    prepared = send(receiver, dict(op='resolve'), trace)
    return send(receiver, dict(op='advance', permit=prepared['status']['permit']), trace)


def save_pair(bridge, receiver, path):
    raw, trusted = bridge.snapshot(receiver)
    with path.open('xb') as stream:
        stream.write(raw)
    return trusted


def run(env, out):
    out.mkdir(parents=True, exist_ok=False)
    bridge = fixture(env)
    owner_initial, owner_initial_sha = bridge.memory.snapshot()
    branches, results, traces, receivers = {}, {}, {}, {}
    projections = {}
    for name, thread in [('retained', 'full-route'), ('omitted', 'short-route')]:
        projection = bridge.project(thread, '保持根拠')
        projections[name] = projection
        receiver = env.api.Session(projection['bundle'], wa.fresh_episode(env))
        trace = []
        send(receiver, dict(op='bind', requirement=NOW), trace)
        current = execute(receiver, 'answer', trace)
        bound = send(receiver, dict(op='bind', requirement=REQ), trace)
        results[name] = dict(current=current['result'], future_options=bound['status']['plans'])
        traces[name] = trace
        receivers[name] = receiver
    assert results['retained']['current']['reply']['body'] == results['omitted']['current']['reply']['body']
    assert len(receivers['retained'].status()['admissible_answers']) == 2
    assert len(receivers['omitted'].status()['admissible_answers']) == 0

    kept = execute(receivers['retained'], 'answer', traces['retained'])
    branches['retained'], _ = bridge.record_action(receivers['retained'], 'retained-answer', 'src-after')
    kept_sha = save_pair(branches['retained'], receivers['retained'], out / 'retained.pair.json')

    asked = execute(receivers['omitted'], 'ask', traces['omitted'], role='before')
    branches['omitted'], _ = bridge.record_action(receivers['omitted'], 'missing-source-request', 'src-after')
    asked_sha = save_pair(branches['omitted'], receivers['omitted'], out / 'after-request.pair.json')
    previous_view = env.weave.view(branches['omitted'].memory, 'short-route')
    previous_commands = deepcopy(receivers['omitted'].commands)
    previous_closed = deepcopy(receivers['omitted'].closed)

    # Explicit original arrival from the retained archive, after the request.
    arrived_bridge, arrived_actor, witness = branches['omitted'].arrive(
        receivers['omitted'], 'full-route', '保持根拠', 'before', 'original-arrival', 'missing-source-request')
    traces['omitted'].append(dict(command=deepcopy(arrived_actor.commands[-1]),
                                   response=witness['supply_response'], execution='staged_source_runtime_supply'))
    assert receivers['omitted'].commands == previous_commands
    assert witness['active']['comparison']['panel_crossed'] is True
    assert witness['current_window']['comparison']['panel_crossed'] is False
    # Supply invalidates the old choice/permit. A new bind and choice are needed.
    assert arrived_actor.status()['phase'] == 'UNBOUND'
    rebound = send(arrived_actor, dict(op='bind', requirement=REQ), traces['omitted'])
    answered = execute(arrived_actor, 'answer', traces['omitted'])
    final_bridge, _ = arrived_bridge.record_action(arrived_actor, 'after-arrival-answer', 'original-arrival')
    env.weave.thread(final_bridge.memory, 'operation-route', 'C-basis', 'src-after', 'after-arrival-answer',
                     'Actual request, source arrival, and executed answer, with separate source/runtime receipts.')
    final_sha = save_pair(final_bridge, arrived_actor, out / 'after-answer.pair.json')
    final_bridge, final_actor = wa.Bridge.restore(env, (out / 'after-answer.pair.json').read_bytes(), final_sha)
    route = env.weave.view(final_bridge.memory, 'operation-route')
    assert route['boundary_events'] == ['original-arrival']
    assert answered['result']['reply'] == kept['result']['reply']
    assert final_actor.closed[:len(previous_closed)] == previous_closed
    assert final_actor.commands[:len(previous_commands)] == previous_commands
    assert env.weave.view(final_bridge.memory, 'short-route', previous_view['as_of']) == previous_view
    assert bridge.memory.snapshot() == (owner_initial, owner_initial_sha)
    assert branches['omitted'].snapshot(receivers['omitted'])[1] == asked_sha
    assert asked['result']['certificate']['contract_satisfied'] is False
    assert answered['result']['certificate']['contract_satisfied'] is True
    answer_counts = dict(retained=2, omitted=0, after_arrival=len(rebound['status']['admissible_answers']))
    assert answer_counts['after_arrival'] == 2
    result = dict(schema=wa.SCHEMA + '-demo-result', status='PASS',
                  same_current_reply=True, answer_counts=answer_counts,
                  actual_first_omitted_action='ask', actual_final_action='answer',
                  request_satisfies_answer_contract=False, answer_satisfies_answer_contract=True,
                  basis_window_boundary=True, current_window_boundary=False,
                  distance_law=wa.LAW, threshold=[1, 2],
                  old_source_commands_preserved=True, old_closed_request_preserved=True,
                  old_view_after_restore_unchanged=True, original_archive_unchanged=True,
                  final_reply_matches_retained=True, historical_projection_verified_on_restore=True,
                  checkpoints=dict(retained=kept_sha, after_request=asked_sha, after_answer=final_sha),
                  e4_owner_commands=final_bridge.memory.status()['accepted_commands'],
                  source_commands=len(final_actor.commands),
                  e4_source_commands=final_actor.status()['e4_accepted_commands'],
                  e1_phase=final_bridge.memory.status()['engine']['phase'],
                  fixed_development_driver=True, independent_ai_trial=False,
                  subjective_duration=None, outer_flower_closed=False)
    for name, value in [('RESULT.json', result), ('projections.json', projections),
                        ('branch-results.json', results), ('boundary-witness.json', witness),
                        ('operation-route.json', route), ('retained-trace.json', traces['retained']),
                        ('omitted-trace.json', traces['omitted'])]:
        (out / name).write_bytes(wa.encode(value))
    (out / 'request.txt').write_text(asked['result']['reply']['body'] + '\n', encoding='utf-8')
    (out / 'answer.txt').write_text(answered['result']['reply']['body'] + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    log = io.StringIO()
    with redirect_stdout(log):
        env = wa.environment(args.runtime_root)
        result = run(env, args.output_dir.resolve())
    (args.output_dir / 'runtime-import.txt').write_text(log.getvalue(), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
