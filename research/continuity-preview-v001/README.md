> Repository source slice: use the [self-contained release ZIP](https://github.com/residual-chart-lab/time-engine/releases/tag/continuity-preview-v0.1-2026-11-19) for the bundled runtime and runnable tests. This source directory does not duplicate `open_use/`. To assemble it yourself, obtain the unchanged open-use v0.1.1 ZIP named in ORIGINS.json, verify its external SHA, and place its extracted contents in `open_use/` beside these modules. The module bytes are the same as the release ZIP.

# Time Engine continuity preview v0.1

Receive a job after context loss, keep originals separate from later readings, and return to an exact source when the current task needs it.

This technical preview adds a local continuity host and an optional trial-evidence route. It includes the unchanged published open-use v0.1.1 backend and runtime. Python 3.12+ and local writable storage are required; no network or external Python libraries are needed to run the examples.

Start with [START_HERE_JA.md](START_HERE_JA.md). Run `python -I -B -X utf8 make_demo.py --workspace demo-room` to create an entirely invented notebook. Existing workspaces are refused.

The archive contains code and synthetic examples, not the authors' conversation archives, private operational checkpoints, credentials, or recipient traces. Audit evidence here is a scoped public summary; the whole assembled archive has publisher-side extraction checks, not a new independent whole-package audit.

The continuity and trial-evidence modules match the locally audited code bytes. See [ORIGINS.json](ORIGINS.json), [AUDIT_SCOPE.md](AUDIT_SCOPE.md), and [CHANGES.md](CHANGES.md). Earlier public releases remain available for reproduction.
