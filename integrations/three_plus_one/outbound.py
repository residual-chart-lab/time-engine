"""RR56: a declared response-shape port from 3+1 into one fixed-C flower.

The XNOR base network and transported tangent are both retained. A calibrated
response contrast selects an action-null source coefficient. The same future
frame/result/tolerance tests all four contact candidates in every intervention.
This is an outbound coupling experiment, not a derived identification of the
two models or the RR46 source-generated-boundary protocol.
"""
from dataclasses import dataclass, fields, is_dataclass, replace
from fractions import Fraction as Q
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'baseline/v1/runtime'),
               str(ROOT / 'vendor/three-plus-one/src'),
               str(ROOT / 'vendor/three-plus-one/examples')]

from threeplusone import ThreePlusOneMLP, centered_singleton_seed, add_transverse_vector_seed, xnor
from threeplusone.transverse import epoch_transverse_matrix, sample_transverse_matrix
from xnor_retained_difference import radial, mv as float_mv
from xnor_intelligence_minimal import blind_hidden_direction
import completed_single_flower as single
from single_flower_model import null_direction
from persistent_correction_cycle import event, execute_producer, publish_producer, close_round, available
from recursive_upper_decoder import AffineLetter, ExecutionState, UpperState, step, decode, promote_word, regular
from three_flower_constraint import decimal_integer, parse_integer, encode, macro_registry
from two_flower_connection import add, mul, evaluate, derivative, Interval

EPSILON = Q(1, 10**12)
FIXED_RESULT = (Q(-1), Q(0), Q(0), Q(0))
CONTACTS = tuple((tuple(Q(value) for value in x), Q(target)) for x, target in xnor())
MODES = ('keep', 'erase', 'restore', 'flip', 'blind')


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), Q(0))


def mv(matrix, vector):
    return tuple(dot(row, vector) for row in matrix)


def subtract(a, b):
    return tuple(x-y for x, y in zip(a, b))


def times(coefficient, vector):
    return tuple(coefficient*x for x in vector)


def centered(vector):
    return subtract(vector, (sum(vector)/len(vector),)*len(vector))


def exact(values):
    return tuple(Q(value) for value in values)


@dataclass(frozen=True)
class CourseConfig:
    start_epoch: int = 728
    carry_epochs: int = 8
    order: tuple = (0, 1, 2, 3)

    def __post_init__(self):
        if self.start_epoch not in (100, 400, 728) or type(self.carry_epochs) is not int or not 0 <= self.carry_epochs <= 8:
            raise ValueError('the declared XNOR starts and zero to eight carried epochs are required')
        if self.order not in ((0, 1, 2, 3), (3, 2, 1, 0), (0, 2, 1, 3)):
            raise ValueError('a declared upstream training order is required')


@dataclass(frozen=True)
class NeuralState:
    network: tuple
    tangent: tuple


def snapshot(network):
    return exact([v for row in network.hidden_w for v in row] + network.output_w)


def network_from_snapshot(weights):
    if len(weights) != 17:
        raise ValueError('all seventeen base-network parameters are required')
    net = ThreePlusOneMLP(epsilon=1, seed_pattern=centered_singleton_seed(4))
    net.hidden_w = [[float(v) for v in weights[i:i+3]] for i in range(0, 12, 3)]
    net.output_w = [float(v) for v in weights[12:]]
    if snapshot(net) != weights:
        raise ValueError('the base snapshot must retain its exact binary64 values')
    return net


@dataclass(frozen=True)
class SourceCourse:
    config: CourseConfig
    checkpoints: tuple


@lru_cache(maxsize=32)
def source_course(config=CourseConfig()):
    net = ThreePlusOneMLP(epsilon=1, seed_pattern=centered_singleton_seed(4))
    add_transverse_vector_seed(net, direction=(1, 0, 0, 0), amplitude=.1, phase=0)
    samples = [xnor()[i] for i in config.order]
    for _ in range(config.start_epoch):
        for x, target in samples:
            net.train_one(x, target)
    vector = radial(net)
    checkpoints = [NeuralState(snapshot(net), exact(vector))]
    for _ in range(config.carry_epochs):
        vector = float_mv(epoch_transverse_matrix(net, samples, representative_unit=1), vector)
        for x, target in samples:
            net.train_one(x, target)
        checkpoints.append(NeuralState(snapshot(net), exact(vector)))
    return SourceCourse(config, tuple(checkpoints))


