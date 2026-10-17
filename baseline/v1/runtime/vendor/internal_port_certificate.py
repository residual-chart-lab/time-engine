#!/usr/bin/env python3
"""RR32: fixed interior-port universal preparation and exact-record freedom.

Standard library, exact rationals. Port relocation is a different specification
from the fixed terminal port in RR31; the old theorem is not contradicted.
"""
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import json

TABLE=((1,2,3,4),(2,-1,4,-3),(3,-4,-1,2),(4,3,-2,-1))
def mul(a,b):return (1 if a*b>0 else -1)*TABLE[abs(a)-1][abs(b)-1]
def compress(w):
    v=1
    for a in w:v=mul(a,v)
    return v
def qvec(u):
    a=[Q(0)]*4;a[abs(u)-1]=Q(1 if u>0 else -1);return a
def qmul(a,b):
    out=[Q(0)]*4
    for i,j in product(range(4),repeat=2):
        u=mul(i+1,j+1);out[abs(u)-1]+=a[i]*b[j]*(1 if u>0 else -1)
    return out
def evaluate(X,ins=None):
    ins={} if ins is None else ins
    out=[Q(0)]*4
    for w,c in X.items():
        new=[]
        for i,a in enumerate(w,1):
            new.append(a)
            if i in ins:new.append(ins[i])
        u=compress(new);out[abs(u)-1]+=c*(1 if u>0 else -1)
    return out
def add(X,Y,c=Q(1)):
    Z=dict(X)
    for w,v in Y.items():Z[w]=Z.get(w,Q(0))+c*v
    return {w:v for w,v in Z.items() if v}
def colmat(cols):return [list(r) for r in zip(*cols)]
def rref(A):
    A=[[Q(v) for v in row] for row in A];p=0;piv=[]
    for c in range(len(A[0])):
        k=next((k for k in range(p,len(A)) if A[k][c]),None)
        if k is None:continue
        A[p],A[k]=A[k],A[p];v=A[p][c];A[p]=[x/v for x in A[p]]
        for k in range(len(A)):
            if k!=p and A[k][c]:
                t=A[k][c];A[k]=[x-t*y for x,y in zip(A[k],A[p])]
        piv.append(c);p+=1
        if p==len(A):break
    return A,piv
def rank(A):return len(rref(A)[1])
def solve(A,b):
    R,piv=rref([row+[v] for row,v in zip(A,b)])
    n=len(A[0]);assert n not in piv
    x=[Q(0)]*n
    for row,p in zip(R,piv):x[p]=row[-1]
    assert all(sum(a*v for a,v in zip(row,x))==t for row,t in zip(A,b))
    return x
def response(X,g):return sum((evaluate(X,{g:e}) for e in (2,3,4)),[])
def serialize(X):return [{'word':list(w),'coefficient':str(c)} for w,c in sorted(X.items())]

