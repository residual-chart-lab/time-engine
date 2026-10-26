"""E4: an explicit event-to-model bridge, not a natural-language interpreter.

Caller reports, declared correspondences, exact diagnostics and certified
execution remain distinct. Outer natural-language goals stay open when E2 closes.
"""
from copy import deepcopy
import hashlib
import json
import re
import step_session as e2
import preservation_targets as targets

SCHEMA = 'time-engine-event-bridge-e4-v1'
MAX_COMMANDS = 128
MAX_COMMAND_BYTES = 8192
MAX_SNAPSHOT_BYTES = 8_000_000


def encode(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def identifier(value):
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', value) is None:
        raise ValueError('a short explicit identifier is required')
    return value


def text(value):
    if type(value) is not str or not value.strip() or len(value) > 4096:
        raise ValueError('nonempty bounded text is required')
    return value


class Episode:
    def __init__(self, session):
        if session.state is not None or session._journal or session.entry.derived._records():
            raise ValueError('a freshly received E2 session is required')
        self._session = session
        self._events = {}
        self._goals = {}
        self._rows = []
        self._binding = None
        self._inspection = None
        self._permit = None

    @classmethod
    def receive(cls, raw, trusted_sha256, expected_entry_digest):
        return cls(e2.Session.receive(raw, trusted_sha256, expected_entry_digest))

    def _refs(self, values):
        if (type(values) is not list or not values or len(values) > 32
                or any(type(v) is not str or v not in self._events for v in values)
                or len(set(values)) != len(values)):
            raise ValueError('reference distinct events already recorded, at most 32')
        return values

    def _goal(self, value):
        if type(value) is not str or value not in self._goals:
            raise ValueError('an existing goal is required')
        return value

    def _token(self):
        _, sha = self._session.snapshot()
        return digest(dict(engine=sha, binding=self._binding, inspection=self._inspection))

    def status(self):
        goals = []
        for value in self._goals.values():
            rows = [r for r in self._rows if r['outcome'].get('goal') == value['id']]
            bound = any(r['command']['op'] == 'bind' for r in rows)
            certified = any(r['outcome'].get('evidence_kind') == 'engine_execution'
                            and r['outcome']['engine']['certified'] for r in rows)
            model_status = 'SCOPED_MODEL_CERTIFIED' if certified else 'SCOPED_MODEL_BOUND' if bound else 'UNMAPPED'
            goals.append(dict(value, status='OPEN', model_status=model_status, semantic_certification=False))
        diagnostic_reads = sum(r['outcome']['report']['exact_source_reads']
                               for r in self._rows if r['command']['op'] == 'inspect')
        execution_reads = self._session.status()['numerical_reads']
        return deepcopy(dict(
            schema=SCHEMA, episode='OPEN', entry=self._session.entry.digest,
            events=list(self._events.values()),
            goals=goals,
            reads=dict(diagnostic_exact_source_reads=diagnostic_reads, execution_exact_queries=execution_reads,
                       combined_exact_queries=diagnostic_reads+execution_reads),
            binding=self._binding, inspection=self._inspection, permit=self._permit,
            engine=self._session.status(), accepted_commands=len(self._rows),
            commands_remaining=MAX_COMMANDS-len(self._rows),
            head=None if not self._rows else self._rows[-1]['sha256'],
            next_step=self._next_step(), erasure_authorized=False))

    def _next_step(self):
        phase = self._session.status()['phase']
        if self._permit:
            return 'advance_one_flower_or_wait'
        if phase == 'STOPPED':
            return 'finite_model_certified_outer_goals_still_open'
        if self._binding is None:
            return 'declare_a_correspondence_or_keep_the_question_open'
        if phase == 'BOUND':
            return 'choose_current_controls'
        if self._inspection is None:
            return 'inspect_the_proposed_omission'
        return self._inspection['next_step']

    def apply(self, command):
        if (type(command) is not dict or len(encode(command)) > MAX_COMMAND_BYTES
                or len(self._rows) >= MAX_COMMANDS):
            raise ValueError('bounded command and remaining episode budget required')
        command = deepcopy(command)
        op = command.get('op')
        outcome = {}
        seq = len(self._rows) + 1
        if op == 'record' and set(command) == {'op', 'id', 'origin', 'source', 'text'}:
            key = identifier(command['id'])
            if (key in self._events or type(command['origin']) is not str
                    or command['origin'] not in ('received', 'reported_in_session')):
                raise ValueError('new event id and explicit report provenance required')
            event = dict(id=key, seq=seq, origin=command['origin'], source=text(command['source']),
                         text=text(command['text']), evidence_kind='caller_report')
            self._events[key] = event
            outcome = dict(event=key, evidence_kind='caller_report')
        elif op == 'goal' and set(command) == {'op', 'id', 'text', 'events'}:
            key = identifier(command['id'])
            if key in self._goals:
                raise ValueError('goals are append-only; use a new id for a revised goal')
            goal = dict(id=key, seq=seq, text=text(command['text']), events=self._refs(command['events']))
            self._goals[key] = goal
            outcome = dict(goal=key, evidence_kind='declared_requirement', mapped=False)
        elif op == 'relate' and set(command) == {'op', 'goal', 'events', 'note'}:
            goal = self._goal(command['goal'])
            self._refs(command['events']); text(command['note'])
            outcome = dict(goal=goal, evidence_kind='later_interpretation', necessity_proved=False)
        elif op == 'bind' and set(command) == {'op', 'goal', 'requirement', 'coordinates', 'correspondence'}:
            goal = self._goal(command['goal'])
            coordinates = command['coordinates']
            if (type(coordinates) is not dict or not coordinates
                    or not set(coordinates) <= {'s', 't'}):
                raise ValueError('explicit event references for E1 coordinate s and/or t required')
            for values in coordinates.values():
                self._refs(values)
            text(command['correspondence'])
            scope, normalized = e2.requirement(self._session.entry, command['requirement'])
            self._session.apply(dict(op='bind', requirement=normalized))
            self._binding = dict(seq=seq, goal=goal, requirement=normalized, scope=scope.digest,
                                 coordinates=deepcopy(coordinates), correspondence=command['correspondence'],
                                 evidence_kind='caller_declared_correspondence', semantic_certification=False)
            self._inspection = self._permit = None
            outcome = deepcopy(self._binding)
        elif op == 'choose' and set(command) == {'op', 'v', 'u', 'word'}:
            if self._binding is None:
                raise ValueError('bind an explicit correspondence first')
            self._session.apply(command)
            self._inspection = self._permit = None
            outcome = dict(goal=self._binding['goal'], choice=self._session.status()['choice'])
        elif op == 'inspect' and set(command) == {'op', 'omitted'}:
            state = self._session.state
            if state is None or state.phase != 'CHOSEN':
                raise ValueError('inspect a chosen, unexecuted candidate')
            omitted = command['omitted']
            if (type(omitted) is not list or not omitted or any(type(k) is not str for k in omitted)
                    or not set(omitted) <= set(self._binding['coordinates'])):
                raise ValueError('every inspected coordinate needs a declared event correspondence')
            report = targets.compare(self._session.entry, state.scope, *state.choice, omitted)
            relation = report['requested']['relation']
            next_step = {
                'DIFFERENT_EXISTENCE': 'retain_the_difference_or_revise_the_choice',
                'DIFFERENT_NEW_ACTION': 'retain_the_difference_or_revise_the_preservation_target',
                'SAME_NEW_ACTION': 'difference_may_stay_unexpanded_in_this_scope_not_erased',
                'SAME_EMPTY': 'no_action_in_this_scope_revise_or_wait',
                'UNDETERMINED': 'keep_open_mapping_or_guarantee_is_insufficient',
            }[relation]
            self._inspection = dict(id=digest(dict(binding=self._binding, report=report)),
                                    goal=self._binding['goal'], binding_seq=self._binding['seq'],
                                    report=report, next_step=next_step)
            self._permit = None
            outcome = deepcopy(self._inspection)
        elif op == 'resolve' and set(command) == {'op', 'inspection', 'retention'}:
            if (self._inspection is None or command['inspection'] != self._inspection['id']
                    or command['retention'] != 'preserve'
                    or self._inspection['report']['requested']['original_status'] != 'ADMISSIBLE'):
                raise ValueError('current admissible inspection and explicit preserve decision required')
            self._session.apply(dict(op='resolve'))
            self._permit = self._token() if self._session.status()['phase'] == 'READY' else None
            outcome = dict(goal=self._binding['goal'], evidence_kind='engine_resolution',
                           retention='preserve', inspection=self._inspection['id'],
                           engine=self._session.status(), permit=self._permit)
        elif op == 'advance' and set(command) == {'op', 'permit'}:
            if self._permit is None or command['permit'] != self._permit:
                raise ValueError('the current step permit is required; a diagnostic is not permission')
            self._session.apply(dict(op='advance'))
            self._permit = None if self._session.status()['phase'] == 'STOPPED' else self._token()
            outcome = dict(goal=self._binding['goal'], evidence_kind='engine_execution',
                           engine=self._session.status(), permit=self._permit,
                           semantic_goal_closed=False)
        else:
            raise ValueError('unknown operation or unexpected fields')
        previous = None if not self._rows else self._rows[-1]['sha256']
        row = dict(seq=seq, previous=previous, command=command, outcome=outcome)
        row['sha256'] = digest(row)
        self._rows.append(row)
        return dict(outcome=deepcopy(outcome), status=self.status())

    def recall(self, goal, as_of=None):
        """Read the recorded horizon, not a retrospective rewrite of the past."""
        self._goal(goal)
        if as_of is None:
            as_of = len(self._rows)
        if type(as_of) is not int or not self._goals[goal]['seq'] <= as_of <= len(self._rows):
            raise ValueError('choose a recorded horizon at or after the goal was declared')
        rows = [deepcopy(r) for r in self._rows[:as_of] if r['outcome'].get('goal') == goal]
        refs = set(self._goals[goal]['events'])
        for row in rows:
            command = row['command']
            refs.update(command.get('events', []))
            for values in command.get('coordinates', {}).values():
                refs.update(values)
        return dict(goal=deepcopy(self._goals[goal]), as_of=as_of,
                    events=[deepcopy(e) for e in self._events.values() if e['id'] in refs and e['seq'] <= as_of],
                    relations_and_model_evidence=rows, semantic_certification=False)

    def snapshot(self):
        engine, sha = self._session.snapshot()
        value = dict(schema=SCHEMA, entry=self._session.entry.digest, journal=self._rows,
                     current=json.loads(engine), engine_sha256=sha)
        raw = encode(value)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            raise ValueError('episode checkpoint byte budget exceeded')
        return raw, hashlib.sha256(raw).hexdigest()

    @classmethod
    def restore(cls, fresh_session, raw, trusted_sha256):
        if (type(raw) is not bytes or len(raw) > MAX_SNAPSHOT_BYTES
                or type(trusted_sha256) is not str
                or re.fullmatch('[0-9a-f]{64}', trusted_sha256) is None
                or hashlib.sha256(raw).hexdigest() != trusted_sha256):
            raise ValueError('bounded bytes and an externally trusted episode SHA-256 required')
        value = json.loads(raw)
        if (type(value) is not dict or set(value) != {'schema', 'entry', 'journal', 'current', 'engine_sha256'}
                or value['schema'] != SCHEMA or value['entry'] != fresh_session.entry.digest
                or type(value['journal']) is not list or len(value['journal']) > MAX_COMMANDS):
            raise ValueError('complete bounded episode checkpoint required')
        result = cls(fresh_session)
        for row in value['journal']:
            if type(row) is not dict or 'command' not in row:
                raise ValueError('complete episode rows required')
            result.apply(row['command'])
        rebuilt, _ = result.snapshot()
        if encode(json.loads(rebuilt)) != encode(value):
            raise ValueError('event provenance, chronology, correspondence, evidence or engine state changed')
        return result

