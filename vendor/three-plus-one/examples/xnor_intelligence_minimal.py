"""A working 3+1 intelligence minimal model: contact, carry, change discrimination.

Response geometry is measured, not injected into training. No new learning rule.
One visible phase plus three hidden tangent directions; the 17-weight base stays.
"""
import hashlib
import json
from pathlib import Path

from xnor_retained_difference import dot, mv, radial, read
from xnor_discrimination_loop import norm, centered, profile_comparison
from threeplusone import ThreePlusOneMLP, centered_singleton_seed, add_transverse_vector_seed, xnor
from threeplusone.transverse import sample_transverse_matrix, epoch_transverse_matrix


def response_matrix(base, samples):
    r = radial(base)
    denominator = dot(r, r)
    rows = []
    for x, target in samples:
        k = sample_transverse_matrix(base, x, target, representative_unit=1)
        # ell_q(K-I), with the same fixed ell_q for every input.
        rows.append([sum(r[i]*(k[i][j]-(1.0 if i == j else 0.0))
                         for i in range(4))/denominator for j in range(4)])
    return rows


def blind_hidden_direction(r, a, visible_response):
    """Construct a diagnostic counterexample, not an added memory mechanism.

Find h with r.h=0 and centered A h parallel to centered A(yR).
In this 4-contact assay, at most three independent row constraints occur.
"""
    mean_row = [sum(row[j] for row in a)/4 for j in range(4)]
    pa = [[row[j]-mean_row[j] for j in range(4)] for row in a]
    b = centered(visible_response)
    b2 = dot(b, b)
    projected_column = [sum(b[i]*pa[i][j] for i in range(4))/b2 for j in range(4)]
    constraints = [r] + [[pa[i][j]-b[i]*projected_column[j] for j in range(4)] for i in range(4)]
    basis = []
    scale = max(norm(row) for row in constraints[1:])
    for idx, row in enumerate(constraints):
        v = row[:]
        # Reorthogonalize to suppress cancellation in near-dependent rows.
        for _ in range(2):
            for u in basis:
                c = dot(v, u)
                v = [z-c*w for z,w in zip(v,u)]
        if norm(v) > (norm(r)*1e-12 if idx == 0 else max(scale, 1e-30)*1e-9):
            basis.append([z/norm(v) for z in v])
    candidates = []
    for j in range(4):
        v = [float(i == j) for i in range(4)]
        for _ in range(2):
            for u in basis:
                c = dot(v,u)
                v = [z-c*w for z,w in zip(v,u)]
        candidates.append(v)
    v = max(candidates, key=norm)
    if norm(v) < 1e-8:
        raise ArithmeticError("blind diagnostic direction unresolved")
    return [z/norm(v) for z in v]


def assay(base, full, samples, step):
    r = radial(base)
    y = read(r, full)
    visible = [y*z for z in r]
    h = [z-w for z,w in zip(full, visible)]
    a = response_matrix(base, samples)
    visible_response, hidden_response = mv(a, visible), mv(a, h)
    keep_response = mv(a, full)
    b, d = centered(visible_response), centered(hidden_response)
    gain_from_hidden = dot(b,d)/dot(b,b)
    new_direction = [z-gain_from_hidden*w for z,w in zip(d,b)]
    total = centered(keep_response)
    expected_residual = norm(new_direction)/norm(total)
    measured = profile_comparison(keep_response, visible_response)["affine_residual_relative"]
    assert abs(expected_residual-measured) < 1e-9
    assert abs(read(r,h)) < 1e-12
    blind = blind_hidden_direction(r, a, visible_response)
    blind = [z*norm(h) for z in blind]
    blind_full = [z+w for z,w in zip(visible,blind)]
    blind_effect = profile_comparison(mv(a,blind_full),visible_response)["affine_residual_relative"]
    assert blind_effect < 1e-8
    assert abs(read(r,blind)) < 1e-12
    return {"step": step, "present_phase": y, "hidden_norm": norm(h),
            "hidden_vector": h, "blind_control_hidden_vector": blind,
            "keep_response": keep_response, "erase_response": visible_response,
            "hidden_response": hidden_response, "new_centered_response_direction": new_direction,
            "shape_change_relative": measured,
            "condition_identity_error": abs(expected_residual-measured),
            "blind_control_hidden_norm": norm(blind), "blind_control_effect": blind_effect}


def course(start, order):
    source = xnor()
    samples = [source[i] for i in order]
    base = ThreePlusOneMLP(epsilon=1, seed_pattern=centered_singleton_seed(4))
    add_transverse_vector_seed(base,direction=(1,0,0,0),amplitude=.1,phase=0)
    for _ in range(start):
        for x,t in samples:
            base.train_one(x,t)
    full = radial(base)
    records = []
    for step in range(9):
        records.append(assay(base, full, samples, step))
        if step < 8:
            j = epoch_transverse_matrix(base,samples,representative_unit=1)
            full = mv(j,full)
            for x,t in samples:
                base.train_one(x,t)
    return {"start_epoch": start, "order": list(order), "contacts": samples,
            "final_shape_change_relative": records[-1]["shape_change_relative"],
            "effect_observed": records[-1]["shape_change_relative"] > 1e-6,
            "records": records}


def run():
    courses = [course(start,order) for start in (100,400,728)
               for order in ((0,1,2,3),(3,2,1,0),(0,2,1,3))]
    canonical = next(c for c in courses if c["start_epoch"] == 728 and c["order"] == [0,1,2,3])
    assert .03 < canonical["final_shape_change_relative"] < .09
    root = Path(__file__).resolve().parents[1]
    files = ["src/threeplusone/core.py","src/threeplusone/transverse.py","src/threeplusone/datasets.py",
             "examples/xnor_retained_difference.py","examples/xnor_discrimination_loop.py",
             "examples/xnor_intelligence_minimal.py", "tests/test_intelligence_minimal.py"]
    return {"source_base_commit":"db99cf56688304a255292df09d394eeefc4254c6",
            "model":"3+1 intelligence minimal model v1",
            "scope":"one visible phase plus three hidden tangent directions, with full base network retained",
            "condition":"component of centered A h perpendicular to centered A(yR) is nonzero",
            "numerics":"binary64 finite diagnostic, not a general minimality proof",
            "blind_control":"constructed same-norm hidden direction; no nonuniform response change in this readout",
            "courses":courses,"checks":"PASS",
            "source_sha256":{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    result = run()
    target = Path(__file__).resolve().parents[1]/"results"/"xnor_intelligence_minimal.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for c in result["courses"]:
        print(c["start_epoch"],c["order"],"shape change",c["final_shape_change_relative"],"observed",c["effect_observed"])
