"""RR65: retained mixed polynomials -> equality of physical bundle action sets."""
from dataclasses import dataclass,field
from fractions import Fraction as Q
import bundle_demand as b
import bundle_execution as plant
from bundle_demand import fn,prior,d,te
from free_numbers.algebra import Polynomial,fingerprint
from free_numbers.evaluate import enclose

KEYS=('s','t')
WORDS=('HHHSUT','HHHUST')
LABELS=('Y0','Y1','Y2','h','dy','prefix','B1','N','D','L','R0n','R1n','R2n')
LIMIT=Q(10**40)
_ISSUED=[]


@dataclass(frozen=True)
class Entry:
    first: object
    second: object
    family: str
    vault: object
    S: object
    U: object
    U_operation: object
    engine: object
    direction_U: tuple
    digest: str
    _cache: dict=field(default_factory=dict,compare=False,repr=False)

    @property
    def base(self):return self.first.base
    @property
    def head(self):return self.first.head
    @property
    def library(self):return self.first.library


def register(family='diagonal',modes=('keep','keep')):
    if family not in ('diagonal','offdiagonal') or len(modes)!=2:raise ValueError('declare two retained origins')
    first=b.register(modes[0]);second=prior.previous.begin(modes[1],2,0)
    s_geometry=prior.data(first.flight)[1]
    _,geometry,axis,library=prior.data(second)
    if library!=first.library or second.pair.representative!=first.flight.pair.representative:
        raise ValueError('the two frozen origins must share the declared chart')
    direction=axis if family=='diagonal' else (Q(-3,4),Q(-4,3),Q(0),Q(25,12),Q(0),Q(0))
    u_leaf=d.AffineLetter(tuple(a+geometry.shift*z for a,z in zip(second.pair.representative.weights,direction)),library)
    ready,u=plant.produce(first.flight.first.closed_engine,first.flight.first.residue.internal_context,u_leaf,'rr65-prior-U-planned')
    bootstrap=plant.consume(ready,(ready.pending.head,u),'rr65-prior-U')
    vault=fn.Vault();envelope=(Q(-1,1024),Q(1,1024))
    if tuple(a+s_geometry.shift*z for a,z in zip(first.flight.pair.representative.weights,first.axis))!=first.flight.pair.original.weights:
        raise ValueError('the retained S must be the actual original source')
    S=fn.retained(vault,'s',s_geometry.shift,envelope,first.digest,first.base,first.direction)
    matrix=tuple(tuple(sum(z*op.source.endpoint[i][j] for z,op in zip(direction,library)) for j in range(3)) for i in range(3))
    U=fn.retained(vault,'t',geometry.shift,envelope,second.digest,first.base,fn.matrix_block(matrix))
    # An authenticated derived observation, computed once at registration.
    # This preserves both original coordinates; it is not their replacement.
    joint=vault.register('p',s_geometry.shift*geometry.shift,(Q(-1,1024**2),Q(1,1024**2)),
        fingerprint(('registered-product',S.digest,U.digest)))
    digest=fingerprint((first.digest,second.digest,family,S.digest,U.digest,joint.digest,u.visible,len(bootstrap.engine.events)))
    result=Entry(first,second,family,vault,S,U,u,bootstrap.engine,direction,digest)
    _ISSUED.append(result)
    return result


def verify_entry(entry):
    # Entry authentication owns the complete immutable bootstrap history.
    # A copied digest cannot authorize a substituted lower inheritance. Keep
    # this check constant with respect to retained coefficient precision.
    if type(entry) is not Entry or not any(entry is issued for issued in _ISSUED):
        raise ValueError('use an authenticated entry returned by register')


def context(entry,name):
    if name=='main':return (Q(-1),Q(2),Q(0))
    if name=='zero_head':return (Q(1,2),Q(1,2),Q(0))
    if name=='outside_chart':return (Q(0),Q(1),Q(0))
    if name!='mixed':raise ValueError('unknown fixed context')
    base=entry.first.flight.pair.representative.weights
    x=Q(1,4);y=(Q(1,2)-base[2]-(base[0]-base[2])*x)/(base[1]-base[2])
    return x,y,1-x-y


