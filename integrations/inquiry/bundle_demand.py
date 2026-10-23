"""RR64: pull one two-flower terminal demand back before first actuation.

The continuation is declared: first HHST/HHTS, RR53 ordered context, a fresh
second correction R, then HR. Primitive source families stay diagonal in the
existing six-generator chart. No completed future path is used by assessment.
"""
from dataclasses import dataclass,field
from fractions import Fraction as Q
from pathlib import Path
import sys
import demand_filter as old
from demand_filter import prior,d,te

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'vendor/free-number-runtime/runtime'))
import free_numbers as fn
from free_numbers.algebra import fingerprint, Polynomial
from free_numbers.evaluate import enclose,mul

EXISTS='existence-of-two-flower-completion'
ACTIONS='next-source-action-set'
AXES=((Q(1),Q(0),Q(0)),(Q(0),Q(1),Q(0)),(Q(0),Q(0),Q(1)))
ONE=(Q(1),Q(0),Q(0),Q(0))
NEG=(-Q(1),Q(0),Q(0),Q(0))


def number(a):return fn.constant((Q(a),Q(0),Q(0),Q(0)))
def plus(*xs):
    out=number(0)
    for x in xs:out=out+x
    return out
def minus(a,b):return a+number(-1)*b


def kernel_observation(y):
    return fn.Observation(2,tuple(fn.Channel((AXES[c],),Q(y[c][b]),fn.BASIS[b+1])
        for c in range(3) for b in range(3) if y[c][b]))


def diagonal_component(tensor,i):
    response=fn.read(tensor,fn.Observation(2,(fn.Channel((AXES[i],)),)))
    return number(Q(1,2))*minus(number(1),fn.component(response,i+1))


@dataclass(frozen=True)
class Entry:
    flight: object
    vault: object
    source: object
    base: object
    direction: object
    head: object
    axis: tuple
    library: tuple
    envelope: tuple
    _recipes: dict=field(default_factory=dict,compare=False,repr=False)
    _digest: str=field(init=False,repr=False)

    def __post_init__(self):
        # This full-history binding belongs to entry authentication, not each
        # query. Assessment must not rehash the latent exact scalar on the way
        # to asking whether it needs to read that scalar.
        object.__setattr__(self,'_digest',fingerprint((self.flight.digest,self.source.digest,
            self.head.visible,self.axis,self.envelope)))

    @property
    def digest(self):return self._digest


def register(mode='keep',envelope=(Q(-1,1024),Q(1,1024))):
    history=prior.previous.begin(mode,1,0)
    head,geometry,axis,library=prior.data(history)
    base_matrix=d.tensor(history.pair.representative)
    axis_matrix=tuple(tuple(sum(a*op.source.endpoint[i][j] for a,op in zip(axis,library))
        for j in range(3)) for i in range(3))
    if any(base_matrix[i][j] or axis_matrix[i][j] for i in range(3) for j in range(3) if i!=j):
        raise ValueError('RR64 declares diagonal source and residual tensors')
    if tuple(leaf.weights for leaf in head.leaves())!=((Q(1),0,0,0,0,0),(0,Q(1),0,0,0,0)):
        raise ValueError('the inherited two-leaf head chart changed')
    vault=fn.Vault();base=fn.matrix_block(base_matrix);direction=fn.matrix_block(axis_matrix)
    root=fn.retained(vault,'retained-s',geometry.shift,tuple(map(Q,envelope)),history.digest,base,direction)
    return Entry(history,vault,root,base,direction,head,axis,library,tuple(map(Q,envelope)))


@dataclass(frozen=True)
class Scope:
    entry_digest: str
    x: Q
    first_control: Q
    first_word: str
    strength: Q=Q(1,1024)
    domain: tuple=(Q(0),Q(16))
    observation: str=ACTIONS
    target: tuple=ONE
    inherited: tuple=NEG
    next_word: str='HR'

    def __post_init__(self):
        for field in ('x','first_control','strength'):object.__setattr__(self,field,Q(getattr(self,field)))
        object.__setattr__(self,'domain',tuple(map(Q,self.domain)))
        if (self.first_word not in old.WORDS or not -64<=self.first_control<=64 or
                not 0<=self.strength<=Q(1,16) or len(self.domain)!=2 or self.domain[0]>self.domain[1] or
                self.observation not in (EXISTS,ACTIONS) or self.target!=ONE or self.inherited!=NEG or self.next_word!='HR'):
            raise ValueError('bind the declared current freedom, continuation, resource interval and bundle target')

    @property
    def context(self):return prior.diagonal(self.x)
    @property
    def digest(self):return fingerprint(tuple(self.__dict__.values()))