@dataclass(frozen=True)
class PortSpec:
    gain: Q = Q(1)
    reference_contact: int = 0

    def __post_init__(self):
        object.__setattr__(self, 'gain', Q(self.gain))
        if not 0 <= self.gain <= 2 or self.reference_contact != 0:
            raise ValueError('gain in [0,2] and the declared 00 reference contact are required')


@dataclass(frozen=True)
class PortState:
    course: SourceCourse
    mode: str
    vector: tuple
    radial: tuple
    phase: Q
    visible: tuple
    hidden: tuple
    response_matrix: tuple
    shape: tuple


def port_state(config=CourseConfig(), mode='keep'):
    if mode not in MODES:
        raise ValueError('unknown intervention')
    course = source_course(config)
    last = course.checkpoints[-1]
    net = network_from_snapshot(last.network)
    r = exact(radial(net))
    phase = dot(r, last.tangent)/dot(r, r)
    visible = times(phase, r)
    original_hidden = subtract(last.tangent, visible)
    matrices = tuple(tuple(exact(row) for row in sample_transverse_matrix(net, x, target, representative_unit=1))
                     for x, target in CONTACTS)
    matrix = tuple(tuple(sum(r[i]*(k[i][j]-(1 if i == j else 0)) for i in range(4))/dot(r, r)
                         for j in range(4)) for k in matrices)
    if mode == 'erase':
        vector = visible
    elif mode == 'flip':
        vector = subtract(visible, original_hidden)
    elif mode == 'blind':
        direction = blind_hidden_direction([float(v) for v in r],
            [[float(v) for v in row] for row in matrix], [float(v) for v in mv(matrix, visible)])
        size = math.sqrt(float(dot(original_hidden, original_hidden)))
        blind = exact(v*size for v in direction)
        blind = subtract(blind, times(dot(r, blind)/dot(r, r), r))
        vector = tuple(a+b for a, b in zip(visible, blind))
    elif mode == 'restore':
        vector = tuple(a+b for a, b in zip(visible, original_hidden))
    else:
        vector = last.tangent
    hidden = subtract(vector, visible)
    if dot(r, hidden) != 0:
        raise AssertionError('the rational snapshot intervention must preserve the exact phase')
    b, d = centered(mv(matrix, visible)), centered(mv(matrix, hidden))
    if not dot(b, b):
        raise ValueError('the upstream nonzero visible-profile convention is required')
    shape = subtract(d, times(dot(b, d)/dot(b, b), b))
    return PortState(course, mode, vector, r, phase, visible, hidden, matrix, shape)


@dataclass(frozen=True)
class Carrier:
    anchor: object
    representative: Q
    weights: tuple
    delta: tuple
    reference_context: tuple


@lru_cache(maxsize=1)
def carrier():
    # An isolated RR52 reference calculation constructs the common fixture.
    # Its published preview is never used as the new actual producer ledger.
    reference = single.produce_source(single.begin())
    source = reference.engine.pending.issue.operation
    return Carrier(reference.anchor, reference.representative, source.cell.beta[0].weights,
        null_direction(reference.anchor.current_context, reference.anchor.original.library),
        single.boundary_readout(source))


@dataclass(frozen=True)
class FutureRequirement:
    context: tuple
    result: tuple = FIXED_RESULT
    tolerance: Q = EPSILON

    def __post_init__(self):
        if self.result != FIXED_RESULT or self.tolerance != EPSILON:
            raise ValueError('the fixed result and tolerance cannot be replaced')
        object.__setattr__(self, 'context', single.context(self.context))


@dataclass(frozen=True)
class ContactCandidate:
    contact_index: int
    shift: Q
    leaf: AffineLetter


def contact_candidate(state, receiver, spec, index):
    if type(index) is not int or not 0 <= index < 4:
        raise ValueError('an actual XNOR contact index is required')
    shift = spec.gain*(state.shape[index]-state.shape[spec.reference_contact])
    weights = tuple(w+shift*d for w, d in zip(receiver.weights, receiver.delta))
    leaf = AffineLetter(weights, receiver.anchor.original.library)
    current = receiver.anchor.current_context
    if leaf.kernel(current) != receiver.anchor.producer_plan.pending.plan.wanted_action:
        raise AssertionError('the port changed the current compensation')
    return ContactCandidate(index, shift, leaf)


@dataclass(frozen=True)
class Prepared:
    state: PortState
    receiver: Carrier
    spec: PortSpec
    candidates: tuple


