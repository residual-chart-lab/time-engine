"""E2: a small in-process command surface over the unchanged RR69 executor.

Entry authentication happens once. A new request clears the old permission,
while authenticated observations can be reused before physical execution.
"""
from dataclasses import replace
from fractions import Fraction as Q
import hashlib
import json
import re
import entry_transport as wire
import three_flower_session as live
from three_flower_session import n, a, m

SCHEMA = 'time-engine-step-session-e2-v1'
MAX_COMMANDS = 64
MAX_COMMAND_BYTES = 16384
MAX_SNAPSHOT_BYTES = 2_000_000
FRAMES = {'identity': (1, 0, 0, 1), 'split': (1, 1, 1, -1)}
CONTEXTS = ('mixed', 'main', 'zero_head', 'outside_chart')


def rational(value):
    if type(value) is int:
        value = str(value)
    if type(value) is not str or len(value) > 160 or re.fullmatch(r'-?\d+(?:/[1-9]\d*)?', value) is None:
        raise ValueError('an exact integer or fraction string is required')
    return Q(value)


def requirement(entry, data):
    if type(data) is not dict or set(data) not in ({'context', 'strengths', 'frame'}, {'context', 'strengths', 'frame', 'domain'}):
        raise ValueError('context, two strengths, frame, and optional domain required')
    if (type(data['context']) is not str or data['context'] not in CONTEXTS
            or type(data['frame']) is not str or data['frame'] not in FRAMES
            or type(data['strengths']) is not list or len(data['strengths']) != 2):
        raise ValueError('supported context, frame and two strengths required')
    strengths = tuple(map(rational, data['strengths']))
    options = {}
    if 'domain' in data:
        if type(data['domain']) is not list or len(data['domain']) != 2:
            raise ValueError('domain needs two exact bounds')
        options['domain'] = tuple(map(rational, data['domain']))
    raw = m.Scope(entry.base.digest, m.context(entry.base, data['context']), strengths[0], **options)
    scope = n.Scope(raw, strengths[1], frame=FRAMES[data['frame']])
    normalized = dict(context=data['context'], strengths=list(map(str, strengths)), frame=data['frame'])
    if 'domain' in options:
        normalized['domain'] = list(map(str, options['domain']))
    return scope, normalized


class Session:
    def __init__(self, entry):
        a.verify_entry(entry)
        self.entry = entry
        self.state = None
        self._cache = ()
        self._journal = []
        self._request = None
        self._last_work = {}
        self._numerical_reads = 0

    @classmethod
    def receive(cls, raw, trusted_sha256, expected_entry_digest):
        return cls(wire.loads(raw, trusted_sha256, expected_entry_digest))

    def status(self):
        state = self.state
        return dict(entry=self.entry.digest, phase='UNBOUND' if state is None else state.phase,
                    requirement=self._request,
                    choice=None if state is None or state.choice is None else
                    dict(v=str(state.choice[0]), u=str(state.choice[1]), word=state.choice[2]),
                    closed_flowers=0 if state is None else len(state.flowers),
                    stock=len(self.entry.base.engine.stock if state is None else state.engine.stock),
                    certified=False if state is None else state.certified,
                    cached_observations=len(self._cache), accepted_commands=len(self._journal),
                    numerical_reads=self._numerical_reads, last_resolution_work=self._last_work)

    def apply(self, command):
        if type(command) is not dict or len(json.dumps(command)) > MAX_COMMAND_BYTES:
            raise ValueError('a bounded command object is required')
        if len(self._journal) >= MAX_COMMANDS:
            raise ValueError('session command budget exhausted; checkpoint remains available')
        op = command.get('op')
        work = {}
        request = self._request
        if op == 'bind' and set(command) == {'op', 'requirement'}:
            if self.state is not None and self.state.flowers:
                raise ValueError('a closed flower cannot be rebound or rewound')
            scope, request = requirement(self.entry, command['requirement'])
            a.validate_cache(self.entry, dict(self._cache))
            state = live.start(self.entry, scope)
            if self._cache:
                # This only attaches validated observations to a new unchosen
                # BOUND state. It supplies no plan, action, or physical motion.
                state = live.issue(replace(state, cache=self._cache))
            normalized = dict(op=op, requirement=request)
        elif op == 'choose' and set(command) == {'op', 'v', 'u', 'word'}:
            if self.state is None or type(command['word']) is not str:
                raise ValueError('bind a request and supply an exact current choice')
            v, u = rational(command['v']), rational(command['u'])
            state = live.choose(self.state, v, u, command['word'])
            normalized = dict(op=op, v=str(v), u=str(u), word=command['word'])
        elif op == 'resolve' and set(command) == {'op'}:
            if self.state is None:
                raise ValueError('choose before resolving')
            state, work = live.resolve(self.state)
            normalized = dict(op=op)
        elif op == 'advance' and set(command) == {'op'}:
            if self.state is None:
                raise ValueError('a prepared admissible action is required')
            state = live.advance(self.state)
            normalized = dict(op=op)
        else:
            raise ValueError('unknown command or unexpected fields')
        self.state, self._request = state, request
        self._cache = state.cache
        self._journal.append(normalized)
        if op in ('bind', 'choose', 'resolve'):
            self._last_work = work
        self._numerical_reads += work.get('total_exact_queries', 0)
        return self.status()

    def snapshot(self):
        value = dict(schema=SCHEMA, entry=self.entry.digest, journal=self._journal,
                     current=None if self.state is None else live.payload(self.state),
                     numerical_reads=self._numerical_reads)
        raw = (json.dumps(value, separators=(',', ':')) + '\n').encode()
        if len(raw) > MAX_SNAPSHOT_BYTES:
            raise ValueError('checkpoint byte budget exceeded')
        return raw, hashlib.sha256(raw).hexdigest()

    @classmethod
    def restore(cls, entry, raw, trusted_sha256):
        if (type(raw) is not bytes or len(raw) > MAX_SNAPSHOT_BYTES
                or type(trusted_sha256) is not str or re.fullmatch('[0-9a-f]{64}', trusted_sha256) is None
                or hashlib.sha256(raw).hexdigest() != trusted_sha256):
            raise ValueError('bounded checkpoint bytes and an external trusted SHA-256 required')
        value = json.loads(raw)
        if (type(value) is not dict or set(value) != {'schema', 'entry', 'journal', 'current', 'numerical_reads'}
                or value['schema'] != SCHEMA or value['entry'] != entry.digest
                or type(value['journal']) is not list or len(value['journal']) > MAX_COMMANDS):
            raise ValueError('complete bounded session checkpoint required')
        if entry.derived._records():
            raise ValueError('resume needs a freshly received entry')
        result = cls(entry)
        for command in value['journal']:
            result.apply(command)
        check = dict(schema=SCHEMA, entry=entry.digest, journal=result._journal,
                     current=None if result.state is None else live.payload(result.state),
                     numerical_reads=result._numerical_reads)
        if check != value:
            raise ValueError('request, observations, actual history or command chronology changed')
        return result
