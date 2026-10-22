"""Demand revisions, selective feature reads, actual motion and exact resume."""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
import hashlib,json
import incremental_resolution as a
from incremental_resolution import m,fn,b
import mixed_execution as old_execution
from mixed_action_sets import plant,d,te,prior
import live_checkpoint as cp
from free_numbers.algebra import fingerprint,integer_text,parse_integer_text

_ISSUED=[]


def F(x):
    q=Q(x);return [integer_text(q.numerator),integer_text(q.denominator)]
def unF(x):
    if type(x) is not list or len(x)!=2 or any(type(v) is not str for v in x):raise ValueError('canonical rational pair required')
    q=Q(parse_integer_text(x[0]),parse_integer_text(x[1]))
    if F(q)!=x:raise ValueError('noncanonical rational pair')
    return q


def scope_data(scope):
    return dict(entry_digest=scope.entry_digest,diagonal=[F(x) for x in scope.diagonal],strength=F(scope.strength),
        domain=[F(x) for x in scope.domain],controls=[F(x) for x in scope.controls],words=list(scope.words),
        target=[F(x) for x in scope.target],inherited=[F(x) for x in scope.inherited],observation=scope.observation)


def read_scope(value):
    if type(value) is not dict or set(value)!={'entry_digest','diagonal','strength','domain','controls','words','target','inherited','observation'}:
        raise ValueError('the complete original scope is required')
    data=value.copy()
    for key in ('diagonal','domain','controls','target','inherited'):data[key]=tuple(unF(x) for x in data[key])
    data['strength']=unF(data['strength']);data['words']=tuple(data['words'])
    return m.Scope(**data)


def policy_data(policy):return dict(max_features=policy.max_features,modes=list(policy.modes))
def read_policy(value):
    if type(value) is not dict or set(value)!={'max_features','modes'}:raise ValueError('complete feature policy required')
    return a.Policy(value['max_features'],tuple(value['modes']))


@dataclass(frozen=True)
class Prepared:
    revision: int
    plan: object
    action: object
    used: tuple

    @property
    def digest(self):
        return fingerprint((self.revision,self.plan.digest,tuple(self.action.__dict__.values()),self.used))


@dataclass(frozen=True)
class Session:
    entry: object
    initial_scope: object
    scope: object
    policy: object
    revision: int
    phase: str
    choice: object
    prepared: object
    cache: tuple
    commands: tuple
    waiting: object
    result: object=None

    @property
    def digest(self):
        # The issued entry binds the old full history once. Do not hash the
        # latent original coefficient arrays again to decide whether to read.
        return fingerprint((self.entry.digest,self.initial_scope.digest,self.scope.digest,self.policy.digest,
            self.revision,self.phase,self.choice,self.prepared.digest if self.prepared else None,
            self.cache,self.commands,tuple(e.kind for e in self.waiting.events[len(self.entry.base.engine.events):]),
            self.result.certified if self.result else None))


def issue(session):_ISSUED.append(session);return session
def verify(session):
    if type(session) is not Session or not any(session is x for x in _ISSUED):raise ValueError('use an issued demand session')
    a.verify_entry(session.entry)


def command_text(command):return json.dumps(command,sort_keys=True,separators=(',',':'))
def history(session):return [json.loads(command) for command in session.commands]


def append(session,command,kind,**changes):
    if len(session.commands)>=100:raise ValueError('finite command budget exhausted')
    waiting=prior.cycle.event(session.waiting,kind)
    return issue(replace(session,commands=session.commands+(command_text(command),),waiting=waiting,**changes))


def start(entry,scope,policy=a.Policy()):
    a.verify_entry(entry)
    if type(scope) is not m.Scope or scope.entry_digest!=entry.base.digest:raise ValueError('original entry and scope required')
    command=dict(kind='start',scope=scope_data(scope),policy=policy_data(policy))
    waiting=prior.cycle.event(entry.base.engine,'rr67-request-bound:'+scope.digest+':'+policy.digest)
    return issue(Session(entry,scope,scope,policy,0,'BOUND',None,None,(),(command_text(command),),waiting))


def revise(session,scope,policy=None):
    verify(session)
    if session.phase=='STOPPED':raise ValueError('the completed two-flower occurrence cannot be retargeted')
    if type(scope) is not m.Scope or scope.entry_digest!=session.entry.base.digest:raise ValueError('the retained entry cannot be replaced')
    policy=session.policy if policy is None else policy
    command=dict(kind='revise',scope=scope_data(scope),policy=policy_data(policy))
    return append(session,command,'rr67-request-revised:'+scope.digest+':'+policy.digest,
        scope=scope,policy=policy,revision=session.revision+1,phase='BOUND',choice=None,prepared=None)