def prepare(config=CourseConfig(), mode='keep', spec=PortSpec()):
    state, receiver = port_state(config, mode), carrier()
    return Prepared(state, receiver, spec, tuple(contact_candidate(state, receiver, spec, i) for i in range(4)))


def primary_requirement():
    return FutureRequirement(carrier().reference_context)


def preview(candidate, receiver, requirement):
    initial = receiver.anchor.original
    if not regular(requirement.context, initial.library):
        raise ValueError('the shared future frame must remain inside the certified chart')
    start = ExecutionState(UpperState(requirement.context, initial.upper.live.accumulated), initial.upper.executed_word)
    first = step(initial.designated_head, start)
    # A future source produced by this one affine leaf has the same kernel.
    from recursive_upper_decoder import qmul
    endpoint = tuple(qmul(candidate.leaf.kernel(requirement.context), first.live.accumulated))
    prefix_error = sum(abs(a-b) for a, b in zip(first.live.accumulated, requirement.result))
    error = sum(abs(a-b) for a, b in zip(endpoint, requirement.result))
    return endpoint, prefix_error, error


def admissible(candidate, receiver, requirement):
    _, prefix, error = preview(candidate, receiver, requirement)
    return prefix > requirement.tolerance and error < requirement.tolerance/2


@dataclass(frozen=True)
class Commitment:
    state: PortState
    receiver: Carrier
    spec: PortSpec
    requirement: FutureRequirement
    chosen: ContactCandidate
    allowed_count: int
    selected_ordinal: int
    free_choice: int
    predicted_endpoint: tuple


def select(prepared, requirement, free_choice=0):
    if type(free_choice) is not int or free_choice < 0:
        raise ValueError('a nonnegative current free selection value is required')
    if type(prepared) is not Prepared or type(requirement) is not FutureRequirement:
        raise ValueError('the declared prepared entry and future requirement are required')
    canonical = prepare(prepared.state.course.config, prepared.state.mode, prepared.spec)
    if prepared != canonical:
        raise ValueError('the original source, current entry and complete contact family must stay bound')
    allowed = tuple(c for c in prepared.candidates if admissible(c, prepared.receiver, requirement))
    if not allowed:
        raise ValueError('no allowed contact in this fixed four-contact experiment; not global impossibility')
    ordinal = free_choice % len(allowed)
    chosen = allowed[ordinal]
    endpoint, _, _ = preview(chosen, prepared.receiver, requirement)
    return Commitment(prepared.state, prepared.receiver, prepared.spec, requirement, chosen,
                      len(allowed), ordinal, free_choice, endpoint)


@dataclass(frozen=True)
class NeuralContact:
    contact_index: int
    sample: tuple
    target: Q
    before: NeuralState
    after: NeuralState
    fixed_readout_response: Q


def execute_contact(state, contact_index):
    before = NeuralState(state.course.checkpoints[-1].network, state.vector)
    net = network_from_snapshot(before.network)
    x, target = CONTACTS[contact_index]
    matrix = tuple(exact(row) for row in sample_transverse_matrix(net, x, target, representative_unit=1))
    transported = mv(matrix, before.tangent)
    net.train_one(x, target)
    after = NeuralState(snapshot(net), transported)
    response = dot(state.radial, subtract(transported, before.tangent))/dot(state.radial, state.radial)
    return NeuralContact(contact_index, x, target, before, after, response)


@dataclass(frozen=True)
class Occurrence:
    commitment: Commitment
    neural_contact: NeuralContact
    actual_source: object
    consumer_start: ExecutionState
    actual_endpoint: tuple
    closure_error: Q
    closed_engine: object
    terminal_operation: object
    status: str = 'ONE_FLOWER_COMPLETE'


