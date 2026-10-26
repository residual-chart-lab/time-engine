# AI handoff — use a correction in your own conversation

Purpose: let a concrete question change which evidence you inspect next.
This is an experimental companion to E4, not the frozen P0 package itself.

Do this for one actual correction, not for a personality score.

1. Choose the next question first. Use current_response, change, retained_basis,
   or next_action as its observation focus.
2. Make a case JSON using examples/correction-relayed-case.json as the schema.
   Copy source excerpts exactly. Keep original turns and later accounts distinct.
   Missing turns stay missing; dates may be null.
3. Supply b/u/p annotations with yes/no/unknown and exact quotes. These are your
   interpretations. For p, a later self-description is not proof of earlier intent.
   For a, separate an utterance, a proposal, and a report of execution.
   Do not ask the human to format JSON or count characters for you.
4. Run:
   python -I -B run_correction_observer.py --case YOUR_CASE.json --output-dir NEW_DIR
5. Act on reading_plan:
   - Source already present? Read it and add the relevant anchor.
   - Source absent? Request only the necessary excerpt, or retain unknown.
   - Only a proposal/report of execution? Do not say it actually ran.
   - Reviewable quotes? Check your interpretation against them, then answer within
     that scope. Do not halt all useful conversation merely because one claim is unknown.
6. Record what you actually did after seeing the report. An announced intention is
   not the same as doing it. Make a new case version for new evidence; retain the old one.

For E4 receipt, send E4-commands.jsonl through the ordinary E4 operation surface.
Check remaining command budget first if using an existing episode. The commands
only record sources, observations, and a question; they leave the math UNMAPPED.
They cannot authorize execution or substitute a conversation feature for E1 s/t.

Do not report this source check as:
- an automatic understanding of the conversation,
- a successful numerical TE execution,
- a verified enduring intention/personality,
- an empirical improvement in AI behavior.

A useful first result may be:
"I can quote what was said later, but I need the earlier turn before claiming
that the same basis survived. The earlier source is already here, so I will read
it rather than ask you to resend it."

Use the tool to change the next concrete check, not merely to explain the tool.
Protocol and input hashes are in the output. For a new held-out test, freeze
the question and protocol before collecting its result.

