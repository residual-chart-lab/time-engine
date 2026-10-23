"""Independent exact polynomial-composition checks, without runtime edits."""
from pathlib import Path
import sys, json
from fractions import Fraction as Q

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import synthesized_resolution as a
import rr68_study as study
import observation_synthesis as s
import adaptive_resolution as old
import adaptive_session as old_live
import rr66_study as old_study


def real(poly):
    out={}
    for monomial,c in poly.terms.items():
        assert not any(c[1:])
        if c[0]:out[tuple(monomial)]=c[0]
    return out


def add(p,q):
    result=dict(p)
    for m,c in q.items():
        result[m]=result.get(m,Q(0))+c
        if not result[m]:del result[m]
    return result


def mul(p,q):
    result={}
    for m,c in p.items():
        for n,d in q.items():result=add(result,{tuple(sorted(m+n)):c*d})
    return result


def compose(expression,definitions):
    out={}
    for monomial,c in expression.items():
        term={():c}
        for name in monomial:term=mul(term,definitions[name])
        out=add(out,term)
    return out


def check_family(inputs,proof):
    assert proof.status=='AVAILABLE'
    definitions={k:real(a.Polynomial(v)) for k,v in proof.definitions}
    for name,coeff in proof.outputs:
        assert compose(real(a.Polynomial(coeff)),definitions)==real(inputs[name])


def run():
    # Rational signed forms, new variable names, and reversed output order.
    u,v=s.variable('u'),s.variable('v');families=0
    for A,B,C,D,E in ((3,5,2,-1,7),(-2,3,1,4,-2),(0,2,3,-5,1),(7,0,-2,1,3)):
        z=u.scaled(Q(A,3)).add(v.scaled(Q(B,5)))
        q=u.mul(u).scaled(Q(C,2)).add(u.mul(v).scaled(Q(D,7))).add(v.mul(v).scaled(Q(E,3)))
        inputs={'first':z.add(q).add(s.scalar(2)),
                'second':q.mul(q).add(z.mul(z).mul(z)),
                'third':q.mul(z).add(z.scaled(-3))}
        for items in (list(inputs.items()),list(reversed(list(inputs.items())))):
            demand=dict(items);proof=s.discover(demand,variables=('u','v'))
            check_family(demand,proof);families+=1

    entry=a.register();plans=0;identities=0
    # Frames outside RR68's three precommitted coordinate fixtures.
    for frame in ((Q(3,2),Q(-2,3),Q(5,7),Q(4,5)),(0,2,-3,0)):
        for name in ('mixed','main'):
            for word in a.m.WORDS:
                request=study.scope(entry,name,'1/1024',frame)
                plan=study.before_values(entry,request,1,word)
                assert plan.status=='AVAILABLE'
                original=a.m.build(entry.base,request.base_scope,1,word).polynomials
                definitions={key:real(a.Polynomial(coeff)) for key,coeff in plan.definitions}
                for label,poly in plan.polynomials.items():
                    assert compose(real(poly),definitions)==real(original[label]);identities+=1
                plans+=1

    # Re-run the prior audit counterexample, without its old expected result.
    e=old.register();fine=old_study.scope(e,'mixed','1/1024');main=old_study.scope(e,'main','1/1024')
    state=old_live.resolve(old_live.choose(old_live.start(e,fine),1,'HHHSUT'))
    meter=old.fn.Meter()
    state=old_live.resolve(old_live.choose(old_live.revise(state,main),1,'HHHSUT'),meter)
    record=old_live.history(state)[-1]
    assert meter.exact_reads==1 and record['new_keys']==['s'] and record['derived_keys']==['t']
    return dict(audited_commit='a189fc12382cdda3011c7b73c2e783821745a16c',
        independent_ring_verifier=True,synthetic_families=families,new_frames=2,
        physical_plans=plans,physical_polynomial_identities=identities,
        rr66_repair=dict(exact_reads=meter.exact_reads,new_keys=record['new_keys'],derived_keys=record['derived_keys']))


if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
