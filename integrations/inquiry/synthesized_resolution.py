"""RR68: discover sufficient observations, authenticate them, actuate TE."""
from dataclasses import dataclass,field
from fractions import Fraction as Q
import incremental_resolution as core
from incremental_resolution import m,fn,b,prior,Polynomial,fingerprint
from free_numbers.evaluate import enclose
import observation_synthesis as synthesis

SCHEMA='RR68-graded-observation-v1'
Policy=synthesis.Budget
_ISSUED=[];_OBSERVATIONS={}


@dataclass(frozen=True)
class Scope:
    base_scope: object
    frame: tuple=(Q(1),Q(0),Q(0),Q(1))
    def __post_init__(self):
        object.__setattr__(self,'frame',tuple(map(Q,self.frame)))
        if type(self.base_scope) is not m.Scope or len(self.frame)!=4 or not self.frame[0]*self.frame[3]-self.frame[1]*self.frame[2]:
            raise ValueError('original TE scope and invertible exact frame required')
    def __getattr__(self,name):
        if name in m.Scope.__dataclass_fields__ or name=='C':return getattr(self.base_scope,name)
        raise AttributeError(name)
    @property
    def digest(self):return fingerprint((self.base_scope.digest,self.frame))


@dataclass(frozen=True)
class Observation:
    key: str
    coefficients: tuple
    origin: str
    envelope: tuple


@dataclass(frozen=True)
class Entry:
    core: object
    derived: object
    digest: str
    _plans: dict=field(default_factory=dict,compare=False,repr=False)
    _proofs: dict=field(default_factory=dict,compare=False,repr=False)
    _observations: dict=field(default_factory=dict,compare=False,repr=False)
    _work: list=field(default_factory=list,compare=False,repr=False)
    @property
    def base(self):return self.core.base


def register(modes=('keep','keep')):
    previous=core.register(modes);entry=Entry(previous,fn.Vault(),fingerprint((SCHEMA,previous.digest)))
    _ISSUED.append(entry);return entry


def verify_entry(entry):
    if type(entry) is not Entry or not any(entry is old for old in _ISSUED):raise ValueError('issued synthesis entry required')
    core.verify_entry(entry.core)


def in_frame(polys,frame):
    a,b_,c,d=frame;det=a*d-b_*c;x,y=synthesis.variable('x'),synthesis.variable('y')
    inverse={'s':x.scaled(d/det).add(y.scaled(-b_/det)),'t':x.scaled(-c/det).add(y.scaled(a/det))}
    return {label:synthesis.expand(poly,inverse) for label,poly in polys.items()}


def observe(entry,definition):
    coeff=synthesis.data(definition);key='obs-'+fingerprint(coeff)
    if key in entry._observations:
        old=entry._observations[key]
        if _OBSERVATIONS.get(id(old)) is not old or old.coefficients!=coeff:raise ValueError('issued observation definition changed')
        return old
    intervals={k:entry.base.vault.reference(k).envelope for k in definition.dependencies}
    envelope=enclose(coeff,intervals,192)[0]
    origin=fingerprint((SCHEMA,entry.digest,'exact-synthesized-definition',coeff))
    result=Observation(key,coeff,origin,envelope);_OBSERVATIONS[id(result)]=result;entry._observations[key]=result;return result


@dataclass(frozen=True)
class Plan:
    entry_digest: str
    scope_digest: str
    policy_digest: str
    recipe_digest: str
    v: Q
    word: str
    mode: str
    status: str
    features: tuple
    coefficients: tuple
    definitions: tuple
    proof: object
    @property
    def digest(self):return fingerprint((self.entry_digest,self.scope_digest,self.policy_digest,self.recipe_digest,
        self.v,self.word,self.mode,self.status,self.features,self.coefficients,self.definitions,self.proof.digest if self.proof else None))
    @property
    def polynomials(self):return {label:Polynomial(coeff) for label,coeff in self.coefficients}


