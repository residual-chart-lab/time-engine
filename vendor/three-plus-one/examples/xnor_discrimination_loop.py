"""Input-resolved assay of the existing eight-contact-loop diagnostic.

Frozen independent probes do not train or alter the continuing base orbit.
All interventions act on the diagnostic equal-pair tangent, not the SGD rule.
The primary readout uses one fixed phase projection for all single contacts.
Moving-phase change and antisymmetric hidden activation are secondary readouts.
Network output cancels at first order in this symmetry sector.
"""
import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path

from xnor_retained_difference import dot, epoch, inject, mv, radial, read
from threeplusone import ThreePlusOneMLP, centered_singleton_seed, add_transverse_vector_seed, transverse_residual, xnor
from threeplusone.transverse import epoch_transverse_matrix, sample_transverse_matrix

READOUTS = ("phase_change", "fixed_phase_change", "hidden_activation")


def norm(v):
    return math.sqrt(dot(v, v))


def centered(v):
    mean = sum(v) / len(v)
    return [x - mean for x in v]


def profile_comparison(reference, candidate):
    """Remove common offset and best common gain, with no per-input fitting."""
    a, b = centered(reference), centered(candidate)
    na, nb = norm(a), norm(b)
    if min(na, nb) < 1e-14:
        return {"resolved": False, "reason": "near-zero centered profile"}
    gain = dot(a, b) / dot(b, b)
    residual = [x - gain*y for x, y in zip(a, b)]
    return {
        "resolved": True,
        "reference_centered_norm": na,
        "candidate_centered_norm": nb,
        "best_gain_candidate_to_reference": gain,
        "affine_residual_relative": norm(residual)/na,
        "normalized_profile_distance": norm([x/na-y/nb for x, y in zip(a, b)]),
        "normalized_pair_gaps_reference": [(a[i]-a[j])/na for i in range(4) for j in range(i+1, 4)],
        "normalized_pair_gaps_candidate": [(b[i]-b[j])/nb for i in range(4) for j in range(i+1, 4)],
    }


def probes(base, v):
    phase_changes, fixed_phase_changes, activation = [], [], []
    for x, target in xnor():
        k = sample_transverse_matrix(base, x, target, representative_unit=1)
        after = deepcopy(base)
        after.train_one(x, target)
        phase_changes.append(read(radial(after), mv(k, v)) - read(radial(base), v))
        fixed_phase_changes.append(read(radial(base), [a-b for a,b in zip(mv(k,v),v)]))
        h, _ = base._forward(x)
        activation.append(h[1]*(1-h[1])*dot([1.0, *x], v[1:]))
    return {"phase_change": phase_changes, "fixed_phase_change": fixed_phase_changes, "hidden_activation": activation}


def finite_probes(base, v, amount):
    phase_changes, fixed_phase_changes, activation, output = [], [], [], []
    for x, target in xnor():
        after = deepcopy(base)
        after.train_one(x, target)
        pair = [inject(base, v, s*amount) for s in (1, -1)]
        initial = [read(radial(base), [z.imag for z in transverse_residual(n)]) for n in pair]
        contrast = []
        predicted = []
        response = []
        fixed_response = []
        for n, start in zip(pair, initial):
            h, y = n._forward(x)
            contrast.append((h[1]-h[2])/math.sqrt(2))
            predicted.append(y)
            n.train_one(x, target)
            response.append(read(radial(after), [z.imag for z in transverse_residual(n)])-start)
            fixed_response.append(read(radial(base), [z.imag for z in transverse_residual(n)])-start)
        phase_changes.append((response[0]-response[1])/(2*amount))
        fixed_phase_changes.append((fixed_response[0]-fixed_response[1])/(2*amount))
        activation.append((contrast[0]-contrast[1])/(2*amount))
        output.append((predicted[0]-predicted[1])/(2*amount))
    return {"phase_change": phase_changes, "fixed_phase_change": fixed_phase_changes, "hidden_activation": activation, "network_output": output}


