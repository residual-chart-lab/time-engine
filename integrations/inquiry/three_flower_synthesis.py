"""RR69: a rational three-flower consumer of the frozen RR68 synthesizer.

The adapter exposes maximal division-free polynomial islands. A proof for all
islands extends by congruence to every rational output and every original
division guard. It never cancels a denominator or prunes a zero factor.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
import synthesized_resolution as a
from synthesized_resolution import m,fn,b,prior,Polynomial,fingerprint
from mixed_action_sets import d,te,plant
import observation_synthesis as synthesis

SCHEMA='RR69-three-flower-rational-islands-v1'
POLICY=synthesis.Budget()
MAX_NODES=1024
_PLANS={}

@dataclass(frozen=True)
class Scope:
    base_scope: object
    last_strength: Q=Q(1,1024)
    middle_controls: tuple=(Q(-1),Q(0),Q(1))
    frame: tuple=(Q(1),Q(0),Q(0),Q(1))
    def __post_init__(self):
        object.__setattr__(self,'last_strength',Q(self.last_strength))
        object.__setattr__(self,'middle_controls',tuple(map(Q,self.middle_controls)))
        object.__setattr__(self,'frame',tuple(map(Q,self.frame)))
        if (type(self.base_scope) is not m.Scope or self.last_strength not in (0,Q(1,1024))
            or not self.middle_controls or len(set(self.middle_controls))!=len(self.middle_controls)
            or any(x not in (-1,0,1) for x in self.middle_controls)
            or len(self.frame)!=4 or not self.frame[0]*self.frame[3]-self.frame[1]*self.frame[2]):
            raise ValueError('complete three-flower scope and invertible frame required')
    @property
    def digest(self):return fingerprint((SCHEMA,self.base_scope.digest,self.last_strength,self.middle_controls,self.frame))
    @property
    def C(self):return self.base_scope.C

@dataclass(frozen=True)
class Node:
    kind: str
    children: tuple=()
    coefficients: tuple=()

class Arithmetic:
    def __init__(self):self.nodes=[];self.index={};self.divisors=[]
    def issue(self,node):
        if node not in self.index:
            if len(self.nodes)>=MAX_NODES:raise ValueError('rational graph budget exceeded')
            self.index[node]=len(self.nodes);self.nodes.append(node)
        return Term(self,self.index[node])
    def poly(self,p):return self.issue(Node('poly',coefficients=synthesis.data(p)))
    def scalar(self,x):return self.poly(synthesis.scalar(x))
    def operation(self,kind,left,right):
        left=self.scalar(left) if not isinstance(left,Term) else left
        right=self.scalar(right) if not isinstance(right,Term) else right
        if left.owner is not self or right.owner is not self:raise ValueError('one issued graph required')
        x,y=(self.nodes[z.index] for z in (left,right))
        if kind=='div':self.divisors.append(right.index)
        if x.kind==y.kind=='poly' and kind!='div':
            p,q=Polynomial(x.coefficients),Polynomial(y.coefficients)
            return self.poly(p.add(q) if kind=='add' else p.mul(q))
        return self.issue(Node(kind,(left.index,right.index)))

@dataclass(frozen=True)
class Term:
    owner: object
    index: int
    def __add__(self,x):return self.owner.operation('add',self,x)
    def __radd__(self,x):return self+x
    def __neg__(self):return self*-1
    def __sub__(self,x):return self+-x if isinstance(x,Term) else self+(-Q(x))
    def __rsub__(self,x):return -self+x
    def __mul__(self,x):return self.owner.operation('mul',self,x)
    def __rmul__(self,x):return self*x
    def __truediv__(self,x):return self.owner.operation('div',self,x)
    def __rtruediv__(self,x):return self.owner.operation('div',x,self)

@dataclass(frozen=True)
class Recipe:
    nodes: tuple
    outputs: tuple
    divisors: tuple
    islands: tuple
    @property
    def digest(self):return fingerprint((tuple((n.kind,n.children,n.coefficients) for n in self.nodes),self.outputs,self.divisors,self.islands))
    @property
    def polynomials(self):return {name:Polynomial(self.nodes[index].coefficients) for name,index in self.islands}


def graph(entry,scope,v,u,word):
    """Known RR65 source family, RR53 ordered port twice, independent common C."""
    a.verify_entry(entry);base=entry.base;raw=scope.base_scope;v,u=Q(v),Q(u)
    if raw.entry_digest!=base.digest or v not in raw.controls or u not in scope.middle_controls or word not in raw.words:
        raise ValueError('original entry, request and current choices required')
    g=Arithmetic();s,t=(g.poly(synthesis.variable(k)) for k in ('s','t'))
    fixed=base.first.flight.pair.representative.weights
    S=tuple(g.scalar(x)+s*z for x,z in zip(fixed[:3],base.first.axis[:3]))
    U=tuple(g.scalar(x)+t*z for x,z in zip(fixed[:3],base.direction_U[:3]))
    T=tuple(g.scalar(x+v*z) for x,z in zip(fixed[:3],base.first.axis[:3]))
    H=tuple(tuple(g.scalar(z) for z in leaf.weights[:3]) for leaf in base.head.leaves())
    anchor=te.pair.boundary_readout(base.head)
    def response(weights,C):return 2*sum(x*c for x,c in zip(weights,C))-1
    def head(Y):return (2*Y[0]-1)*(2*Y[1]-1)
    def port(leaves,strength):
        den=Q(len(leaves)*(len(leaves)+1),2)
        return tuple(g.scalar(anchor[i][i]-strength/3)+strength*sum(Q(pos)/den*x[i] for pos,x in enumerate(leaves,1)) for i in range(3))
    def correction(Y,control):
        h=head(Y);dy=Y[0]-Y[1]
        axis=((Y[1]-Y[2])/dy,(Y[2]-Y[0])/dy,g.scalar(1))
        first=((1/h+1)/2-Y[1])/dy
        return (first+control*axis[0],1-first+control*axis[1],control*axis[2]),h,axis,first
    mapping={'H':H,'S':(S,),'U':(U,),'T':(T,)}
    leaves=tuple(x for k in word for x in mapping[k]);Y2=port(leaves,raw.strength)
    R2,h2,axis2,first2=correction(Y2,g.scalar(u))
    Y3=port(H+(R2,),scope.last_strength);h3=head(Y3);dy3=Y3[0]-Y3[1]
    c=raw.diagonal;hc=prior.scalar(base.head.kernel(raw.C))
    B1=g.scalar(hc**3)*response(S,c)*response(U,c)*response(T,c)
    B2=hc*response(R2,c)
    # The final source must satisfy h3*J_Y3(R3)=1 locally and
    # -B1*B2*hc*J_C(R3)=+1 at the common upper boundary.
    first3=((1/h3+1)/2-Y3[1])/dy3
    R30=(first3,1-first3,g.scalar(0))
    axis3=((Y3[1]-Y3[2])/dy3,(Y3[2]-Y3[0])/dy3,g.scalar(1))
    gain=2*sum(x*z for x,z in zip(axis3,c))
    alpha=(1/(-hc*B1*B2)-response(R30,c))/gain
    R3=tuple(x+alpha*z for x,z in zip(R30,axis3));B3=hc*response(R3,c)
    outputs={**{'Y2_'+str(i):z.index for i,z in enumerate(Y2)},'h2':h2.index,'B1':B1.index,
        **{'R2_'+str(i):z.index for i,z in enumerate(R2)},**{'Y3_'+str(i):z.index for i,z in enumerate(Y3)},
        'h3':h3.index,'B2':B2.index,'gain3':gain.index,'alpha3':alpha.index,
        **{'R3_'+str(i):z.index for i,z in enumerate(R3)},'B3':B3.index,
        'upper_prefix1':(-B1).index,'upper_prefix2':(-B1*B2).index,'upper_terminal':(-B1*B2*B3).index}
    needed=set();todo=list(outputs.values())+list(g.divisors)
    while todo:
        index=todo.pop()
        if index in needed:continue
        needed.add(index);node=g.nodes[index]
        if node.kind!='poly':todo.extend(node.children)
    islands=tuple(('p'+str(i),i) for i in sorted(needed) if g.nodes[i].kind=='poly')
    result=Recipe(tuple(g.nodes),tuple(outputs.items()),tuple(g.divisors),islands)
    verify_graph(result);return result


def verify_graph(recipe):
    if type(recipe) is not Recipe or not 0<len(recipe.nodes)<=MAX_NODES:raise ValueError('finite typed rational recipe required')
    for i,node in enumerate(recipe.nodes):
        if type(node) is not Node:raise ValueError('typed arithmetic node required')
        if node.kind=='poly':
            p=Polynomial(node.coefficients)
            if node.children or not set(p.dependencies)<={'s','t'} or any(any(c[1:]) for c in p.terms.values()):raise ValueError('exact real input island required')
        elif node.kind not in ('add','mul','div') or node.coefficients or len(node.children)!=2 or any(type(j) is not int or not 0<=j<i for j in node.children):
            raise ValueError('acyclic binary arithmetic graph required')
    output=dict(recipe.outputs)
    if len(output)!=len(recipe.outputs) or not output:raise ValueError('unique output names required')
    roots=list(output.values())+list(recipe.divisors)
    if any(type(i) is not int or not 0<=i<len(recipe.nodes) for i in roots):raise ValueError('valid output and denominator roots required')
    expected_div=tuple(n.children[1] for n in recipe.nodes if n.kind=='div')
    # Arithmetic may issue the same division more than once. Every denominator
    # occurrence is bound, and every actual division node must be covered.
    if set(expected_div)!=set(recipe.divisors):raise ValueError('complete original denominator guards required')
    needed=set();todo=roots[:]
    while todo:
        i=todo.pop()
        if i in needed:continue
        needed.add(i)
        if recipe.nodes[i].kind!='poly':todo.extend(recipe.nodes[i].children)
    expected=tuple(('p'+str(i),i) for i in sorted(needed) if recipe.nodes[i].kind=='poly')
    if recipe.islands!=expected:raise ValueError('all maximal division-free islands required')
    return True

class Singular(Exception):pass

class Values:
    def __init__(self,recipe,islands):
        if set(islands)!=set(recipe.polynomials):raise ValueError('all polynomial islands required')
        self.recipe=recipe;self.cache={index:Q(islands[name]) for name,index in recipe.islands}
        self.outputs=dict(recipe.outputs)
    def node(self,index):
        if index not in self.cache:
            n=self.recipe.nodes[index]
            x,y=(self.node(i) for i in n.children)
            if n.kind=='div' and not y:raise Singular('zero original denominator')
            self.cache[index]=x+y if n.kind=='add' else x*y if n.kind=='mul' else x/y
        return self.cache[index]
    def get(self,key):return self.node(self.outputs[key])
    def all(self):return {key:self.get(key) for key,_ in self.recipe.outputs}
    def guard_all_divisions(self):
        for i in self.recipe.divisors:
            if not self.node(i):raise Singular('zero original denominator')

@dataclass(frozen=True)
class Plan:
    entry_digest: str
    scope_digest: str
    v: Q
    u: Q
    word: str
    recipe: object
    status: str
    proof: object=None
    definitions: tuple=()
    coefficients: tuple=()
    @property
    def digest(self):return fingerprint((self.entry_digest,self.scope_digest,self.v,self.u,self.word,
        self.recipe.digest,self.status,self.proof.digest if self.proof else None,self.definitions,self.coefficients))
    @property
    def features(self):return tuple(key for key,_ in self.definitions)
    @property
    def polynomials(self):return {key:Polynomial(coeff) for key,coeff in self.coefficients}


def compile(entry,scope,v,u,word):
    a.verify_entry(entry)
    key=(id(entry),scope.digest,Q(v),Q(u),word)
    if key in _PLANS:return _PLANS[key]
    recipe=graph(entry,scope,v,u,word);raw=scope.base_scope
    initial=('EMPTY' if not prior.scalar(entry.base.head.kernel(scope.C)) else
             'UNKNOWN_CHART' if not te.port.regular(scope.C,entry.base.library) else None)
    if initial:plan=Plan(entry.digest,scope.digest,Q(v),Q(u),word,recipe,initial)
    else:
        demands=a.in_frame(recipe.polynomials,scope.frame)
        proof=synthesis.discover(demands,budget=POLICY)
        if proof.status!='AVAILABLE':plan=Plan(entry.digest,scope.digest,Q(v),Q(u),word,recipe,proof.status,proof)
        else:
            synthesis.verify(demands,proof,POLICY)
            aa,bb,cc,dd=scope.frame;s,t=synthesis.variable('s'),synthesis.variable('t')
            forward={'x':s.scaled(aa).add(t.scaled(bb)),'y':s.scaled(cc).add(t.scaled(dd))}
            definitions=[];substitution={}
            for name,coeff in proof.definitions:
                p=synthesis.expand(Polynomial(coeff),forward);lead=p.terms[min(p.terms)][0]
                obs=a.observe(entry,p.scaled(1/lead));definitions.append((obs.key,obs.coefficients))
                substitution[name]=synthesis.variable(obs.key).scaled(lead)
            polys={label:synthesis.expand(Polynomial(coeff),substitution) for label,coeff in proof.outputs}
            original=recipe.polynomials;actual={name:Polynomial(coeff) for name,coeff in definitions}
            if any(synthesis.expand(poly,actual).terms!=original[label].terms for label,poly in polys.items()):
                raise AssertionError('island identity failed in physical coordinates')
            plan=Plan(entry.digest,scope.digest,Q(v),Q(u),word,recipe,'AVAILABLE',proof,tuple(definitions),tuple((name,synthesis.data(p)) for name,p in polys.items()))
    _PLANS[key]=plan;return plan


def verify_plan(entry,scope,plan):
    if type(plan) is not Plan or plan is not compile(entry,scope,plan.v,plan.u,plan.word):raise ValueError('issued three-flower plan required')
    verify_graph(plan.recipe)
    if plan.status=='AVAILABLE':
        synthesis.verify(a.in_frame(plan.recipe.polynomials,scope.frame),plan.proof,POLICY)
        definitions={key:Polynomial(coeff) for key,coeff in plan.definitions}
        if set(plan.polynomials)!=set(plan.recipe.polynomials) or any(synthesis.expand(poly,definitions).terms!=plan.recipe.polynomials[key].terms for key,poly in plan.polynomials.items()):
            raise ValueError('all rational-island identities required')
    return True

@dataclass(frozen=True)
class Action:
    plan_digest: str
    status: str
    T: tuple=()
    R2: tuple=()
    R3: tuple=()
    alpha: object=None
    values: tuple=()


def assess(entry,scope,plan,values):
    """Exact scalar guards; no future operations or Decoder execution here."""
    get=values.get;raw=scope.base_scope
    def vector(prefix):return tuple(get(prefix+str(i)) for i in range(3))
    def context(diag):return tuple(tuple(x if i==j else Q(0) for j,x in enumerate(diag)) for i in range(3))
    try:
        y2=vector('Y2_')
        if not te.port.regular(context(y2),entry.base.library):return Action(plan.digest,'UNKNOWN_CHART')
        h2=get('h2')
        if not h2:return Action(plan.digest,'EMPTY')
        if abs(h2-1)<=te.port.EPSILON:return Action(plan.digest,'UNDETERMINED_FIRST_BOUNDARY')
        if not get('B1'):return Action(plan.digest,'EMPTY')
        R2=vector('R2_');y3=vector('Y3_')
        if not te.port.regular(context(y3),entry.base.library):return Action(plan.digest,'UNKNOWN_CHART')
        h3=get('h3')
        if not h3 or not get('B2'):return Action(plan.digest,'EMPTY')
        if abs(h3-1)<=te.port.EPSILON:return Action(plan.digest,'UNDETERMINED_FIRST_BOUNDARY')
        if any(abs(get(k)-1)<=te.port.EPSILON for k in ('upper_prefix1','upper_prefix2')):
            return Action(plan.digest,'UNDETERMINED_FIRST_BOUNDARY')
        if not get('gain3'):return Action(plan.digest,'UNDETERMINED_SINGULAR')
        alpha=get('alpha3')
        if not raw.domain[0]<=alpha<=raw.domain[1]:return Action(plan.digest,'EMPTY')
        R3=vector('R3_');values.guard_all_divisions();all_values=values.all()
    except Singular:return Action(plan.digest,'UNDETERMINED_SINGULAR')
    def response(weights,diag):return 2*sum(x*y for x,y in zip(weights,diag))-1
    if (sum(R2)!=1 or sum(R3)!=1 or h2*response(R2,y2)!=1 or h3*response(R3,y3)!=1 or all_values['upper_terminal']!=1):
        raise AssertionError('the rational action failed exact local or upper identities')
    base=entry.base;T=tuple(x+plan.v*z for x,z in zip(base.first.flight.pair.representative.weights,base.first.axis))
    return Action(plan.digest,'ADMISSIBLE',T,R2+(Q(0),)*3,R3+(Q(0),)*3,alpha,tuple(all_values.items()))


def read_observations(entry,plan,cache=(),meter=None):
    cache=dict(cache);a.validate_cache(entry,cache);meter=fn.Meter() if meter is None else meter
    sources={};new=[];derived=[];registered=[]
    for key in plan.features:
        obs=a.observation(entry,key);poly=Polynomial(obs.coefficients)
        if key in cache:continue
        known=[(k,Polynomial(a.observation(entry,k).coefficients)) for k in sorted(cache)]
        expression=synthesis.represent(poly,known,POLICY)
        if expression is not None:
            if synthesis.expand(expression,dict(known)).terms!=poly.terms:raise AssertionError('derived observation identity failed')
            value=expression.exact({k:v[1] for k,v in cache.items()})[0];derived.append(key)
        else:
            try:entry.derived.reference(key);present=True
            except KeyError:present=False
            if present:value=entry.derived.exact(key,meter)
            else:
                for dep in poly.dependencies:
                    if dep not in sources:sources[dep]=entry.base.vault.exact(dep,meter)
                value=poly.exact(sources)[0];registered.append(key)
            new.append(key)
        entry.derived.register(key,value,obs.envelope,obs.origin)
        if key in registered:value=entry.derived.exact(key,meter)
        cache[key]=(entry.derived.reference(key).digest,value)
    a.validate_cache(entry,cache)
    work=dict(new_feature_queries=len(new),source_reads_for_registration=len(sources),newly_registered=registered,derived_features=derived,total_exact_queries=meter.exact_reads)
    return tuple(sorted(cache.items())),work


def resolve(entry,scope,plan,cache=(),meter=None):
    verify_plan(entry,scope,plan);a.validate_cache(entry,dict(cache))
    if plan.status!='AVAILABLE':return Action(plan.digest,plan.status),tuple(cache),{}
    cache,work=read_observations(entry,plan,cache,meter)
    actual={key:dict(cache)[key][1] for key in plan.features}
    islands={label:poly.exact(actual)[0] for label,poly in plan.polynomials.items()}
    return assess(entry,scope,plan,Values(plan.recipe,islands)),cache,work
