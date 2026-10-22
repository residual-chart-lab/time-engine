"""RR67: scope-bound plans from reusable, issued exact arithmetic identities.

The closed arithmetic schema is the RR65 diagonal two-flower pullback. A cache
hit certifies equal complete operands; it never authorizes copying a decision
from a different request. Original RR65/RR66 modules remain unchanged.
"""
from dataclasses import dataclass,field
from fractions import Fraction as Q
import adaptive_resolution as old
from adaptive_resolution import m,fn,b,prior,algebra,Polynomial,fingerprint
from free_numbers.evaluate import enclose

SCHEMA='RR67-diagonal-pullback-v1'
Policy=old.Policy
_ISSUED=[]
_NODE_ISSUED={}
_FACTOR_ISSUED={}
_BOUND_ISSUED={}


def coefficients(poly):return tuple(sorted(poly.terms.items()))
def P(node):return Polynomial(node.coefficients)
def C(x):return algebra.constant(x)
def add(*xs):
    out=C(0)
    for x in xs:out=out.add(x)
    return out
def sub(x,y):return x.add(y.scaled(-1))


@dataclass(frozen=True)
class Node:
    signature: str
    projection: tuple
    name: str
    coefficients: tuple
    digest: str


@dataclass(frozen=True)
class Factor:
    signature: str
    projection: tuple
    coefficients: object


@dataclass(frozen=True)
class Bound:
    signature: str
    projection: tuple
    interval: tuple


@dataclass
class Work:
    nodes_new: list=field(default_factory=list)
    nodes_reused: list=field(default_factory=list)
    factors_new: list=field(default_factory=list)
    factors_reused: list=field(default_factory=list)
    bounds_new: list=field(default_factory=list)
    bounds_reused: list=field(default_factory=list)
    plan_cache_hits: int=0


@dataclass(frozen=True)
class Entry:
    original: object
    basis: tuple
    digest: str
    _nodes: dict=field(default_factory=dict,compare=False,repr=False)
    _factors: dict=field(default_factory=dict,compare=False,repr=False)
    _bounds: dict=field(default_factory=dict,compare=False,repr=False)
    _plans: dict=field(default_factory=dict,compare=False,repr=False)
    _receipts: list=field(default_factory=list,compare=False,repr=False)
    @property
    def base(self):return self.original.base
    @property
    def derived(self):return self.original.derived


def register(modes=('keep','keep')):
    original=old.register(modes);e=original.base
    base=m.d.tensor(e.first.flight.pair.representative)
    axes=tuple(tuple(tuple(sum(z*op.source.endpoint[i][j] for z,op in zip(axis,e.library))
        for j in range(3)) for i in range(3)) for axis in (e.first.axis,e.direction_U))
    heads=tuple(m.d.tensor(leaf) for leaf in e.head.leaves())
    if any(matrix[i][j] for matrix in (base,*axes,*heads) for i in range(3) for j in range(3) if i!=j):
        raise ValueError('RR67 requires the certified diagonal chart')
    basis=tuple(tuple(x[i][i] for i in range(3)) for x in (base,*axes,*heads))
    if sum(basis[0])!=1 or any(sum(x) for x in basis[1:3]) or any(sum(x)!=1 for x in basis[3:]):
        raise ValueError('source trace or residual direction changed')
    entry=Entry(original,basis,fingerprint((SCHEMA,original.digest,basis)));_ISSUED.append(entry);return entry


def verify_entry(entry):
    if type(entry) is not Entry or not any(entry is e for e in _ISSUED):raise ValueError('issued incremental entry required')
    old.verify_entry(entry.original)


def port_weights(entry,word):return old.port_weights(entry,word)
def vault_for(entry,key):return old.vault_for(entry.original,key)
def validate_cache(entry,cache):return old.validate_cache(entry.original,cache)
def derive_cached(entry,key,cache):return old.derive_cached(entry.original,key,cache)


class Graph:
    def __init__(self,entry,work):self.entry=entry;self.work=work;self.nodes=[]
    def node(self,name,operation,parents,parameters,calculate):
        projection=(SCHEMA,self.entry.digest,name,operation,tuple(x.coefficients for x in parents),parameters)
        key=fingerprint(projection)
        if key in self.entry._nodes:
            out=self.entry._nodes[key]
            if (type(out) is not Node or _NODE_ISSUED.get(id(out)) is not out or out.signature!=key
                or out.projection!=projection):
                raise ValueError('issued arithmetic identity changed')
            self.work.nodes_reused.append(name)
        else:
            result=calculate(*(P(x) for x in parents));data=coefficients(result)
            out=Node(key,projection,name,data,result.digest);_NODE_ISSUED[id(out)]=out
            self.entry._nodes[key]=out;self.work.nodes_new.append(name)
        self.nodes.append(out);return out