@dataclass(frozen=True)
class Recipe:
    scope_digest: str
    expressions: tuple
    plans: tuple

    @property
    def dependencies(self):return tuple(sorted({k for p in self.plans for k in p.dependencies}))
    @property
    def digest(self):return fingerprint((self.scope_digest,tuple(p.digest for p in self.plans)))


LABELS=('Y0','Y1','Y2','head2','deltaY','K','A','B','N','D','prefix-error')


def query(entry,scope,label,expression):
    return fn.Query(expression,fn.Scope(entry.digest,scope.digest,'RR64-'+label))


def build(entry,scope):
    if type(entry) is not Entry or type(scope) is not Scope or scope.entry_digest!=entry.digest:
        raise ValueError('the demand must retain its authenticated entry')
    if scope.digest in entry._recipes:return entry._recipes[scope.digest]
    v=scope.first_control
    t=entry.base+entry.direction.scaled(v)
    h=tuple(fn.matrix_block(d.tensor(leaf)) for leaf in entry.head.leaves())
    mapping={'H':h,'S':(entry.source,),'T':(t,)}
    leaves=tuple(leaf for letter in scope.first_word for leaf in mapping[letter])
    denominator=Q(len(leaves)*(len(leaves)+1),2)
    raw=leaves[0].scaled(Q(1)/denominator)
    for i,leaf in enumerate(leaves[1:],2):raw=raw+leaf.scaled(Q(i)/denominator)
    anchor=te.pair.boundary_readout(entry.head)
    y=tuple(number(anchor[i][i]-scope.strength/3)+number(scope.strength)*diagonal_component(raw,i) for i in range(3))
    head2=minus(number(2)*y[0],number(1))*minus(number(2)*y[1],number(1))
    delta=minus(y[0],y[1])
    c=scope.context;hC=prior.scalar(entry.head.kernel(c))
    sourceC=fn.read(entry.source,kernel_observation(c))
    tC=fn.read(t,kernel_observation(c))
    first_kernel=number(hC*hC)*sourceC*tC
    k=number(-hC)*first_kernel
    a=(number(c[0][0]-c[1][1])*(number(1)+head2*minus(number(1),number(2)*y[1]))
       +number(2*c[1][1]-1)*head2*delta)
    b=number(2)*plus(number(c[0][0])*minus(y[1],y[2]),number(c[1][1])*minus(y[2],y[0]),number(c[2][2])*delta)
    n=minus(head2*delta,k*a)
    denominator_=k*head2*b
    prefix=minus(number(-1)*first_kernel,number(1))
    expressions=(*y,head2,delta,k,a,b,n,denominator_,prefix)
    plans=tuple(fn.plan(query(entry,scope,label,expr),entry.vault,fn.Policy(max_depth=1)) for label,expr in zip(LABELS,expressions))
    if any(p.status!='AVAILABLE' for p in plans):raise ValueError('the registered finite polynomial chart was not available')
    recipe=Recipe(scope.digest,expressions,plans)
    entry._recipes[scope.digest]=recipe
    return recipe


def polynomial_values(recipe,values):
    out=[]
    for p in recipe.plans:
        q=Polynomial(p.coefficients).exact(values)
        if any(q[1:]):raise ValueError('RR64 requires real diagonal response polynomials')
        out.append(q[0])
    return dict(zip(LABELS,out))


def polynomial_bounds(recipe,values,bits=80):
    return dict(zip(LABELS,(enclose(p.coefficients,values,bits)[0] for p in recipe.plans)))


def nonzero(interval):return interval[1]<0 or interval[0]>0
def separated(interval):return interval[1]<-te.port.EPSILON or interval[0]>te.port.EPSILON
def subtract(x,y):return x[0]-y[1],x[1]-y[0]
def ratio(n,d):
    if not nonzero(d):return None
    inv=tuple(sorted((1/d[0],1/d[1])))
    products=tuple(a*b for a in n for b in inv)
    return min(products),max(products)


@dataclass(frozen=True)
class Assessment:
    scope_digest: str
    recipe_digest: str
    status: str
    feasible: object
    control_bounds: object
    needs_exact: bool
    bounds: tuple