def run():
    base = ThreePlusOneMLP(epsilon=1, seed_pattern=centered_singleton_seed(4))
    add_transverse_vector_seed(base, direction=(1, 0, 0, 0), amplitude=.1, phase=0)
    for _ in range(728):
        epoch(base)
    full, erased_y = radial(base), 1.0
    records = []
    for step in range(9):
        r = radial(base)
        y = read(r, full)
        erased = [y*x for x in r]
        hidden = [a-b for a, b in zip(full, erased)]
        cases = {
            "keep": full,
            "erase_same_phase": erased,
            "restore": [a+b for a, b in zip(erased, hidden)],
            "flip_hidden_same_norm_phase": [a-b for a, b in zip(erased, hidden)],
            "erase_matched_state_norm": [x*norm(full)/norm(erased) for x in erased],
            "gain_only_null": [1.7*x for x in erased],
            "erase_each_epoch": [erased_y*x for x in r],
        }
        responses = {name: probes(base, v) for name, v in cases.items()}
        checks = []
        for amount in (1e-2, 1e-3, 1e-4):
            finite = {name: finite_probes(base, cases[name], amount) for name in
                      ("keep", "erase_same_phase", "restore", "flip_hidden_same_norm_phase")}
            errors = {key: max(abs(a-b) for name in finite
                              for a, b in zip(finite[name][key], responses[name][key]))
                      for key in READOUTS}
            finite_gap = {key: [a-b for a,b in zip(finite["keep"][key], finite["erase_same_phase"][key])]
                          for key in READOUTS}
            checks.append({"amplitude": amount, "max_derivative_errors": errors,
                           "keep_minus_erase": finite_gap,
                           "phase_profile_comparison": profile_comparison(finite["keep"]["phase_change"], finite["erase_same_phase"]["phase_change"]),
                           "fixed_phase_profile_comparison": profile_comparison(finite["keep"]["fixed_phase_change"], finite["erase_same_phase"]["fixed_phase_change"]),
                           "max_network_output_derivative": max(abs(z) for name in finite for z in finite[name]["network_output"])})
        comparisons = {key: {name: profile_comparison(responses["keep"][key], value[key])
                            for name, value in responses.items() if name != "keep"}
                       for key in READOUTS}
        nulls = {key: profile_comparison(responses["gain_only_null"][key], responses["erase_same_phase"][key])
                 for key in READOUTS}
        assert abs(read(r, hidden)) < 1e-13
        assert abs(norm(cases["flip_hidden_same_norm_phase"])-norm(full)) < 1e-13
        assert abs(norm(cases["erase_matched_state_norm"])-norm(full)) < 1e-13
        assert abs(read(r, cases["flip_hidden_same_norm_phase"])-y) < 1e-13
        assert all(c["affine_residual_relative"] < 1e-9 for c in nulls.values())
        assert all(comparisons[key]["restore"]["affine_residual_relative"] < 1e-9 for key in comparisons)
        assert max(checks[1]["max_derivative_errors"].values()) < 2e-8
        records.append({"step": step, "epoch": 728+step, "present_phase": y,
                        "hidden_norm": norm(hidden), "state_norms": {n: norm(v) for n,v in cases.items()},
                        "responses": responses, "comparisons": comparisons, "gain_null_checks": nulls,
                        "finite_checks": checks})
        if step < 8:
            j = epoch_transverse_matrix(base, xnor(), representative_unit=1)
            jr = mv(j, r)
            full = mv(j, full)
            epoch(base)
            erased_y *= read(radial(base), jr)
    # Protect this published representative, not every possible learning orbit.
    # A vanished effect must not silently retain the PASS label.
    initial_effect = records[0]["comparisons"]["fixed_phase_change"]["erase_same_phase"]["affine_residual_relative"]
    final_effect = records[-1]["comparisons"]["fixed_phase_change"]["erase_same_phase"]["affine_residual_relative"]
    activation_effect = records[-1]["comparisons"]["hidden_activation"]["erase_same_phase"]["affine_residual_relative"]
    assert initial_effect < 1e-9, "zero-hidden baseline changed"
    assert .03 < final_effect < .09, "representative nonuniform contact effect disappeared or changed materially"
    assert .01 < activation_effect < .04, "target-free internal effect disappeared or changed materially"
    root = Path(__file__).resolve().parents[1]
    files = ["src/threeplusone/core.py", "src/threeplusone/transverse.py", "src/threeplusone/datasets.py",
             "examples/xnor_retained_difference.py", "examples/xnor_discrimination_loop.py"]
    return {"base_commit": "de4ee70002b2b049f77b728cf8b46accff0686c6",
            "scope": "fixed ordered XNOR orbit, epoch 728 through 736; local equal-pair antisymmetric tangent",
            "contacts_in_order": xnor(), "pair_gap_order": [[i,j] for i in range(4) for j in range(i+1,4)],
            "primary_readout": "fixed-phase projected tangent change ell_q((K_x-I)v), same ell_q for all independent labelled contacts",
            "secondary_readout": "moving-phase contact change and target-free hidden activation contrast; external network output is zero to first order",
            "controls": "same-phase erase/restore; hidden sign flip with same norm and phase; norm-matched erase; pure gain null; erase each epoch",
            "arithmetic": "binary64 diagnostic, not an interval proof", "checks": "PASS", "records": records,
            "representative_effect_guard": {"fixed_phase_relative_residual": final_effect,
                                             "hidden_activation_relative_residual": activation_effect},
            "source_sha256": {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    result = run()
    target = Path(__file__).resolve().parents[1]/"results"/"xnor_discrimination_loop.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for row in result["records"]:
        print(row["step"], "hidden", row["hidden_norm"], "phase affine residual",
              row["comparisons"]["phase_change"]["erase_same_phase"]["affine_residual_relative"],
              "activation affine residual", row["comparisons"]["hidden_activation"]["erase_same_phase"]["affine_residual_relative"])
