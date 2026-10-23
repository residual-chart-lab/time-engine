"""Actually produce and publish both demanded sources, then certify the bundle."""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
import bundle_demand as b
from bundle_demand import prior,d,te,fn
import live_checkpoint as checkpoint

cycle=prior.cycle


@dataclass(frozen=True)
class FlowerExecution:
    engine: object
    terminal: object
    new_source: object
    context: tuple
    prefix_errors: tuple


@dataclass(frozen=True)
class BundleExecution:
    scope_digest: str
    recipe_digest: str
    resolution: object
    control: Q
    first: FlowerExecution
    second: FlowerExecution
    port: tuple
    upper_start: object
    upper_trial: object
    upper_decoded: object
    certified: bool
    future_prefix_errors: tuple


def produce(engine,context,leaf,kind,emitted=False):
    before=engine
    engine=cycle.request_boundary(engine)
    if emitted:engine=cycle.event(engine,'rr53-terminal-residue-port-emitted')
    engine=cycle.accept_context(engine,context)
    if engine.phase!='OPEN':raise ValueError('the declared current head must leave one nonzero open tail')
    p=engine.pending
    wanted=tuple(cycle.qmul(p.result,cycle.inverse(p.trial_response)))
    if leaf.kernel(context)!=wanted:raise ValueError('the source must close from the actual inherited current state')
    plan=cycle.CorrectionPlan(p.decoded,engine.lower,p.trial_response,wanted,leaf,
        tuple(cycle.qmul(wanted,engine.lower.live.accumulated)))
    engine=cycle.event(engine,kind,phase='PLANNED',pending=replace(p,plan=plan))
    engine=cycle.publish_producer(cycle.execute_producer(engine))
    source=engine.pending.issue.operation
    if (source not in engine.stock or source.level!=2 or engine.stock[:-1]!=before.stock
            or source.cell.start.live.accumulated!=before.lower.live.accumulated):
        raise ValueError('actual source certification and publication must precede consumption')
    return engine,source


def consume(engine,ops,route):
    start=engine.pending.consumer_start
    engine=cycle.event(engine,route+'-word-chosen',upper=start)
    errors=[]
    for op in ops:
        cycle.available(engine,op)
        engine=cycle.event(engine,route+'-action-executed',upper=te.port.step(op,engine.upper))
        errors.append(sum(abs(a-c) for a,c in zip(engine.upper.live.accumulated,b.NEG)))
    decoded=te.port.decode(start,ops,(b.NEG,))
    if (engine.upper.live.accumulated!=b.NEG or any(e<=te.port.EPSILON for e in errors[:-1])
            or len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries or decoded.state!=engine.upper):
        raise ValueError('each flower must close at its first nonempty actual boundary')
    source=engine.pending.issue.operation
    engine=cycle.close_round(engine,decoded,route)
    return FlowerExecution(engine,decoded.outputs[0],source,start.live.context,tuple(errors))


