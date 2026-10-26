"""Observe one correction case and export ordinary, UNMAPPED E4 commands."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'integrations/inquiry'))
from correction_observer import analyze, e4_commands, encode, PROTOCOL, FOCI, MAX_INPUT_BYTES


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True, help='new directory in an existing parent')
    parser.add_argument('--focus', choices=FOCI)
    parser.add_argument('--expected-input-sha256')
    args = parser.parse_args(argv)
    try:
        with args.case.open('rb') as stream:
            raw = stream.read(MAX_INPUT_BYTES+1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError('case file byte budget exceeded')
        actual = hashlib.sha256(raw).hexdigest()
        if args.expected_input_sha256 is not None and args.expected_input_sha256 != actual:
            raise ValueError('input file differs from the expected SHA-256')
        case = json.loads(raw.decode('utf-8'))
        report = analyze(case, args.focus)
        commands = e4_commands(case, report)
        # All input/export validation finishes before any output directory is made.
        out = args.output_dir
        out.mkdir(parents=False, exist_ok=False)
        (out/'case.input.json').write_bytes(raw)
        (out/'protocol.json').write_bytes(encode(PROTOCOL))
        (out/'observation.json').write_bytes(encode(report))
        with (out/'E4-commands.jsonl').open('wb') as stream:
            for command in commands:
                stream.write((json.dumps(command, ensure_ascii=True, separators=(',',':'))+'\n').encode())
        files = {}
        for name in ('case.input.json','protocol.json','observation.json','E4-commands.jsonl'):
            content = (out/name).read_bytes()
            files[name] = dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
        receipt = dict(schema='time-engine-correction-delivery-v1', input_sha256=actual,
                       report_id=report['report_id'], protocol_sha256=report['protocol_sha256'],
                       exported_commands=len(commands), files=files,
                       source_and_anchor_checks=True, semantic_correctness_certified=False,
                       numerical_model_bound=False, ai_behavior_effect_measured=False)
        (out/'MANIFEST.json').write_bytes(encode(receipt))
        print(json.dumps(dict(ok=True, output_dir=str(out), report_id=report['report_id'],
                              reading_plan=report['reading_plan'], continuity=report['observations']['p']['continuity_evidence'],
                              semantic_mapping='UNMAPPED', exported_commands=len(commands)), ensure_ascii=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError) as error:
        print(json.dumps(dict(ok=False, error=str(error)), ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

