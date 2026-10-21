"""Run one requested flower, or resume an authenticated stopped/in-flight one."""
from pathlib import Path
from fractions import Fraction as Q
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'integrations/inquiry'))
import live_flower as live
import live_checkpoint as checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    start = sub.add_parser('start', help='supply C; stop for current choice or answer the requested query')
    start.add_argument('--mode', choices=('keep', 'erase', 'restore'), default='keep')
    start.add_argument('--x', required=True, help='exact rational diagonal C coordinate, e.g. -1 or 1/4')
    start.add_argument('--query', choices=('actions', 'exists'), default='actions')
    start.add_argument('--domain', nargs=2, default=('-64', '64'))
    resume = sub.add_parser('resume', help='verify and resume an exact saved state')
    resume.add_argument('checkpoint', type=Path)
    resume.add_argument('--sha256', required=True, help='the externally retained digest from the previous command')
    resume.add_argument('--word', choices=live.f.WORDS)
    resume.add_argument('--connect', action='store_true', help='request exactly one connection after a stop')
    resume.add_argument('--strength', default='1/1024')
    resume.add_argument('--x', help='new query only before actuation; cannot replace an active C')
    resume.add_argument('--query', choices=('actions', 'exists'), default='actions')
    resume.add_argument('--domain', nargs=2, default=('-64', '64'))
    for item in (start, resume):
        item.add_argument('--ticks', type=int, default=32, help='finite work budget; 1 exposes each stage')
        item.add_argument('--out', type=Path, required=True, help='new checkpoint file; refuses overwrite')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output already exists; choose a new filename to keep the previous checkpoint')
    if args.command == 'start':
        session = live.Session(live.Seed(mode=args.mode))
        session.request(Q(args.x), live.f.EXISTS if args.query == 'exists' else live.f.ACTIONS,
                        tuple(map(Q, args.domain)))
    else:
        if sum((bool(args.word), args.connect, args.x is not None)) > 1:
            parser.error('choose one current input: a word, a connection request, or a new query')
        session = checkpoint.loads(args.checkpoint.read_bytes(), trusted_sha256=args.sha256)
        if args.word:
            session.choose(args.word)
        elif args.connect:
            session.connect(Q(args.strength))
        elif args.x is not None:
            session.request(Q(args.x), live.f.EXISTS if args.query == 'exists' else live.f.ACTIONS,
                            tuple(map(Q, args.domain)))
    session.run(args.ticks)
    raw = checkpoint.dumps(session)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('xb') as stream:
        stream.write(raw)
    print(json.dumps(dict(**session.status(), checkpoint=str(args.out),
                         sha256=hashlib.sha256(raw).hexdigest()), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
