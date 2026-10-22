"""RR66: a request selects a certified sufficient observation, before values."""
from dataclasses import dataclass,field
from fractions import Fraction as Q
import mixed_action_sets as m
from mixed_action_sets import fn,b,prior
from free_numbers.algebra import Polynomial,fingerprint
import resolution_algebra as algebra

MODES=('CONSTANT','PRODUCT','SUM_PRODUCT','PORT_PRODUCT','INDIVIDUAL')
_ISSUED=[]


def port_weights(base,word):
    index=0;weights={'S':Q(0),'U':Q(0)}
    for letter in word:
        if letter in weights:weights[letter]+=index+1
        index+=len(base.head.leaves()) if letter=='H' else 1
    return weights['S'],weights['U']


@dataclass(frozen=True)
class Entry:
    base: object
    derived: object
    digest: str
    _plans: dict=field(default_factory=dict,compare=False,repr=False)


def register(modes=('keep','keep')):
    base=m.register(modes=modes);derived=fn.Vault()
    values={ref.key:value for ref,value in base.vault._records()}
    eps=Q(1,1024)
    derived.register('sum',values['s']+values['t'],(-2*eps,2*eps),fingerprint((base.digest,'sum','s','t')))
    for word in m.WORDS:
        a,b_=port_weights(base,word)
        derived.register('port-'+word,a*values['s']+b_*values['t'],(-(a+b_)*eps,(a+b_)*eps),
            fingerprint((base.digest,'RR53-primitive-position',word,a,b_)))
    digest=fingerprint((base.digest,tuple(ref.digest for ref,value in derived._records())))
    result=Entry(base,derived,digest);_ISSUED.append(result);return result


def verify_entry(entry):
    if type(entry) is not Entry or not any(entry is old for old in _ISSUED):raise ValueError('an issued adaptive entry is required')
    m.verify_entry(entry.base)


def vault_for(entry,key):return entry.base.vault if key in ('s','t','p') else entry.derived


@dataclass(frozen=True)
class Policy:
    max_features: int=2
    modes: tuple=MODES

    def __post_init__(self):
        if type(self.max_features) is not int or not 0<=self.max_features<=2 or type(self.modes) is not tuple or not self.modes or any(x not in MODES for x in self.modes) or len(set(self.modes))!=len(self.modes):
            raise ValueError('declare a finite feature budget and catalogue order')
    @property
    def digest(self):return fingerprint((self.max_features,self.modes))


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
    tested_modes: tuple

    @property
    def digest(self):return fingerprint(tuple(self.__dict__.values()))
    @property
    def polynomials(self):return {label:Polynomial(coeff) for label,coeff in self.coefficients}


def compile(entry,scope,v,word,policy=Policy()):
    verify_entry(entry)
    if type(scope) is not m.Scope or scope.entry_digest!=entry.base.digest:raise ValueError('the original scope changed')
    v=Q(v);cache=(scope.digest,v,word,policy.digest)
    if cache in entry._plans:return entry._plans[cache]
    recipe=m.build(entry.base,scope,v,word);polys=recipe.polynomials
    coarse={key:entry.base.vault.coarse(key,fn.Meter()) for key in m.KEYS}
    initial,_=m.status(entry.base,scope,polys,coarse)
    def issued(mode,status,features=(),converted=None,tested=()):
        result=Plan(entry.digest,scope.digest,policy.digest,recipe.digest,v,word,mode,status,tuple(features),
            tuple((label,tuple(sorted(poly.terms.items()))) for label,poly in (converted or {}).items()),tuple(tested))
        entry._plans[cache]=result;return result
    if initial=='EMPTY':return issued('CONSTANT','EMPTY')
    if initial=='UNKNOWN_CHART':return issued('CONSTANT','UNKNOWN_CHART')
    tested=[]
    for mode in policy.modes:
        features=(() if mode=='CONSTANT' else ('p',) if mode=='PRODUCT' else
            ('p','sum') if mode=='SUM_PRODUCT' else ('p','port-'+word) if mode=='PORT_PRODUCT' else ('s','t'))
        converted={}
        for label,poly in polys.items():
            if mode=='CONSTANT':out=poly if not poly.dependencies else None
            elif mode=='PRODUCT':out=algebra.product_only(poly)
            elif mode in ('SUM_PRODUCT','PORT_PRODUCT'):
                a,b_=((Q(1),Q(1)) if mode=='SUM_PRODUCT' else port_weights(entry.base,word))
                out=algebra.linear_product(poly,features[1],a,b_)
            else:out=poly
            if out is None:break
            converted[label]=out
        if len(converted)!=len(polys):tested.append((mode,'NONZERO_REMAINDER'));continue
        features=tuple(key for key in features if any(key in poly.dependencies for poly in converted.values()))
        if len(features)>policy.max_features:tested.append((mode,'FEATURE_BUDGET'));continue
        # A certificate is accepted only after exact re-expansion reproduces
        # every original action and guard polynomial, not merely sampled values.
        definitions={'s':algebra.variable('s'),'t':algebra.variable('t'),
            'p':algebra.variable('s').mul(algebra.variable('t')),'sum':algebra.variable('s').add(algebra.variable('t'))}
        a,b_=port_weights(entry.base,word)
        definitions['port-'+word]=algebra.variable('s').scaled(a).add(algebra.variable('t').scaled(b_))
        if any(algebra.expand(converted[label],definitions).terms!=poly.terms for label,poly in polys.items()):
            raise AssertionError('accepted factorization failed its exact identity')
        tested.append((mode,'EXACT_IDENTITY'))
        return issued(mode,'AVAILABLE',features,converted,tested)
    return issued('NONE','UNDETERMINED_NO_SCHEMA',tested=tested)