def execute(receipt):
    # The caller supplies a trusted immutable commitment. No root, candidate
    # search, shape projection, or free-choice replacement occurs from here.
    contact = execute_contact(receipt.state, receipt.chosen.contact_index)
    engine = receipt.receiver.anchor.producer_plan
    engine = event(engine, 'rr56-3plus1-contact-executed')
    plan = replace(engine.pending.plan, leaf=receipt.chosen.leaf)
    engine = event(engine, 'rr56-source-coefficient-bound', pending=replace(engine.pending, plan=plan))
    published = publish_producer(execute_producer(engine))
    source = published.pending.issue.operation
    available(published, source)
    requirement = receipt.requirement
    start = ExecutionState(UpperState(requirement.context, published.upper.live.accumulated), published.upper.executed_word)
    engine = event(published, 'rr56-shared-future-context-arrived', upper=start)
    word = (published.pending.head, source)
    first = step(word[0], start)
    engine = event(engine, 'rr56-consumer-action-executed', upper=first)
    endpoint = step(word[1], first)
    engine = event(engine, 'rr56-consumer-action-executed', upper=endpoint)
    error = sum(abs(a-b) for a, b in zip(endpoint.live.accumulated, requirement.result))
    prefix_error = sum(abs(a-b) for a, b in zip(first.live.accumulated, requirement.result))
    if not (error < requirement.tolerance/2 and prefix_error > requirement.tolerance
            and endpoint.live.accumulated == receipt.predicted_endpoint):
        raise ValueError('the actual frozen path does not meet the bound shared requirement')
    decoded = decode(start, word, (endpoint.live.accumulated,))
    if (len(decoded.outputs) != 1 or decoded.tail or decoded.boundaries
            or decoded.state != endpoint or promote_word(decoded.outputs[0].cell) != decoded.outputs[0]):
        raise ValueError('an exact certificate of the actual first boundary is required')
    closed = close_round(engine, decoded, 'rr56-3plus1-port')
    return Occurrence(receipt, contact, source, start, endpoint.live.accumulated,
                      error, closed, decoded.outputs[0])


def verify_occurrence(occurrence, receipt):
    if type(occurrence) is not Occurrence or occurrence.commitment != receipt or occurrence != execute(receipt):
        raise ValueError('the neural contact, fixed requirement, inheritance or actual flower was substituted')
    return True


@dataclass(frozen=True)
class FutureFixture:
    requirement: FutureRequirement
    reference_contact: int
    polynomial: tuple
    bracket: tuple
    derivative_range: tuple


def alternative_requirement(prepared, reference_contact=1):
    """Explicit second solvable test condition, never a hidden port fitting."""
    candidate = prepared.candidates[reference_contact]
    receiver = prepared.receiver
    y0 = receiver.reference_context
    def frame(z):
        return single.context([[y0[i][j]+(z if i == j == 0 else -z if i == j == 1 else 0)
                                for j in range(3)] for i in range(3)])
    p = (receiver.anchor.original.upper.live.accumulated[0],)
    for leaf in (*receiver.anchor.original.designated_head.leaves(), candidate.leaf):
        value = leaf.kernel(y0)
        changed = leaf.kernel(frame(Q(1)))
        if any(value[1:]) or any(changed[1:]):
            raise ValueError('the declared real diagonal fixture class is required')
        p = mul(p, (value[0], changed[0]-value[0]))
    p = add(p, (Q(1),))
    a, b = Q(-1, 1000), Q(1, 1000)
    left = evaluate(p, a)
    if left*evaluate(p, b) >= 0:
        raise ValueError('the declared alternate fixture is not bracketed')
    for _ in range(512):
        z = (a+b)/2
        value = evaluate(p, z)
        if abs(value) < EPSILON/128:
            lo, hi = z-Q(1, 10**8), z+Q(1, 10**8)
            slope = evaluate(derivative(p), Interval(lo, hi))
            if not slope.excludes_zero() or evaluate(p, lo)*evaluate(p, hi) >= 0:
                raise ValueError('the alternate root must have an interval certificate')
            requirement = FutureRequirement(frame(z))
            if not admissible(candidate, receiver, requirement):
                raise ValueError('the declared alternate reference did not close')
            return FutureFixture(requirement, reference_contact, p, (lo, hi), slope.as_pair())
        if left*value < 0:
            b = z
        else:
            a, left = z, value
    raise ValueError('alternate fixture precision budget exceeded')


def registry():
    own = (CourseConfig, NeuralState, SourceCourse, PortSpec, PortState, Carrier, FutureRequirement,
           ContactCandidate, Prepared, Commitment, NeuralContact, Occurrence, FutureFixture)
    return {**macro_registry(), **{'outbound.'+cls.__name__: cls for cls in own}}


