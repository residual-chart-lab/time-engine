"""Build the v0.2 continuity preview from repository text and the public v0.1 ZIP."""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SOURCE = Path(__file__).resolve().parents[1] / "research" / "continuity-preview-v001"
BASE_SHA256 = "2071a9970dd64633393d23ca3bdd5ea1637731f5cbcf7ee3b1d7349e2f122847"
VERSION = "continuity-preview-v0.2"
DATE = "2026-11-26"
ZIP_ROOT = "te-continuity/"
SOURCE_FILES = (
    "AUDIT_SCOPE.md", "CHANGES.md", "LICENSE", "ORIGINS.json", "README.md",
    "START_HERE_JA.md", "VERSION.json", "continuity.py", "make_demo.py",
    "test_continuity.py", "test_trial_evidence.py", "trial_evidence.py",
)


def runtime_from(base_zip):
    data = base_zip.read_bytes()
    if sha256(data).hexdigest() != BASE_SHA256:
        raise ValueError("Base ZIP differs from the published v0.1 SHA-256")
    files = {}
    with ZipFile(BytesIO(data)) as archive:
        manifest = json.loads(archive.read(ZIP_ROOT + "MANIFEST.json"))
        for item in manifest["files"]:
            name = item["path"]
            if name.startswith("open_use/"):
                raw = archive.read(ZIP_ROOT + name)
                if len(raw) != item["bytes"] or sha256(raw).hexdigest() != item["sha256"]:
                    raise ValueError(f"Base runtime differs from its manifest: {name}")
                files[name] = raw
    return files


def build(base_zip, out_dir):
    files = runtime_from(base_zip)
    for name in SOURCE_FILES:
        # Git checkouts on Windows can have CRLF working-tree bytes.
        files[name] = (SOURCE / name).read_text(encoding="utf-8").encode("utf-8")

    version = json.loads(files["VERSION.json"])
    origins = json.loads(files["ORIGINS.json"])
    if version["version"] != VERSION or version["release_date"] != DATE or origins["bundle"] != VERSION:
        raise ValueError("VERSION.json and ORIGINS.json must identify this preview")
    for name in ("continuity.py", "trial_evidence.py"):
        if sha256(files[name]).hexdigest() != origins["components"][name]["sha256"]:
            raise ValueError(f"The source fingerprint differs from ORIGINS.json: {name}")

    entries = [dict(path=name, bytes=len(raw), sha256=sha256(raw).hexdigest())
               for name, raw in sorted(files.items())]
    manifest = dict(files=entries, origin=origins)
    files["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                              + "\n").encode("utf-8")
    filename = f"time-engine-{VERSION}-{DATE}.zip"
    out_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out_dir) as staging:
        package = Path(staging) / filename
        with ZipFile(package, "w") as archive:
            for name, raw in sorted(files.items()):
                entry = ZipInfo(ZIP_ROOT + name, date_time=(2026, 11, 26, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, raw, compress_type=ZIP_DEFLATED, compresslevel=9)
        checksum = sha256(package.read_bytes()).hexdigest()
        sidecar = package.with_suffix(".zip.sha256")
        sidecar.write_text(f"{checksum}  {filename}\n", encoding="ascii", newline="\n")
        package.replace(out_dir / filename)
        sidecar.replace(out_dir / sidecar.name)
    print(f"{checksum}  {filename} ({len(files)} files)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-zip", type=Path, required=True, help="published v0.1 continuity ZIP")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    build(args.base_zip, args.out_dir)