def compile(entry,scope,v,word,policy=Policy()):
    verify_entry(entry);v=Q(v)
    if type(scope) is not Scope or type(policy) is not Policy or scope.entry_digest!=entry.base.digest:
        raise ValueError('the original request, frame and finite synthesis policy are required')
    key=(scope.digest,v,word,tuple(policy.__dict__.values()))
    if key in entry._plans:return entry._plans[key]
    roots,_=core.graph(entry.core,scope.base_scope,v,word,core.Work());original={k:core.P(n) for k,n in roots.items()}
    recipe_digest=fingerprint((SCHEMA,entry.digest,scope.digest,v,word,tuple((k,p.digest) for k,p in original.items())))
    policy_digest=fingerprint(tuple(policy.__dict__.values()))
    initial=core.assessed(entry.core,scope.base_scope,original,
        {k:entry.base.vault.coarse(k,fn.Meter()) for k in m.KEYS},core.Work())
    def issue(status,proof=None,features=(),converted=(),definitions=()):
        plan=Plan(entry.digest,scope.digest,policy_digest,recipe_digest,v,word,
            'SYNTHESIZED_'+str(len(features)) if status=='AVAILABLE' else 'CONSTANT' if status in ('EMPTY','UNKNOWN_CHART') else 'UNRESOLVED',
            status,tuple(features),tuple(converted),tuple(definitions),proof)
        entry._plans[key]=plan;return plan
    if initial in ('EMPTY','UNKNOWN_CHART'):return issue(initial)
    demands=in_frame(original,scope.frame)
    proof_key=(fingerprint(tuple((k,synthesis.data(p)) for k,p in demands.items())),tuple(policy.__dict__.values()))
    if proof_key not in entry._proofs:entry._proofs[proof_key]=synthesis.discover(demands,budget=policy)
    proof=entry._proofs[proof_key]
    if proof.status!='AVAILABLE':return issue(proof.status,proof)
    synthesis.verify(demands,proof,policy)
    a,b_,c,d=scope.frame;s,t=synthesis.variable('s'),synthesis.variable('t')
    forward={'x':s.scaled(a).add(t.scaled(b_)),'y':s.scaled(c).add(t.scaled(d))}
    replace={};definitions=[]
    for name,coeff in proof.definitions:
        definition=synthesis.expand(Polynomial(coeff),forward)
        lead=definition.terms[min(definition.terms)][0];definition=definition.scaled(1/lead)
        observation=observe(entry,definition);definitions.append((observation.key,observation.coefficients))
        replace[name]=synthesis.variable(observation.key).scaled(lead)
    converted={label:synthesis.expand(Polynomial(coeff),replace) for label,coeff in proof.outputs}
    actual={key:Polynomial(coeff) for key,coeff in definitions}
    if any(synthesis.expand(converted[label],actual).terms!=poly.terms for label,poly in original.items()):
        raise AssertionError('physical-coordinate synthesis identity failed')
    return issue('AVAILABLE',proof,[key for key,coeff in definitions],
        [(label,synthesis.data(poly)) for label,poly in converted.items()],definitions)


def verify_plan(entry,scope,policy,plan):
    if type(plan) is not Plan or plan is not compile(entry,scope,plan.v,plan.word,policy):raise ValueError('issued synthesis plan changed')


def observation(entry,key):
    out=entry._observations.get(key)
    if type(out) is not Observation or _OBSERVATIONS.get(id(out)) is not out:raise ValueError('issued observation required')
    return out


def validate_cache(entry,cache):
    for key,(digest,value) in cache.items():
        obs=observation(entry,key)
        try:ref=entry.derived.reference(key)
        except KeyError:raise ValueError('unregistered synthesized value') from None
        if (digest!=ref.digest or ref.origin!=obs.origin or ref.envelope!=obs.envelope
            or fingerprint((ref.key,ref.origin,value,ref.envelope))!=ref.commitment):raise ValueError('cached synthesized value or origin changed')


def resolve(entry,scope,policy,plan,cache=(),meter=None):
    verify_plan(entry,scope,policy,plan);cache=dict(cache);validate_cache(entry,cache)
    meter=fn.Meter() if meter is None else meter
    if plan.status!='AVAILABLE':return m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,plan.status),tuple(sorted(cache.items())),(),(),()
    new=[];derived=[];used=[];sources={};registration_reads=0;registered=[]
    for key in plan.features:
        obs=observation(entry,key);poly=Polynomial(obs.coefficients)
        if key not in cache:
            known=[(name,Polynomial(observation(entry,name).coefficients)) for name in sorted(cache)]
            expression=synthesis.represent(poly,known,policy)
            if expression is not None:
                if synthesis.expand(expression,dict(known)).terms!=poly.terms:raise AssertionError('cached feature derivation failed')
                value=expression.exact({name:record[1] for name,record in cache.items()})[0];derived.append(key)
            else:
                try:entry.derived.reference(key);exists=True
                except KeyError:exists=False
                if not exists:
                    for dep in poly.dependencies:
                        if dep not in sources:sources[dep]=entry.base.vault.exact(dep,meter);registration_reads+=1
                    value=poly.exact(sources)[0];registered.append(key)
                else:value=entry.derived.exact(key,meter)
                new.append(key)
            entry.derived.register(key,value,obs.envelope,obs.origin)
            ref=entry.derived.reference(key)
            if key in registered:value=entry.derived.exact(key,meter)
            cache[key]=(ref.digest,value)
        used.append((key,cache[key][1]))
    validate_cache(entry,cache)
    values=dict(used)
    status=core.assessed(entry.core,scope.base_scope,plan.polynomials,{k:(v,v) for k,v in values.items()},core.Work())
    if status!='ADMISSIBLE':action=m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,status,read_keys=plan.features)
    else:
        q={label:poly.exact(values)[0] for label,poly in plan.polynomials.items()}
        R=tuple(q['R'+str(i)+'n']/q['L'] for i in range(3))+(Q(0),)*3
        T=tuple(x+plan.v*z for x,z in zip(entry.base.first.flight.pair.representative.weights,entry.base.first.axis))
        action=m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,status,T,R,q['N']/q['D'],read_keys=plan.features)
    entry._work.append(dict(new_feature_queries=len(new),source_reads_for_registration=registration_reads,
        newly_registered=registered,derived_features=len(derived)))
    return action,tuple(sorted(cache.items())),tuple(new),tuple(derived),tuple(used)