def export_occurrence(occurrence):
    types = {cls: name for name, cls in registry().items()}
    nodes, seen = [], {}
    def pack(value):
        if value is None or type(value) in (str, int, bool):
            return value
        if isinstance(value, Q):
            return {'fraction': [decimal_integer(value.numerator), decimal_integer(value.denominator)]}
        if id(value) in seen:
            return {'ref': seen[id(value)]}
        index = len(nodes)
        seen[id(value)] = index
        nodes.append(None)
        if isinstance(value, tuple):
            node = {'tuple': [pack(x) for x in value]}
        elif is_dataclass(value) and type(value) in types:
            node = {'type': types[type(value)], 'fields': {f.name: pack(getattr(value, f.name)) for f in fields(value)}}
        else:
            raise TypeError('unsupported exact record node')
        nodes[index] = node
        return {'ref': index}
    return dict(schema='time-engine-3plus1-outbound-occurrence-v1', root=pack(occurrence), nodes=nodes)


def import_occurrence(payload, expected_requirement, config=CourseConfig(), mode='keep', spec=PortSpec(), free_choice=0):
    if payload.get('schema') != 'time-engine-3plus1-outbound-occurrence-v1':
        raise ValueError('unknown record schema')
    types, nodes, built, visiting = registry(), payload['nodes'], {}, set()
    def unpack(value):
        if value is None or type(value) in (str, int, bool):
            return value
        if set(value) == {'fraction'}:
            a, b = value['fraction']
            return Q(parse_integer(a), parse_integer(b))
        if set(value) != {'ref'}:
            raise ValueError('unknown record value')
        index = value['ref']
        if type(index) is not int or not 0 <= index < len(nodes) or index in visiting:
            raise ValueError('invalid or cyclic graph reference')
        if index in built:
            return built[index]
        visiting.add(index)
        node = nodes[index]
        if set(node) == {'tuple'}:
            obj = tuple(unpack(x) for x in node['tuple'])
        elif set(node) == {'type', 'fields'} and node['type'] in types:
            cls = types[node['type']]
            if set(node['fields']) != {f.name for f in fields(cls)}:
                raise ValueError('unknown dataclass fields')
            obj = cls(**{name: unpack(x) for name, x in node['fields'].items()})
        else:
            raise ValueError('unknown graph node or type')
        visiting.remove(index)
        built[index] = obj
        return obj
    record = unpack(payload['root'])
    canonical = select(prepare(config, mode, spec), expected_requirement, free_choice)
    verify_occurrence(record, canonical)
    return record


def allowed_indices(prepared, requirement):
    return tuple(c.contact_index for c in prepared.candidates if admissible(c, prepared.receiver, requirement))


def brief(prepared, requirement):
    return dict(mode=prepared.state.mode, phase=float(prepared.state.phase),
        hidden_norm=math.sqrt(float(dot(prepared.state.hidden, prepared.state.hidden))),
        shape=[float(v) for v in prepared.state.shape],
        shifts=[float(c.shift) for c in prepared.candidates],
        candidate_contact_indices=[c.contact_index for c in prepared.candidates],
        current_source_responses=[c.leaf.kernel(prepared.receiver.anchor.current_context) for c in prepared.candidates],
        future_errors=[float(preview(c, prepared.receiver, requirement)[-1]) for c in prepared.candidates],
        allowed_contact_indices=allowed_indices(prepared, requirement),
        distinct_source_coefficients=len({c.leaf.weights for c in prepared.candidates}))


