"""Verify the exact files in the unpacked P0 candidate before importing engine code."""
from pathlib import Path, PurePosixPath
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def verify(root=ROOT):
    root = Path(root).resolve()
    raw = (root/'MANIFEST.json').read_bytes()
    manifest = json.loads(raw)
    if manifest.get('schema') != 'time-engine-p0-manifest-v1':
        raise ValueError('unknown candidate manifest')
    expected = set()
    for item in manifest['files']:
        name = item['path']; parts = PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or name in expected:
            raise ValueError('invalid or repeated package path')
        expected.add(name)
        path = root.joinpath(*parts.parts)
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('regular package files required')
        content = path.read_bytes()
        if len(content) != item['bytes'] or hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError('file changed: '+name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and not any(x in ('.work', '__pycache__') for x in p.relative_to(root).parts)}
    if actual != expected | {'MANIFEST.json'}:
        raise ValueError('candidate file set differs from manifest')
    return dict(passed=True, files=len(expected), manifest_sha256=hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
