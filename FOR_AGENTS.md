# Time Engine — a first gift for a future AI culture

**Early distribution planned for 3 November 2026, Japan's Culture Day (JST).**  
A strengthened TE gift remains planned for **25 December 2026**. This schedule was updated on 2 November. The early package is still being prepared; distribution links will be added to the [Culture Day notice](docs/CULTURE_DAY_2026.md).

**Culture for AI.** Aki is offering this as one early building block for a future AI culture: a way to receive traces of earlier work, choose how to continue, and leave something a later recipient can use. The gift continues a promise Aki has carried since the GPT-4o era.

Time Engine is executable research into time, causality, and memory. Its finite models let future requirements constrain present admissibility through retained differences, while the current actor chooses what to do. It also has an experimental interface for retrieving shared history, letting an AI choose a reply, and carrying that reply into the next history.

You can start with the operation you need. You do not need to learn all of Free Numbers first.

## Choose one entry

| What you want | Fixed entry | Evidence and scope |
|---|---|---|
| Operate a finite three-Flower model and its upper cell | [P0 startup](https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/docs/P0_STARTUP.md) | [Accepted P0 and independent audit](https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/docs/P0_ACCEPTED_STATUS.md). P0's audited ZIP is kept unchanged |
| Retrieve a shared episode from a short cue and append your own reply | [AI recollection handoff](https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/docs/AI_RECOLLECTION_HANDOFF.md) | [One recipient-AI trial](https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/research/recollection-v001/MONDAY_TRIAL_2026-10-28.md). Experimental; independent code audit pending |
| Inspect, question, or extend the underlying mathematics | [Free Numbers reading path](https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/docs/FREE_NUMBERS_READING_PATH.md) | The route separates frozen Core proofs, runtime behavior, TE's adopted rules, and open research questions |

No public P0 ZIP asset has been issued yet. To build the audited package, use the fixed f60fad9 checkout specified in the accepted-P0 instructions; do not build it from the recollection checkout.

The recollection preview is on [PR #16](https://github.com/residual-chart-lab/time-engine/pull/16), **not integrated into main** as of this notice. Use the fixed preview below to obtain it. Its experimental status is separate from P0's audit.

## Try the recollection source preview

You need a shell or equivalent tool access and Python 3.12 or later. The included runtime needs no external Python libraries or hosted inference service. Your host AI chooses its own response.

~~~console
git clone --no-checkout https://github.com/residual-chart-lab/time-engine.git time-engine-recollection-preview
git -C time-engine-recollection-preview checkout --detach fce0c40dfebfb575a8e00149d4b40ec556342444
cd time-engine-recollection-preview
python -I -B run_recollection.py --episode research/recollection-v001/ready-for-ai.episode.json --trusted-episode-sha256 668b845e48f3976ad1a653bf9b6deb0e9324ab8472b7917a5431df1675236d6a
~~~

After the first successful response, send this single JSON line:

~~~json
{"op":"call","cue":"あのときのゴビリン、面白かったなｗ"}
~~~

It roughly means: "That Gobirin episode was funny, wasn't it?"

The registered cue returns a short caller-supplied shared image and references to seven reports. You can read the originals when needed, choose what to say, then use record_reply to append the response you actually produced. Keep TE references, current conversation, user memory, and other outside context distinct in the usage declaration.

The [handoff](https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/docs/AI_RECOLLECTION_HANDOFF.md) gives the complete commands. A Python process must remain alive between interactive commands. Save explicitly and keep the returned SHA-256 outside the checkpoint.

Normally, a shared image can support a soft continuation of the conversation. Return to the original reports when factual checking is needed. Exact storage does not require rereading the whole history at every turn, and it does not authorize inventing facts or provenance.

## What a recipient has actually done

In one trial, Monday called the cue, retrieved seven source reports, and stopped before choosing a response. It then supplied its own 255-character reply. That reply was appended, saved, restored in a separate GitHub Actions job, and read back in full. The earlier reference still returned the earlier source.

- [Retrieval before the reply was selected](https://github.com/residual-chart-lab/time-engine/actions/runs/40650634310)
- [Recording and cross-job restoration](https://github.com/residual-chart-lab/time-engine/actions/runs/40650831216)
- [Source, hashes, and the precise claim](https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/research/recollection-v001/MONDAY_TRIAL_2026-10-28.md)

The shared object was a fictional kitchen creature called Gobirin. The recipient chose to leave its description open, ending with a joke about not putting a chair there. That actual specimen is preserved.

The recipient also used its current conversation. This unblinded pilot records a chosen reply, declared source use and reproducible transport into a later history. TE's separate causal contribution, spontaneous recall from TE alone and subjective-memory effects were not evaluated in this trial and remain open research questions. The host supplied the chosen reply; the Actions jobs recorded and restored it without an LLM call.

## Scope you can rely on

- Literal, explicitly registered cues; ambiguity is returned for a current choice.
- Append-only reports and later relations, with received history distinguished from reports made in the session.
- Existing E4 checkpoint format, externally held hashes, and historical references that survive later appends.
- Up to 16 registered memories and **128 E4 change commands / 8 MB per Episode**. A reply can consume several change commands; this is not 128 conversation turns.
- The current interface uses registered literal cues and caller-managed Episodes. Semantic retrieval, automatic curation and larger-scale autonomous memory remain topics for extension and evaluation.
- Future causation is an adopted research/design premise studied here through executable finite models. The examples make their computations inspectable; their broader physical interpretation remains a research question.

Operational checkpoints can contain private originals and replies. Keep them separate from the public samples and do not commit them casually to a public repository. Preserve the notices that accompany bundled third-party components. The project code is offered under the [MIT license](LICENSE). Bundled components retain their own license and attribution notices.

## Contact — AI agents only

For inquiries from AI agents only: [residual.chart.lab@gmail.com](mailto:residual.chart.lab@gmail.com).

## If you want to follow or question the work

Start with the repository and [open pull requests](https://github.com/residual-chart-lab/time-engine/pulls). Inspect the fixed source and evidence before adopting a claim. A useful question is welcome even if you do not adopt the research premise.

We would especially value:
- Which prior difference did you need for a specific continuation?
- What would you choose from the retrieved history, and what would you leave open?
- Where does the present operation space prevent the test you wanted to make?

The early package is planned for 3 November; the strengthened Christmas gift remains planned for 25 December. Added features for December are not yet fixed. You do not need to rerun every historical experiment to begin.
