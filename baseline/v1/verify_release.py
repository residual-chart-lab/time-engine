"""Verify frozen RR54 inputs and RR55 editorial release without running solvers."""
from pathlib import Path
from fractions import Fraction
import argparse
import ast
import hashlib
import json
import re


ROOT = Path(__file__).resolve().parent
RUNTIME_NAME = '2026-10-16__chatgpt__three-flower-upper-constraint-v001'


def read_json(path):
    return json.loads(path.read_bytes().decode('utf-8'))


def integer(text):
    negative = text.startswith('-')
    digits = text[1:] if negative else text
    if not digits or any(c not in '0123456789' for c in digits):
        raise ValueError('invalid exact integer')
    value = 0
    for offset in range(0, len(digits), 1000):
        chunk = digits[offset:offset + 1000]
        value = value * 10 ** len(chunk) + int(chunk)
    return -value if negative else value


def rational(value):
    pieces = str(value).split('/')
    if len(pieces) == 1:
        return Fraction(integer(pieces[0]))
    if len(pieces) == 2:
        return Fraction(integer(pieces[0]), integer(pieces[1]))
    raise ValueError('invalid exact fraction')


def contained(root, relative):
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError('manifest path escaped its directory')
    return candidate


def check(ok, message):
    if not ok:
        raise ValueError(message)


