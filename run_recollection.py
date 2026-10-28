"""Use a short registered cue to retrieve E4 history and record an AI's reply."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'integrations/inquiry'))
from event_bridge import Episode, MAX_SNAPSHOT_BYTES
from recollection import Recollection, MAX_COMMAND_BYTES
import entry_transport as wire

ENTRY = ROOT / 'integrations/inquiry/E1-entry.record.json'
ENTRY_SHA = 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
ENTRY_DIGEST = '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'


def read(path, limit):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('input file byte budget exceeded')
    return raw


def emit(value):
    print(json.dumps(value, ensure_ascii=True, separators=(',', ':')), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', type=Path, default=ENTRY)
    parser.add_argument('--trusted-sha256', default=ENTRY_SHA)
    parser.add_argument('--expected-entry-digest', default=ENTRY_DIGEST)
    parser.add_argument('--episode', type=Path)
    parser.add_argument('--trusted-episode-sha256')
    args = parser.parse_args(argv)
    errors = (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError)
    try:
        if (args.episode is None) != (args.trusted_episode_sha256 is None):
            raise ValueError('supply both episode and trusted episode SHA-256')
        episode = Episode.receive(read(args.entry, wire.MAX_BYTES),
                                  args.trusted_sha256, args.expected_entry_digest)
        if args.episode is not None:
            episode = Episode.restore(episode._session,
                        read(args.episode, MAX_SNAPSHOT_BYTES), args.trusted_episode_sha256)
        session = Recollection(episode)
    except errors as error:
        emit(dict(ok=False, error=str(error))); return 2
    emit(dict(ok=True, event='resumed' if args.episode else 'received', status=session.status()))
    while True:
        line = sys.stdin.buffer.readline(MAX_COMMAND_BYTES + 1)
        if not line:
            return 0
        if len(line) > MAX_COMMAND_BYTES:
            emit(dict(ok=False, error='command byte budget exceeded')); return 2
        try:
            command = json.loads(line)
            if command == {'op': 'quit'}:
                emit(dict(ok=True, event='quit', status=session.status())); return 0
            if command == {'op': 'status'}:
                emit(dict(ok=True, status=session.status()))
            elif type(command) is dict and set(command) == {'op', 'path'} and command['op'] == 'save':
                if type(command['path']) is not str or not command['path']:
                    raise ValueError('new checkpoint file path required')
                raw, sha = session.snapshot()
                with Path(command['path']).open('xb') as stream:
                    stream.write(raw)
                emit(dict(ok=True, saved=command['path'], sha256=sha, bytes=len(raw),
                          status=session.status()))
            else:
                emit(dict(ok=True, **session.apply(command)))
        except errors as error:
            emit(dict(ok=False, error=str(error), status=session.status()))


if __name__ == '__main__':
    raise SystemExit(main())