@dataclass(frozen=True)
class Scope:
    entry_digest: str
    diagonal: tuple
    strength: Q=Q(1,1024)
    domain: tuple=(-LIMIT,LIMIT)
    controls: tuple=(Q(-64),Q(0),Q(1),Q(64))
    words: tuple=WORDS
    target: tuple=b.ONE
    inherited: tuple=b.NEG
    observation: str='physical-new-T-and-R-coefficients'

    def __post_init__(self):
        object.__setattr__(self,'diagonal',tuple(map(Q,self.diagonal)))
        object.__setattr__(self,'strength',Q(self.strength))
        object.__setattr__(self,'domain',tuple(map(Q,self.domain)))
        object.__setattr__(self,'controls',tuple(map(Q,self.controls)))
        if (len(self.diagonal)!=3 or sum(self.diagonal)!=1 or len(self.domain)!=2 or self.domain[0]>self.domain[1]
            or not self.controls or len(set(self.controls))!=len(self.controls) or any(abs(v)>64 for v in self.controls)
            or self.words!=WORDS or self.strength not in (0,Q(1,1024)) or self.target!=b.ONE or self.inherited!=b.NEG
            or self.observation!='physical-new-T-and-R-coefficients'):
            raise ValueError('bind the finite physical action observation and complete bundle requirement')

    @property
    def C(self):return tuple(tuple(self.diagonal[i] if i==j else Q(0) for j in range(3)) for i in range(3))
    @property
    def digest(self):return fingerprint(tuple(self.__dict__.values()))


@dataclass(frozen=True)
class Recipe:
    scope_digest: str
    v: Q
    word: str
    roots: tuple
    plans: tuple

    @property
    def digest(self):return fingerprint((self.scope_digest,self.v,self.word,tuple(p.digest for p in self.plans)))
    @property
    def polynomials(self):return dict(zip(LABELS,(Polynomial(p.coefficients) for p in self.plans)))


def build(entry,scope,v,word):
    verify_entry(entry)
    v=Q(v)
    if (scope.entry_digest!=entry.digest or v not in scope.controls or word not in scope.words
        or entry.family=='offdiagonal' and scope.strength):raise ValueError('the declared chart or current candidate changed')
    cache=(scope.digest,v,word)
    if cache in entry._cache:return entry._cache[cache]
    n,add,sub=b.number,b.plus,b.minus
    T=entry.base+entry.first.direction.scaled(v)
    H=tuple(fn.matrix_block(d.tensor(leaf)) for leaf in entry.head.leaves())
    mapping={'H':H,'S':(entry.S,),'U':(entry.U,),'T':(T,)}
    leaves=tuple(x for letter in word for x in mapping[letter])
    den=Q(len(leaves)*(len(leaves)+1),2)
    raw=leaves[0].scaled(1/den)
    for i,leaf in enumerate(leaves[1:],2):raw=raw+leaf.scaled(Q(i)/den)
    anchor=te.pair.boundary_readout(entry.head)
    y=tuple(n(anchor[i][i]-scope.strength/3)+n(scope.strength)*b.diagonal_component(raw,i) for i in range(3))
    h=sub(n(2)*y[0],n(1))*sub(n(2)*y[1],n(1));dy=sub(y[0],y[1])
    c=scope.diagonal;hc=prior.scalar(entry.head.kernel(scope.C))
    obs=b.kernel_observation(scope.C)
    B1=n(hc**3)*fn.read(entry.S,obs)*fn.read(entry.U,obs)*fn.read(T,obs)
    k=n(-hc)*B1
    A=n(c[0]-c[1])*(n(1)+h*sub(n(1),n(2)*y[1]))+n(2*c[1]-1)*h*dy
    B=n(2)*add(n(c[0])*sub(y[1],y[2]),n(c[1])*sub(y[2],y[0]),n(c[2])*dy)
    N=sub(h*dy,k*A);D=k*h*B
    a0=n(1)+h*sub(n(1),n(2)*y[1])
    L=n(2)*h*dy*D
    r0=a0*D+n(2)*h*N*sub(y[1],y[2])
    r1=sub(n(2)*h*dy,a0)*D+n(2)*h*N*sub(y[2],y[0])
    r2=n(2)*h*dy*N
    roots=(*y,h,dy,sub(n(-1)*B1,n(1)),B1,N,D,L,r0,r1,r2)
    plans=tuple(fn.plan(fn.Query(root,fn.Scope(entry.digest,scope.digest,'RR65-'+label+':'+str(v)+':'+word)),
        entry.vault,fn.Policy(max_depth=1)) for root,label in zip(roots,LABELS))
    if any(p.status!='AVAILABLE' for p in plans):raise ValueError('finite polynomial budget unavailable')
    result=Recipe(scope.digest,v,word,roots,plans);entry._cache[cache]=result
    return result


