"""E1 acceptance from frozen records under another isolated Python runtime.

Never registers or trains a source. Exact verification replays remain enabled.
The input manifest describes the 403 files at the first published E1 commit.
"""
from pathlib import Path
from fractions import Fraction as Q
from contextlib import ExitStack
from unittest.mock import patch
import argparse
import hashlib
import json
import platform
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

ENTRY_SHA256 = 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
ENTRY_DIGEST = '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'
INPUT_COMMIT = '1a2e0c9b706055f2ef04fd10380e73807c6e0207'


def check(value, message):
    if not value:
        raise AssertionError(message)


def run(output, external_checkpoint=None, external_sha256=None):
    check(sys.flags.isolated, 'run with python -I to exclude user environment paths')
    manifest = json.loads((HERE / 'E1-PORTABILITY-INPUT.json').read_bytes())
    check(manifest['commit'] == INPUT_COMMIT and len(manifest['files']) == 403, 'expected frozen input manifest')
    for item in manifest['files']:
        raw = (ROOT / item['path']).read_bytes()
        check(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], item['path'])

    import entry_transport as wire
    import three_flower_session as live
    import rr69_study as study

    raw = (HERE / 'E1-entry.record.json').read_bytes()
    checks = ['403_frozen_input_files_match']
    generators = ((wire.a, 'register'), (wire.incremental, 'register'),
                  (wire.adaptive, 'register'), (wire.m, 'register'),
                  (wire.b, 'register'), (wire.prior.previous, 'begin'),
                  (wire.prior.te, 'prepare'))
    mocks = []
    with ExitStack() as stack:
        for module, name in generators:
            mocks.append(stack.enter_context(patch.object(module, name, side_effect=AssertionError('past generator forbidden'))))
        entry = wire.loads(raw, ENTRY_SHA256, ENTRY_DIGEST)
        check(len(entry.base.engine.stock) == 6 and not entry.derived._records(), 'unbound original entry')
        check(wire.dumps(entry) == (raw, ENTRY_SHA256), 'canonical entry roundtrip')
        checks += ['unbound_entry_received', 'entry_bytes_roundtrip']

        registries = (wire.m._ISSUED, wire.adaptive._ISSUED, wire.incremental._ISSUED, wire.a._ISSUED)
        before = tuple(map(len, registries))
        def rejects(data, sha, digest):
            try:
                wire.loads(data, sha, digest)
            except ValueError:
                return
            raise AssertionError('invalid entry accepted')
        rejects(raw, '0' * 64, ENTRY_DIGEST)
        rejects(raw, ENTRY_SHA256, '0' * 64)
        changed = json.loads(raw)
        roots = changed['graph']['nodes'][changed['graph']['root']['ref']]['tuple']
        roots[0], roots[1] = roots[1], roots[0]
        forged = (json.dumps(changed, separators=(',', ':')) + '\n').encode()
        rejects(forged, hashlib.sha256(forged).hexdigest(), ENTRY_DIGEST)
        check(tuple(map(len, registries)) == before, 'failed import left issued authority')
        checks += ['wrong_external_hash_rejected', 'wrong_entry_identity_rejected',
                   'source_history_swap_rejected', 'failed_imports_issue_no_authority']

        def request(e):
            return study.scope(e, 'mixed', ('1/1024', '1/1024'), 'split')
        ready = live.resolve(live.choose(live.start(entry, request(entry)), 1, 0, 'HHHSUT'))[0]
        closed_first = live.advance(ready)
        check(closed_first.phase == 'CLOSED1', 'actual first flower must close')
        prefix, prefix_sha = live.dumps(closed_first)
        new_entry = wire.loads(raw, ENTRY_SHA256, ENTRY_DIGEST)
        resumed = live.loads(prefix, prefix_sha, new_entry, request(new_entry), (Q(1), Q(0), 'HHHSUT'))
        done = live.finish(resumed)
        check(done.phase == 'STOPPED' and done.certified and len(done.engine.stock) == 9, 'three flowers and upper closure')
        completed, completed_sha = live.dumps(done)
        actual = json.loads(completed)
        reference = json.loads((HERE / 'RR69-mixed-connected.record.json').read_bytes())
        check(wire.checkpoint.unpack(actual.pop('graph')) == wire.checkpoint.unpack(reference.pop('graph')), 'exact physical history differs from RR69')
        check(actual == reference, 'scope, action, numbers, observations or commands differ from RR69')
        checks += ['first_flower_checkpoint_replayed', 'three_flowers_and_upper_certified',
                   'exact_full_history_matches_RR69', 'all_non_graph_fields_match_RR69']
        other_entry = wire.loads(raw, ENTRY_SHA256, ENTRY_DIGEST)
        replayed = live.loads(completed, completed_sha, other_entry, request(other_entry), (Q(1), Q(0), 'HHHSUT'))
        check(replayed.certified and replayed.engine == done.engine, 'completed checkpoint replay')
        checks += ['completed_checkpoint_replayed']
        if external_checkpoint is not None:
            check(type(external_sha256) is str and len(external_sha256) == 64, 'external checkpoint needs its independently retained SHA-256')
            external_entry = wire.loads(raw, ENTRY_SHA256, ENTRY_DIGEST)
            transported = live.loads(external_checkpoint.read_bytes(), external_sha256, external_entry,
                                     request(external_entry), (Q(1), Q(0), 'HHHSUT'))
            check(transported.certified and transported.engine == done.engine, 'external runtime checkpoint replay')
            checks += ['other_runtime_checkpoint_replayed']
        for mock in mocks:
            mock.assert_not_called()
        checks += ['seven_past_generators_never_called']

    output.mkdir(parents=True, exist_ok=True)
    (output / 'completed.record.json').write_bytes(completed)
    report = dict(schema='time-engine-e1-runtime-portability-v1', passed=True,
                  input_commit=INPUT_COMMIT, input_files=403,
                  runtime=dict(implementation=platform.python_implementation(), version=platform.python_version(),
                               compiler=platform.python_compiler(), platform=platform.platform(),
                               isolated=bool(sys.flags.isolated)),
                  entry_sha256=ENTRY_SHA256, entry_digest=ENTRY_DIGEST,
                  checkpoint_sha256=completed_sha, checkpoint_bytes=len(completed),
                  phase=done.phase, certified=done.certified, stock=9,
                  checks=checks, checks_passed=len(checks),
                  past_generators_called=sum(x.call_count for x in mocks),
                  external_checkpoint_checked=external_checkpoint is not None,
                  external_checkpoint_sha256=external_sha256,
                  old_RR69_record_byte_identity_claimed=False,
                  operating_system_changed=False)
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.work/e1-runtime-portability')
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--trusted-checkpoint-sha256')
    args = parser.parse_args()
    if (args.checkpoint is None) != (args.trusted_checkpoint_sha256 is None):
        parser.error('--checkpoint and --trusted-checkpoint-sha256 must be supplied together')
    run(args.output, args.checkpoint, args.trusted_checkpoint_sha256)


if __name__ == '__main__':
    main()
