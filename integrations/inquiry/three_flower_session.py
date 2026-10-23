"""RR69: staged three-flower motion and replay of immutable retained history."""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
import hashlib,json
import three_flower_synthesis as n
from three_flower_synthesis import a,m,b,fn,prior,d,te,plant
import synthesized_session as old
import live_checkpoint as cp

SCHEMA='time-engine-rr69-three-flower-session-v1'
MAX_COMMANDS=100
_STATES=[]

@dataclass(frozen=True)
class State:
    entry: object
    scope: object
    phase: str
    commands: tuple
    choice: object=None
    plan: object=None
    action: object=None
    cache: tuple=()
    engine: object=None
    flowers: tuple=()
    ports: tuple=()
    upper: tuple=()
    certified: bool=False


def issue(state):_STATES.append(state);return state

def verify(state):
    if type(state) is not State or not any(state is x for x in _STATES):raise ValueError('issued three-flower state required')
    a.verify_entry(state.entry)
    if state.plan is not None:n.verify_plan(state.entry,state.scope,state.plan)
    return True

def append(state,command,**changes):
    if len(state.commands)>=MAX_COMMANDS:raise ValueError('finite command budget exhausted')
    return issue(replace(state,commands=state.commands+(json.dumps(command,sort_keys=True,separators=(',',':')),),**changes))

def scope_data(scope):return dict(original=old.scope_data(a.Scope(scope.base_scope,scope.frame)),last_strength=old.F(scope.last_strength),middle_controls=[old.F(x) for x in scope.middle_controls])

def read_scope(value):
    if type(value) is not dict or set(value)!={'original','last_strength','middle_controls'}:raise ValueError('complete three-flower requirement required')
    raw=old.read_scope(value['original'])
    return n.Scope(raw.base_scope,old.unF(value['last_strength']),tuple(old.unF(x) for x in value['middle_controls']),raw.frame)


def start(entry,scope):
    a.verify_entry(entry)
    if type(scope) is not n.Scope or scope.base_scope.entry_digest!=entry.base.digest:raise ValueError('original retained entry required')
    command=json.dumps(dict(kind='start',scope=scope_data(scope)),sort_keys=True,separators=(',',':'))
    return issue(State(entry,scope,'BOUND',(command,),engine=entry.base.engine))


def choose(state,v,u,word):
    verify(state)
    if state.flowers or state.phase=='STOPPED':raise ValueError('closed past cannot be retargeted')
    plan=n.compile(state.entry,state.scope,v,u,word)
    return append(state,dict(kind='choose',v=old.F(v),u=old.F(u),word=word),phase='CHOSEN',choice=(Q(v),Q(u),word),plan=plan,action=None)


def resolve(state,meter=None):
    verify(state)
    if state.phase!='CHOSEN':raise ValueError('choose before reading')
    action,cache,work=n.resolve(state.entry,state.scope,state.plan,state.cache,meter)
    return append(state,dict(kind='resolve'),phase='READY' if action.status=='ADMISSIBLE' else 'REJECTED',action=action,cache=cache),work


def arrived(state,previous):
    from live_flower import ExitView,ExitResidue
    strength=state.scope.base_scope.strength if not state.ports else state.scope.last_strength
    raw,y=te.pair.connection_context(ExitView(previous.engine,ExitResidue(previous.terminal)),te.pair.ConnectionSpec(strength=strength))
    prefix='Y2_' if not state.ports else 'Y3_';pred=dict(state.action.values)
    expected=tuple(tuple(pred[prefix+str(i)] if i==j else Q(0) for j in range(3)) for i in range(3))
    if y!=expected:raise ValueError('actual ordered exit and reconstructed context disagree')
    return raw,y


