#!/usr/bin/env python3
"""RR31: two closed flowers, a prescribed interleaving, and its exact kernel.

All arithmetic is rational. No future-source autonomy or backward causal law
is implemented. The three-direction bound is conditional on the stated cut.
"""
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import json

TABLE=((1,2,3,4),(2,-1,4,-3),(3,-4,-1,2),(4,3,-2,-1))
def mul(a,b):
    return (1 if a*b>0 else -1)*TABLE[abs(a)-1][abs(b)-1]
def compress(w):
    v=1
    for a in w:
        v=mul(a,v)
    return v
def zmat():
    return [[Q(0) for _ in range(3)] for _ in range(3)]
def eye():
    return [[Q(a==b) for b in range(3)] for a in range(3)]
def plus(X,Y):
    return [[X[a][b]+Y[a][b] for b in range(3)] for a in range(3)]
def scale(c,X):
    return [[c*v for v in row] for row in X]
def mm(X,Y):
    return [[sum(X[a][c]*Y[c][b] for c in range(3)) for b in range(3)] for a in range(3)]
def mv(X,y):
    return [sum(X[a][b]*y[b] for b in range(3)) for a in range(3)]
def tr(X):
    return sum(X[a][a] for a in range(3))
def outer(y):
    return [[a*b for b in y] for a in y]
def basis(a,b):
    X=zmat();X[a][b]=Q(1);return X
def push(out,c,w):
    u=compress(w)
    out[abs(u)-1]+=c*(1 if u>0 else -1)
def qstate(X):
    out=[Q(0)]*4
    for a,b in product(range(3),repeat=2):
        push(out,X[a][b],(a+2,b+2))
    return out
def probe(X,y):
    out=[Q(0)]*4
    for a,b,c in product(range(3),repeat=3):
        push(out,X[a][b]*y[c],(a+2,c+2,b+2))
    return out
def join(X,Y):
    out=[Q(0)]*4
    for a,b,c,d in product(range(3),repeat=4):
        push(out,X[a][b]*Y[c][d],(a+2,c+2,b+2,d+2))
    return out
def predicted_join(X,Y):
    C=plus(mm(X,Y),scale(-1,mm(Y,X)))
    return [2*tr(mm(X,Y))-tr(X)*tr(Y),2*C[1][2],2*C[2][0],2*C[0][1]]
def rank(A):
    A=[[Q(v) for v in row] for row in A]
    if not A:return 0
    p=0
    for c in range(len(A[0])):
        k=next((k for k in range(p,len(A)) if A[k][c]),None)
        if k is None:continue
        A[p],A[k]=A[k],A[p]
        v=A[p][c];A[p]=[x/v for x in A[p]]
        for k in range(len(A)):
            if k!=p and A[k][c]:
                t=A[k][c];A[k]=[x-t*y for x,y in zip(A[k],A[p])]
        p+=1
        if p==len(A):break
    return p
def columns(xs):
    return list(map(list,zip(*xs)))
def flat(X):
    return [v for row in X for v in row]

