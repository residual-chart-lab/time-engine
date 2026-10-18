"""RR58 finite experiment: authenticated RR57 data and undeleted differences."""
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,time

import deferred as d
from deferred import embedded

HERE=Path(__file__).resolve().parent
OUTPUT=d.ROOT/'.work/rr58-local'


@lru_cache(maxsize=1)
def actuals():
    directory=d.ROOT/'integrations/three_plus_one/rr57-records'
    manifest=json.loads((directory/'manifest.json').read_bytes())
    if manifest['schema']!='time-engine-rr57-published-records-v1':
        raise ValueError('the authenticated RR57 record manifest is required')
    result={}
    for item in manifest['records']:
        raw=(directory/item['path']).read_bytes()
        record=embedded.import_record(raw,embedded.triple.TerminalRequirement(Q(item['upper_x'])),
            mode=item['mode'],gain=Q(item['gain']),free_choice=item['free_choice'],trusted_sha256=item['sha256'])
        again=(json.dumps(embedded.export_record(record),ensure_ascii=False,separators=(',',':'))+'\n').encode()
        if again!=raw: raise ValueError('the original RR57 history bytes changed')
        result[item['path'].replace('.record.json','')]=(record,item['sha256'])
    return result


@lru_cache(maxsize=1)
def fixtures():
    a=actuals()
    prepared=embedded.prepare('keep')
    firsts=embedded.first_options(prepared)
    current=prepared.receiver.anchor.current_context
    future=prepared.receiver.reference_context
    reference=prepared.candidates[0].leaf
    pairs=tuple(d.RetainedPair(c.leaf,reference,c.shift,prepared.receiver.delta,
        a['keep-primary'][1]+':RR56-preserved-contact:'+str(c.contact_index)) for c in prepared.candidates)
    # The original word, grouped prefix boundaries and inherited value are all
    # retained. This is a response/readout experiment, not new macro search.
    queries=[]
    for i,first in enumerate(firsts):
        for name,y in (('local',current),('later',future)):
            queries.append((f'first-{i}-{name}',d.query_from_first(first,y,'RR57-first-'+str(i)+'-'+name)))
    primary=a['keep-primary'][0].commitment.requirement.context
    alternate=a['keep-alternate'][0].commitment.requirement.context
    for name,(record,sha) in a.items():
        for frame,y in (('primary',primary),('alternate',alternate)):
            queries.append((name+'@'+frame,d.query_from_macro(record,y,sha+'@'+frame)))
    return prepared,firsts,pairs,current,future,tuple(queries)