def main():
    checks=[]
    def check(name,ok,**detail):
        assert ok,name;checks.append(dict(name=name,passed=True,**detail))
    Xstar={w:Q(1,2) for w in ((2,2,2,2),(4,3,4,3),(2,4,2,4),(3,2,3,2))}
    identity=sum((qvec(e) for e in (2,3,4)),[])
    check('the four-term committed boundary has compression minus one and identity interior response',
          evaluate(Xstar)==[-1,0,0,0] and response(Xstar,2)==identity,terms=4,length=4)
    unitvectors=[[1,0,0],[0,1,0],[0,0,1],[Q(3,5),Q(4,5),0],
                 [0,Q(3,5),Q(4,5)],[Q(2,3),Q(1,3),Q(2,3)]]
    for v in unitvectors:
        F=[sum(v[a]*evaluate(Xstar,{2:a+2})[b] for a in range(3)) for b in range(4)]
        assert F==[0]+v
        assert qmul([0]+v,F)==[-1,0,0,0]
    check('one fixed interior response succeeds for each tested unknown-later unit direction',True,cases=6)
    ranks=[];outer_cases=0
    for n in range(2,6):
        for g in range(1,n):
            cols=[]
            for w in product((2,3,4),repeat=n):
                X={w:Q(1)};q=evaluate(X);F=[evaluate(X,{g:e}) for e in (2,3,4)]
                cols.append(q+sum(F,[]))
                if g==1:
                    assert [sum(qmul(f,qvec(e))[a] for f,e in zip(F,(2,3,4))) for a in range(4)]==q
                    outer_cases+=1
                if g==n-1:
                    assert [sum(qmul(qvec(e),f)[a] for f,e in zip(F,(2,3,4))) for a in range(4)]==q
                    outer_cases+=1
            expected=9 if n==2 else 12 if g in (1,n-1) else 16
            actual=rank(colmat(cols));assert actual==expected
            ranks.append(dict(length=n,gap=g,rank=actual,expected=expected))
    check('outer contraction identities hold at both ends',True,basis_checks=outer_cases)
    check('joint compression-response ranks distinguish outer ports from interior ports',True,
          port_configurations=len(ranks))
    # Multiplication on H at both sides spans every real-linear map H -> H.
    LR=[]
    for p,q in product(range(1,5),repeat=2):
        LR.append(sum((qvec(mul(q,mul(d,p))) for d in range(1,5)),[]))
    check('two quaternionic sides give all sixteen real-linear quaternion maps',rank(colmat(LR))==16)
    # For the required map M(1)=-1, M(i)=i, M(j)=j, M(k)=k, the compressed
    # bipartite coefficient matrix is one half of the 4x4 identity.
    C=[[Q(0)]*4 for _ in range(4)]
    for w,c in Xstar.items():
        p,q=compress(w[:2]),compress(w[2:])
        C[abs(p)-1][abs(q)-1]+=c*(1 if p*q>0 else -1)
    check('the universal map has rank four across the compressed cut',
          C==[[Q(a==b,2) for b in range(4)] for a in range(4)] and rank(C)==4)
    # RR19 local STF correction, with internal bridge at local gap 3.
    gadgets=[{(a,b,2,2,z):Q(1),(a,b,3,3,z):Q(1),(a,b,4,4,z):Q(-2)}
             for a,b,z in product((2,3,4),repeat=3)]
    zero=[Q(0)]*4
    for G in gadgets:
        assert evaluate(G)==zero
        # The bridge decoder Im m2 kills every diagonal bridge term.
        assert all(abs(compress(w[2:4]))==1 for w in G)
        for choices in product((None,2,3,4),repeat=3):
            ins={g:e for g,e in zip((1,2,4),choices) if e is not None}
            assert evaluate(G,ins)==zero
    check('STF corrections preserve compression, bridge decoding, and every exterior multigap probe',True,
          gadgets=27,exterior_probe_cases=27*64)
    A=colmat([response(G,3) for G in gadgets])
    check('the fixed-record correction space spans every internal response',rank(A)==12)
    solved=[]
    for t in range(12):
        target=[Q(a==t) for a in range(12)];coef=solve(A,target);G={}
        for c,base in zip(coef,gadgets):G=add(G,base,c)
        assert response(G,3)==target and evaluate(G)==zero
        solved.append([str(c) for c in coef])
    check('an exact rational right inverse realizes all twelve internal response coordinates',True,targets=12)
    coef=solve(A,identity);H={}
    for c,base in zip(coef,gadgets):H=add(H,base,c)
    check('the identity internal-response increment has an explicit zero-compression realization',
          response(H,3)==identity and evaluate(H)==zero)
    # Success at the middle does not erase the failure of the original fixed
    # terminal test on the same committed Xstar.
    terminal=[qmul(qvec(e),evaluate(Xstar,{3:e})) for e in (2,3,4)]
    check('the same universal-interior state still obeys the RR31 terminal obstruction',
          [sum(row[a] for row in terminal) for a in range(4)]==[-1,0,0,0]
          and not all(row==[-1,0,0,0] for row in terminal))
    result=dict(note='RR32',passed=True,groups=len(checks),checks=checks,port_ranks=ranks,
                universal_boundary=serialize(Xstar),identity_increment=serialize(H),
                correction_right_inverse_columns=solved,
                terminal_results_on_universal_state=[[str(v) for v in row] for row in terminal],
                limitations=['Interior and terminal ports are different causal test specifications.',
                             'The full RR19 renewal certificate was not rerun.',
                             'No source autonomy, mandatory port rule, or backward causal dynamics is derived.',
                             'Four terms is a lower bound for product blocks across the compressed cut.'])
    path=Path(__file__).with_name('internal_port_result.json')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(groups=len(checks),passed=True,port_ranks=ranks)))
if __name__=='__main__':main()