def advance(state):
    verify(state)
    if state.phase not in ('READY','CLOSED1','CLOSED2','CLOSED3'):raise ValueError('a prepared admissible action or a closed preceding flower is required')
    before=state.engine;action=state.action;base=state.entry.base
    if state.phase=='READY':
        T=d.AffineLetter(action.T,base.library)
        ready,t=plant.produce(before,before.upper.live.context,T,'rr69-first-source-planned')
        retained=base.first.flight.first.residue.source
        mapping={'H':ready.pending.head,'S':retained,'U':base.U_operation,'T':t}
        flower=plant.consume(ready,tuple(mapping[k] for k in state.plan.word),'rr69-first')
        ports=state.ports
    elif state.phase in ('CLOSED1','CLOSED2'):
        raw,y=arrived(state,state.flowers[-1]);index=len(state.flowers)+1
        leaf=d.AffineLetter(action.R2 if index==2 else action.R3,base.library)
        ready,r=plant.produce(before,y,leaf,'rr69-source-'+str(index)+'-planned',emitted=True)
        flower=plant.consume(ready,(ready.pending.head,r),'rr69-flower-'+str(index));ports=state.ports+((raw,y),)
    else:
        start_state=te.port.ExecutionState(te.port.UpperState(state.scope.C,before.upper.live.accumulated),before.upper.executed_word)
        current=start_state;errors=[];operations=tuple(x.terminal for x in state.flowers)
        for op in operations:
            current=te.port.step(op,current);errors.append(sum(abs(x-y) for x,y in zip(current.live.accumulated,state.scope.base_scope.target)))
        decoded=te.port.decode(start_state,operations,(state.scope.base_scope.target,))
        certified=bool(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries
            and current.live.accumulated==state.scope.base_scope.target and decoded.state==current
            and len(decoded.outputs[0].cell.beta)==3 and decoded.outputs[0].level==4
            and all(x>te.port.EPSILON for x in errors[:-1]) and errors[-1]==0
            and te.port.promote_word(decoded.outputs[0].cell)==decoded.outputs[0])
        if not certified:raise ValueError('actual three-flower upper certificate failed')
        return append(state,dict(kind='advance'),phase='STOPPED',upper=(start_state,current,decoded,tuple(errors)),certified=True)
    if (flower.engine.events[:len(before.events)]!=before.events or flower.engine.stock[:-1]!=before.stock
        or flower.engine.outputs[:-1]!=before.outputs or flower.engine.rounds[:-1]!=before.rounds
        or flower.engine.upper.live.accumulated!=b.NEG):raise ValueError('every new flower must inherit actual stock, past and endpoint')
    return append(state,dict(kind='advance'),phase='CLOSED'+str(len(state.flowers)+1),engine=flower.engine,flowers=state.flowers+(flower,),ports=ports)


def finish(state):
    while state.phase in ('READY','CLOSED1','CLOSED2','CLOSED3'):state=advance(state)
    return state


def graph(state):
    return cp.pack((state.engine,tuple((f.engine,f.terminal,f.new_source,f.context,f.prefix_errors) for f in state.flowers),state.ports,state.upper))


def payload(state):
    return dict(schema=SCHEMA,entry=state.entry.digest,scope=scope_data(state.scope),commands=[json.loads(x) for x in state.commands],
        phase=state.phase,certified=state.certified,plan_digest=state.plan.digest if state.plan else None,
        action=dict(status=state.action.status,T=list(map(old.F,state.action.T)),R2=list(map(old.F,state.action.R2)),R3=list(map(old.F,state.action.R3)),
                    alpha=old.F(state.action.alpha) if state.action.alpha is not None else None) if state.action else None,
        cache=[[key,digest,old.F(value)] for key,(digest,value) in state.cache],numbers=old.archives(state.entry,state.cache),graph=graph(state))


def dumps(state):
    verify(state)
    raw=(json.dumps(payload(state),separators=(',',':'))+'\n').encode()
    return raw,hashlib.sha256(raw).hexdigest()


def loads(raw,trusted,entry,scope,expected_choice=None):
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=trusted:raise ValueError('external trusted snapshot hash required')
    value=json.loads(raw)
    if set(value)!={'schema','entry','scope','commands','phase','certified','plan_digest','action','cache','numbers','graph'} or value['schema']!=SCHEMA:
        raise ValueError('complete three-flower snapshot required')
    if value['entry']!=entry.digest or value['scope']!=scope_data(scope):raise ValueError('original entry and request required')
    commands=value['commands']
    if type(commands) is not list or not 1<=len(commands)<=MAX_COMMANDS or commands[0]!={'kind':'start','scope':scope_data(scope)}:raise ValueError('complete bounded chronology required')
    state=start(entry,scope)
    for command in commands[1:]:
        if type(command) is not dict:raise ValueError('typed replay command required')
        if command.get('kind')=='choose' and set(command)=={'kind','v','u','word'}:
            state=choose(state,old.unF(command['v']),old.unF(command['u']),command['word'])
        elif command=={'kind':'resolve'}:state=resolve(state)[0]
        elif command=={'kind':'advance'}:state=advance(state)
        else:raise ValueError('unknown replay command')
    if expected_choice is not None and state.choice!=expected_choice:raise ValueError('original current choice required')
    if payload(state)!=value:raise ValueError('observations, action, past, exact endpoint or chronology changed')
    return state