def run():
    started=time.monotonic()
    prepared,firsts,pairs,current,future,queries=fixtures()
    groups=[]
    def check(name,ok,**details):
        groups.append(dict(name=name,passed=bool(ok),**details))
        if not ok: raise AssertionError(name)
    basis=[]
    for i in range(3):
        for j in range(3):
            x=tuple(tuple(Q(r==i and c==j) for c in range(3)) for r in range(3))
            value,s=d.split_tensor(x);base=d.sigma2(value)
            assert tuple(tuple(base[r][c]+s[r][c] for c in range(3)) for r in range(3))==x
            assert sum(s[r][r] for r in range(3))==0 and all(s[r][c]==s[c][r] for r in range(3) for c in range(3))
            for k in range(3):
                assert tuple(d.probe(s,d.eye()[k]))==(Q(0),*tuple(-2*s[r][k] for r in range(3)))
            basis.append(x)
    check('free_core_B2_split_and_probe_recovery',len(basis)==9,basis_tensors=9,probe_basis_evaluations=27)
    check('B2_adapter_matches_actual_TE_action',all(tuple(d.join(d.tensor(pair.original),y))==pair.original.kernel(y)
        for pair in pairs for y in (current,future)),cases=8)
    local=d.Scope((current,),entry='first-flower-kernel')
    local_certificates=tuple(d.assess(p,local) for p in pairs)
    meter=d.Meter()
    values=tuple(d.read(p,local,meter,c) for p,c in zip(pairs,local_certificates))
    check('local_replaceability_does_not_expand_or_erase_residue',
        all(c.status==d.SAFE for c in local_certificates) and len(set(values))==1 and
        meter.exact_retained_responses==0 and pairs[1].original.weights!=pairs[1].representative.weights,
        exact_retained_responses=meter.exact_retained_responses)
    widened=d.Scope((current,future),entry='two-flower-kernel')
    check('expanded_scope_reopens_the_same_retained_difference',
        d.assess(pairs[1],widened,budget=1).status==d.UNKNOWN and d.assess(pairs[1],widened).status==d.DIFFERENT)
    late=d.Scope((future,),entry='later-flower-kernel')
    rebound=d.assess(pairs[1],late);expanded=d.Meter()
    actual=d.read(pairs[1],late,expanded,rebound)
    check('later_read_recovers_original_response',actual==pairs[1].original.kernel(future) and
        actual!=pairs[1].representative.kernel(future) and expanded.exact_retained_responses==1)
    word=d.DeferredWord(pairs[1])
    for leaf in prepared.receiver.anchor.original.designated_head.leaves(): word=word.append(leaf)
    direct=pairs[1].original.kernel(future)
    for leaf in word.tail: direct=tuple(d.qmul(leaf.kernel(future),direct))
    check('deferred_difference_survives_ordered_following_operations',word.read(late,d.Meter())==direct)
    tiny=Q(1,10**20)
    tiny_leaf=d.AffineLetter(tuple(w+tiny*v for w,v in zip(pairs[0].representative.weights,pairs[0].direction)),
                            pairs[0].original.library)
    tiny_pair=d.RetainedPair(tiny_leaf,pairs[0].representative,tiny,pairs[0].direction,'declared-tiny-B2-control')
    amplified=embedded.port.single.context(((Q(10**20),0,0),(0,Q(1-10**20),0),(0,0,0)))
    tiny_scope=d.Scope((amplified,),entry='declared-regular-B2-frame')
    difference=tuple(x-y for x,y in zip(tiny_leaf.kernel(amplified),tiny_pair.representative.kernel(amplified)))
    check('tiny_coefficient_difference_has_a_large_legal_frame_response',
        d.assess(tiny_pair,local).status==d.SAFE and d.assess(tiny_pair,tiny_scope).status==d.DIFFERENT and
        sum(abs(x) for x in difference)>1,response_difference=[embedded.triple.encode(x) for x in difference],
        scope='primitive B2 chart control, not an available certified upper suffix')
    fast=d.Meter();oracle=d.Meter();rows=[]
    fast_start=time.monotonic()
    certificates={name:d.adaptive_preview(query,fast) for name,query in queries}
    fast_seconds=time.monotonic()-fast_start
    oracle_start=time.monotonic()
    for name,query in queries:
        expected,errors,endpoint=d.exact_preview(query,oracle)
        certificate=certificates[name]
        assert all(lo<=value<=hi for value,(lo,hi) in zip(errors,certificate.error_bounds))
        rows.append(dict(name=name,verdict=certificate.verdict,oracle=expected,bits=certificate.bits,
            certificate=dict(query_digest=certificate.query_digest,bits=certificate.bits,
                verdict=certificate.verdict,error_bounds=[[embedded.triple.encode(a),embedded.triple.encode(b)]
                                                         for a,b in certificate.error_bounds])))
    oracle_seconds=time.monotonic()-oracle_start
    check('bounded_filter_matches_original_TE_for_22_queries',len(rows)==22 and
        all(r['verdict'] is not None and r['verdict']==r['oracle'] for r in rows),queries=rows)
    check('only_the_needed_precision_is_used',fast.exact_retained_responses==0 and
        len({r['bits'] for r in rows})>=2,filter=asdict(fast),oracle=asdict(oracle),
        precision_histogram={str(bits):sum(r['bits']==bits for r in rows) for bits in sorted({r['bits'] for r in rows})},
        filter_seconds=fast_seconds,oracle_seconds=oracle_seconds,
        cost_scope='query evaluation only; excludes input authentication, source construction and exact execution')
    check('published_RR57_records_unchanged',len(actuals())==3,records={name:sha for name,(_,sha) in actuals().items()})
    result=dict(date='2026-10-18',experiment='RR58 scoped replacement without disappearance',groups=groups,
        premise='replacement certificates authorize observations, never deletion',
        input_commit='ee4f9b0fa4e70de7318c6bf0d6504d6360c4c714',free_core_commit='9efc241d38e5ca2cd07f425b747bfb5d67ea0235',
        full_RR57_128_family_reenumerated=False,full_baseline_252_rerun=False,
        seconds=round(time.monotonic()-started,3))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/'result.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,groups=len(groups),queries=len(rows),
        bits={str(b):sum(r['bits']==b for r in rows) for b in sorted({r['bits'] for r in rows})},
        exact_filter_reads=fast.exact_retained_responses,exact_oracle_reads=oracle.exact_retained_responses,
        filter_seconds=fast_seconds,oracle_seconds=oracle_seconds)),flush=True)
    return result


if __name__=='__main__':run()
