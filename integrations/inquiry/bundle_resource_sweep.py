"""A labelled follow-up diagnostic, separate from the fixed primary grid."""
from pathlib import Path
from fractions import Fraction as Q
import json
import bundle_demand as b


def run(entry=None):
    spec=json.loads(Path(__file__).with_name('RR64-resource-sweep-inputs.json').read_bytes())
    entry=b.register(spec['mode']) if entry is None else entry
    rows=[];previous=set();meter=b.fn.Meter()
    for maximum in spec['resource_maxima']:
        allowed=[]
        for v in spec['first_controls']:
            for word in spec['words']:
                scope=b.Scope(entry.digest,Q(spec['future_x']),Q(v),word,Q(spec['strength']),
                    (Q(spec['resource_minimum']),Q(maximum)),b.EXISTS)
                recipe=b.build(entry,scope);assessment=b.assess(entry,scope,recipe)
                resolved=b.resolve(entry,scope,recipe,assessment,meter)
                if resolved.feasible:allowed.append((v,word))
        current=set(allowed)
        if not previous<=current:raise AssertionError('relaxing the same resource bound lost an admitted current choice')
        rows.append(dict(maximum=maximum,allowed=allowed,count=len(allowed)))
        previous=current
    return dict(role=spec['role'],rows=rows,exact_residual_reads=meter.exact_reads,
                completed_future_paths=0)
