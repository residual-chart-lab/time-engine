"""Actual certified sources and flowers for the RR65 mixed action observation."""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
import hashlib,json
import mixed_action_sets as m
from mixed_action_sets import b,plant,d,te,prior,fn
import live_checkpoint as cp


@dataclass(frozen=True)
class Execution:
    scope_digest: str
    action: object
    first: object
    second: object
    port: tuple
    upper_start: object
    upper_trial: object
    upper_decoded: object
    certified: bool
    counterfactual: bool=False


def run(entry,scope,action,counterfactual_alpha=None):
    expected=(m.joint_action(entry,scope,action.v,action.word) if action.read_keys==('p',) else
              m.action(entry,scope,action.v,action.word))
    if counterfactual_alpha is None and (expected.status!='ADMISSIBLE' or action.T!=expected.T or action.R!=expected.R or action.alpha!=expected.alpha
        or action.scope_digest!=scope.digest or action.recipe_digest!=expected.recipe_digest or action.status!='ADMISSIBLE'):
        raise ValueError('a bound physical action is required')
    if action.scope_digest!=scope.digest or action.recipe_digest!=m.build(entry,scope,action.v,action.word).digest:
        raise ValueError('the current choice or bundle requirement changed')
    # Registration has already executed and certified the retained U in this
    # same stock. No foreign historical operation is silently inserted.
    before=entry.engine
    retained=entry.first.flight.first.residue.source
    T_weights=tuple(a+action.v*z for a,z in zip(entry.first.flight.pair.representative.weights,entry.first.axis))
    T=d.AffineLetter(T_weights,entry.library)
    ready,t=plant.produce(before,before.upper.live.context,T,'rr65-current-T-planned')
    mapping={'H':ready.pending.head,'S':retained,'U':entry.U_operation,'T':t}
    first=plant.consume(ready,tuple(mapping[k] for k in action.word),'rr65-first')
    from live_flower import ExitView,ExitResidue
    raw,y=te.pair.connection_context(ExitView(first.engine,ExitResidue(first.terminal)),te.pair.ConnectionSpec(strength=scope.strength))
    if any(y[i][j] for i in range(3) for j in range(3) if i!=j):raise ValueError('RR65 execution requires its declared diagonal chart')
    if counterfactual_alpha is None:weights=action.R
    else:
        alpha=Q(counterfactual_alpha)
        if not scope.domain[0]<=alpha<=scope.domain[1]:raise ValueError('negative control escaped its declared resource interval')
        h=prior.scalar(entry.head.kernel(y));y0,y1,y2=(y[i][i] for i in range(3));dy=y0-y1
        a=((1/h+1)/2-y1)/dy
        weights=(a+alpha*(y1-y2)/dy,1-a+alpha*(y2-y0)/dy,alpha,Q(0),Q(0),Q(0))
    R=d.AffineLetter(weights,entry.library)
    ready,r=plant.produce(first.engine,y,R,'rr65-current-R-planned',emitted=True)
    second=plant.consume(ready,(ready.pending.head,r),'rr65-second')
    if (second.engine.events[:len(before.events)]!=before.events or second.engine.stock[:-2]!=before.stock
        or second.engine.rounds[:-2]!=before.rounds or second.engine.outputs[:-2]!=before.outputs):
        raise ValueError('the complete prior stock and chronology must remain inherited')
    start=te.port.ExecutionState(te.port.UpperState(scope.C,second.engine.upper.live.accumulated),second.engine.upper.executed_word)
    current=start
    for op in (first.terminal,second.terminal):current=te.port.step(op,current)
    decoded=te.port.decode(start,(first.terminal,second.terminal),(scope.target,))
    certified=bool(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries
        and current.live.accumulated==scope.target and decoded.state==current
        and len(decoded.outputs[0].cell.beta)==2 and decoded.outputs[0].level==4)
    if counterfactual_alpha is None and not certified:raise ValueError('predicted physical bundle action failed')
    return Execution(scope.digest,action,first,second,(raw,y),start,current,decoded,certified,counterfactual_alpha is not None)


def graph(record):
    return cp.pack((record.first.engine,record.first.terminal,record.first.new_source,
        record.second.engine,record.second.terminal,record.second.new_source,record.port,
        record.upper_start,record.upper_trial,record.upper_decoded))


def dumps(entry,scope,record):
    if not record.certified or record.counterfactual or record!=run(entry,scope,record.action):
        raise ValueError('only a replayed certified occurrence can become a completed record')
    from free_numbers.checkpoint import dumps as save
    recipe=m.build(entry,scope,record.action.v,record.action.word)
    numbers,h=save(recipe.roots,entry.vault)
    value=dict(schema='time-engine-rr65-mixed-occurrence-v1',entry=entry.digest,scope=scope.digest,
        v=str(record.action.v),word=record.action.word,joint=record.action.read_keys==('p',),
        graph=graph(record),numbers=numbers.hex(),number_sha256=h)
    raw=(json.dumps(value,separators=(',',':'))+'\n').encode()
    return raw,hashlib.sha256(raw).hexdigest()


def loads(raw,trusted,entry,scope,expected_v,expected_word):
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=trusted:raise ValueError('externally trusted complete occurrence bytes required')
    value=json.loads(raw)
    if (set(value)!={'schema','entry','scope','v','word','joint','graph','numbers','number_sha256'}
        or value['schema']!='time-engine-rr65-mixed-occurrence-v1' or value['entry']!=entry.digest
        or value['scope']!=scope.digest or type(value['joint']) is not bool):raise ValueError('original entry and demand must be retained')
    v=Q(value['v']);word=value['word'];recipe=m.build(entry,scope,v,word)
    if v!=Q(expected_v) or word!=expected_word:raise ValueError('the original current selection changed')
    from free_numbers.checkpoint import dumps as save,loads as load
    roots,vault=load(bytes.fromhex(value['numbers']),value['number_sha256'])
    expected,expected_h=save(recipe.roots,entry.vault)
    if bytes.fromhex(value['numbers'])!=expected or value['number_sha256']!=expected_h:
        raise ValueError('original s,t, authenticated p relation, or number graphs changed')
    action=(m.joint_action if value['joint'] else m.action)(entry,scope,v,word)
    result=run(entry,scope,action)
    if cp.unpack(value['graph'])!=cp.unpack(graph(result)):raise ValueError('actual endpoint, sources, inheritance or chronology changed')
    return result