def verify_plan(entry,scope,policy,plan):
    if type(plan) is not Plan or plan!=compile(entry,scope,plan.v,plan.word,policy):raise ValueError('the request or observation proof changed')


def validate_cache(entry,cache):
    known={'s','t','p','sum',*('port-'+w for w in m.WORDS)}
    for key,(digest,value) in cache.items():
        if key not in known:raise ValueError('unknown cached observation')
        ref=vault_for(entry,key).reference(key)
        if digest!=ref.digest or fingerprint((ref.key,ref.origin,value,ref.envelope))!=ref.commitment:
            raise ValueError('cached exact feature or retained origin changed')


def derive_cached(entry,key,cache):
    values={k:record[1] for k,record in cache.items()}
    pair=None
    if 's' in values and 't' in values:pair=values['s'],values['t']
    elif 'sum' in values:
        for word in m.WORDS:
            if 'port-'+word in values:
                a,b_=port_weights(entry.base,word);z=values['port-'+word];u=values['sum']
                pair=((b_*u-z)/(b_-a),(z-a*u)/(b_-a));break
    elif all('port-'+w in values for w in m.WORDS):
        a,b_=port_weights(entry.base,m.WORDS[0]);c,d=port_weights(entry.base,m.WORDS[1])
        x,y=(values['port-'+w] for w in m.WORDS);det=a*d-b_*c
        pair=((d*x-b_*y)/det,(a*y-c*x)/det)
    if pair is None:return None
    s,t=pair
    if key=='s':return s
    if key=='t':return t
    if key=='p':return s*t
    if key=='sum':return s+t
    a,b_=port_weights(entry.base,key[len('port-'):]);return a*s+b_*t


def resolve(entry,scope,policy,plan,cache=(),meter=None):
    verify_plan(entry,scope,policy,plan)
    cache=dict(cache);meter=fn.Meter() if meter is None else meter
    validate_cache(entry,cache)
    if plan.status!='AVAILABLE':
        action=m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,plan.status)
        return action,tuple(sorted(cache.items())),(),(),()
    # Do not silently expand an insufficient feature map or request the
    # original coordinates after certifying a coarser map.
    new=[];derived=[];used=[]
    for key in plan.features:
        vault=vault_for(entry,key);ref=vault.reference(key)
        if key not in cache:
            value=derive_cached(entry,key,cache)
            if value is None:value=vault.exact(key,meter);new.append(key)
            else:derived.append(key)
            cache[key]=(ref.digest,value)
        if cache[key][0]!=ref.digest:raise ValueError('cached feature belongs to another retained entry')
        if fingerprint((ref.key,ref.origin,cache[key][1],ref.envelope))!=ref.commitment:
            raise ValueError('cached exact feature value changed')
        used.append((key,cache[key][1]))
    values=dict(used);status,_=m.status(entry.base,scope,plan.polynomials,{k:(x,x) for k,x in values.items()})
    if status!='ADMISSIBLE':
        action=m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,status,read_keys=plan.features)
    else:
        q={label:poly.exact(values)[0] for label,poly in plan.polynomials.items()}
        R=tuple(q['R'+str(i)+'n']/q['L'] for i in range(3))+(Q(0),)*3
        T=tuple(a+plan.v*z for a,z in zip(entry.base.first.flight.pair.representative.weights,entry.base.first.axis))
        action=m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,'ADMISSIBLE',T,R,q['N']/q['D'],read_keys=plan.features)
    return action,tuple(sorted(cache.items())),tuple(new),tuple(derived),tuple(used)
