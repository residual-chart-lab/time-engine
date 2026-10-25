"""Separate current readout preservation from a requested continuation's action.

A diagnostic shadow sets declared retained coordinates to zero. It never edits
an issued entry, creates a substitute history, or grants execution authority.
"""
from fractions import Fraction as Q
import three_flower_synthesis as n
from three_flower_synthesis import a, fn, d

SCHEMA = 'time-engine-preservation-targets-v1'


def _current_endpoint(entry, v, word, coordinates):
    base = entry.base
    fixed = base.first.flight.pair.representative.weights
    letters = {
        'H': base.head.leaves(),
        'S': (d.AffineLetter(tuple(x + coordinates['s']*z for x, z in zip(fixed, base.first.axis)), base.library),),
        'U': (d.AffineLetter(tuple(x + coordinates['t']*z for x, z in zip(fixed, base.direction_U)), base.library),),
        'T': (d.AffineLetter(tuple(x + Q(v)*z for x, z in zip(fixed, base.first.axis)), base.library),),
    }
    endpoint = base.engine.upper.live.accumulated
    context = base.engine.upper.live.context
    for k in word:
        for letter in letters[k]:
            endpoint = d.qmul(letter.kernel(context), endpoint)
    return tuple(endpoint)


def _requested(entry, scope, plan, coordinates):
    if plan.status != 'AVAILABLE':
        return plan.status, None
    islands = {key: poly.exact(coordinates)[0] for key, poly in plan.recipe.polynomials.items()}
    action = n.assess(entry, scope, plan, n.Values(plan.recipe, islands))
    if action.status != 'ADMISSIBLE':
        return action.status, None
    # These are comparison data, not an issued Action or an execution state.
    return action.status, (action.T, action.R2, action.R3)


def _relation(left, right):
    ls, la = left
    rs, ra = right
    if ls == rs == 'EMPTY':
        return 'SAME_EMPTY'
    if {ls, rs} == {'ADMISSIBLE', 'EMPTY'}:
        return 'DIFFERENT_EXISTENCE'
    if ls == rs == 'ADMISSIBLE':
        return 'SAME_NEW_ACTION' if la == ra else 'DIFFERENT_NEW_ACTION'
    return 'UNDETERMINED'


def compare(entry, scope, v, u, word, omitted):
    """One exact comparison in the existing E1/RR69 family, before new motion.

    P_current is the first word's endpoint at its actual inherited context.
    P_requested is this choice's admissible new (T,R2,R3), or the empty set,
    under the complete supplied three-flower requirement and original guards.
    Neither observation is the entire retained state or every possible future.
    """
    a.verify_entry(entry)
    if type(omitted) not in (tuple, list) or any(type(k) is not str for k in omitted):
        raise ValueError('declare distinct retained coordinates s and/or t')
    omitted = tuple(omitted)
    if not omitted or len(set(omitted)) != len(omitted) or not set(omitted) <= {'s', 't'}:
        raise ValueError('declare distinct retained coordinates s and/or t')
    omitted = tuple(sorted(omitted))
    # compile verifies the original finite scope, current controls and word.
    plan = n.compile(entry, scope, v, u, word)
    n.verify_plan(entry, scope, plan)
    meter = fn.Meter()
    original = {key: entry.base.vault.exact(key, meter) for key in ('s', 't')}
    projected = {key: Q(0) if key in omitted else value for key, value in original.items()}
    current = _current_endpoint(entry, v, word, original)
    shadow_current = _current_endpoint(entry, v, word, projected)
    full = _requested(entry, scope, plan, original)
    shadow = _requested(entry, scope, plan, projected)
    return dict(
        schema=SCHEMA,
        entry=entry.digest,
        scope=scope.digest,
        choice=dict(v=str(Q(v)), u=str(Q(u)), word=word),
        projection=dict(omitted=list(omitted), rule='set these coordinates to zero in a diagnostic shadow'),
        current=dict(observation='first-word endpoint at the actual inherited context',
                     original=list(map(str, current)), projected=list(map(str, shadow_current)),
                     equal=current == shadow_current, cell_certification_claimed=False),
        requested=dict(observation='new T/R2/R3 or empty set for this fixed choice and three-flower requirement',
                       original_status=full[0], projected_status=shadow[0], relation=_relation(full, shadow),
                       original_new_action_digest=None if full[1] is None else a.fingerprint(full[1]),
                       projected_new_action_digest=None if shadow[1] is None else a.fingerprint(shadow[1])),
        exact_source_reads=meter.exact_reads,
        hypothetical_projection_only=True,
        erasure_authorized=False,
        execution_authorized=False,
    )