def choose(session,v,word):
    verify(session)
    if session.phase=='STOPPED':raise ValueError('a completed bundle stops')
    plan=a.compile(session.entry,session.scope,Q(v),word,session.policy)
    return append(session,dict(kind='choose',v=F(v),word=word),'rr67-current-chosen:'+plan.digest,
        phase='CHOSEN',choice=(Q(v),word),prepared=None)


def resolve(session,meter=None):
    verify(session)
    if session.phase!='CHOSEN':raise ValueError('the current must choose before precise resolution')
    v,word=session.choice;plan=a.compile(session.entry,session.scope,v,word,session.policy)
    action,cache,new,derived,used=a.resolve(session.entry,session.scope,session.policy,plan,session.cache,meter)
    prepared=Prepared(session.revision,plan,action,used)
    return append(session,dict(kind='resolve',revision=session.revision,mode=plan.mode,new_keys=list(new),derived_keys=list(derived),plan_digest=plan.digest),
        'rr67-demand-resolved:'+prepared.digest,phase='READY' if action.status=='ADMISSIBLE' else 'BLOCKED',
        prepared=prepared,cache=cache)


def validate_prepared(session,prepared):
    verify(session)
    if (session.phase!='READY' or type(prepared) is not Prepared or prepared!=session.prepared
        or prepared.revision!=session.revision or session.choice!=(prepared.action.v,prepared.action.word)):
        raise ValueError('the original current choice, request revision and resolved action must remain bound')
    action,cache,new,derived,used=a.resolve(session.entry,session.scope,session.policy,prepared.plan,session.cache)
    if action!=prepared.action or used!=prepared.used or new or derived:raise ValueError('the exact sufficient observation or physical action changed')


def actual_motion(session):
    """Verify with the selected observations, never by silently reading s,t."""
    p=session.prepared;validate_prepared(session,p)
    e=session.entry.base;scope=session.scope;action=p.action;before=session.waiting
    retained=e.first.flight.first.residue.source
    T=d.AffineLetter(action.T,e.library)
    ready,t=plant.produce(before,before.upper.live.context,T,'rr67-current-T-planned')
    mapping={'H':ready.pending.head,'S':retained,'U':e.U_operation,'T':t}
    first=plant.consume(ready,tuple(mapping[c] for c in action.word),'rr67-first')
    from live_flower import ExitView,ExitResidue
    raw,y=te.pair.connection_context(ExitView(first.engine,ExitResidue(first.terminal)),te.pair.ConnectionSpec(strength=scope.strength))
    values=dict(p.used);q={label:poly.exact(values)[0] for label,poly in p.plan.polynomials.items()}
    predicted=tuple(tuple(q['Y'+str(i)] if i==j else Q(0) for j in range(3)) for i in range(3))
    if y!=predicted:raise ValueError('the actual RR53 exit must equal the selected-observation prediction')
    R=d.AffineLetter(action.R,e.library)
    ready,r=plant.produce(first.engine,y,R,'rr67-current-R-planned',emitted=True)
    second=plant.consume(ready,(ready.pending.head,r),'rr67-second')
    if (second.engine.events[:len(before.events)]!=before.events or second.engine.stock[:-2]!=before.stock
        or second.engine.rounds[:-2]!=before.rounds or second.engine.outputs[:-2]!=before.outputs):
        raise ValueError('original source stock, prior decision revisions and actual clocks must all survive')
    start_state=te.port.ExecutionState(te.port.UpperState(scope.C,second.engine.upper.live.accumulated),second.engine.upper.executed_word)
    current=start_state
    for op in (first.terminal,second.terminal):current=te.port.step(op,current)
    decoded=te.port.decode(start_state,(first.terminal,second.terminal),(scope.target,))
    ok=bool(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries and current.live.accumulated==scope.target
        and decoded.state==current and len(decoded.outputs[0].cell.beta)==2 and decoded.outputs[0].level==4)
    if not ok:raise ValueError('actual two-flower actuation must certify the fixed bundle requirement')
    return old_execution.Execution(scope.digest,action,first,second,(raw,y),start_state,current,decoded,True)


def execute(session,prepared=None):
    prepared=session.prepared if prepared is None else prepared
    validate_prepared(session,prepared)
    committed=append(session,dict(kind='execute',prepared_digest=prepared.digest),
        'rr67-demand-and-current-committed:'+prepared.digest)
    result=actual_motion(committed)
    return issue(replace(committed,phase='STOPPED',result=result,waiting=result.second.engine))


