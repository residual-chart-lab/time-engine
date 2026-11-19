"""Local trial evidence: sealed inputs, fixed task delivery and exact submissions.

This is an auditable route, not an authentication or OS sandbox boundary.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import argparse
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid

SCHEMA = 'te-trial-evidence-v0.2'
TABLES = ('sources', 'intake', 'receipts', 'meta', 'cursors', 'attempts')
SELF = Path(__file__).resolve()


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def digest(raw):
    return sha256(raw).hexdigest()


def fingerprint(path):
    return digest(path.read_bytes())


def fresh(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    fresh(path, encoded(value))


def load(path):
    return json.loads(path.read_bytes())


def relative_file(root, name):
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('file escapes the trial root')
    return path


def file_map(root):
    return {p.relative_to(root).as_posix(): dict(sha256=fingerprint(p), bytes=p.stat().st_size)
            for p in sorted(root.rglob('*')) if p.is_file()}


def rows_fingerprint(db, *, sealed_standalone=False):
    # Operational databases can have committed WAL frames. Only a known standalone sealed backup may ignore WAL.
    suffix = '?mode=ro&immutable=1' if sealed_standalone else '?mode=ro'
    with sqlite3.connect(db.resolve().as_uri() + suffix, uri=True) as con:
        result = {}
        for table in TABLES:
            rows = con.execute('SELECT * FROM ' + table + ' ORDER BY rowid').fetchall()
            normalized = [[dict(bytes_b64=base64.b64encode(v).decode()) if isinstance(v, bytes) else v
                           for v in row] for row in rows]
            result[table] = dict(rows=len(rows), sha256=digest(encoded(normalized)))
        return result


def backend(entry, workspace, args):
    command = [sys.executable, '-I', '-B', '-X', 'utf8', str(entry), '--workspace', str(workspace), *args]
    p = subprocess.run(command, capture_output=True, timeout=90)
    record = dict(args=command, returncode=p.returncode,
                  stdout_b64=base64.b64encode(p.stdout).decode(), stderr_b64=base64.b64encode(p.stderr).decode())
    if p.returncode:
        raise RuntimeError('backend failed: ' + p.stdout.decode('utf-8', 'replace') + p.stderr.decode('utf-8', 'replace'))
    value = json.loads(p.stdout)
    if not value.get('ok'):
        raise RuntimeError('backend returned an unsuccessful response')
    return value['result'], record


def prepare(root, source, entry, tasks, routing, protocol):
    if root.exists():
        raise FileExistsError('trial root must be new')
    root.mkdir(parents=True)
    sealed = root / 'sealed'
    sealed.mkdir()
    with sqlite3.connect((source / 'archive.sqlite3').resolve().as_uri() + '?mode=ro', uri=True) as src:
        with sqlite3.connect(sealed / 'archive.sqlite3') as dst:
            src.backup(dst)
            dst.execute('PRAGMA journal_mode=DELETE').fetchone()
    shutil.copy2(source / 'CONFIG.json', sealed / 'CONFIG.json')
    shutil.copytree(source / 'te', sealed / 'te')
    before = file_map(sealed)
    initial = rows_fingerprint(sealed / 'archive.sqlite3', sealed_standalone=True)
    assert file_map(sealed) == before
    initial_copies = {}
    for name in ('execution', 'packet-preparation'):
        shutil.copytree(sealed, root / name)
        observed = file_map(root / name)
        logical = rows_fingerprint(root / name / 'archive.sqlite3')
        assert observed == before and logical == initial
        assert file_map(root / name) == observed
        initial_copies[name] = dict(files=observed, logical_rows=logical, observed_at=now())
    packet, packet_trace = backend(entry, root / 'packet-preparation', ['resume'])
    if packet['inventory']['pending'] or packet['recovered_pending']:
        raise ValueError('this read-only receiver trial requires a fully committed input')
    save(root / 'fixed/PACKET_B.json', packet)
    save(root / 'preparation/PACKET_BUILD.json', packet_trace)
    original, original_trace = backend(entry, root / 'packet-preparation', ['source', '--id', 's000029'])
    save(root / 'fixed/FORWARD_B3.json', original)
    save(root / 'preparation/FORWARD_BUILD.json', original_trace)
    quote = next(line for line in original['text'].splitlines() if line.startswith('僕は黙って'))
    if any(quote in text for text in tasks.values()) or quote in json.dumps(packet, ensure_ascii=False):
        raise ValueError('target quote was already supplied in a task or the initial packet')
    required = {'a1', 'b1', 'a2', 'b2', 'b3'}
    if set(tasks) != required or set(routing) != required:
        raise ValueError('all five stages must be fixed before the trial')
    for key, text in tasks.items():
        fresh(root / 'fixed/tasks' / (key + '.txt'), text.encode('utf-8'))
        save(root / 'fixed/routing' / (key + '.json'), routing[key])
    save(root / 'fixed/PROTOCOL.json', protocol)
    config = load(sealed / 'CONFIG.json')
    backend_entry = Path(config['backend_entry'])
    dependencies = [backend_entry, backend_entry.parent / 'RUNTIME_REFERENCE.json']
    dependencies.extend(sorted((backend_entry.parent / 'runtime').rglob('*.py')))
    manifest = dict(schema=SCHEMA, trial_id=uuid.uuid4().hex, prepared_at=now(),
        source_workspace=str(source.resolve()), source_scope='New backup of a historically verified logical state, not reconstruction of the old initial DB bytes.',
        entry=str(entry.resolve()), entry_sha256=fingerprint(entry), harness=str(SELF), harness_sha256=fingerprint(SELF),
        sealed_files=before, initial_logical_rows=initial,
        initial_execution_files_match_sealed=True, initial_execution_logical_rows=initial,
        measured_initial_copies=initial_copies,
        dependency_files={str(p): fingerprint(p) for p in dependencies},
        initial_comparison_at=now(), fixed_files=file_map(root / 'fixed'),
        preparation_files=file_map(root / 'preparation'),
        capability=dict(a=['resume', 'source', 'read', 'status'], b=[],
            scope='CLI route restriction; shell/filesystem access is not physically removed.'),
        limits=['Model context and opaque bootstrap dispatch bodies are not fully attested.',
                'Task receipt proves delivery, not reading or comprehension.',
                'Role declaration is not identity authentication.'])
    assert file_map(sealed) == before
    save(root / 'MANIFEST.json', manifest)
    save(root / 'ANCHOR.json', dict(manifest_sha256=fingerprint(root / 'MANIFEST.json'), created_at=now()))
    for path in ('events', 'receipts', 'submissions', 'incoming/a', 'incoming/b'):
        (root / path).mkdir(parents=True)
    return manifest


@contextmanager
def lock(root):
    path = root / '.operation.lock'
    deadline = time.monotonic() + 120
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError('trial operation lock is still held')
            time.sleep(.05)
    try:
        yield
    finally:
        path.unlink()


def check_files(root, expected):
    actual = file_map(root)
    if actual != expected:
        raise ValueError('sealed/fixed files differ: ' + str(root))


def verify_static(root):
    manifest = load(root / 'MANIFEST.json')
    if fingerprint(root / 'MANIFEST.json') != load(root / 'ANCHOR.json')['manifest_sha256']:
        raise ValueError('manifest fingerprint differs')
    if manifest['schema'] != SCHEMA or fingerprint(Path(manifest['entry'])) != manifest['entry_sha256']:
        raise ValueError('backend entry differs')
    if fingerprint(Path(manifest['harness'])) != manifest['harness_sha256']:
        raise ValueError('harness differs')
    if any(fingerprint(Path(p)) != expected for p, expected in manifest['dependency_files'].items()):
        raise ValueError('fixed dependency differs')
    for measured in manifest['measured_initial_copies'].values():
        if measured['files'] != manifest['sealed_files'] or measured['logical_rows'] != manifest['initial_logical_rows']:
            raise ValueError('recorded initial copy comparison differs')
    for name, expected in [('sealed', manifest['sealed_files']), ('fixed', manifest['fixed_files']),
                           ('preparation', manifest['preparation_files'])]:
        check_files(root / name, expected)
    for relative, expected in manifest['sealed_files'].items():
        if relative == 'archive.sqlite3':
            continue
        path = relative_file(root / 'execution', relative)
        if not path.is_file() or fingerprint(path) != expected['sha256'] or path.stat().st_size != expected['bytes']:
            raise ValueError('execution immutable file differs: ' + relative)
    if rows_fingerprint(root / 'execution/archive.sqlite3') != manifest['initial_logical_rows']:
        raise ValueError('execution immutable logical rows differ')
    return manifest


def verify_events(root, manifest):
    previous = None
    events = []
    for number, path in enumerate(sorted((root / 'events').glob('*.json')), 1):
        event = load(path)
        if path.name != f'{number:04d}.json' or event['seq'] != number or event['previous_event_sha256'] != previous:
            raise ValueError('event chain is missing or reordered')
        if event['trial_id'] != manifest['trial_id'] or event['manifest_sha256'] != fingerprint(root / 'MANIFEST.json'):
            raise ValueError('event belongs to another trial/input')
        response_path = relative_file(root, event['response_file'])
        raw = response_path.read_bytes()
        if digest(raw) != event['response_sha256'] or len(raw) != event['response_bytes']:
            raise ValueError('returned response bytes differ')
        response = json.loads(raw)
        if response['ok'] != event['ok']:
            raise ValueError('success/refusal record differs')
        event['_response'] = response
        event['_path'] = path.name
        previous = fingerprint(path)
        events.append(event)
    expected_blobs = {e['response_file'].split('/')[-1] for e in events}
    if {p.name for p in (root / 'events').glob('*.response.bin')} != expected_blobs:
        raise ValueError('response evidence is missing or orphaned')
    return events


def stage_open(events):
    return max([1] + [e['stage'] for e in events if e['ok'] and e['operation'] == 'open-stage'])


def receipt(root, events, role, stage, token):
    key = role + str(stage)
    path = root / 'receipts' / (key + '.json')
    if not path.exists():
        raise ValueError('task has not been delivered')
    value = load(path)
    if value['token'] != token or value['role'] != role or value['stage'] != stage:
        raise ValueError('receipt role/stage/token differs')
    delivered = next((e for e in events if e['ok'] and e['operation'] == 'receive'
                      and e['role'] == role and e['stage'] == stage), None)
    if delivered is None or delivered['_response']['result']['receipt'] != value:
        raise ValueError('receipt is not backed by actual delivery bytes')
    return value


def handle(root, manifest, events, operation, role, stage, token, args, source_file):
    key = role + str(stage) if role else None
    if operation == 'open-stage':
        if stage not in (2, 3) or stage != stage_open(events) + 1:
            raise ValueError('stage is not the next stage')
        required = ('a1', 'b1') if stage == 2 else ('a2', 'b2')
        done = {str(e['role']) + str(e['stage']) for e in events if e['ok'] and e['operation'] == 'submit'}
        if not set(required).issubset(done):
            raise ValueError('prior-stage submissions are incomplete')
        return dict(opened_stage=stage)
    if role not in ('a', 'b') or key not in ('a1', 'b1', 'a2', 'b2', 'b3'):
        raise ValueError('unsupported role/stage')
    if stage != stage_open(events):
        raise ValueError('stage is not currently open')
    if operation == 'receive':
        task_file = root / 'fixed/tasks' / (key + '.txt')
        task_raw = task_file.read_bytes()
        delivery = dict(trial_id=manifest['trial_id'], role=role, stage=stage,
            task=dict(text=task_raw.decode('utf-8'), utf8_b64=base64.b64encode(task_raw).decode(),
                      sha256=digest(task_raw), bytes=len(task_raw)),
            input_manifest_sha256=fingerprint(root / 'MANIFEST.json'),
            context=(dict(workspace=str(root / 'execution')) if role == 'a'
                     else load(root / 'fixed' / ('FORWARD_B3.json' if stage == 3 else 'PACKET_B.json'))))
        path = root / 'receipts' / (key + '.json')
        if path.exists():
            value = load(path)
        else:
            value = dict(trial_id=manifest['trial_id'], role=role, stage=stage, token=uuid.uuid4().hex,
                         task_sha256=digest(task_raw), issued_at=now())
            save(path, value)
        delivery['receipt'] = value
        return delivery
    receipt(root, events, role, stage, token)
    if operation == 'use':
        if role != 'a':
            raise ValueError('this role has no backend capability on the CLI route')
        if not args or args[0] not in manifest['capability']['a']:
            raise ValueError('backend mutation or unsupported command')
        if args[0] in ('resume', 'status') and len(args) != 1:
            raise ValueError('extra backend arguments are not allowed')
        if args[0] in ('read', 'source') and (len(args) != 3 or args[1] != '--id'):
            raise ValueError('use an explicit id')
        result, trace = backend(Path(manifest['entry']), root / 'execution', args)
        return dict(value=result, backend=trace)
    if operation == 'submit':
        if source_file is None:
            raise ValueError('a submission file is required')
        file = Path(source_file).resolve()
        incoming = (root / 'incoming' / role).resolve()
        if not file.is_relative_to(incoming) or file.is_symlink():
            raise ValueError('submission must be in the role incoming directory')
        raw = file.read_bytes()
        if not raw or len(raw) > 30000:
            raise ValueError('submission is empty or exceeds 30000 bytes')
        raw.decode('utf-8')
        destination = root / 'submissions' / (key + '.md')
        fresh(destination, raw)
        value = dict(trial_id=manifest['trial_id'], role=role, stage=stage,
            receipt_token=token, task_sha256=load(root / 'receipts' / (key + '.json'))['task_sha256'],
            raw_file=destination.relative_to(root).as_posix(), raw_sha256=digest(raw), bytes=len(raw), received_at=now())
        save(root / 'submissions' / (key + '.json'), value)
        return value
    raise ValueError('unsupported operation')


def operate(root, operation, role=None, stage=1, token=None, args=None, source_file=None):
    started = now()
    with lock(root):
        manifest = load(root / 'MANIFEST.json')
        events = verify_events(root, manifest)
        try:
            verify_static(root)
            result = handle(root, manifest, events, operation, role, stage, token, args or [], source_file)
            verify_static(root)
            response = dict(ok=True, result=result)
        except (ValueError, FileExistsError, FileNotFoundError, RuntimeError) as error:
            response = dict(ok=False, error=str(error), error_type=type(error).__name__)
        raw = encoded(response)
        number = len(events) + 1
        response_file = 'events/' + f'{number:04d}.response.bin'
        fresh(root / response_file, raw)
        save(root / 'events' / f'{number:04d}.json', dict(
            seq=number, trial_id=manifest['trial_id'], role=role, stage=stage, operation=operation,
            request=dict(operation=operation, role=role, stage=stage, receipt=token,
                         args=args or [], file=str(source_file) if source_file else None),
            started_at=started, completed_at=now(), ok=response['ok'],
            manifest_sha256=fingerprint(root / 'MANIFEST.json'),
            previous_event_sha256=fingerprint(root / 'events' / f'{number-1:04d}.json') if number > 1 else None,
            response_file=response_file, response_sha256=digest(raw), response_bytes=len(raw)))
        return response


def verify(root, complete=False):
    with lock(root):
        manifest = verify_static(root)
        events = verify_events(root, manifest)
        delivered = []
        submitted = []
        for index, e in enumerate(events):
            if not e['ok']:
                continue
            result = e['_response']['result']
            key = str(e['role']) + str(e['stage'])
            previous = events[:index]
            if e['operation'] == 'open-stage':
                done = {str(x['role']) + str(x['stage']) for x in previous if x['ok'] and x['operation'] == 'submit'}
                required = {'a1', 'b1'} if e['stage'] == 2 else {'a2', 'b2'}
                if e['stage'] != stage_open(previous) + 1 or not required.issubset(done):
                    raise ValueError('stage opening has no completed prerequisite')
            elif e['stage'] != stage_open(previous):
                raise ValueError('successful operation is outside its stage')
            if e['operation'] == 'receive':
                raw = (root / 'fixed/tasks' / (key + '.txt')).read_bytes()
                if base64.b64decode(result['task']['utf8_b64']) != raw or result['task']['text'].encode() != raw:
                    raise ValueError('delivered task text differs')
                if result['task']['sha256'] != digest(raw) or result['task']['bytes'] != len(raw):
                    raise ValueError('delivered task fingerprint differs')
                value = receipt(root, events, e['role'], e['stage'], result['receipt']['token'])
                if value['task_sha256'] != digest(raw):
                    raise ValueError('task receipt fingerprint differs')
                if e['role'] == 'b':
                    expected = load(root / 'fixed' / ('FORWARD_B3.json' if e['stage'] == 3 else 'PACKET_B.json'))
                    if result['context'] != expected:
                        raise ValueError('delivered context differs')
                delivered.append(key)
            elif e['operation'] in ('use', 'submit'):
                receipt(root, previous, e['role'], e['stage'], e['request']['receipt'])
                if e['operation'] == 'use':
                    trace = result['backend']
                    response = json.loads(base64.b64decode(trace['stdout_b64']))
                    if trace['returncode'] or not response.get('ok') or response['result'] != result['value']:
                        raise ValueError('backend evidence differs')
                else:
                    value = load(root / 'submissions' / (key + '.json'))
                    if value != result:
                        raise ValueError('submission receipt differs')
                    raw = relative_file(root, value['raw_file']).read_bytes()
                    if digest(raw) != value['raw_sha256'] or len(raw) != value['bytes']:
                        raise ValueError('submitted original bytes differ')
                    submitted.append(key)
        if {p.stem for p in (root / 'receipts').glob('*.json')} != set(delivered):
            raise ValueError('receipt evidence is missing or unreferenced')
        for suffix in ('*.json', '*.md'):
            if {p.stem for p in (root / 'submissions').glob(suffix)} != set(submitted):
                raise ValueError('submission evidence is missing or unreferenced')
        if complete and (set(delivered) != {'a1', 'b1', 'a2', 'b2', 'b3'} or set(submitted) != set(delivered)):
            raise ValueError('required deliveries/submissions are missing')
        return dict(schema=SCHEMA, passed=True, complete=complete, trial_id=manifest['trial_id'],
            deliveries=delivered, submissions=submitted, events=len(events), refusals=sum(not e['ok'] for e in events),
            sealed_byte_fingerprints_verified=True, execution_logical_rows_verified=True,
            execution_initial_byte_comparison_recorded=manifest['initial_execution_files_match_sealed'],
            execution_db_current_sha256=fingerprint(root / 'execution/archive.sqlite3'),
            sealed_db_sha256=fingerprint(root / 'sealed/archive.sqlite3'),
            scope='Recorded CLI route and fixed inputs; not full bootstrap/model-context attestation or authentication.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trial', type=Path, required=True)
    sub = p.add_subparsers(dest='operation', required=True)
    for name in ('receive', 'use', 'submit'):
        parser = sub.add_parser(name)
        parser.add_argument('--role', choices=['a', 'b'], required=True)
        parser.add_argument('--stage', type=int, required=True)
        if name != 'receive':
            parser.add_argument('--receipt', required=True)
        if name == 'submit':
            parser.add_argument('--file', type=Path, required=True)
        if name == 'use':
            parser.add_argument('backend_args', nargs=argparse.REMAINDER)
    sub.add_parser('open-stage').add_argument('--stage', type=int, required=True)
    sub.add_parser('verify').add_argument('--complete', action='store_true')
    a = p.parse_args()
    root = a.trial.resolve()
    try:
        if a.operation == 'verify':
            response = dict(ok=True, result=verify(root, a.complete))
        else:
            args = getattr(a, 'backend_args', [])
            if args[:1] == ['--']:
                args = args[1:]
            response = operate(root, a.operation, getattr(a, 'role', None), a.stage,
                getattr(a, 'receipt', None), args, getattr(a, 'file', None))
        sys.stdout.buffer.write(encoded(response))
        return 0 if response['ok'] else 2
    except (ValueError, RuntimeError, FileNotFoundError) as error:
        sys.stdout.buffer.write(encoded(dict(ok=False, error=str(error), error_type=type(error).__name__)))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