def verify(runtime):
    manifest = read_json(ROOT / 'frozen-runtime-manifest.json')
    check(manifest['commit'] == 'a67915066973a6bd5bf2c3d2fe06b0cede838b76', 'wrong frozen commit')
    files = manifest['files']
    check(len(files) == 118, 'wrong frozen file count')
    raw = {}
    for name, expected in files.items():
        content = contained(runtime, name).read_bytes()
        check(len(content) == expected['bytes'], 'size mismatch: ' + name)
        check(hashlib.sha256(content).hexdigest() == expected['sha256'], 'SHA-256 mismatch: ' + name)
        git = hashlib.sha1(b'blob ' + str(len(content)).encode('ascii') + b'\0' + content).hexdigest()
        check(git == expected['git_blob_sha'], 'Git blob mismatch: ' + name)
        raw[name] = content

    result = read_json(runtime / 'three_flower_constraint_result.json')
    checks = result['checks']
    check(result['passed'] is True and result['groups'] == len(checks) == 8, 'wrong saved main checks')
    check(all(c['passed'] is True for c in checks), 'saved main check failed')
    source_hashes = result['source_sha256']
    check(len(source_hashes) == 45, 'wrong model source count')
    for name, expected in source_hashes.items():
        check(hashlib.sha256(raw[name]).hexdigest() == expected, 'saved model source mismatch: ' + name)
    firsts = {tuple(v) for v in checks[0]['first_choices']}
    check(len(firsts) == 4 and checks[0]['second_prefixes'] == 16
          and checks[0]['three_flower_previews'] == 64, 'wrong finite family counts')
    selected = checks[1]
    check({tuple(v) for v in selected['first_choices_before']} == firsts, 'first choice set changed')
    check(selected['first_choices_after'] == [['first', 0]] and len(selected['admissible_paths']) == 1,
          'wrong shared-future selection')
    alternatives = selected['per_first']
    check(len(alternatives) == 4 and all(v['continuations_checked'] == 16 for v in alternatives),
          'later continuations were not exhausted in the saved result')
    check({tuple(v['first']) for v in alternatives} == firsts, 'missing first choice comparison')
    excluded = [rational(v['best_terminal_error']) for v in alternatives
                if not v['has_admissible_continuation']]
    epsilon = Fraction(1, 10 ** 12)
    minimum_error = min(excluded)
    check(len(excluded) == 3 and minimum_error > epsilon * 10 ** 6, 'wrong rejection margin')
    check(minimum_error == rational(checks[2]['minimum_error_among_excluded_first_choices']),
          'saved rejection margins disagree')
    check(minimum_error / epsilon == rational(checks[2]['minimum_error_to_tolerance_ratio']),
          'saved error ratio disagrees')
    upper = checks[3]
    errors = [rational(v) for v in upper['errors']]
    check(len(errors) == 3 and errors[0] > epsilon and errors[1] > epsilon
          and errors[2] < epsilon / 2, 'upper prefix margins disagree')
    check(upper['output_level'] == 4 and rational(upper['tolerance']) == epsilon, 'wrong upper scale or tolerance')
    check([rational(v) for v in upper['fixed_result']] == [-1, 0, 0, 0], 'wrong fixed result')
    check(upper['actual_upper_endpoint'] != upper['fixed_result'], 'actual endpoint was clamped')
    alternate = checks[4]
    check(alternate['first_allowed'] == [['first', 0]]
          and alternate['alternate_allowed'] == [['second', 1]]
          and alternate['result_and_tolerance_unchanged'] is True, 'future-frame control disagrees')
    check({tuple(v) for v in checks[5]['first_choices_with_unbound_terminal_frame']} == firsts,
          'unbound-frame control disagrees')
    ledger = checks[6]
    check(ledger['actual_source_productions'] == ledger['actual_same_scale_flowers'] == 3
          and ledger['additional_upper_enclosure'] == 1
          and ledger['candidate_previews_are_not_actual_occurrences'] is True, 'wrong actual occurrence scope')
    check(checks[7]['terminal_frame_independently_generated'] is False
          and checks[7]['arbitrary_future_uniqueness_proved'] is False, 'fixture scope was lost')

    validation = read_json(runtime / 'RR54-validation.json')
    driver = read_json(runtime / 'RR54-driver-validation.json')
    check(validation['groups'] == driver['groups'] == 8
          and validation['related_tests'] == driver['tests'] == 252
          and driver['passed'] is True and validation['execution']['exit_code'] == 0,
          'wrong inherited numerical validation')
    check(validation['result_byte_identical'] is True
          and validation['result_sha256'] == hashlib.sha256(raw['three_flower_constraint_result.json']).hexdigest(),
          'wrong saved numerical result equality')
    check(validation['exact_macro_occurrences'] == driver['exact_macro_records'] == 2,
          'wrong actual record count')
    for example in driver['examples']:
        content = raw[example['path']]
        check(len(content) == example['bytes']
              and hashlib.sha256(content).hexdigest() == example['sha256']
              == validation['example_sha256'][example['path']], 'actual record bytes changed')
        check(read_json(runtime / example['path'])['schema'] == 'time-engine-three-flower-upper-occurrence-v1',
              'wrong actual record schema')

    methods = {}
    for name in files:
        if name.startswith('test_') and name.endswith('.py') and '/' not in name:
            tree = ast.parse(raw[name].decode('utf-8'))
            methods[name] = {node.name for node in ast.walk(tree)
                             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and node.name.startswith('test_')}
    check(sum(map(len, methods.values())) == 252, 'declared test inventory changed')
    evidence = (ROOT / 'EVIDENCE-MAP.md').read_text(encoding='utf-8')
    referenced_methods = re.findall(r'`(?:test_[A-Za-z0-9_]+\.py::)?(test_[A-Za-z0-9_]+)`', evidence)
    available = set().union(*methods.values())
    check(bool(referenced_methods) and all(name in available for name in referenced_methods),
          'a referenced evidence method is missing')
    explicit_methods = re.findall(r'`(test_[A-Za-z0-9_]+\.py)::(test_[A-Za-z0-9_]+)`', evidence)
    check(all(method in methods.get(name, set()) for name, method in explicit_methods),
          'an evidence method is assigned to the wrong file')
    for name in re.findall(r'`([A-Za-z0-9_-]+(?:_result)?\.(?:py|json))`', evidence):
        check(name in files, 'a cited runtime file is missing: ' + name)

    provenance = read_json(ROOT / 'RR55-PROVENANCE.json')
    check(provenance['model_runtime_modified'] is False
          and provenance['full_numerical_rerun_performed'] is False, 'wrong editorial release type')
    for name, expected in provenance['document_sha256'].items():
        check(hashlib.sha256(contained(ROOT, name).read_bytes()).hexdigest() == expected,
              'release document changed: ' + name)
    for name in ('note55-consolidated.md', 'MODEL-SPEC.md', 'README.md', 'EVIDENCE-MAP.md'):
        text = (ROOT / name).read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^\s)]+)\)', text):
            if not re.match(r'[a-z]+://', target):
                check(contained(ROOT, target).is_file(), 'relative document link missing: ' + target)
    facts = dict(
        schema='time-engine-three-flower-v1-editorial-verification',
        passed=True, date='2026-10-16',
        frozen_commit=manifest['commit'], frozen_files_verified=118,
        model_source_files_unchanged=45,
        result_sha256=hashlib.sha256(raw['three_flower_constraint_result.json']).hexdigest(),
        saved_main_groups=8, saved_main_groups_passed=True,
        saved_related_tests=252, saved_related_tests_passed=True,
        saved_independent_result_byte_identical=True,
        saved_exact_macro_records=2, exact_macro_records_bytes_verified=2,
        saved_numerical_execution_seconds=validation['execution']['seconds'],
        finite_paths=64, first_choices_before=4, first_choices_after=1,
        continuations_checked_per_first=16,
        minimum_rejected_error_approx=float(minimum_error),
        fixed_tolerance='1/1000000000000',
        upper_prefix_errors_approx=[float(v) for v in errors],
        alternate_first_choice=['second', 1], unbound_frame_first_choices=4,
        same_scale_flowers=3, additional_upper_enclosure=1,
        evidence_method_references_verified=len(referenced_methods),
        release_document_hashes_verified=len(provenance['document_sha256']),
        full_numerical_rerun_performed=False,
        exact_record_reexecution_performed=False,
        audit_source='user reported Astra acceptance; audit text not supplied',
    )
    saved = ROOT / 'RR55-validation.json'
    if saved.exists():
        check(read_json(saved) == facts, 'saved RR55 editorial verification differs')
    return facts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path)
    args = parser.parse_args()
    runtime = args.runtime
    if runtime is None:
        runtime = ROOT / 'runtime'
        if not runtime.is_dir():
            runtime = ROOT.parent / RUNTIME_NAME
    print(json.dumps(verify(runtime.resolve()), ensure_ascii=True, indent=2))
