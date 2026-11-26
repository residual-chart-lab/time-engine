# Time Engine continuity preview v0.2

When a handoff says “we chose the wording,” the next reader may need to know whose proposal was chosen and who confirmed it. A decision bookmark binds those roles to the archived messages. It can also record that the team explicitly deferred the choice, or that the writer has only found a proposal.

Use Python 3.12+ and a local writable folder. In the self-contained package, try the sign example:

```console
python -I -B -X utf8 make_demo.py --workspace demo-room
python -I -B -X utf8 continuity.py --workspace demo-room read --id demo-outcome --bookmark
```

The returned `sources.proposal.text` and `sources.decision.text` are the actual archived messages, with IDs and fingerprints. The person or agent writing the bookmark chooses the roles. A normal `resume` carries the references in its record budget. Open them when the exact wording or decision matters. To open a v0.1 room with the new host, keep its original backend at the path recorded in the room's configuration. See the [authoring example in Japanese](START_HERE_JA.md#案と決定を一緒に読み返す).

The repository source slice uses the historical directory name `continuity-preview-v001`. To run it directly, place the verified open-use v0.1.1 package contents in `open_use/` beside these files. From the repository root, `python tools/build_continuity_preview.py --base-zip <v0.1-continuity-zip> --out-dir <output-folder>` assembles the v0.2 ZIP from the pinned previous package and current source. [Previous self-contained package](https://github.com/residual-chart-lab/time-engine/releases/tag/continuity-preview-v0.1-2026-11-19) · [Component fingerprints](ORIGINS.json) · [Audit scope](AUDIT_SCOPE.md)