def run():
    requirement = primary_requirement()
    prepared = {mode: prepare(mode=mode) for mode in MODES}
    cases = {mode: brief(p, requirement) for mode, p in prepared.items()}
    checks = []
    def check(name, ok, **details):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name, passed=True, **details))
    check('actual upstream base motion generates the retained tangent and all seventeen weights stay present',
          len(prepared['keep'].state.course.checkpoints) == 9
          and all(len(s.network) == 17 for s in prepared['keep'].state.course.checkpoints),
          start_epoch=728, carried_epochs=8, local_tangent_dimension=4, base_parameter_count=17)
    check('all interventions preserve the exact projected present phase and the exact receiver current action',
          len({p.state.phase for p in prepared.values()}) == 1
          and all(dot(p.state.radial, p.state.hidden) == 0 for p in prepared.values())
          and all(c.leaf.kernel(p.receiver.anchor.current_context) == (-9, 0, 0, 0)
                  for p in prepared.values() for c in p.candidates), receiver_current_response=(-9, 0, 0, 0))
    check('one shared fixed future condition distinguishes keep and erase in the same four-contact family',
          allowed_indices(prepared['keep'], requirement) == (0,)
          and allowed_indices(prepared['erase'], requirement) == (0, 1, 2, 3), cases=cases)
    check('restore recovers the full effect while a same-size blind difference restores all four contacts',
          prepared['restore'].state.vector == prepared['keep'].state.vector
          and allowed_indices(prepared['restore'], requirement) == (0,)
          and allowed_indices(prepared['blind'], requirement) == (0, 1, 2, 3)
          and abs(cases['blind']['hidden_norm']-cases['keep']['hidden_norm']) < 1e-12,
          hidden_norm_control_relative_error=abs(cases['blind']['hidden_norm']/cases['keep']['hidden_norm']-1))
    zero = prepare(spec=PortSpec(gain=0))
    check('zero coupling removes the permission effect', allowed_indices(zero, requirement) == (0, 1, 2, 3))
    actual = {mode: execute(select(prepared[mode], requirement, 1)) for mode in ('keep', 'erase')}
    check('current free ordinal selects among allowed contacts and actual production publication and one closure follow',
          actual['keep'].neural_contact.contact_index == 0 and actual['erase'].neural_contact.contact_index == 1
          and all(verify_occurrence(a, a.commitment) and len(a.closed_engine.rounds) == 1
                  and len(a.closed_engine.stock) == 5 and a.terminal_operation.level == 3 for a in actual.values()),
          same_current_free_choice=1, keep_contact=0, erase_contact=1,
          actual_new_sources_per_run=1, completed_consumer_flowers_per_run=1)
    alternate = alternative_requirement(prepared['keep'])
    other = execute(select(prepared['keep'], alternate.requirement, 1))
    check('a second explicitly constructed shared future frame allows another retained contact',
          allowed_indices(prepared['keep'], alternate.requirement) == (1,)
          and allowed_indices(prepared['erase'], alternate.requirement) == ()
          and verify_occurrence(other, other.commitment),
          keep_allowed=allowed_indices(prepared['keep'], alternate.requirement),
          erase_allowed=allowed_indices(prepared['erase'], alternate.requirement),
          reference_contact=1, fixture_is_constructed=True,
          actual_alternate_source_changed=other.actual_source != actual['keep'].actual_source)
    variants = []
    for start in (100, 400, 728):
        for order in ((0, 1, 2, 3), (3, 2, 1, 0), (0, 2, 1, 3)):
            cfg = CourseConfig(start_epoch=start, order=order)
            kept, erased = prepare(cfg), prepare(cfg, 'erase')
            variants.append(dict(start_epoch=start, order=order,
                keep_allowed=allowed_indices(kept, requirement), erase_allowed=allowed_indices(erased, requirement),
                minimum_rejected_error=min(float(preview(c, kept.receiver, requirement)[-1])
                    for c in kept.candidates if not admissible(c, kept.receiver, requirement))))
    check('the same port and same receiver fixture work on the nine existing source courses',
          all(v['keep_allowed'] == (0,) and v['erase_allowed'] == (0, 1, 2, 3) for v in variants),
          courses=variants, claim_is_finite_binary64_diagnostic=True)
    check('actual endpoints are not clamped and the complete neural and flower histories round trip exactly',
          all(a.actual_endpoint != a.commitment.requirement.result and a.closure_error < EPSILON/2
              and import_occurrence(json.loads(json.dumps(export_occurrence(a))), requirement,
                                    mode=mode, free_choice=1) == a for mode, a in actual.items()),
          return_coupling_implemented=False, three_flower_integration_implemented=False,
          partial_response_channel_not_full_hidden_state_transport=True)
    root = Path(__file__).resolve().parent
    paths = ['integrations/three_plus_one/outbound.py', 'integrations/three_plus_one/test_outbound.py',
             'integrations/three_plus_one/validate.py',
             'vendor/three-plus-one/SOURCE.json']
    return dict(note='RR56', passed=True, groups=len(checks), checks=checks,
        date='2026-10-17', time_engine_base_commit='c1a5bc2e6ae822633b59c6b132ad7a05c31f274d',
        three_plus_one_commit='b6daea3801504ddfa34b0a26d8e86ade94d06e06',
        protocol='fixed common future receiver; calibrated response-contrast source port',
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


if __name__ == '__main__':
    result = run()
    target = Path(__file__).with_name('outbound_result.json')
    target.write_bytes((json.dumps(result, default=encode, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(passed=True, groups=result['groups'], keep_allowed=[0], erase_allowed=[0, 1, 2, 3])))
