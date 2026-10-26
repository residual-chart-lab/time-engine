"""E4 JSON-lines bridge for declared event/model correspondences."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'integrations/inquiry'))
from event_bridge import Episode, MAX_COMMAND_BYTES, MAX_SNAPSHOT_BYTES
import entry_transport as wire


def bounded_read(path, limit):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('input file exceeds byte budget')
    return raw


def emit(value):
    print(json.dumps(value, ensure_ascii=True, separators=(',', ':')), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', type=Path, required=True)
    parser.add_argument('--trusted-sha256', required=True)
    parser.add_argument('--expected-entry-digest', required=True)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--trusted-resume-sha256')
    args = parser.parse_args(argv)
    if (args.resume is None) != (args.trusted_resume_sha256 is None):
        parser.error('supply both resume options')
    try:
        episode = Episode.receive(bounded_read(args.entry, wire.MAX_BYTES),
                                  args.trusted_sha256, args.expected_entry_digest)
        if args.resume:
            episode = Episode.restore(episode._session, bounded_read(args.resume, MAX_SNAPSHOT_BYTES),
                                      args.trusted_resume_sha256)
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as error:
        emit(dict(ok=False, error=str(error)))
        return 2
    emit(dict(ok=True, event='resumed' if args.resume else 'received', status=episode.status()))
    while True:
        line = sys.stdin.buffer.readline(MAX_COMMAND_BYTES + 1)
        if not line:
            return 0
        if len(line) > MAX_COMMAND_BYTES:
            emit(dict(ok=False, error='command byte budget exceeded'))
            return 2
        try:
            cmd = json.loads(line)
            if cmd == {'op': 'quit'}:
                emit(dict(ok=True, event='quit', status=episode.status()))
                return 0
            if cmd == {'op': 'status'}:
                emit(dict(ok=True, status=episode.status()))
            elif type(cmd) is dict and set(cmd) in ({'op', 'goal'}, {'op', 'goal', 'as_of'}) and cmd['op'] == 'recall':
                emit(dict(ok=True, recall=episode.recall(cmd['goal'], cmd.get('as_of'))))
            elif type(cmd) is dict and set(cmd) == {'op', 'path'} and cmd['op'] == 'save':
                if type(cmd['path']) is not str or not cmd['path']:
                    raise ValueError('save needs a new file path')
                raw, sha = episode.snapshot()
                with Path(cmd['path']).open('xb') as stream:
                    stream.write(raw)
                emit(dict(ok=True, saved=cmd['path'], sha256=sha, bytes=len(raw), status=episode.status()))
            else:
                emit(dict(ok=True, **episode.apply(cmd)))
        except (ValueError, TypeError, KeyError, OSError, RecursionError) as error:
            emit(dict(ok=False, error=str(error), status=episode.status()))


if __name__ == '__main__':
    raise SystemExit(main())