def execute(entry,scope,recipe,assessment,resolution,control_test=None):
    b.verify_recipe(entry,scope,recipe)
    expected=b.resolve(entry,scope,recipe,assessment,fn.Meter())
    if (scope.observation!=b.ACTIONS or resolution!=expected or not resolution.feasible or resolution.control is None):
        raise ValueError('a bound exact action resolution is required; feasibility alone cannot actuate')
    control=resolution.control if control_test is None else Q(control_test)
    if not scope.domain[0]<=control<=scope.domain[1]:raise ValueError('the declared later resource interval changed')
    # The original one-flower history is authenticated, never replaced with a
    # candidate future history or a receipt from a different requirement.
    prior.previous.verify_flight(entry.flight)
    before=entry.flight.first.closed_engine
    retained=entry.flight.first.residue.source
    cycle.available(before,retained)
    first_leaf=d.AffineLetter(tuple(a+scope.first_control*v for a,v in zip(
        entry.flight.pair.representative.weights,entry.axis)),entry.library)
    ready,t=produce(before,entry.flight.first.residue.internal_context,first_leaf,'rr64-first-source-planned')
    mapping={'H':ready.pending.head,'S':retained,'T':t}
    first=consume(ready,tuple(mapping[c] for c in scope.first_word),'rr64-first')
    from live_flower import ExitView,ExitResidue
    raw_y,actual_y=te.pair.connection_context(ExitView(first.engine,ExitResidue(first.terminal)),
                                       te.pair.ConnectionSpec(strength=scope.strength))
    scalars=dict(resolution.exact_values)
    values=b.polynomial_values(recipe,scalars)
    predicted=tuple(tuple(values['Y'+str(i)] if i==j else Q(0) for j in range(3)) for i in range(3))
    if actual_y!=predicted:raise ValueError('the future demand must use the actual first exit and unchanged RR53 port')
    h=values['head2'];y0,y1,y2=(actual_y[i][i] for i in range(3))
    denominator=y0-y1
    a=((1/h+1)/2-y1)/denominator
    axis=((y1-y2)/denominator,(y2-y0)/denominator,Q(1),Q(0),Q(0),Q(0))
    base=(a,1-a,Q(0),Q(0),Q(0),Q(0))
    source=d.AffineLetter(tuple(u+control*v for u,v in zip(base,axis)),entry.library)
    if source.kernel(actual_y)!=(1/h,0,0,0):raise ValueError('the future-selected source lost its current null freedom')
    ready,r=produce(first.engine,actual_y,source,'rr64-bundle-bound-source-planned',emitted=True)
    second=consume(ready,(ready.pending.head,r),'rr64-second')
    if (second.engine.events[:len(first.engine.events)]!=first.engine.events or
            second.engine.rounds[:-1]!=first.engine.rounds or second.engine.outputs[:-1]!=first.engine.outputs or
            second.engine.stock[:-1]!=first.engine.stock):
        raise ValueError('the second flower must inherit actual stock, clocks, outputs and history')
    start=te.port.ExecutionState(te.port.UpperState(scope.context,second.engine.upper.live.accumulated),
                                second.engine.upper.executed_word)
    current=start;errors=[]
    for operation in (first.terminal,second.terminal):
        current=te.port.step(operation,current)
        errors.append(sum(abs(x-y) for x,y in zip(current.live.accumulated,scope.target)))
    decoded=te.port.decode(start,(first.terminal,second.terminal),(scope.target,))
    ok=bool(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries and
            current.live.accumulated==scope.target and decoded.state==current and
            len(decoded.outputs[0].cell.beta)==2 and decoded.outputs[0].level==4)
    if ok and (errors[0]<=te.port.EPSILON or te.port.promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]):
        raise ValueError('the two outputs must form one certified first-boundary upper cell')
    if control_test is None and not ok:raise ValueError('predicted bundle actuation failed its actual upper certificate')
    return BundleExecution(scope.digest,recipe.digest,resolution,control,first,second,(raw_y,actual_y),start,current,decoded,ok,tuple(errors))


def graph(record):
    return checkpoint.pack((record.first.engine,record.first.terminal,record.first.new_source,
        record.second.engine,record.second.terminal,record.second.new_source,record.upper_start,
        record.upper_trial,record.upper_decoded,record.port))


def dumps(entry,scope,recipe,assessment,record):
    import json,hashlib
    from free_numbers.checkpoint import dumps as save_numbers
    if not record.certified or record.control!=record.resolution.control:
        raise ValueError('a failed control cannot become a completed bundle record')
    if record!=execute(entry,scope,recipe,assessment,record.resolution):raise ValueError('the actual two-flower occurrence changed')
    retained_raw,retained_sha=save_numbers(recipe.expressions,entry.vault)
    doc=dict(schema='time-engine-rr64-bundle-occurrence-v1',entry_digest=entry.digest,scope_digest=scope.digest,
        recipe_digest=recipe.digest,graph=graph(record),number_state=retained_raw.hex(),number_sha256=retained_sha)
    raw=(json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    return raw,hashlib.sha256(raw).hexdigest()


def loads(raw,trusted_sha256,entry,scope):
    import json,hashlib
    from free_numbers.checkpoint import loads as read_numbers,dumps as save_numbers
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=trusted_sha256:
        raise ValueError('the complete occurrence requires its external trusted hash')
    doc=json.loads(raw)
    if (set(doc)!={'schema','entry_digest','scope_digest','recipe_digest','graph','number_state','number_sha256'} or
            doc['schema']!='time-engine-rr64-bundle-occurrence-v1' or doc['entry_digest']!=entry.digest or doc['scope_digest']!=scope.digest):
        raise ValueError('the entry, future requirement or current selection was substituted')
    recipe=b.build(entry,scope)
    if doc['recipe_digest']!=recipe.digest:raise ValueError('the bound demand recipe changed')
    roots,vault=read_numbers(bytes.fromhex(doc['number_state']),doc['number_sha256'])
    if tuple(r.digest for r in roots)!=tuple(r.digest for r in recipe.expressions):
        raise ValueError('the retained observation graphs changed')
    expected_numbers,expected_sha=save_numbers(recipe.expressions,entry.vault)
    if bytes.fromhex(doc['number_state'])!=expected_numbers or doc['number_sha256']!=expected_sha:
        raise ValueError('the retained exact values or complete archive changed')
    # Trusted outer bytes bind the complete TE graph and retained number state.
    # Independent exact replay binds them to the original request and chronology.
    assessment=b.assess(entry,scope,recipe);resolution=b.resolve(entry,scope,recipe,assessment)
    actual=execute(entry,scope,recipe,assessment,resolution)
    if checkpoint.unpack(doc['graph'])!=checkpoint.unpack(graph(actual)):
        raise ValueError('the actual stock, endpoint, source or chronology changed')
    return actual
