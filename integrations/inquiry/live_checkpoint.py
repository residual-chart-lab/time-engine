"""Exact authenticated snapshots with replay-verified command chronology.

No pickle, arbitrary classes, floating point regeneration or future search.
An externally trusted SHA-256 is required for loading persisted bytes.
"""
from dataclasses import fields, is_dataclass
from fractions import Fraction as Q
import hashlib
import json
import re
import live_flower as live
from live_flower import f, d, prior, te

SCHEMA = 'time-engine-rr63-live-checkpoint-v1'
BASE = '5e0b40871ccda4f0bbf2b6d49b6a9c62d0580bd8'


def registry():
    own = (live.Seed, live.State, f.Entry, f.Scope, f.Demand, f.Resolution,
           prior.Requirement, d.RetainedPair, d.Scope, d.ReplacementCertificate,
           prior.previous.Flight)
    return {**te.registry(), **{c.__module__ + '.' + c.__name__: c for c in own}}


def pack(value):
    names = {cls: name for name, cls in registry().items()}
    nodes, seen = [], {}
    def visit(x):
        if x is None or type(x) in (str, int, bool):
            return x
        if type(x) is Q:
            return {'q': [te.triple.decimal_integer(x.numerator), te.triple.decimal_integer(x.denominator)]}
        if id(x) in seen:
            return {'ref': seen[id(x)]}
        i = len(nodes); seen[id(x)] = i; nodes.append(None)
        if type(x) is tuple:
            node = {'tuple': [visit(v) for v in x]}
        elif is_dataclass(x) and type(x) in names:
            node = {'type': names[type(x)], 'fields': {z.name: visit(getattr(x, z.name)) for z in fields(x)}}
        else:
            raise ValueError('unsupported snapshot type')
        nodes[i] = node
        return {'ref': i}
    root = visit(value)
    return dict(root=root, nodes=nodes)


def unpack(graph):
    if type(graph) is not dict or set(graph) != {'root', 'nodes'} or type(graph['nodes']) is not list:
        raise ValueError('invalid snapshot graph')
    types, nodes, built, active = registry(), graph['nodes'], {}, set()
    def visit(x):
        if x is None or type(x) in (str, int, bool):
            return x
        if type(x) is not dict:
            raise ValueError('invalid graph value')
        if set(x) == {'q'}:
            return Q(*(te.triple.parse_integer(v) for v in x['q']))
        if set(x) != {'ref'} or type(x['ref']) is not int:
            raise ValueError('invalid graph reference')
        i = x['ref']
        if not 0 <= i < len(nodes) or i in active:
            raise ValueError('invalid or cyclic reference')
        if i in built:
            return built[i]
        active.add(i); node = nodes[i]
        if set(node) == {'tuple'}:
            obj = tuple(visit(v) for v in node['tuple'])
        elif set(node) == {'type', 'fields'} and node['type'] in types:
            cls = types[node['type']]
            if set(node['fields']) != {z.name for z in fields(cls)}:
                raise ValueError('unknown fields')
            values = {k: visit(v) for k, v in node['fields'].items()}
            obj = cls(**values)
            for k, v in values.items():
                if type(getattr(obj, k)) is not type(v) or getattr(obj, k) != v:
                    raise ValueError('snapshot fields must already be canonical')
                object.__setattr__(obj, k, v)
        else:
            raise ValueError('unknown snapshot type')
        active.remove(i); built[i] = obj
        return obj
    return visit(graph['root'])


def dumps(session):
    payload = dict(schema=SCHEMA, base_commit=BASE,
        graph=pack((session.seed, session.history, session.entry, session.state)),
        commands=list(session.commands))
    return (json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def loads(raw, *, trusted_sha256):
    if (type(raw) is not bytes or type(trusted_sha256) is not str
            or not re.fullmatch('[0-9a-f]{64}', trusted_sha256)
            or hashlib.sha256(raw).hexdigest() != trusted_sha256):
        raise ValueError('original bytes and an external trusted SHA-256 are required')
    payload = json.loads(raw)
    if (set(payload) != {'schema', 'base_commit', 'graph', 'commands'}
            or payload['schema'] != SCHEMA or payload['base_commit'] != BASE
            or type(payload['commands']) is not list):
        raise ValueError('unknown checkpoint format or base')
    saved = unpack(payload['graph'])
    if type(saved) is not tuple or len(saved) != 4:
        raise ValueError('a complete checkpoint is required')
    seed, history, entry, state = saved
    replay = live.Session(seed)
    if (type(state) is not live.State or replay.history != history or replay.entry != entry):
        raise ValueError('the archived input or authenticated source changed')
    for command in payload['commands']:
        replay.apply(command)
    if replay.state != state:
        raise ValueError('snapshot differs from exact command replay')
    # Restore all four roots together: state also shares nodes with history.
    replay.seed, replay.history, replay.entry, replay._state = saved
    return replay
