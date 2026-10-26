# AI handoff — execute a source-backed reply

Use this when a future question needs a supported account of a prior correction.
This family constrains a concrete reply operation; it does not score personality.

1. Pick a concrete question before inspecting which route succeeds.
2. Prepare an observer-format case from actual source excerpts and your annotations.
   Preserve unknowns and distinguish original turns from retrospective accounts.
3. Compile it:
   python -I -B run_source_reply.py compile --case YOUR_CASE.json --output-dir NEW_PACKETS
4. Start the recipient runtime with a bundle and its external MANIFEST hash:
   python -I -B run_source_reply.py run --bundle NEW_PACKETS/retained.bundle.json --trusted-sha256 HASH
5. Bind either current_response or retained_basis, with the actual question.
6. Read plans. Choose a current enabled operation:
   - answer: construct a source-backed answer under the declared annotation;
   - review: inspect a supplied original;
   - ask: request a missing original;
   - defer: leave the requirement open.
7. Choose its id, resolve, then advance with the new permit.
   The emitted body is a real constructed reply artifact. It has not been posted.
8. Use the reply if appropriate and record what you actually did, not only an intention.

An answer certificate covers the exact body, citations and this finite contract.
It does not certify the annotator's semantics, psychological continuity, or source
provenance in the outside world. Requests and deferrals close an operation while
leaving the requirement unsatisfied.

For a retention comparison, give the recipient only the chosen packet.
Do not secretly include the withheld source in a prompt, an annotation explanation,
a task hint, or a source copy while claiming it was absent. The compiler model
contains only reference metadata/hashes, not the omitted quotations.
Keep the original archive at the operator side.

Save checkpoints to new files and keep their SHA outside the checkpoint.
A supplied source must match a declared missing slot. After a closed operation,
bind the next response; do not rewrite the old one.

The E4 ledger retains this source-family execution. The E1 numerical backend stays
UNBOUND; its certification is not being reused for this new family.

Try one new conversation. Record:
- the future question fixed before selection,
- which source packet was actually available,
- all available plans and the plan you chose,
- the emitted reply and whether you actually used it,
- what changed in your next action.

The bundled example uses a fixed driver policy, not an independent AI behavior trial.