def verify(entry,scope,recipe):
    if type(recipe) is not Recipe or recipe!=build(entry,scope,recipe.v,recipe.word):
        raise ValueError('the issued mixed action recipe changed')


def project(poly,omitted):
    return Polynomial((m,c) for m,c in poly.terms.items() if not set(m).intersection(omitted))


def cross_polynomials(recipe,omitted):
    p=recipe.polynomials;reduced={k:project(v,omitted) for k,v in p.items()}
    return tuple(p['R'+str(i)+'n'].mul(reduced['L']).add(
        reduced['R'+str(i)+'n'].mul(p['L']).scaled(-1)) for i in range(3))


def bounds(polys,intervals):return {k:enclose(tuple(p.terms.items()),intervals,192)[0] for k,p in polys.items()}


def status(entry,scope,p,intervals):
    q=bounds(p,intervals)
    if not prior.scalar(entry.head.kernel(scope.C)) or q['B1']==(0,0):return 'EMPTY',q
    if not te.port.regular(scope.C,entry.library):return 'UNKNOWN_CHART',q
    y=tuple(q['Y'+str(i)] for i in range(3))
    if not all(b.nonzero(b.subtract(y[i],y[j])) for i,j in ((0,1),(0,2),(1,2))):return 'REFINE',q
    if (not b.nonzero(q['h']) or not b.separated(b.subtract(q['h'],(Q(1),Q(1))))
        or not b.nonzero((q['h'][0]+3,q['h'][1]+3)) or not b.separated(q['prefix'])):return 'REFINE',q
    alpha=b.ratio(q['N'],q['D'])
    if alpha is None:return ('EMPTY' if q['D']==(0,0) and b.nonzero(q['N']) else 'REFINE'),q
    lo,hi=scope.domain
    if alpha[1]<lo or alpha[0]>hi:return 'EMPTY',q
    if not lo<=alpha[0]<=alpha[1]<=hi or not b.nonzero(q['L']):return 'REFINE',q
    return 'ADMISSIBLE',q


@dataclass(frozen=True)
class Comparison:
    entry_digest: str
    scope_digest: str
    omitted: tuple
    verdict: str
    rows: tuple
    reads: tuple


def compare(entry,scope,omitted,precisions=(16,32,64,128)):
    omitted=tuple(sorted(omitted))
    if not omitted or len(set(omitted))!=len(omitted) or not set(omitted)<=set(KEYS):raise ValueError('declare a retained subset')
    if any(type(x) is not int or not 1<=x<=4096 for x in precisions):raise ValueError('finite refinement budget required')
    meter=fn.Meter();rows=[]
    for v in scope.controls:
        for word in scope.words:
            r=build(entry,scope,v,word);p=r.polynomials;rp={k:project(x,omitted) for k,x in p.items()}
            crosses=cross_polynomials(r,omitted)
            interval={k:entry.vault.coarse(k,meter) for k in KEYS}
            verdict='UNDETERMINED';stage=0
            for bits in (0,)+tuple(precisions):
                if bits:interval={k:entry.vault.refine(k,bits,meter) for k in KEYS}
                full,q=status(entry,scope,p,interval);replaced,rq=status(entry,scope,rp,interval)
                c_bounds=tuple(enclose(tuple(x.terms.items()),interval,192)[0] for x in crosses)
                if full=='EMPTY' and replaced=='EMPTY':verdict='SAME_EMPTY'
                elif {full,replaced}=={'ADMISSIBLE','EMPTY'}:verdict='DIFFERENT_EXISTENCE'
                elif full==replaced=='ADMISSIBLE':
                    if all(x==(0,0) for x in c_bounds):verdict='SAME_PHYSICAL_ACTION'
                    elif any(b.nonzero(x) for x in c_bounds):verdict='DIFFERENT_PHYSICAL_ACTION'
                if verdict!='UNDETERMINED' or 'UNKNOWN_CHART' in (full,replaced):stage=bits;break
                stage=bits
            rows.append((str(v),word,verdict,full,replaced,stage,tuple(x.digest for x in crosses),
                tuple(any(set(m)==set(KEYS) for m in x.terms) for x in crosses),
                all(not x.terms for x in crosses)))
    verdict=('DIFFERENT' if any(x[2].startswith('DIFFERENT') for x in rows) else
             'SAME' if all(x[2].startswith('SAME') for x in rows) else 'UNDETERMINED')
    return Comparison(entry.digest,scope.digest,omitted,verdict,tuple(rows),
        (meter.coarse_reads,meter.refinement_reads,meter.exact_reads))


