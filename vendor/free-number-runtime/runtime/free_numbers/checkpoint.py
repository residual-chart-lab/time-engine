"""Lossless, known-operation DAG checkpoints requiring a trusted outer hash.

This is a structural replay format, not a signature or a TE occurrence receipt.
Every retained exact value survives, including values unused by the last query.
"""
from fractions import Fraction as Q
from dataclasses import dataclass
from hashlib import sha256
import json
from .algebra import canonical, integer_text, parse_integer_text
from .expression import Tensor, Circuit, Channel, Observation
from .retention import Vault
from .traversal import postorder


@dataclass(frozen=True)
class CheckpointLimits:
    max_nodes: int = 10000
    max_references: int = 10000
    max_bytes: int = 20_000_000

    def __post_init__(self):
        if any(type(n) is not int or n < 1 for n in (self.max_nodes,self.max_references,self.max_bytes)):
            raise ValueError('checkpoint budgets must be positive finite integers')


DEFAULT_LIMITS = CheckpointLimits()


def _check_counts(node_count, reference_count, limits):
    if type(limits) is not CheckpointLimits:
        raise TypeError('explicit checkpoint limits are required')
    if node_count > limits.max_nodes or reference_count > limits.max_references:
        raise ValueError('checkpoint node or retained-reference budget exceeded')


def _check_bytes(size, limits):
    if size > limits.max_bytes:
        raise ValueError('checkpoint byte budget exceeded')


def _postorder(roots, limits=DEFAULT_LIMITS):
    if any(type(root) is not Circuit for root in roots):
        raise ValueError('checkpoint roots must be observation circuits')
    def children(node):
        if type(node) is Circuit and node.kind == 'read':
            return (node.data[0],) + node.children
        return node.children
    return tuple(postorder(roots,children,limits.max_nodes))


def dumps(roots, vault, limits=DEFAULT_LIMITS):
    roots = tuple(roots)
    retained = vault._records()
    _check_counts(0,len(retained),limits)
    nodes = []
    for node in _postorder(roots,limits):
        record = {'id':node.digest, 'type':'tensor' if type(node) is Tensor else 'circuit',
                  'kind':node.kind, 'children':[c.digest for c in node.children]}
        if type(node) is Tensor:
            record['grade'] = node.grade
            if node.kind == 'retained':
                vault.verify(node.data[0])
                record['data'] = [node.data[0].key]
            else:
                record['data'] = node.data
        elif node.kind == 'read':
            tensor, obs = node.data
            record['data'] = {'tensor':tensor.digest, 'grade':obs.grade,
                'channels':[(c.gaps,c.weight,c.left,c.right) for c in obs.channels]}
        else:
            record['data'] = node.data
        nodes.append(record)
    values = [(r.key,value,r.envelope,r.origin,r.digest) for r,value in retained]
    _check_counts(len(nodes),len(values),limits)
    payload = canonical({'format':'free-numbers-demand-dag-v1', 'nodes':nodes,
                         'roots':[r.digest for r in roots], 'retained':values})
    _check_bytes(len(payload),limits)
    return payload, sha256(payload).hexdigest()


def _object(pairs):
    d = {}
    for key, value in pairs:
        if key in d:
            raise ValueError('duplicate JSON keys are not allowed')
        d[key] = value
    if set(d) == {'q'}:
        v = d['q']
        if type(v) is not list or len(v) != 2 or any(type(a) is not str for a in v):
            raise ValueError('invalid exact rational record')
        q = Q(parse_integer_text(v[0]),parse_integer_text(v[1]))
        if v != [integer_text(q.numerator),integer_text(q.denominator)]:
            raise ValueError('rational records must be normalized')
        return q
    if set(d) == {'integer'}:
        value = parse_integer_text(d['integer'])
        if value.bit_length() <= 2000:
            raise ValueError('small metadata integers must use JSON integer encoding')
        return value
    return d


def _freeze(x):
    if type(x) is list:
        return tuple(_freeze(v) for v in x)
    return x


def loads(payload, expected_sha256, limits=DEFAULT_LIMITS):
    _check_counts(0,0,limits)
    if type(payload) is not bytes or not isinstance(expected_sha256,str) or sha256(payload).hexdigest() != expected_sha256:
        raise ValueError('a matching externally trusted checkpoint hash is required')
    _check_bytes(len(payload),limits)
    def reject(value):
        raise ValueError('JSON floating values are not part of the exact format')
    doc = json.loads(payload.decode('utf-8'), object_pairs_hook=_object,
                     parse_int=parse_integer_text, parse_float=reject, parse_constant=reject)
    if (type(doc) is not dict or set(doc) != {'format','nodes','roots','retained'} or
            doc['format'] != 'free-numbers-demand-dag-v1' or type(doc['nodes']) is not list or
            type(doc['roots']) is not list or type(doc['retained']) is not list):
        raise ValueError('unknown checkpoint schema')
    _check_counts(len(doc['nodes']),len(doc['retained']),limits)
    vault, seen_keys = Vault(), set()
    for key,value,envelope,origin,digest in doc['retained']:
        if key in seen_keys:
            raise ValueError('duplicate retained reference')
        seen_keys.add(key)
        ref = vault.register(key,value,envelope,origin)
        if ref.digest != digest:
            raise ValueError('the exact value, bound or provenance changed')
    nodes = {}
    for record in doc['nodes']:
        if type(record) is not dict:
            raise ValueError('invalid graph record')
        expected_keys = {'id','type','kind','children','data'}
        if record.get('type') == 'tensor':
            expected_keys.add('grade')
        if set(record) != expected_keys or record['id'] in nodes:
            raise ValueError('invalid or duplicate graph record')
        try:
            children = tuple(nodes[key] for key in record['children'])
            kind, data = record['kind'], record['data']
            if record['type'] == 'tensor':
                if kind == 'retained':
                    if type(data) is not list or len(data) != 1:
                        raise ValueError('invalid retained node')
                    data = (vault.reference(data[0]),)
                else:
                    data = _freeze(data)
                node = Tensor(kind,record['grade'],data,children)
            elif record['type'] == 'circuit':
                if kind == 'read':
                    if type(data) is not dict or set(data) != {'tensor','grade','channels'}:
                        raise ValueError('invalid observation record')
                    obs = Observation(data['grade'],tuple(Channel(_freeze(g),w,_freeze(l),_freeze(r))
                        for g,w,l,r in data['channels']))
                    data = (nodes[data['tensor']],obs)
                else:
                    data = _freeze(data)
                node = Circuit(kind,data,children)
            else:
                raise ValueError('unknown graph type')
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError('invalid or non-topological operation graph') from exc
        if node.digest != record['id']:
            raise ValueError('ordered structure or retained observation changed')
        nodes[node.digest] = node
    try:
        roots = tuple(nodes[key] for key in doc['roots'])
    except KeyError as exc:
        raise ValueError('missing checkpoint root') from exc
    if any(type(root) is not Circuit for root in roots) or len(_postorder(roots,limits)) != len(nodes):
        raise ValueError('all operation nodes must be reachable from declared roots')
    return roots,vault