def graph(entry,scope,v,word,work):
    """No retained scalar is read here: s,t remain formal polynomial variables."""
    verify_entry(entry);e=entry.base;v=Q(v)
    if type(scope) is not m.Scope or scope.entry_digest!=e.digest or v not in scope.controls or word not in scope.words:
        raise ValueError('complete original scope and current choice required')
    g=Graph(entry,work);n=g.node;base,ds,du,*heads=entry.basis
    s,t=algebra.variable('s'),algebra.variable('t')
    S=tuple(n('S'+str(i),'retained-affine-S',(),(base[i],ds[i]),lambda i=i:C(base[i]).add(s.scaled(ds[i]))) for i in range(3))
    U=tuple(n('U'+str(i),'retained-affine-U',(),(base[i],du[i]),lambda i=i:C(base[i]).add(t.scaled(du[i]))) for i in range(3))
    T=tuple(n('T'+str(i),'current-affine-T',(),(base[i],ds[i],v),lambda i=i:C(base[i]+v*ds[i])) for i in range(3))
    index=0;weights={'S':Q(0),'U':Q(0),'T':Q(0)};fixed=[Q(0)]*3
    for letter in word:
        if letter=='H':
            for head in heads:
                index+=1
                for i in range(3):fixed[i]+=index*head[i]
        else:index+=1;weights[letter]+=index
    den=Q(index*(index+1),2);anchor=m.te.pair.boundary_readout(e.head)
    y=[]
    for i in range(3):
        if not scope.strength:
            # Exact annihilation by zero removes the raw context dependency.
            out=n('Y'+str(i),'zero-connection',(),(anchor[i][i],),lambda i=i:C(anchor[i][i]))
        else:
            raw=n('raw'+str(i),'ordered-diagonal', (S[i],U[i],T[i]),
                (fixed[i],den,tuple(weights.items())),lambda x,u,z,i=i:
                    add(C(fixed[i]),x.scaled(weights['S']),u.scaled(weights['U']),z.scaled(weights['T'])).scaled(1/den))
            out=n('Y'+str(i),'connection',(raw,),(anchor[i][i],scope.strength),lambda r,i=i:
                C(anchor[i][i]-scope.strength/3).add(r.scaled(scope.strength)))
        y.append(out)
    y0,y1,y2=y
    h=n('h','next-head',(y0,y1),(),lambda x,z:sub(x.scaled(2),C(1)).mul(sub(z.scaled(2),C(1))))
    dy=n('dy','difference',(y0,y1),(),sub)
    c=scope.diagonal;hc=prior.scalar(e.head.kernel(scope.C))
    def kernel(label,parts):
        return n(label,'diagonal-kernel',parts,c,lambda *xs:sub(add(*(x.scaled(2*a) for x,a in zip(xs,c))),C(1)))
    sc,uc,tc=kernel('SC',S),kernel('UC',U),kernel('TC',T)
    B1=n('B1','first-word',(sc,uc,tc),(hc,),lambda x,z,u:x.mul(z).mul(u).scaled(hc**3))
    prefix=n('prefix','prefix-error',(B1,),(),lambda x:sub(x.scaled(-1),C(1)))
    k=n('k','inherited-first-word',(B1,),(hc,),lambda x:x.scaled(-hc))
    A=n('A','future-affine',(h,dy,y1),c,lambda h_,d_,z:
        C(1).add(h_.mul(sub(C(1),z.scaled(2)))).scaled(c[0]-c[1]).add(h_.mul(d_).scaled(2*c[1]-1)))
    B=n('B','future-null-direction',(y0,y1,y2,dy),c,lambda x,z,u,d_:
        add(sub(z,u).scaled(c[0]),sub(u,x).scaled(c[1]),d_.scaled(c[2])).scaled(2))
    N=n('N','correction-numerator',(h,dy,k,A),(),lambda h_,d_,k_,a_:sub(h_.mul(d_),k_.mul(a_)))
    D=n('D','correction-denominator',(k,h,B),(),lambda k_,h_,b_:k_.mul(h_).mul(b_))
    a0=n('a0','local-affine',(h,y1),(),lambda h_,z:C(1).add(h_.mul(sub(C(1),z.scaled(2)))))
    L=n('L','common-action-denominator',(h,dy,D),(),lambda h_,d_,dd:h_.mul(d_).mul(dd).scaled(2))
    r0=n('R0n','action-0',(a0,D,h,N,y1,y2),(),lambda a_,dd,h_,nn,z,u:
        a_.mul(dd).add(h_.mul(nn).mul(sub(z,u)).scaled(2)))
    r1=n('R1n','action-1',(h,dy,a0,D,N,y2,y0),(),lambda h_,d_,a_,dd,nn,u,x:
        sub(h_.mul(d_).scaled(2),a_).mul(dd).add(h_.mul(nn).mul(sub(u,x)).scaled(2)))
    r2=n('R2n','action-2',(h,dy,N),(),lambda h_,d_,nn:h_.mul(d_).mul(nn).scaled(2))
    roots=(*y,h,dy,prefix,B1,N,D,L,r0,r1,r2)
    return dict(zip(m.LABELS,roots)),tuple(g.nodes)


