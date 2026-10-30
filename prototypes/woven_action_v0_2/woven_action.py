"""Connect declared E4 routes to the unchanged finite source-reply action family.

No source is inferred from text similarity. A compiled model and explicit slot
mapping bind the original text hashes. Choices remain with the caller.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

SCHEMA = 'time-engine-woven-action-prototype-v0.2'
LAW = 'source-reply-candidate-set-window-v1'
MAX_SNAPSHOT_BYTES = 12_000_000
ADAPTER_SHA = '1646975df28daa4cc90851ba7a16ff761910216092c9a33de6d08e53928938ce'


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment(runtime_root):
    root = Path(runtime_root).resolve()
    adapter = Path(__file__).with_name('woven_time_v0_1.py')
    if hashlib.sha256(adapter.read_bytes()).hexdigest() != ADAPTER_SHA:
        raise ValueError('the v0.1 route adapter changed')
    weave = _load('woven_route_v01', adapter)
    runtime = _load('woven_recollection_runtime', root / 'run_recollection.py')
    import source_reply
    if Path(source_reply.__file__).resolve() != root / 'integrations/inquiry/source_reply.py':
        raise ValueError('source runtime loaded from a different tree')
    return SimpleNamespace(root=root, weave=weave, runtime=runtime, api=source_reply)


def fresh_episode(env):
    r = env.runtime
    return r.Episode.receive(r.ENTRY.read_bytes(), r.ENTRY_SHA, r.ENTRY_DIGEST)


def fresh_memory(env):
    return env.runtime.Recollection(fresh_episode(env))


def clone_memory(env, memory):
    raw, trusted = memory.snapshot()
    return env.runtime.Recollection(env.runtime.Episode.restore(fresh_episode(env)._session, raw, trusted))


def clone_receiver(env, receiver):
    raw, trusted = receiver.snapshot()
    return env.api.Session.restore(receiver.initial, fresh_episode(env), raw, trusted)


def capacity(env, model, packet, requirement):
    """Construction candidates under fixed C; not current phase/permit status."""
    req = env.api.requirement(requirement)
    candidates = env.api.plans(model, packet, req)
    return dict(law=LAW, family=env.api.FAMILY, contract=env.api.digest(env.api.CONTRACT),
                model=model['digest'], requirement=req, requirement_digest=env.api.digest(req),
                packet=deepcopy(packet),
                fingerprints=sorted(p['fingerprint'] for p in candidates),
                answer_fingerprints=sorted(p['fingerprint'] for p in candidates if p['kind'] == 'answer'))


def compare(before, after):
    """A declared finite window, with discrete distance and delta = 1/2.

    It counts a change of candidate equivalence class, not seconds or a model's
    subjective duration. A change of C is an incomparable scope, not aging.
    """
    fields = ('law', 'family', 'contract', 'model', 'requirement', 'requirement_digest')
    if any(before.get(k) != after.get(k) for k in fields):
        return dict(law=LAW, relation='INCOMPARABLE_SCOPE', distance=None, delta=[1, 2],
                    panel_crossed=None, subjective_duration=None)
    old, new = set(before['fingerprints']), set(after['fingerprints'])
    changed = old != new
    return dict(law=LAW, relation='CHANGED' if changed else 'SAME',
                family=before['family'], contract=before['contract'], model=before['model'],
                requirement_digest=before['requirement_digest'],
                before_packet=before['packet']['digest'], after_packet=after['packet']['digest'],
                before_answers=len(before['answer_fingerprints']), after_answers=len(after['answer_fingerprints']),
                added=sorted(new - old), removed=sorted(old - new),
                distance=[int(changed), 1], delta=[1, 2], panel_crossed=changed,
                subjective_duration=None, semantic_certification=False, e1_permit_issued=False)


def verify_observation(env, model, observation):
    rebuilt = []
    for label in ('before', 'after'):
        value = observation[label]
        actual = capacity(env, model, value['packet'], value['requirement'])
        if actual != value:
            raise ValueError('candidate observation does not match the fixed generator')
        rebuilt.append(actual)
    if compare(*rebuilt) != observation['comparison']:
        raise ValueError('boundary observation changed')
    return True


def arrival_receipt(evidence):
    return dict(schema=evidence['schema'], event_id=evidence['event_id'], source=evidence['source'],
                source_command_index=evidence['source_command_index'],
                source_before_sha256=evidence['source_before_sha256'],
                source_after_sha256=evidence['source_after_sha256'],
                projection_sha256=sha(evidence['projection']),
                comparison=evidence['active']['comparison'],
                current_window=evidence['current_window']['comparison'],
                current_window_is_readonly=True, construction_change_not_execution_permit=True)


def execution_receipt(env, requirement, result, state_sha):
    return dict(schema=SCHEMA + '-executed-action', source_state_sha256=state_sha,
                family=env.api.FAMILY, requirement=deepcopy(requirement),
                operation=result['reply']['operation'], body=result['reply']['body'],
                certificate=result['certificate'], outer_flower_closed=False, semantic_certification=False)


class Bridge:
    def __init__(self, env, memory, model, source_map, goal, requirement, boundaries=()):
        env.api.verify_model(model)
        req = env.api.requirement(requirement)
        events = {e['id']: e for e in memory.episode.status()['events']}
        if (type(source_map) is not dict or not source_map
                or any(type(k) is not str or type(v) is not str for k, v in source_map.items())
                or not set(source_map) <= set(events)
                or set(source_map.values()) != set(model['sources'])
                or len(set(source_map.values())) != len(source_map)):
            raise ValueError('explicit one-to-one event-to-source-slot map required')
        originals = {slot: events[event]['text'] for event, slot in source_map.items()}
        env.api.packet(model, originals)  # Exact frozen length and text hash.
        for event, slot in source_map.items():
            if events[event]['origin'] != model['sources'][slot]['origin']:
                raise ValueError('source origin differs from the frozen model')
        recalled = memory.episode.recall(goal)
        if recalled['goal']['text'] != req['question']:
            raise ValueError('explicit goal/question binding required')
        if not set(source_map) <= {e['id'] for e in recalled['events']}:
            raise ValueError('all declared slots must belong to this goal')
        self.env, self.memory = env, memory
        self.model, self.source_map = deepcopy(model), deepcopy(source_map)
        self.goal, self.requirement = goal, req
        self.boundaries = deepcopy(list(boundaries))

    def clone(self):
        return Bridge(self.env, clone_memory(self.env, self.memory), self.model,
                      self.source_map, self.goal, self.requirement, self.boundaries)

    def project(self, thread_id, cue, horizon=None, resolution='all'):
        env = self.env
        view = env.weave.view(self.memory, thread_id, horizon, resolution)
        if view['goal']['id'] != self.goal or view['route_status'] != 'CONNECTED':
            raise ValueError('a connected route for the bound goal is required')
        recalled = self.memory.call(cue, horizon=view['as_of'])
        reads = env.weave.read_plan(self.memory, view, recalled)
        texts, refs = {}, []
        for command in reads:
            event = command['event']
            if event not in self.source_map:
                raise ValueError('route contains an event outside the frozen source-slot map')
            value = self.memory.apply(command)
            slot = self.source_map[event]
            texts[slot] = value['text']
            refs.append(dict(event=event, slot=slot, origin=value['event']['origin'],
                             text_sha256=value['text_sha256']))
        bundle = dict(schema=env.api.FAMILY + '-bundle', model=deepcopy(self.model),
                      packet=env.api.packet(self.model, texts))
        return dict(bundle=bundle, route=view,
                    provenance=dict(schema=SCHEMA + '-projection', goal=self.goal, thread=thread_id,
                                    requirement_digest=env.api.digest(self.requirement),
                                    model=self.model['digest'], as_of=view['as_of'],
                                    route_sha256=view['route_sha256'], ticket=recalled['ticket'],
                                    source_refs=refs, source_mapping='caller_declared_exact_slots'))

    def _record(self, key, value, predecessor=None, boundary=False):
        body = encode(value).decode().rstrip('\n')
        self.memory.apply(dict(op='record', id=key, origin='reported_in_session',
            source=encode(dict(schema=SCHEMA, kind='computed_finite_family_receipt')).decode().strip(), text=body))
        self.memory.apply(dict(op='relate', goal=self.goal, events=[key],
                               note='Computed source-family evidence; E1 remains separate.'))
        self.env.weave.passage(self.memory, 'mark-' + key, key,
            'The finite candidate-set window supplies this boundary flag; not subjective duration.',
            boundary=boundary)
        if predecessor is not None:
            self.env.weave.step(self.memory, 'link-' + key, self.goal, predecessor, key,
                                'Observed operation sequence in this integration run.')

    def record_action(self, receiver, key, predecessor=None):
        """Record an already executed source action; the finite reply is replayed."""
        receiver = clone_receiver(self.env, receiver)
        if (not receiver.closed or receiver.model != self.model or receiver.req != self.requirement
                or receiver.phase != 'CLOSED' or receiver.commands[-1].get('op') != 'advance'):
            raise ValueError('executed action in this exact model/C required')
        result = receiver.closed[-1]
        self.env.api.verify_reply(self.model, receiver.available, self.requirement, result['reply'])
        _, state_sha = receiver.snapshot()
        value = execution_receipt(self.env, self.requirement, result, state_sha)
        candidate = self.clone()
        candidate._record(key, value, predecessor)
        return candidate, value

    def arrive(self, receiver, full_thread, cue, source, key, predecessor=None):
        """Stage both ledgers; a failed owner write leaves both borrowed states intact."""
        env = self.env
        if receiver.model != self.model or receiver.req != self.requirement:
            raise ValueError('recipient must be bound to this exact model/C')
        projection = self.project(full_thread, cue)
        texts = projection['bundle']['packet']['texts']
        if type(source) is not str or source not in texts:
            raise ValueError('requested original must be present on the supplied route')
        before_raw, before_sha = receiver.snapshot()
        staged = clone_receiver(env, receiver)
        before = capacity(env, self.model, staged.available, self.requirement)
        supply_response = staged.apply(dict(op='supply', source=source, text=texts[source]))
        after = capacity(env, self.model, staged.available, self.requirement)
        after_raw, after_sha = staged.snapshot()
        active = dict(before=before, after=after, comparison=compare(before, after))
        current_req = dict(target='current_response', question='What does the current record answer?')
        c0 = capacity(env, self.model, receiver.available, current_req)
        c1 = capacity(env, self.model, staged.available, current_req)
        current_window = dict(before=c0, after=c1, comparison=compare(c0, c1))
        evidence = dict(schema=SCHEMA + '-arrival-witness', event_id=key, source=source,
                        source_command_index=len(staged.commands),
                        source_before_sha256=before_sha, source_after_sha256=after_sha,
                        projection=projection['provenance'], active=active,
                        current_window=current_window, current_window_is_readonly=True,
                        supply_response=supply_response)
        verify_observation(env, self.model, active)
        verify_observation(env, self.model, current_window)
        receipt = arrival_receipt(evidence)
        owner = self.clone()
        owner._record(key, receipt, predecessor, boundary=active['comparison']['panel_crossed'])
        owner.boundaries.append(evidence)
        owner.snapshot(staged)  # Preflight the combined checkpoint before adoption.
        assert receiver.snapshot() == (before_raw, before_sha)
        assert staged.snapshot() == (after_raw, after_sha)
        return owner, staged, evidence

    def snapshot(self, receiver):
        if receiver.model != self.model:
            raise ValueError('matching receiver model required')
        owner, _ = self.memory.snapshot()
        actor, _ = receiver.snapshot()
        value = dict(schema=SCHEMA + '-pair', config=dict(model=self.model, source_map=self.source_map,
                    goal=self.goal, requirement=self.requirement), memory=json.loads(owner),
                    receiver=json.loads(actor), boundaries=self.boundaries)
        raw = encode(value)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            raise ValueError('combined prototype checkpoint budget exceeded')
        return raw, hashlib.sha256(raw).hexdigest()

    @classmethod
    def restore(cls, env, raw, trusted):
        if (type(raw) is not bytes or len(raw) > MAX_SNAPSHOT_BYTES
                or hashlib.sha256(raw).hexdigest() != trusted):
            raise ValueError('bounded combined checkpoint and externally trusted SHA required')
        value = json.loads(raw)
        if (type(value) is not dict or set(value) != {'schema', 'config', 'memory', 'receiver', 'boundaries'}
                or value['schema'] != SCHEMA + '-pair' or type(value['boundaries']) is not list
                or len(value['boundaries']) > 32):
            raise ValueError('complete bounded pair checkpoint required')
        # E4 canonical encoding is intentionally different; use its own encoder.
        import event_bridge
        owner_raw = event_bridge.encode(value['memory'])
        memory = env.runtime.Recollection(env.runtime.Episode.restore(
            fresh_episode(env)._session, owner_raw, hashlib.sha256(owner_raw).hexdigest()))
        actor_raw = env.api.obs.encode(value['receiver'])
        receiver = env.api.Session.restore(value['receiver']['initial'], fresh_episode(env),
                    actor_raw, hashlib.sha256(actor_raw).hexdigest())
        config = value['config']
        if type(config) is not dict or set(config) != {'model', 'source_map', 'goal', 'requirement'}:
            raise ValueError('complete explicit binding required')
        result = cls(env, memory, **config, boundaries=value['boundaries'])
        if receiver.model != result.model:
            raise ValueError('receiver family differs from the bound model')
        event_ids, indices = set(), set()
        stored = {e['id']: e for e in result.memory.episode.status()['events']}
        computed_arrivals, executed = set(), []
        for event in stored.values():
            try:
                meta = json.loads(event['source'])
            except (TypeError, ValueError):
                continue
            if (type(meta) is not dict or meta.get('schema') != SCHEMA
                    or meta.get('kind') != 'computed_finite_family_receipt'):
                continue
            payload = json.loads(event['text'])
            if type(payload) is not dict:
                raise ValueError('complete computed receipt required')
            if payload.get('schema') == SCHEMA + '-arrival-witness':
                computed_arrivals.add(event['id'])
            elif payload.get('schema') == SCHEMA + '-executed-action':
                executed.append(payload)
            else:
                raise ValueError('unsupported computed receipt schema')
        if computed_arrivals != {w['event_id'] for w in result.boundaries}:
            raise ValueError('computed arrival receipts and boundary witnesses must match both ways')
        # Computed action receipts also refer to a real completed source prefix,
        # not merely an opaque statement stored in an otherwise valid E4 log.
        wanted = {r['source_state_sha256'] for r in executed}
        verified_actions = {}
        if wanted:
            replay_actions = env.api.Session(receiver.initial, fresh_episode(env))
            for command in receiver.commands:
                replay_actions.apply(command)
                _, state_sha = replay_actions.snapshot()
                if state_sha in wanted and command['op'] == 'advance' and replay_actions.phase == 'CLOSED':
                    verified_actions[state_sha] = execution_receipt(
                        env, replay_actions.req, replay_actions.closed[-1], state_sha)
            if any(verified_actions.get(r['source_state_sha256']) != r for r in executed):
                raise ValueError('computed action receipt differs from the executed source prefix')
        # Reconstruct every claimed arrival from the source engine's real prefix.
        for witness in result.boundaries:
            index = witness['source_command_index']
            if type(index) is not int or not 1 <= index <= len(receiver.commands):
                raise ValueError('recorded source operation index required')
            key = witness['event_id']
            if key in event_ids or index in indices:
                raise ValueError('one boundary receipt per actual arrival required')
            event_ids.add(key); indices.add(index)
            replay = env.api.Session(receiver.initial, fresh_episode(env))
            for command in receiver.commands[:index - 1]:
                replay.apply(command)
            _, before_sha = replay.snapshot()
            before_packet = deepcopy(replay.available)
            if (replay.req != result.requirement or witness['active']['before']['requirement'] != replay.req
                    or witness['active']['after']['requirement'] != replay.req):
                raise ValueError('active boundary must use the actually bound source requirement')
            command = receiver.commands[index - 1]
            if command.get('op') != 'supply' or command.get('source') != witness['source']:
                raise ValueError('boundary must refer to the recorded supply operation')
            provenance = witness['projection']
            if (key not in stored or type(provenance['as_of']) is not int
                    or provenance['as_of'] != stored[key]['seq'] - 1):
                raise ValueError('projection horizon must be immediately before its arrival receipt')
            projected = result.project(provenance['thread'], provenance['ticket']['cue'], provenance['as_of'])
            if (projected['provenance'] != provenance or command['text'] !=
                    projected['bundle']['packet']['texts'].get(witness['source'])):
                raise ValueError('arrival no longer matches the historical route/source read')
            supply_response = replay.apply(command)
            _, after_sha = replay.snapshot()
            if (before_sha != witness['source_before_sha256'] or after_sha != witness['source_after_sha256']
                    or witness['active']['before']['packet'] != before_packet
                    or witness['active']['after']['packet'] != replay.available
                    or supply_response != witness['supply_response']):
                raise ValueError('boundary detached from actual source-state transition')
            verify_observation(env, result.model, witness['active'])
            verify_observation(env, result.model, witness['current_window'])
            if (witness['current_window']['before']['packet'] != before_packet
                    or witness['current_window']['after']['packet'] != replay.available):
                raise ValueError('read-only window refers to another transition')
            current_req = dict(target='current_response', question='What does the current record answer?')
            if any(witness['current_window'][label]['requirement'] != current_req for label in ('before', 'after')):
                raise ValueError('fixed read-only observation window required')
            if key not in stored or stored[key]['text'] != encode(arrival_receipt(witness)).decode().rstrip('\n'):
                raise ValueError('stored boundary receipt differs from the reconstructed transition')
            mark = stored.get('mark-' + key)
            if mark is None:
                raise ValueError('stored boundary mark required')
            metadata = json.loads(mark['source'])
            if (metadata.get('schema') != env.weave.SCHEMA or metadata.get('kind') != 'passage'
                    or metadata.get('event') != key
                    or metadata.get('boundary') is not witness['active']['comparison']['panel_crossed']):
                raise ValueError('stored boundary mark differs from the computed window')
        rebuilt, _ = result.snapshot(receiver)
        if rebuilt != raw:
            raise ValueError('combined checkpoint changed during verified reconstruction')
        return result, receiver