def main():
    checks=[]
    def check(name,ok,**detail):
        assert ok,name
        checks.append(dict(name=name,passed=True,**detail))
    E=eye();axes=E;pure=[outer(y) for y in axes]
    sym=pure+[plus(basis(a,b),basis(b,a)) for a,b in ((0,1),(0,2),(1,2))]
    stf=[plus(pure[0],scale(-1,pure[1])),plus(pure[1],scale(-1,pure[2]))]+sym[3:]
    check('the fixed-real-compression fibre has five independent symmetric trace-free differences',
          rank(columns([qstate(basis(a,b)) for a,b in product(range(3),repeat=2)]))==4
          and rank(columns([flat(S) for S in stf]))==5
          and all(qstate(S)==[0,0,0,0] for S in stf))
    check('insertion on every symmetric basis tensor equals (trace X I minus 2 X)y',
          all(probe(X,y)==[Q(0)]+mv(plus(scale(tr(X),E),scale(-2,X)),y)
              for X,y in product(sym,axes)),basis_cases=18)
    terminal_cases=0
    for n in range(2,6):
        for w in product((2,3,4),repeat=n):
            total=[Q(0)]*4;old=[Q(0)]*4
            for e in (2,3,4):
                push(total,Q(1),w[:-1]+(e,)+w[-1:]+(e,))
            push(old,Q(1),w)
            assert total==old
            terminal_cases+=1
    check('the three future read-and-close values sum to the old compression at any tested terminal gap',
          True,lengths=[2,3,4,5],word_basis_cases=terminal_cases)
    check('the two-flower interleaving has the trace and commutator formula',
          all(join(X,Y)==predicted_join(X,Y) for X,Y in product(sym,repeat=2)),basis_pairs=36)
    response_columns=[sum((join(S,outer(y)) for y in axes[:2]),[]) for S in stf]
    check('two future axes already detect all five exact residual directions',
          rank(columns(response_columns))==5)
    X0=scale(Q(1,3),E)
    check('every nonzero tested residual changes a legal pure-flower upper response from zero baseline',
          all(any(join(plus(X0,S),Y)!=join(X0,Y) for Y in pure) for S in stf))
    directions=axes+[[Q(3,5),Q(4,5),Q(0)],[Q(0),Q(3,5),Q(4,5)],
                     [Q(2,3),Q(1,3),Q(2,3)]]
    cases=0;rank_success={1:set(),2:set(),3:set()}
    for coeffs in product((-1,0,1),repeat=5):
        X=X0
        for c,S in zip(coeffs,stf):X=plus(X,scale(c,S))
        assert qstate(X)==[-1,0,0,0]
        for y in directions:
            assert qstate(outer(y))==[-1,0,0,0]
            good=join(X,outer(y))==[-1,0,0,0]
            assert good==(mv(X,y)==[0,0,0])
            cases+=1
    check('joint result minus one is equivalent to the future direction lying in the current kernel',True,
          rational_boundary_direction_cases=cases)
    rank_examples=[pure[0],[[Q(1,2),0,0],[0,Q(1,2),0],[0,0,0]],X0]
    for expected,X in enumerate(rank_examples,1):
        assert rank(X)==expected
        rank_success[expected]=[join(X,Y)==[-1,0,0,0] for Y in pure]
    check('rank one two and three leave respectively two one and zero kernel dimensions',
          all(3-rank(X)==d for X,d in zip(rank_examples,(2,1,0))))
    A,B,C=pure
    four=[join(X,Y)[0] for X,Y in ((A,B),(C,B),(A,C),(C,C))]
    mixed=join(plus(C,scale(-1,A)),plus(C,scale(-1,B)))
    check('two separately result-preserving substitutions fail when combined',
          four==[-1,-1,-1,1] and mixed==[2,0,0,0])
    # Solve the full affine fibre, not only the three pure diagonal candidates.
    def system(ys):
        M=[];rhs=[]
        for y in ys:
            vectors=[mv(S,y) for S in stf]
            v0=mv(X0,y)
            for a in range(3):
                M.append([v[a] for v in vectors]);rhs.append(-v0[a])
        return M,rhs
    M2,b2=system([axes[0],axes[2]])
    M3,b3=system(axes)
    check('two independent future directions admit a unique full-fibre current boundary',
          rank(M2)==rank([r+[b] for r,b in zip(M2,b2)])==5
          and mv(B,axes[0])==mv(B,axes[2])==[0,0,0])
    check('three independent future directions have no solution anywhere in the full affine fibre',
          rank(M3)==5 and rank([r+[b] for r,b in zip(M3,b3)])==6)
    success=[[join(X,Y)==[-1,0,0,0] for Y in pure] for X in pure]
    check('the conditional uniform three-direction forward bound of two thirds is attained',
          success==[[False,True,True],[True,False,True],[True,True,False]])
    check('a forward protocol controlling or learning the future direction still attains certainty',
          all(join(pure[(u+1)%3],pure[u])==[-1,0,0,0] for u in range(3)))
    result=dict(note='RR31',passed=True,groups=len(checks),checks=checks,
                local_substitution_results=[int(x) for x in four],mixed_residual=[str(x) for x in mixed],
                axis_success_table=success,rank_example_axis_success=rank_success,
                affine_constraint_ranks={'two_axes':rank(M2),'two_axes_augmented':rank([r+[b] for r,b in zip(M2,b2)]),
                                         'three_axes':rank(M3),'three_axes_augmented':rank([r+[b] for r,b in zip(M3,b3)])},
                limitations=['Interleaving is a chosen composition of existing boundary operations.',
                             'Future-source autonomy and the closure-before-source event cut are not derived.',
                             'The two-thirds bound assumes that cut and a uniform independent future source.',
                             'This is an active residual realization for B2, not full v18 terminality or retrocausality.'])
    path=Path(__file__).with_name('two_flower_kernel_result.json')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(groups=len(checks),passed=True,cases=cases)))
if __name__=='__main__':main()