def assessed(entry,scope,polys,intervals,work):
    q={}
    for label,poly in polys.items():
        intervals_used=tuple((k,intervals[k]) for k in poly.dependencies)
        projection=(SCHEMA,coefficients(poly),intervals_used,192)
        key=fingerprint(projection)
        if key in entry._bounds:
            bound=entry._bounds[key]
            if (type(bound) is not Bound or _BOUND_ISSUED.get(id(bound)) is not bound or bound.signature!=key
                or bound.projection!=projection):
                raise ValueError('issued interval identity changed')
            q[label]=bound.interval;work.bounds_reused.append(label)
        else:
            q[label]=enclose(coefficients(poly),dict(intervals_used),192)[0]
            bound=Bound(key,projection,q[label]);_BOUND_ISSUED[id(bound)]=bound;entry._bounds[key]=bound;work.bounds_new.append(label)
    # Always bind the current C, domain and exact/coarse intervals again.
    if not prior.scalar(entry.base.head.kernel(scope.C)) or q['B1']==(0,0):return 'EMPTY'
    if not m.te.port.regular(scope.C,entry.base.library):return 'UNKNOWN_CHART'
    y=tuple(q['Y'+str(i)] for i in range(3))
    if not all(b.nonzero(b.subtract(y[i],y[j])) for i,j in ((0,1),(0,2),(1,2))):return 'REFINE'
    if (not b.nonzero(q['h']) or not b.separated(b.subtract(q['h'],(Q(1),Q(1))))
        or not b.nonzero((q['h'][0]+3,q['h'][1]+3)) or not b.separated(q['prefix'])):return 'REFINE'
    alpha=b.ratio(q['N'],q['D'])
    if alpha is None:return 'EMPTY' if q['D']==(0,0) and b.nonzero(q['N']) else 'REFINE'
    lo,hi=scope.domain
    if alpha[1]<lo or alpha[0]>hi:return 'EMPTY'
    if not lo<=alpha[0]<=alpha[1]<=hi or not b.nonzero(q['L']):return 'REFINE'
    return 'ADMISSIBLE'


def factor(entry,mode,key,weights,poly,work,label):
    projection=(SCHEMA,mode,key,weights,coefficients(poly));signature=fingerprint(projection)
    if signature in entry._factors:
        proof=entry._factors[signature]
        if (type(proof) is not Factor or _FACTOR_ISSUED.get(id(proof)) is not proof or proof.signature!=signature
            or proof.projection!=projection):
            raise ValueError('issued observation identity changed')
        work.factors_reused.append((mode,label))
    else:
        if mode=='CONSTANT':out=poly if not poly.dependencies else None
        elif mode=='PRODUCT':out=algebra.product_only(poly)
        elif mode in ('SUM_PRODUCT','PORT_PRODUCT'):out=algebra.linear_product(poly,key,*weights)
        else:out=poly
        if out is not None:
            s,t=algebra.variable('s'),algebra.variable('t');definitions={'s':s,'t':t,'p':s.mul(t)}
            if key:definitions[key]=s.scaled(weights[0]).add(t.scaled(weights[1]))
            if algebra.expand(out,definitions).terms!=poly.terms:raise AssertionError('new observation identity failed exact re-expansion')
        proof=Factor(signature,projection,None if out is None else coefficients(out));_FACTOR_ISSUED[id(proof)]=proof
        entry._factors[signature]=proof
        work.factors_new.append((mode,label))
    return None if proof.coefficients is None else Polynomial(proof.coefficients)


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
    node_bindings: tuple
    @property
    def digest(self):return fingerprint(tuple(self.__dict__.values()))
    @property
    def polynomials(self):return {label:Polynomial(coeff) for label,coeff in self.coefficients}