def replay(entry,commands):
    if type(commands) is not list or not 1<=len(commands)<=100:raise ValueError('finite command history required')
    first=commands[0]
    if type(first) is not dict or set(first)!={'kind','scope','policy'} or first['kind']!='start':raise ValueError('explicit original request required')
    session=start(entry,read_scope(first['scope']),read_policy(first['policy']))
    for command in commands[1:]:
        if type(command) is not dict or 'kind' not in command:raise ValueError('known command required')
        kind=command['kind']
        if kind=='revise' and set(command)=={'kind','scope','policy'}:session=revise(session,read_scope(command['scope']),read_policy(command['policy']))
        elif kind=='choose' and set(command)=={'kind','v','word'}:session=choose(session,unF(command['v']),command['word'])
        elif kind=='resolve' and set(command)=={'kind','revision','mode','new_keys','derived_keys','plan_digest'}:session=resolve(session)
        elif kind=='execute' and set(command)=={'kind','prepared_digest'}:session=execute(session)
        else:raise ValueError('unsupported or changed command')
        if json.loads(session.commands[-1])!=command:raise ValueError('the declared observation, query or current choice changed')
    return session


def archives(entry):
    from free_numbers.checkpoint import dumps
    # All exact values, including unused originals, are retained in both vaults.
    base_raw,base_h=dumps((fn.read(entry.base.S,fn.compression(2)),fn.read(entry.base.U,fn.compression(2))),entry.base.vault)
    derived_raw,derived_h=dumps((b.number(0),),entry.derived)
    return dict(base=base_raw.hex(),base_sha256=base_h,derived=derived_raw.hex(),derived_sha256=derived_h)


def view(session):
    return dict(digest=session.digest,phase=session.phase,revision=session.revision,scope_digest=session.scope.digest,
        choice=([F(session.choice[0]),session.choice[1]] if session.choice else None),
        mode=session.prepared.plan.mode if session.prepared else None,
        action_status=session.prepared.action.status if session.prepared else None,
        cached_keys=[k for k,value in session.cache],
        read_log=[dict(revision=c['revision'],mode=c['mode'],new_keys=c['new_keys'],derived_keys=c['derived_keys']) for c in history(session) if c['kind']=='resolve'],
        certified=session.result.certified if session.result else False)


def dumps(session):
    verify(session)
    if replay(session.entry,history(session)).digest!=session.digest:raise ValueError('issued session must match its complete command replay')
    doc=dict(schema='time-engine-rr67-adaptive-session-v1',entry_digest=session.entry.digest,
        commands=history(session),state=view(session),numbers=archives(session.entry),
        waiting=cp.pack(session.waiting),occurrence=old_execution.graph(session.result) if session.result else None)
    raw=(json.dumps(doc,separators=(',',':'))+'\n').encode()
    if len(raw)>20_000_000:raise ValueError('finite checkpoint byte budget exceeded')
    return raw,hashlib.sha256(raw).hexdigest()


def loads(raw,trusted_sha256,entry,expected_initial_scope,expected_current_scope=None,expected_choice=None):
    a.verify_entry(entry)
    if type(raw) is not bytes or len(raw)>20_000_000 or hashlib.sha256(raw).hexdigest()!=trusted_sha256:
        raise ValueError('externally trusted bounded checkpoint bytes required')
    doc=json.loads(raw)
    if (type(doc) is not dict or set(doc)!={'schema','entry_digest','commands','state','numbers','waiting','occurrence'}
        or doc['schema']!='time-engine-rr67-adaptive-session-v1' or doc['entry_digest']!=entry.digest):raise ValueError('original adaptive entry required')
    if (type(doc['commands']) is not list or not 1<=len(doc['commands'])<=100
        or type(doc['commands'][0]) is not dict or set(doc['commands'][0])!={'kind','scope','policy'}
        or doc['commands'][0]['kind']!='start' or read_scope(doc['commands'][0]['scope'])!=expected_initial_scope):
        raise ValueError('the original initial requirement changed')
    if type(doc['numbers']) is not dict or set(doc['numbers'])!={'base','base_sha256','derived','derived_sha256'}:
        raise ValueError('both complete number archives are required')
    from free_numbers.checkpoint import loads as load
    for key in ('base','derived'):load(bytes.fromhex(doc['numbers'][key]),doc['numbers'][key+'_sha256'])
    if doc['numbers']!=archives(entry):raise ValueError('originals, derived features or their authenticated relations changed')
    session=replay(entry,doc['commands'])
    if (view(session)!=doc['state'] or cp.unpack(doc['waiting'])!=cp.unpack(cp.pack(session.waiting))
        or (old_execution.graph(session.result) if session.result else None)!=doc['occurrence']):
        raise ValueError('the actual chronology, source inheritance or resolved occurrence changed')
    if expected_current_scope is not None and session.scope!=expected_current_scope:raise ValueError('current request changed')
    if expected_choice is not None and session.choice!=expected_choice:raise ValueError('the original current selection changed')
    return session
