"""Keep / erase / restore a difference produced by the existing SGD tangent.

No new learning rule. Interventions affect the diagnostic tangent only.
Finite perturbations of actual networks independently check its derivative.
Run: PYTHONPATH=src python examples/xnor_retained_difference.py
"""
import json
import math
from copy import deepcopy
from pathlib import Path
import hashlib

from threeplusone import (
    ThreePlusOneMLP, centered_singleton_seed, add_transverse_vector_seed,
    transverse_residual, xnor,
)
from threeplusone.transverse import epoch_transverse_matrix


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def mv(a, x):
    return [dot(row, x) for row in a]


def epoch(net):
    for x, target in xnor():
        net.train_one(x, target)


def radial(net):
    return [z.real for z in transverse_residual(net)]


def read(r, v):
    return dot(r, v) / dot(r, r)


def inject(net, v, amount):
    # Equal-pair antisymmetric perturbation: Im Z changes by amount*v.
    work = deepcopy(net)
    for unit, coefficient in ((1, 1/math.sqrt(2)), (2, -1/math.sqrt(2))):
        work.output_w[unit+1] += amount*coefficient*v[0]
        for j in range(3):
            work.hidden_w[unit][j] += amount*coefficient*v[j+1]
    return work


def finite_response(base, vector, next_radius, amount):
    plus, minus = inject(base, vector, amount), inject(base, vector, -amount)
    r = radial(base)
    initial = [read(r, [z.imag for z in transverse_residual(n)])
               for n in (plus, minus)]
    epoch(plus)
    epoch(minus)
    outputs = [read(next_radius, [z.imag for z in transverse_residual(n)])
               for n in (plus, minus)]
    return {
        "initial_central_derivative": (initial[0]-initial[1])/(2*amount),
        "next_central_derivative": (outputs[0]-outputs[1])/(2*amount),
    }


def run():
    base = ThreePlusOneMLP(epsilon=1, seed_pattern=centered_singleton_seed(4))
    add_transverse_vector_seed(base, direction=(1, 0, 0, 0), amplitude=.1, phase=0)
    for _ in range(728):
        epoch(base)
    r0 = radial(base)
    j0 = epoch_transverse_matrix(base, xnor(), representative_unit=1)
    transported = mv(j0, r0)
    epoch(base)
    r1 = radial(base)
    y1 = read(r1, transported)
    erased = [y1*x for x in r1]
    hidden = [a-b for a, b in zip(transported, erased)]
    restored = [a+b for a, b in zip(erased, hidden)]
    j1 = epoch_transverse_matrix(base, xnor(), representative_unit=1)
    next_base = deepcopy(base)
    epoch(next_base)
    r2 = radial(next_base)
    cases = {"keep": transported, "erase": erased, "restore": restored}
    tangent = {name: {"present": read(r1, v), "next": read(r2, mv(j1, v))}
               for name, v in cases.items()}
    returned = read(r2, mv(j1, hidden))
    finite = []
    for amount in (1e-2, 1e-3, 1e-4):
        rows = {name: finite_response(base, v, r2, amount)
                for name, v in cases.items()}
        gap = rows["keep"]["next_central_derivative"] - rows["erase"]["next_central_derivative"]
        finite.append({"amplitude": amount, "cases": rows,
                       "keep_minus_erase": gap, "error_vs_tangent_return": gap-returned})
    assert abs(read(r1, hidden)) < 1e-14
    assert max(abs(tangent[n]["present"]-y1) for n in cases) < 1e-14
    assert abs(tangent["keep"]["next"]-tangent["erase"]["next"]-returned) < 1e-14
    assert returned > 1e-6
    assert abs(returned-2.869405956915665e-6) < 5e-12
    assert abs(tangent["keep"]["next"]-tangent["restore"]["next"]) < 1e-14
    assert abs(finite[-1]["error_vs_tangent_return"]) < 2e-9
    assert abs(finite[-1]["error_vs_tangent_return"]) < abs(finite[0]["error_vs_tangent_return"])
    root = Path(__file__).resolve().parents[1]
    names = ("src/threeplusone/core.py", "src/threeplusone/transverse.py",
             "src/threeplusone/datasets.py", "examples/xnor_retained_difference.py")
    return {
        "base_commit": "508a113aeb13c2bf94cee8002992aeade2e4622c",
        "scope": "ordered XNOR; epochs 728->729->730; equal-pair antisymmetric tangent; supplied base orbit",
        "arithmetic": "binary64 diagnostic, not a new interval certificate",
        "input_including_targets": xnor(),
        "hidden_vector_at_729": hidden,
        "hidden_present_readout": read(r1, hidden),
        "hidden_return_at_730": returned,
        "tangent_cases": tangent,
        "nonlinear_finite_checks": finite,
        "checks": "PASS",
        "source_sha256": {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
