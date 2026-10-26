"""Compile source packets or operate one source-backed TE reply family."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import source_reply as api
import correction_observer as obs
from event_bridge import Episode

ENTRY=ROOT/'integrations/inquiry/E1-entry.record.json'
ENTRY_SHA='d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
ENTRY_DIGEST='24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'


def read(path,limit):
    with path.open('rb') as stream:raw=stream.read(limit+1)
    if len(raw)>limit:raise ValueError('input byte budget exceeded')
    return raw


def emit(value):
    print(json.dumps(value,ensure_ascii=True,separators=(',',':')),flush=True)


def new_ledger():
    return Episode.receive(read(ENTRY,200_000),ENTRY_SHA,ENTRY_DIGEST)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_subparsers(dest='mode',required=True)
    compile_args=modes.add_parser('compile')
    compile_args.add_argument('--case',type=Path,required=True)
    compile_args.add_argument('--output-dir',type=Path,required=True)
    run=modes.add_parser('run')
    run.add_argument('--bundle',type=Path,required=True)
    run.add_argument('--trusted-sha256',required=True)
    run.add_argument('--resume',type=Path)
    run.add_argument('--trusted-resume-sha256')
    args=parser.parse_args(argv)
    errors=(ValueError,TypeError,KeyError,OSError,UnicodeError,RecursionError)
    try:
        if args.mode=='compile':
            raw=read(args.case,obs.MAX_INPUT_BYTES);case=json.loads(raw)
            variants={'retained':(), 'without-before':('before',),
                      'current-only':('before','correction','continuation'), 'blind-control':('continuation',)}
            values={name:api.bundle(case,roles) for name,roles in variants.items()}
            args.output_dir.mkdir(exist_ok=False,parents=False)
            files={}
            for name,value in values.items():
                data=obs.encode(value);path=args.output_dir/(name+'.bundle.json');path.write_bytes(data)
                files[path.name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            (args.output_dir/'CONTRACT.json').write_bytes(obs.encode(api.CONTRACT))
            (args.output_dir/'case.input.json').write_bytes(raw)
            manifest=dict(schema=api.FAMILY+'-delivery',input_sha256=hashlib.sha256(raw).hexdigest(),
                          contract=api.digest(api.CONTRACT),files=files,erasure_authorized=False,
                          note='Recipient variants differ in available source bodies; the original case is retained.')
            (args.output_dir/'MANIFEST.json').write_bytes(obs.encode(manifest))
            emit(dict(ok=True,manifest=manifest));return 0
        if (args.resume is None)!=(args.trusted_resume_sha256 is None):
            raise ValueError('supply both resume options')
        raw=read(args.bundle,api.MAX_BUNDLE_BYTES)
        if hashlib.sha256(raw).hexdigest()!=args.trusted_sha256:
            raise ValueError('external trusted bundle SHA-256 required')
        value=json.loads(raw)
        if args.resume:
            session=api.Session.restore(value,new_ledger(),read(args.resume,api.MAX_SNAPSHOT_BYTES),args.trusted_resume_sha256)
        else:
            session=api.Session(value,new_ledger())
    except errors as error:
        emit(dict(ok=False,error=str(error)));return 2
    emit(dict(ok=True,event='resumed' if args.resume else 'received',status=session.status()))
    while True:
        line=sys.stdin.buffer.readline(api.MAX_COMMAND_BYTES+1)
        if not line:return 0
        if len(line)>api.MAX_COMMAND_BYTES:
            emit(dict(ok=False,error='command byte budget exceeded'));return 2
        try:
            command=json.loads(line)
            if command=={'op':'quit'}:
                emit(dict(ok=True,status=session.status()));return 0
            if command=={'op':'status'}:
                emit(dict(ok=True,status=session.status()))
            elif type(command) is dict and set(command)=={'op','path'} and command['op']=='save':
                if type(command['path']) is not str or not command['path']:raise ValueError('new checkpoint path required')
                raw,sha=session.snapshot()
                with Path(command['path']).open('xb') as stream:stream.write(raw)
                emit(dict(ok=True,saved=command['path'],sha256=sha,bytes=len(raw),status=session.status()))
            else:
                emit(dict(ok=True,**session.apply(command)))
        except errors as error:
            emit(dict(ok=False,error=str(error),status=session.status()))


if __name__=='__main__':raise SystemExit(main())

