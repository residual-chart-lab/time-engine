# AI handoff — Time Engine P0

This is a technical candidate for a finite, executable Time Engine model. Its
source is pinned to commit `1c185365bfcb2ea9f6c52c73ba263cf48c356d32`.
The target publication date is 2026-12-25. Start with `README.md`.

## Operate

1. Run `python -I verify_package.py` from this directory.
2. Run `python -I smoke_test.py` once. It exercises actual execution and recovery.
3. For your own interaction, keep `engine/run_time_engine.py` alive and send
   JSON-lines commands to its stdin. See `engine/docs/STEP_SESSION_E2.md`.
4. Bind the future requirement, choose current controls, resolve the required
   observations, then explicitly advance one Flower at a time.
5. Save at a recovery boundary. Keep the returned SHA-256 separately and supply
   it with `--resume`. Entry authentication and checkpoint replay happen at
   startup/recovery; ordinary commands reuse the accepted in-memory state.

## Preserve the model's distinctions

- Future requirements constrain admissibility through retained differences;
  this coupling is an adopted design principle of this system.
- A requirement does not choose the current petal. Current selection is explicit.
- A normally closed Flower stops. The next advance is a separate command.
- Authenticating past history does not authorize a new future requirement.
- Changing a request before physical execution clears the prior plan and action.
  Valid observations can be reused; a new admissibility judgment is still needed.
- A closed Flower cannot be rewound, rebound, or reselected by this interface.
- Scope-specific replaceability permits omitted expansion, not erasure of the
  originals. All retained exact values and their provenance remain available.
- Zero additional numeric reads is not zero computation. Validation and replay
  have costs. The candidate does not claim universal future causation or an
  indefinitely stable, autonomous engine.

## Evidence and scope

E1's limited entry was independently audited on Linux; the Windows entry and
checkpoint records also reproduced. E2 has eight focused tests, real stdin/stdout
execution, exact agreement with the existing RR69 histories, and Windows Python
3.12-to-3.14 checkpoint recovery. E2's independent audit and Linux execution
remain pending. Use `engine/docs/ENTRY_TRANSPORT_E1_STATUS.md` for current E1 scope.

The source tree includes the implementation, examples, prior records and vendor
notices. It needs no network access for the included acceptance run. Avoid
retraining sources or rerunning all historical experiments for routine operation.
Run focused checks when making changes; keep the version and evidence for any
modified model distinct from this pinned candidate.

The package is a useful starting point for experiments and modification. A new
claim or changed scope needs corresponding evidence. Announcement and distribution
channels are handled separately from this technical artifact.
