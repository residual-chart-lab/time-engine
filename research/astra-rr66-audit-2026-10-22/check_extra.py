"""Independent RR66 audit probes. Does not change runtime or TE operations."""
from pathlib import Path
import sys, json
from fractions import Fraction as Q

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'integrations/inquiry'))
import adaptive_resolution as a
import adaptive_session as live
import rr66_study as study


def run():
    entry = a.register()
    mixed = study.scope(entry, 'mixed', '1/1024')
    main = study.scope(entry, 'main', '1/1024')
    same = 0
    separated = 0
    for word in a.m.WORDS:
        A, B = a.port_weights(entry.base, word)
        original = a.m.build(entry.base, mixed, 1, word).polynomials
        next_request = a.m.build(entry.base, main, 1, word).polynomials
        for s, t in ((Q(1,4096),Q(1,8192)), (Q(-1,4096),Q(1,8192)),
                     (Q(0),Q(1,4096)), (Q(1,4096),Q(0)),
                     (Q(1,8192),Q(-1,8192)), (Q(0),Q(0))):
            other_s, other_t = B*t/A, A*s/B
            assert s*t == other_s*other_t
            assert A*s+B*t == A*other_s+B*other_t
            left, right = {'s':s,'t':t}, {'s':other_s,'t':other_t}
            assert all(p.exact(left) == p.exact(right) for p in original.values())
            same += 1
            separated += any(p.exact(left) != p.exact(right) for p in next_request.values())

    ready = live.resolve(live.choose(live.start(entry, mixed), 1, 'HHHSUT'))
    meter = a.fn.Meter()
    fine = live.resolve(live.choose(live.revise(ready, main), 1, 'HHHSUT'), meter)
    cache = dict(ready.cache)
    cache['s'] = dict(fine.cache)['s']
    A, B = a.port_weights(entry.base, 'HHHSUT')
    restored_t = (cache['port-HHHSUT'][1] - A*cache['s'][1]) / B
    actual_t = dict(fine.cache)['t'][1]
    assert restored_t == actual_t
    current_derive = a.derive_cached(entry, 't', cache)
    cache['t'] = (entry.base.vault.reference('t').digest, restored_t)
    a.validate_cache(entry, cache)
    plan = a.compile(entry, main, 1, 'HHHSUT')
    reused_meter = a.fn.Meter()
    reused, _, new, derived, _ = a.resolve(entry, main, a.Policy(), plan, tuple(cache.items()), reused_meter)
    assert reused == fine.prepared.action
    assert not new and reused_meter.exact_reads == 0
    return {
        'audited_commit': 'cb4d505dd1c93bd1b6194593a1225500f0e304e4',
        'same_product_and_port_preserve_all_13_original_polynomials': same,
        'pairs_distinguished_by_the_main_request': separated,
        'read_redundancy': {
            'starting_cache': sorted(dict(ready.cache)),
            'current_new_keys': live.history(fine)[-1]['new_keys'],
            'current_exact_reads': meter.exact_reads,
            'after_reading_s_t_is_unique': True,
            'formula': 't = (port-HHHSUT - 7*s) / 8',
            'existing_derive_cached_returns_none': current_derive is None,
            'derived_t_matches_original_commitment': True,
            'same_action_from_derived_t': True,
            'extra_exact_reads_with_derived_cache': reused_meter.exact_reads,
        },
    }


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False, indent=2))
