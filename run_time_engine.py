"""E2 JSON-lines interface: receive once, then bind/choose/resolve/advance."""
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'integrations/inquiry'))
from step_session import Session, MAX_COMMAND_BYTES, MAX_SNAPSHOT_BYTES
import entry_transport as wire


def bounded_read(path, limit):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('input file exceeds byte budget')
    return raw


def emit(value):
    print(json.dumps(value, separators=(',', ':')), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', type=Path, required=True)
    parser.add_argument('--trusted-sha256', required=True)
    parser.add_argument('--expected-entry-digest', required=True)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--trusted-resume-sha256')
    args = parser.parse_args(argv)
    if (args.resume is None) != (args.trusted_resume_sha256 is None):
        parser.error('--resume and --trusted-resume-sha256 must be supplied together')
    try:
        session = Session.receive(bounded_read(args.entry, wire.MAX_BYTES), args.trusted_sha256, args.expected_entry_digest)
        if args.resume is not None:
            session = Session.restore(session.entry, bounded_read(args.resume, MAX_SNAPSHOT_BYTES), args.trusted_resume_sha256)
    except (ValueError, OSError, TypeError, KeyError) as error:
        emit(dict(ok=False, error=str(error)))
        return 2
    emit(dict(ok=True, event='resumed' if args.resume is not None else 'received', status=session.status()))
    while True:
        line = sys.stdin.buffer.readline(MAX_COMMAND_BYTES + 1)
        if not line:
            return 0
        if len(line) > MAX_COMMAND_BYTES:
            emit(dict(ok=False, error='command byte budget exceeded'))
            return 2
        try:
            command = json.loads(line)
            if command == {'op': 'quit'}:
                emit(dict(ok=True, event='quit', status=session.status()))
                return 0
            if command == {'op': 'status'}:
                emit(dict(ok=True, status=session.status()))
            elif type(command) is dict and set(command) == {'op', 'path'} and command['op'] == 'save':
                if type(command['path']) is not str or not command['path']:
                    raise ValueError('save needs a new file path')
                raw, sha = session.snapshot()
                path = Path(command['path'])
                # Never replace an existing recovery checkpoint.
                with path.open('xb') as stream:
                    stream.write(raw)
                emit(dict(ok=True, saved=str(path), sha256=sha, bytes=len(raw), status=session.status()))
            else:
                emit(dict(ok=True, status=session.apply(command)))
        except (ValueError, TypeError, KeyError, OSError) as error:
            emit(dict(ok=False, error=str(error), status=session.status()))


if __name__ == '__main__':
    raise SystemExit(main())
