"""Exact factorization through a finite catalogue of real retained features."""
from fractions import Fraction as Q
from math import comb
from free_numbers.algebra import Polynomial,ONE


def constant(x):return Polynomial.constant((Q(x),Q(0),Q(0),Q(0)))
def variable(key):return Polynomial((((key,),ONE),))
def power(p,n):
    out=constant(1)
    for _ in range(n):out=out.mul(p)
    return out


def product_only(poly):
    terms=[]
    for monomial,coefficient in poly.terms.items():
        if set(monomial)-{'s','t'} or monomial.count('s')!=monomial.count('t'):return None
        terms.append((('p',)*monomial.count('s'),coefficient))
    return Polynomial(terms)


def linear_product(poly,key,a,b):
    """f(s,t)=A(p,z)+s B(p,z), p=st, z=a*s+b*t; accept only B=0.

    Substitute t=(z-a*s)/b, reduce s^2=(z*s-b*p)/a. Coefficients
    remain exact; a nonzero remainder is never dropped.
    """
    a,b=Q(a),Q(b)
    if not a or not b:raise ValueError('both linear feature weights must be nonzero')
    z,p=variable(key),variable('p')
    reduced=[(constant(1),constant(0))]
    def sn(n):
        while len(reduced)<=n:
            A,B=reduced[-1]
            reduced.append((p.mul(B).scaled(-b/a),A.add(z.mul(B).scaled(1/a))))
        return reduced[n]
    A,B=constant(0),constant(0)
    for monomial,coefficient in poly.terms.items():
        if set(monomial)-{'s','t'}:raise ValueError('unregistered original scalar')
        i,j=monomial.count('s'),monomial.count('t')
        for k in range(j+1):
            factor=Polynomial.constant(coefficient).scaled(Q(comb(j,k))*(-a)**k/b**j).mul(power(z,j-k))
            x,y=sn(i+k)
            A=A.add(factor.mul(x));B=B.add(factor.mul(y))
    return A if not B.terms else None


def expand(poly,definitions):
    """Independent exact re-expansion used to verify accepted factorizations."""
    out=constant(0)
    for monomial,coefficient in poly.terms.items():
        term=Polynomial.constant(coefficient)
        for key in monomial:term=term.mul(definitions[key])
        out=out.add(term)
    return out