def verify_comparison(entry,scope,certificate):
    # Recompute against authenticated bounds and the issued physical action map.
    if type(certificate) is not Comparison or certificate!=compare(entry,scope,certificate.omitted):
        raise ValueError('the entry, requirement, omission or action-set certificate changed')
    return True


@dataclass(frozen=True)
class Action:
    scope_digest: str
    recipe_digest: str
    v: Q
    word: str
    status: str
    T: tuple=()
    R: tuple=()
    alpha: object=None
    omitted: tuple=()
    read_keys: tuple=()


def action(entry,scope,v,word,certificate=None,meter=None):
    omitted=()
    if certificate is not None:
        verify_comparison(entry,scope,certificate)
        if certificate.verdict!='SAME':raise ValueError('an unsafe or unresolved omission cannot authorize an action')
        omitted=certificate.omitted
    r=build(entry,scope,v,word);p={k:project(x,omitted) for k,x in r.polynomials.items()}
    meter=fn.Meter() if meter is None else meter
    coarse={k:entry.vault.coarse(k,meter) for k in KEYS}
    initial,_=status(entry,scope,p,coarse)
    if initial=='EMPTY':return Action(scope.digest,r.digest,Q(v),word,'EMPTY',omitted=omitted)
    if initial=='UNKNOWN_CHART':return Action(scope.digest,r.digest,Q(v),word,initial,omitted=omitted)
    keys=tuple(sorted({k for x in p.values() for k in x.dependencies}))
    values={k:entry.vault.exact(k,meter) for k in keys}
    intervals={k:(x,x) for k,x in values.items()}
    accepted,_=status(entry,scope,p,intervals)
    if accepted!='ADMISSIBLE':return Action(scope.digest,r.digest,Q(v),word,accepted,omitted=omitted,read_keys=keys)
    q={k:x.exact(values)[0] for k,x in p.items()}
    weights=tuple(q['R'+str(i)+'n']/q['L'] for i in range(3))+(Q(0),)*3
    T=tuple(a+Q(v)*z for a,z in zip(entry.first.flight.pair.representative.weights,entry.first.axis))
    return Action(scope.digest,r.digest,Q(v),word,'ADMISSIBLE',T,weights,q['N']/q['D'],omitted,keys)


def joint_polynomials(recipe):
    """An exact quotient: every surviving s^i t^j must satisfy i=j."""
    result={}
    for label,poly in recipe.polynomials.items():
        terms=[]
        for monomial,coefficient in poly.terms.items():
            if set(monomial)-set(KEYS) or monomial.count('s')!=monomial.count('t'):
                return None
            terms.append((('p',)*monomial.count('s'),coefficient))
        result[label]=Polynomial(terms)
    return result


def joint_action(entry,scope,v,word,meter=None):
    """Read the preserved mixed observation p, omitting individual exact reads."""
    recipe=build(entry,scope,v,word);polys=joint_polynomials(recipe)
    if polys is None:raise ValueError('this requirement also needs unbalanced individual residual information')
    meter=fn.Meter() if meter is None else meter
    accepted,_=status(entry,scope,polys,{'p':entry.vault.coarse('p',meter)})
    if accepted=='EMPTY':return Action(scope.digest,recipe.digest,Q(v),word,'EMPTY',omitted=KEYS)
    if accepted=='UNKNOWN_CHART':return Action(scope.digest,recipe.digest,Q(v),word,accepted,omitted=KEYS)
    values={'p':entry.vault.exact('p',meter)}
    accepted,_=status(entry,scope,polys,{k:(x,x) for k,x in values.items()})
    if accepted!='ADMISSIBLE':return Action(scope.digest,recipe.digest,Q(v),word,accepted,omitted=KEYS,read_keys=('p',))
    q={k:p.exact(values)[0] for k,p in polys.items()}
    weights=tuple(q['R'+str(i)+'n']/q['L'] for i in range(3))+(Q(0),)*3
    T=tuple(a+Q(v)*z for a,z in zip(entry.first.flight.pair.representative.weights,entry.first.axis))
    return Action(scope.digest,recipe.digest,Q(v),word,'ADMISSIBLE',T,weights,q['N']/q['D'],KEYS,('p',))
