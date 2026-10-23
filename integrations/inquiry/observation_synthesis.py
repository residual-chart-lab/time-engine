"""Bounded graded generator discovery from exact polynomial demands only.

No source geometry, word positions, feature catalogue or retained values enter
this module. Homogeneous components give a sufficient graded algebra; this is
not a search for the globally smallest sufficient observation.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from free_numbers.algebra import Polynomial,fingerprint


def scalar(x):return Polynomial.constant((Q(x),Q(0),Q(0),Q(0)))
def variable(name):return Polynomial((((name,),(Q(1),Q(0),Q(0),Q(0))),))
def data(poly):return tuple(sorted(poly.terms.items()))
def minus(x,y):return x.add(y.scaled(-1))
def degree(poly):return max(map(len,poly.terms),default=0)


class Limit(Exception):pass


@dataclass(frozen=True)
class Budget:
    max_features: int=2
    max_feature_degree: int=2
    max_input_degree: int=16
    max_terms: int=512
    max_products: int=512
    @property
    def digest(self):return fingerprint(tuple(self.__dict__.values()))
    def __post_init__(self):
        for name,lo,hi in (('max_features',0,2),('max_feature_degree',1,2),('max_input_degree',1,16),
                ('max_terms',1,4096),('max_products',1,4096)):
            value=getattr(self,name)
            if type(value) is not int or not lo<=value<=hi:raise ValueError('finite exact synthesis budget required')


def homogeneous(poly,d):return Polynomial((m,c) for m,c in poly.terms.items() if len(m)==d)


def checked(poly,variables,budget):
    if not set(poly.dependencies)<=set(variables):raise ValueError('unregistered formal variable')
    if any(any(c[1:]) for c in poly.terms.values()):raise ValueError('RR68 graded discovery requires real coefficients')
    if len(poly.terms)>budget.max_terms:raise Limit('TERM_BUDGET')
    if degree(poly)>budget.max_input_degree:raise Limit('INPUT_DEGREE_BUDGET')


def expand(poly,definitions):
    out=scalar(0)
    for monomial,coefficient in poly.terms.items():
        term=Polynomial.constant(coefficient)
        for key in monomial:term=term.mul(definitions[key])
        out=out.add(term)
    return out


class Space:
    """Exact row echelon reduction carrying an expression certificate."""
    def __init__(self):self.rows={}
    def reduce(self,poly):
        remainder=poly;expression=scalar(0)
        for pivot in sorted(self.rows):
            c=remainder.terms.get(pivot,(Q(0),)*4)[0]
            if c:
                row,certificate=self.rows[pivot]
                remainder=minus(remainder,row.scaled(c));expression=expression.add(certificate.scaled(c))
        return remainder,expression
    def add(self,poly,expression):
        remainder,used=self.reduce(poly)
        if not remainder.terms:return False
        pivot=min(remainder.terms);c=remainder.terms[pivot][0]
        self.rows[pivot]=(remainder.scaled(1/c),minus(expression,used).scaled(1/c));return True


def powers(weights,total):
    def walk(index,left,exponents):
        if index==len(weights):
            if not left:yield tuple(exponents)
            return
        for n in range(left//weights[index]+1):yield from walk(index+1,left-n*weights[index],exponents+[n])
    yield from walk(0,total,[])


def product_basis(definitions,d,budget):
    space=Space();weights=[degree(p) for _,p in definitions];count=0
    for exponents in powers(weights,d):
        count+=1
        if count>budget.max_products:raise Limit('PRODUCT_BUDGET')
        poly=scalar(1);monomial=[]
        for (name,definition),n in zip(definitions,exponents):
            for _ in range(n):poly=poly.mul(definition);monomial.append(name)
        if len(poly.terms)>budget.max_terms:raise Limit('TERM_BUDGET')
        space.add(poly,Polynomial(((tuple(monomial),(Q(1),Q(0),Q(0),Q(0))),)))
    return space


@dataclass(frozen=True)
class Proof:
    status: str
    variables: tuple
    definitions: tuple
    outputs: tuple
    origins: tuple
    input_digest: str
    @property
    def digest(self):return fingerprint(tuple(self.__dict__.values()))


def discover(inputs,variables=('x','y'),budget=Budget()):
    if type(inputs) is not dict or not inputs or len(set(variables))!=len(variables):raise ValueError('named exact demands required')
    definitions=[];origins=[];spaces={}
    source=fingerprint(tuple((label,data(poly)) for label,poly in inputs.items()))
    def result(status,outputs=()):return Proof(status,tuple(variables),tuple((n,data(p)) for n,p in definitions),
        tuple(outputs),tuple(origins),source)
    try:
        for poly in inputs.values():checked(poly,variables,budget)
        maximum=max(degree(p) for p in inputs.values())
        for d in range(1,maximum+1):
            space=product_basis(definitions,d,budget)
            for label,poly in inputs.items():
                remainder,used=space.reduce(homogeneous(poly,d))
                if not remainder.terms:continue
                if d>budget.max_feature_degree:raise Limit('FEATURE_DEGREE_BUDGET')
                if len(definitions)>=budget.max_features:raise Limit('FEATURE_COUNT_BUDGET')
                pivot=min(remainder.terms);c=remainder.terms[pivot][0];definition=remainder.scaled(1/c)
                name='g'+str(len(definitions));definitions.append((name,definition));origins.append((name,label,d))
                space.add(definition,variable(name))
            spaces[d]=space
        outputs=[]
        for label,poly in inputs.items():
            expression=homogeneous(poly,0)
            for d in range(1,maximum+1):
                remainder,used=spaces[d].reduce(homogeneous(poly,d))
                if remainder.terms:raise AssertionError('incomplete graded span')
                expression=expression.add(used)
            if len(expression.terms)>budget.max_terms:raise Limit('TERM_BUDGET')
            outputs.append((label,data(expression)))
        proof=result('AVAILABLE',outputs)
        verify(inputs,proof,budget);return proof
    except Limit as error:return result('UNDETERMINED_'+str(error))


def verify(inputs,proof,budget=Budget()):
    if type(proof) is not Proof or proof.status!='AVAILABLE':raise ValueError('complete synthesis proof required')
    if proof.input_digest!=fingerprint(tuple((label,data(poly)) for label,poly in inputs.items())):
        raise ValueError('the complete demanded polynomial family changed')
    definitions={name:Polynomial(coeff) for name,coeff in proof.definitions}
    if (len(definitions)!=len(proof.definitions) or len(definitions)>budget.max_features
        or set(k for k,v in proof.outputs)!=set(inputs) or len(proof.outputs)!=len(inputs)):
        raise ValueError('all demand outputs are required')
    try:
        for poly in inputs.values():checked(poly,proof.variables,budget)
        for definition in definitions.values():
            checked(definition,proof.variables,budget)
            degrees={len(m) for m in definition.terms}
            if len(degrees)!=1 or not 1<=degree(definition)<=budget.max_feature_degree:
                raise ValueError('low-degree homogeneous observations required')
        for _,coeff in proof.outputs:
            if len(Polynomial(coeff).terms)>budget.max_terms:raise Limit('TERM_BUDGET')
    except Limit as error:raise ValueError('certificate exceeds the declared synthesis budget') from error
    for label,coeff in proof.outputs:
        expression=Polynomial(coeff)
        if not set(expression.dependencies)<=set(definitions) or expand(expression,definitions).terms!=inputs[label].terms:
            raise ValueError('synthesis identity failed exact re-expansion')
    return True


def represent(poly,definitions,budget=Budget()):
    """Express a new homogeneous feature through already read features, if safe."""
    if not poly.terms:return scalar(0)
    if any(not p.terms or len({len(m) for m in p.terms})!=1 for _,p in definitions):return None
    try:
        out=homogeneous(poly,0)
        for d in range(1,degree(poly)+1):
            remainder,used=product_basis(definitions,d,budget).reduce(homogeneous(poly,d))
            if remainder.terms:return None
            out=out.add(used)
        return out
    except Limit:return None
