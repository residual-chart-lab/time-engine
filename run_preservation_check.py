"""Read-only comparison of current endpoint and requested continuation targets."""
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'integrations/inquiry'))
import preservation_targets as targets
import step_session as api
from run_time_engine import bounded_read


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', type=Path, required=True)
    parser.add_argument('--trusted-sha256', required=True)
    parser.add_argument('--expected-entry-digest', required=True)
    parser.add_argument('--omit', choices=('s', 't'), nargs='+', required=True)
    parser.add_argument('--context', choices=api.CONTEXTS, default='mixed')
    parser.add_argument('--strengths', nargs=2, default=('0', '0'))
    parser.add_argument('--frame', choices=tuple(api.FRAMES), default='identity')
    parser.add_argument('--domain', nargs=2)
    parser.add_argument('--v', default='1')
    parser.add_argument('--u', default='0')
    parser.add_argument('--word', choices=('HHHSUT', 'HHHUST'), default='HHHSUT')
    args = parser.parse_args(argv)
    data = dict(context=args.context, strengths=list(args.strengths), frame=args.frame)
    if args.domain is not None:
        data['domain'] = list(args.domain)
    try:
        entry = api.wire.loads(bounded_read(args.entry, api.wire.MAX_BYTES), args.trusted_sha256, args.expected_entry_digest)
        scope, normalized = api.requirement(entry, data)
        report = targets.compare(entry, scope, api.rational(args.v), api.rational(args.u), args.word, args.omit)
        report['requirement'] = normalized
        print(json.dumps(dict(ok=True, assessment=report), separators=(',', ':')))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(json.dumps(dict(ok=False, error=str(error)), separators=(',', ':')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