def assess(entry,scope,recipe=None,meter=None):
    recipe=build(entry,scope) if recipe is None else recipe
    verify_recipe(entry,scope,recipe)
    meter=fn.Meter() if meter is None else meter
    intervals={k:entry.vault.coarse(k,meter) for k in recipe.dependencies}
    bounds=polynomial_bounds(recipe,intervals)
    def result(status,feasible=None,control=None,needs=False):
        return Assessment(scope.digest,recipe.digest,status,feasible,control,needs,tuple(bounds.items()))
    if prior.scalar(entry.head.kernel(scope.context))==0:return result('EMPTY_ZERO_FUTURE_HEAD',False)
    if not te.port.regular(scope.context,entry.library):return result('OUTSIDE_FUTURE_CHART')
    y=tuple(bounds['Y'+str(i)] for i in range(3))
    if not all(nonzero(subtract(y[i],y[j])) for i,j in ((0,1),(0,2),(1,2))):
        return result('CURRENT_CHART_NEEDS_REFINEMENT',needs=True)
    if not nonzero(bounds['head2']) or not separated(subtract(bounds['head2'],(Q(1),Q(1)))):
        return result('HEAD_NEEDS_REFINEMENT',needs=True)
    if not nonzero((bounds['head2'][0]+3,bounds['head2'][1]+3)):
        return result('SOURCE_ACTIVITY_NEEDS_REFINEMENT',needs=True)
    if not separated(bounds['prefix-error']):return result('UPPER_PREFIX_NEEDS_REFINEMENT',needs=True)
    den=bounds['D'];num=bounds['N']
    if den==(0,0) and nonzero(num):return result('EMPTY_BLIND_CONTINUATION',False)
    control=ratio(num,den)
    if control is None:return result('CONTROL_POLE_NEEDS_REFINEMENT',needs=True)
    lo,hi=scope.domain
    if control[1]<lo or control[0]>hi:return result('EMPTY_RESOURCE_DOMAIN',False,control)
    wholly=lo<=control[0] and control[1]<=hi
    if scope.observation==EXISTS and wholly:return result('EXISTENCE_WITHOUT_EXACT_RESIDUAL',True,control)
    return result('ACTION_NEEDS_RETAINED_RESIDUAL' if scope.observation==ACTIONS else 'RESOURCE_EDGE_NEEDS_REFINEMENT',
                  control=control,needs=True)


def verify_recipe(entry,scope,recipe):
    expected=build(entry,scope)
    if (type(recipe) is not Recipe or recipe.scope_digest!=scope.digest or
            recipe.digest!=expected.digest or tuple(x.digest for x in recipe.expressions)!=tuple(x.digest for x in expected.expressions)):
        raise ValueError('the declared continuation or scope changed')
    # A deterministic recipe issued by this authenticated entry is the cache
    # authority, as with the existing retained-scalar archives. Values remain
    # unread. An arbitrary replacement plan with the same query tag is rejected.
    return True


@dataclass(frozen=True)
class Resolution:
    scope_digest: str
    recipe_digest: str
    status: str
    feasible: object
    control: object
    exact_values: tuple


def resolve(entry,scope,recipe,assessment,meter=None):
    if assessment!=assess(entry,scope,recipe):raise ValueError('the bound assessment changed')
    if not assessment.needs_exact:
        return Resolution(scope.digest,recipe.digest,assessment.status,assessment.feasible,None,())
    meter=fn.Meter() if meter is None else meter
    values={key:entry.vault.exact(key,meter) for key in recipe.dependencies}
    v=polynomial_values(recipe,values)
    y=tuple(v['Y'+str(i)] for i in range(3))
    if (len(set(y))!=3 or not v['head2'] or abs(v['head2']-1)<=te.port.EPSILON
            or abs(v['prefix-error'])<=te.port.EPSILON):
        return Resolution(scope.digest,recipe.digest,'OUTSIDE_DECLARED_CONTINUATION',None,None,tuple(values.items()))
    if not v['D']:
        return Resolution(scope.digest,recipe.digest,'DEGENERATE_CONTROL_RELATION',None,None,tuple(values.items()))
    control=v['N']/v['D'];ok=scope.domain[0]<=control<=scope.domain[1]
    if v['head2']==-3 and control==Q(1,3):
        return Resolution(scope.digest,recipe.digest,'INACTIVE_LOWER_SOURCE',None,None,tuple(values.items()))
    return Resolution(scope.digest,recipe.digest,'ADMISSIBLE' if ok else 'EMPTY_RESOURCE_DOMAIN',ok,
                      control if ok and scope.observation==ACTIONS else None,tuple(values.items()))
