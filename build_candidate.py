"""Build the pinned technical candidate, from its repository or unpacked copy."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import zipfile
ROOT = Path(__file__).resolve().parent
PREFIX = 'time-engine-p0'
FIXED_TIME = (2026,10,24,0,0,0)
TEMPLATES = ('README.md','AI_HANDOFF.md','verify_package.py','smoke_test.py','P0-SOURCE.json')


def canonical(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def build(output):
    templates = ROOT/'distribution/p0' if (ROOT/'distribution/p0').is_dir() else ROOT
    source = ROOT/'engine' if (ROOT/'engine').is_dir() else ROOT
    frozen = json.loads((templates/'P0-SOURCE.json').read_bytes())
    if frozen['schema'] != 'time-engine-p0-source-v1' or len(frozen['files']) != 422:
        raise ValueError('the pinned 422-file source snapshot is required')
    files = {}
    for row in frozen['files']:
        path = PurePosixPath(row['path'])
        if path.is_absolute() or '..' in path.parts or ('engine/'+row['path']) in files:
            raise ValueError('invalid or repeated source path')
        raw = source.joinpath(*path.parts).read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('pinned source changed: '+row['path'])
        files['engine/'+row['path']] = raw
    for name in TEMPLATES:
        files[name] = (templates/name).read_bytes()
    files['build_candidate.py'] = Path(__file__).read_bytes()
    files['PACKAGE.json'] = canonical(dict(schema='time-engine-p0-candidate-v1',date='2026-10-24',
        release_target='2026-12-25',status='engineering candidate P0',source_commit=frozen['source_commit'],
        source_tree=frozen['source_tree'],source_files=422,E1_independent_audit='PASS',
        E1_audited_commit='0f708c1d35eda52415a24347839d122046cf595b',
        E2_independent_audit=False,E2_linux_tested=False,
        build_timestamp=FIXED_TIME,builder_sha256=hashlib.sha256(files['build_candidate.py']).hexdigest()))
    rows = [dict(path=p,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)) for p,raw in sorted(files.items())]
    files['MANIFEST.json'] = canonical(dict(schema='time-engine-p0-manifest-v1',files=rows,manifest_self_hash_excluded=True))
    output.mkdir(parents=True,exist_ok=True)
    archive = output/(PREFIX+'.zip')
    sidecar = output/(PREFIX+'.zip.sha256')
    if archive.exists() or sidecar.exists():
        raise FileExistsError('build needs new archive and checksum paths')
    with archive.open('xb') as stream, zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for path,raw in sorted(files.items()):
            info = zipfile.ZipInfo(PREFIX+'/'+path,FIXED_TIME)
            info.create_system=3; info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    with sidecar.open('x',encoding='ascii',newline='\n') as stream:
        stream.write(sha+'  '+archive.name+'\n')
    report = dict(schema='time-engine-p0-build-v1',passed=True,archive=archive.name,sha256=sha,
                  bytes=archive.stat().st_size,source_files=422,archive_files=len(files),
                  source_commit=frozen['source_commit'],manifest_sha256=hashlib.sha256(files['MANIFEST.json']).hexdigest())
    print(json.dumps(report,indent=2))
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    build(parser.parse_args().output_dir)
