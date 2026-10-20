"""RR63: interruptible RR62 execution, followed by requested RR53/RR43 motion.

One tick performs one declared stage. Completion is a normal stop. C and
word choice remain supplied inputs; no scheduler or new primitive is added.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
import demand_filter as f
from demand_filter import prior, d, te

cycle = prior.cycle
QUIET = frozenset(('IDLE', 'AWAIT_CHOICE', 'ANSWERED', 'REJECTED',
                   'OUTSIDE_CHART', 'STOPPED', 'BLOCKED'))


@dataclass(frozen=True)
class Seed:
    mode: str = 'keep'
    contact: int = 1
    petal: int = 0
    gain: Q = Q(1)


@dataclass(frozen=True)
class State:
    phase: str
    engine: object
    scope: object = None
    demand: object = None
    resolution: object = None
    word: str = ''
    cursor: int = 0
    start: object = None
    errors: tuple = ()
    source: object = None
    terminal: object = None
    future_receipts: tuple = ()
    connection: object = None
    port: object = None
    exact_shift_reads: int = 0
    answers: tuple = ()


@dataclass(frozen=True)
class ExitResidue:
    terminal_operation: object


@dataclass(frozen=True)
class ExitView:
    """Verified interface to RR53; never masquerades as an RR52 receipt."""
    closed_engine: object
    residue: ExitResidue


def exit_view(state):
    e, t = state.engine, state.terminal
    if (e.phase != 'IDLE' or e.pending is not None or not e.outputs
            or t != e.outputs[-1] or t.level != 3
            or te.port.promote_word(t.cell) != t
            or t.cell.endpoint != e.upper):
        raise ValueError('a stopped actual level-three exit is required')
    return ExitView(e, ExitResidue(t))


class Session:
    def __init__(self, seed=Seed()):
        if type(seed) is not Seed:
            raise ValueError('an explicit authenticated seed is required')
        self.seed = seed
        self.archive = f.Archive()
        self.history = prior.previous.begin(seed.mode, seed.contact, seed.petal, seed.gain)
        self.entry = self.archive.register(self.history)
        self._state = State('IDLE', self.history.first.closed_engine)
        self._commands = []

    @property
    def state(self):
        return self._state

    @property
    def commands(self):
        return tuple({k: list(v) if isinstance(v, list) else v for k, v in c.items()}
                     for c in self._commands)

    def request(self, x, observation=f.ACTIONS, domain=(-64, 64)):
        return self.apply(dict(op='request', x=str(Q(x)), observation=observation,
                               domain=[str(Q(v)) for v in domain]))

    def choose(self, word):
        return self.apply(dict(op='choose', word=word))

    def connect(self, strength=Q(1, 1024)):
        return self.apply(dict(op='connect', strength=str(Q(strength))))

    def tick(self):
        if self.state.phase in QUIET:
            return False
        self.apply(dict(op='tick'))
        return True

    def run(self, max_ticks=32):
        if type(max_ticks) is not int or max_ticks < 0:
            raise ValueError('a nonnegative tick budget is required')
        for _ in range(max_ticks):
            if not self.tick():
                break
        return self.state

    def apply(self, command):
        """Commit the new immutable state only after a successful operation."""
        s = self.state
        if type(command) is not dict:
            raise ValueError('a command object is required')
        op = command.get('op')
        keys = {'request': {'op', 'x', 'observation', 'domain'},
                'choose': {'op', 'word'}, 'connect': {'op', 'strength'}, 'tick': {'op'}}
        if op not in keys or set(command) != keys[op]:
            raise ValueError('unknown command or fields')
        if op == 'request':
            if s.phase not in ('IDLE', 'ANSWERED', 'REJECTED', 'OUTSIDE_CHART'):
                raise ValueError('a new C cannot replace an active or completed actuation')
            scope = f.Scope(self.entry.digest, prior.Requirement(prior.diagonal(Q(command['x']))),
                            tuple(map(Q, command['domain'])), command['observation'])
            fresh = replace(s, phase='REQUESTED', scope=scope, demand=None, resolution=None)
        elif op == 'choose':
            if s.phase != 'AWAIT_CHOICE' or command['word'] not in s.scope.words:
                raise ValueError('current must choose an admitted word after action resolution')
            fresh = replace(s, phase='COMMITTED', word=command['word'])
        elif op == 'connect':
            if s.phase != 'STOPPED':
                raise ValueError('only a completed stopped flower may request a connection')
            exit_view(s)
            spec = te.pair.ConnectionSpec(strength=Q(command['strength']))
            fresh = replace(s, phase='CONNECT_WAIT', engine=cycle.request_boundary(s.engine),
                            connection=spec, port=None)
        else:
            if s.phase in QUIET:
                raise ValueError('no automatic transition at a stop or a choice boundary')
            fresh = self._tick(s)
        self._state = fresh
        # Keep commands as plain JSON inputs, separate from actual TE events.
        self._commands.append({k: list(v) if isinstance(v, list) else v for k, v in command.items()})
        return fresh

    def _tick(self, s):
        e = s.engine
        if s.phase == 'REQUESTED':
            demand = f.assess(self.archive, self.entry, s.scope)
            return replace(s, phase='ASSESSED', demand=demand)
        if s.phase == 'ASSESSED':
            meter = f.Meter()
            resolution = f.resolve(self.archive, self.entry, s.scope, s.demand, meter)
            phase = ('OUTSIDE_CHART' if resolution.feasible is None else
                     'REJECTED' if not resolution.feasible else
                     'ANSWERED' if s.scope.observation == f.EXISTS else 'AWAIT_CHOICE')
            return replace(s, phase=phase, resolution=resolution,
                exact_shift_reads=s.exact_shift_reads + meter.exact_shift_reads,
                answers=s.answers + ((s.scope, s.demand, resolution),))
        if s.phase == 'COMMITTED':
            f.verify_demand(self.archive, self.entry, s.scope, s.demand)
            if (s.scope.observation != f.ACTIONS or not s.resolution.feasible
                    or s.resolution.control is None):
                raise ValueError('an existence answer cannot execute a source')
            return replace(s, phase='CURRENT_WAIT', engine=cycle.request_boundary(e))
        if s.phase == 'CURRENT_WAIT':
            e = cycle.accept_context(e, self.history.first.residue.internal_context)
            if e.phase != 'OPEN':
                raise ValueError('the declared RR62 current chart must be open')
            return replace(s, phase='CURRENT_OPEN', engine=e)
        if s.phase == 'CURRENT_OPEN':
            p = e.pending
            leaf = d.AffineLetter(tuple(a+s.resolution.control*b for a, b in
                zip(self.entry.reference.weights, self.entry.axis)), self.entry.reference.library)
            wanted = tuple(cycle.qmul(p.result, cycle.inverse(p.trial_response)))
            if leaf.kernel(p.arrived_context) != wanted:
                raise ValueError('the current response changed')
            plan = cycle.CorrectionPlan(p.decoded, e.lower, p.trial_response, wanted, leaf,
                                       tuple(cycle.qmul(wanted, e.lower.live.accumulated)))
            e = cycle.event(e, 'rr62-demand-bound-source-planned', phase='PLANNED',
                            pending=replace(p, plan=plan))
            return replace(s, phase='CURRENT_PLANNED', engine=e)
        if s.phase == 'CURRENT_PLANNED':
            return replace(s, phase='CURRENT_LOWER_CLOSED', engine=cycle.execute_producer(e))
        if s.phase == 'CURRENT_LOWER_CLOSED':
            e = cycle.publish_producer(e)
            return replace(s, phase='CURRENT_AVAILABLE', engine=e, source=e.pending.issue.operation)
        if s.phase == 'CURRENT_AVAILABLE':
            start = e.pending.consumer_start
            e = cycle.event(e, 'rr62-current-word-chosen', upper=start)
            return replace(s, phase='EXECUTING', engine=e, start=start, cursor=0, errors=())
        if s.phase == 'EXECUTING':
            retained = self.history.first.residue.source
            action = {'H': e.pending.head, 'S': retained, 'T': s.source}[s.word[s.cursor]]
            cycle.available(e, action)
            e = cycle.event(e, 'rr62-current-action-executed', upper=te.port.step(action, e.upper))
            errors = s.errors + (sum(abs(a-b) for a, b in zip(e.upper.live.accumulated, prior.NEG)),)
            cursor = s.cursor + 1
            if cursor < len(s.word):
                return replace(s, engine=e, errors=errors, cursor=cursor)
            ops = tuple({'H': e.pending.head, 'S': retained, 'T': s.source}[c] for c in s.word)
            decoded = te.port.decode(s.start, ops, (prior.NEG,))
            if (e.upper.live.accumulated != prior.NEG or any(x <= te.port.EPSILON for x in errors[:-1])
                    or len(decoded.outputs) != 1 or decoded.tail or decoded.boundaries
                    or decoded.state != e.upper):
                raise ValueError('first-boundary exact closure failed')
            e = cycle.close_round(e, decoded, 'rr62-retained-plus-new')
            return replace(s, phase='CURRENT_CLOSED', engine=e, terminal=decoded.outputs[0],
                           errors=errors, cursor=cursor)
        if s.phase == 'CURRENT_CLOSED':
            exit_view(s)
            c = s.scope.requirement
            if e.upper.live.accumulated != c.inherited:
                raise ValueError('C must inherit the actual current endpoint')
            start = te.port.ExecutionState(te.port.UpperState(c.context, c.inherited), ())
            trial = te.port.step(s.terminal, start)
            decoded = te.port.decode(start, (s.terminal,), (c.target,))
            if (trial.live.accumulated != c.target or len(decoded.outputs) != 1
                    or decoded.tail or decoded.boundaries or decoded.state != trial
                    or decoded.outputs[0].level != 4
                    or te.port.promote_word(decoded.outputs[0].cell) != decoded.outputs[0]):
                raise ValueError('the actual output did not certify at the bound C')
            return replace(s, phase='STOPPED', future_receipts=s.future_receipts + ((c, trial, decoded),))
        if s.phase == 'CONNECT_WAIT':
            # The previous actual terminal is still the last output. The
            # request has only added a pending entry; never reset the tapes.
            view = ExitView(e, ExitResidue(s.terminal))
            raw, y = te.pair.connection_context(view, s.connection)
            e = cycle.accept_context(cycle.event(e, 'rr53-terminal-residue-port-emitted'), y)
            return self._connected(s, e, (raw, y))
        if s.phase == 'CONNECT_OPEN':
            return self._connected(s, cycle.resolve_open(e))
        if s.phase == 'CONNECT_PLANNED':
            return self._connected(s, cycle.execute_producer(e))
        if s.phase == 'CONNECT_LOWER_CLOSED':
            return self._connected(s, cycle.publish_producer(e))
        if s.phase == 'CONNECT_AVAILABLE':
            return self._connected(s, cycle.consume_produced(e))
        raise ValueError('unknown live phase')

    @staticmethod
    def _connected(s, e, port=None):
        phase = ('STOPPED' if e.phase == 'IDLE' else
                 'BLOCKED' if e.phase in ('CHART_STOP', 'ZERO_STOP') else 'CONNECT_' + e.phase)
        return replace(s, phase=phase, engine=e, port=s.port if port is None else port,
                       terminal=e.outputs[-1] if e.phase == 'IDLE' else s.terminal)

    def status(self):
        s = self.state
        return dict(phase=s.phase, engine_phase=s.engine.phase, word=s.word, cursor=s.cursor,
            rounds=len(s.engine.rounds), stock=len(s.engine.stock), outputs=len(s.engine.outputs),
            future_certificates=len(s.future_receipts), exact_shift_reads=s.exact_shift_reads,
            endpoint=[str(x) for x in s.engine.upper.live.accumulated],
            commands=len(self._commands), needs_current_choice=s.phase == 'AWAIT_CHOICE',
            stopped=s.phase == 'STOPPED')