def compile(entry,scope,v,word,policy=Policy()):
    verify_entry(entry);v=Q(v)
    if type(scope) is not m.Scope or scope.entry_digest!=entry.base.digest or v not in scope.controls or word not in scope.words:
        raise ValueError('complete original scope and current choice required')
    key=(scope.digest,v,word,policy.digest);work=Work()
    if key in entry._plans:
        work.plan_cache_hits=1;entry._receipts.append((key,work));return entry._plans[key]
    roots,nodes=graph(entry,scope,v,word,work);polys={label:P(node) for label,node in roots.items()}
    bindings=tuple((x.name,x.signature,x.digest) for x in nodes)
    recipe_digest=fingerprint((SCHEMA,entry.digest,scope.digest,v,word,tuple((k,x.digest) for k,x in roots.items())))
    initial=assessed(entry,scope,polys,{k:entry.base.vault.coarse(k,fn.Meter()) for k in m.KEYS},work)
    def issue(mode,status,features=(),converted=None,tested=()):
        plan=Plan(entry.digest,scope.digest,policy.digest,recipe_digest,v,word,mode,status,tuple(features),
            tuple((label,coefficients(poly)) for label,poly in (converted or {}).items()),tuple(tested),bindings)
        entry._plans[key]=plan;entry._receipts.append((key,work));return plan
    if initial in ('EMPTY','UNKNOWN_CHART'):return issue('CONSTANT',initial)
    tested=[]
    for mode in policy.modes:
        features=(() if mode=='CONSTANT' else ('p',) if mode=='PRODUCT' else ('p','sum') if mode=='SUM_PRODUCT'
            else ('p','port-'+word) if mode=='PORT_PRODUCT' else ('s','t'))
        name=features[1] if mode in ('SUM_PRODUCT','PORT_PRODUCT') else None
        weights=((Q(1),Q(1)) if mode=='SUM_PRODUCT' else port_weights(entry.base,word) if mode=='PORT_PRODUCT' else ())
        converted={}
        for label,poly in polys.items():
            out=factor(entry,mode,name,weights,poly,work,label)
            if out is None:break
            converted[label]=out
        if len(converted)!=len(polys):tested.append((mode,'NONZERO_REMAINDER'));continue
        features=tuple(k for k in features if any(k in poly.dependencies for poly in converted.values()))
        if len(features)>policy.max_features:tested.append((mode,'FEATURE_BUDGET'));continue
        tested.append((mode,'EXACT_IDENTITY'));return issue(mode,'AVAILABLE',features,converted,tested)
    return issue('NONE','UNDETERMINED_NO_SCHEMA',tested=tested)


def verify_plan(entry,scope,policy,plan):
    if type(plan) is not Plan or plan is not compile(entry,scope,plan.v,plan.word,policy):
        raise ValueError('the scope-bound issued incremental plan changed')


def resolve(entry,scope,policy,plan,cache=(),meter=None):
    verify_plan(entry,scope,policy,plan);cache=dict(cache);validate_cache(entry,cache)
    meter=fn.Meter() if meter is None else meter
    if plan.status!='AVAILABLE':return m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,plan.status),tuple(sorted(cache.items())),(),(),()
    new=[];derived=[];used=[]
    for key in plan.features:
        vault=vault_for(entry,key);ref=vault.reference(key)
        if key not in cache:
            value=derive_cached(entry,key,cache)
            if value is None:value=vault.exact(key,meter);new.append(key)
            else:derived.append(key)
            cache[key]=(ref.digest,value)
        if cache[key][0]!=ref.digest or fingerprint((ref.key,ref.origin,cache[key][1],ref.envelope))!=ref.commitment:
            raise ValueError('cached exact feature or derived coordinate changed')
        used.append((key,cache[key][1]))
    values=dict(used);work=Work();status=assessed(entry,scope,plan.polynomials,{k:(x,x) for k,x in values.items()},work)
    if status!='ADMISSIBLE':action=m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,status,read_keys=plan.features)
    else:
        q={label:poly.exact(values)[0] for label,poly in plan.polynomials.items()}
        R=tuple(q['R'+str(i)+'n']/q['L'] for i in range(3))+(Q(0),)*3
        T=tuple(x+plan.v*z for x,z in zip(entry.base.first.flight.pair.representative.weights,entry.base.first.axis))
        action=m.Action(scope.digest,plan.recipe_digest,plan.v,plan.word,'ADMISSIBLE',T,R,q['N']/q['D'],read_keys=plan.features)
    return action,tuple(sorted(cache.items())),tuple(new),tuple(derived),tuple(used)
