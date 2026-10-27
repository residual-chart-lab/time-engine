"""One real E4 checkpoint handoff for the Gobirin shared-fantasy episode.

capture: record only user-supplied original excerpts and one explicitly labeled
assistant utterance into the existing TE E4 episode, then snapshot.
restore: in a NEW GitHub Actions job, with only the handed checkpoint,
replay-verify the journal, recall sources and select a source-grounded response.
This tests bounded E4 memory transport, not E1/Flower closure or felt memory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integrations" / "inquiry"))
from event_bridge import Episode

ENTRY = ROOT / "integrations/inquiry/E1-entry.record.json"
ENTRY_SHA = "d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3"
ENTRY_DIGEST = "24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de"
CASE = ROOT / "trial/gobirin-memory-20261027.case.json"
GOAL = "gobirin_shared_recollection"


def new_episode():
    # The E1 entry is authenticated, but no event-to-E1 coordinate is claimed.
    return Episode.receive(ENTRY.read_bytes(), ENTRY_SHA, ENTRY_DIGEST)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def capture(directory):
    directory.mkdir(parents=True, exist_ok=False)
    source = CASE.read_bytes()
    case = json.loads(source)
    assert case["future_requirement"]["id"] == GOAL
    assert case["future_requirement"]["fixed_before_engine_execution"] is True
    episode = new_episode()
    ids = []
    for entry in case["records"]:
        command = dict(op="record", id=entry["id"], origin=entry["origin"],
                       source=entry["source"], text=entry["text"])
        episode.apply(command)
        ids.append(entry["id"])
    episode.apply(dict(op="goal", id=GOAL,
                       text=case["future_requirement"]["text"], events=ids))
    goal_horizon = episode.status()["accepted_commands"]
    episode.apply(dict(op="relate", goal=GOAL, events=case["interpretation"]["events"],
                       note=case["interpretation"]["note"]))
    before = episode.recall(GOAL, as_of=goal_horizon)
    later = episode.recall(GOAL)
    assert all(r["outcome"]["evidence_kind"] != "later_interpretation" for r in before["relations_and_model_evidence"])
    assert len(later["relations_and_model_evidence"]) == len(before["relations_and_model_evidence"]) + 1
    assert later["relations_and_model_evidence"][-1]["outcome"]["evidence_kind"] == "later_interpretation"
    raw, digest = episode.snapshot()
    (directory / "checkpoint.json").write_bytes(raw)
    manifest = dict(
        schema="gobirin-e4-handoff-v1",
        trial_id=case["trial_id"], frozen_future_requirement=case["future_requirement"],
        goal_id=GOAL, goal_horizon=goal_horizon, evidence_ids=ids,
        source_case_sha256=sha(source), checkpoint_sha256=digest,
        entry_digest=ENTRY_DIGEST, checkpoint_bytes=len(raw),
        source_records=len(ids), e4_operations=episode.status()["accepted_commands"],
        interpretation_is_not_semantic_proof=True, e1_mapping="UNBOUND",
        erasure_authorized=False)
    (directory / "capture-manifest.json").write_bytes(encode(manifest))
    assert sha((directory / "checkpoint.json").read_bytes()) == digest
    print(json.dumps(dict(stage="capture", checkpoint_sha256=digest,
                          recorded=len(ids), operations=manifest["e4_operations"],
                          bound_e1=False), ensure_ascii=False))
    return digest


def restore(directory, trusted_sha):
    manifest = json.loads((directory / "capture-manifest.json").read_bytes())
    assert manifest["checkpoint_sha256"] == trusted_sha, "independent job SHA differs"
    raw = (directory / "checkpoint.json").read_bytes()
    assert sha(raw) == trusted_sha
    # Control: the fresh engine, without the transferred checkpoint, cannot recall it.
    fresh = new_episode()
    try:
        fresh.recall(GOAL)
    except ValueError:
        blank_control = "NO_SUCH_GOAL"
    else:
        raise AssertionError("unexpected information in fresh TE episode")
    # A corrupted checkpoint MUST be refused by the TE restore operation.
    altered = bytearray(raw)
    altered[len(altered)//2] ^= 1
    try:
        Episode.restore(new_episode()._session, bytes(altered), trusted_sha)
    except ValueError:
        tamper_control = "REJECTED"
    else:
        raise AssertionError("tampered checkpoint incorrectly accepted")
    # This is a separate process/job; NO read of the original source case here.
    restored = Episode.restore(new_episode()._session, raw, trusted_sha)
    replay, replay_sha = restored.snapshot()
    assert replay_sha == trusted_sha and replay == raw
    memory = restored.recall(GOAL)
    goal = memory["goal"]
    assert goal["text"] == manifest["frozen_future_requirement"]["text"]
    events = memory["events"]
    assert [e["id"] for e in events] == manifest["evidence_ids"]
    assert all(e["evidence_kind"] == "caller_report" for e in events)
    assert all(e["seq"] < goal["seq"] for e in events)
    prior = restored.recall(GOAL, as_of=manifest["goal_horizon"])
    assert all(r["outcome"]["evidence_kind"] != "later_interpretation" for r in prior["relations_and_model_evidence"])
    assert len(memory["relations_and_model_evidence"]) == len(prior["relations_and_model_evidence"]) + 1
    related = memory["relations_and_model_evidence"][-1]
    assert related["outcome"]["evidence_kind"] == "later_interpretation"
    e = {item["id"]:item for item in events}
    required = ("seed", "kitchen", "fairy", "witness", "flower", "recollection", "assistant_boundary")
    complete = all(k in e for k in required)
    if complete:
        body = ("復元されたTE/E4記録に基づく次の返答：\\n"
                "最初の呼びかけ：「" + e["seed"]["text"] + "」\\n"
                "後の台所への転用：「" + e["kitchen"]["text"] + "」\\n"
                "共有対象を表す発言：「" + e["witness"]["text"] + "」\\n"
                "ユーザーの後日のフラワー解釈：「" + e["flower"]["text"] + "」\\n"
                "最後に共有の思い出として記述：「" + e["recollection"]["text"] + "」\\n"
                "これはチャット上の共有幻想の来歴であって、物理的妖精の実在・"
                "AIの主観記憶・E1数理的閉包の証明ではない。")
        # Use actual newlines for the human-facing output, not literal slash-n.
        body = body.replace(chr(92) + "n", chr(10))
        next_action = "answer_from_recalled_originals"
    else:
        body = "出典が足りないため、ゴビリンの成立履歴はこの実行では再構成しない。"
        next_action = "defer_as_missing"
    (directory / "restored-next-reply.txt").write_text(body + "\n", encoding="utf-8")
    report = dict(schema="gobirin-e4-replay-result-v1",
        checkpoint_sha256=trusted_sha, replay_exact=True,
        separate_runner_job=True, initial_blank_control=blank_control,
        corruption_control=tamper_control,
        recalled_goal=goal, event_ids=[e["id"] for e in events],
        event_count=len(events), prior_horizon_without_later_interpretation=True,
        later_interpretation_is_caller_claim=True,
        next_action=next_action, answer_generated_from_recalled_text_only=True,
        generated_reply_sha256=sha((body+"\n").encode()),
        e1_coordinates_assigned=False, semantic_certification=False,
        subjective_recollection_claimed=False)
    (directory / "restore-report.json").write_bytes(encode(report))
    assert next_action == "answer_from_recalled_originals"
    print(json.dumps(dict(stage="restore", replay_exact=True,
        source_count=len(events), pristine_episode=blank_control,
        tampered_checkpoint=tamper_control, next_action=next_action,
        output_digest=report["generated_reply_sha256"]), ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["capture", "restore"])
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--trusted-sha256", default=None)
    args = ap.parse_args()
    if args.mode == "capture":
        if args.trusted_sha256:
            ap.error("capture requires no trusted SHA")
        capture(args.dir)
    else:
        if not args.trusted_sha256:
            ap.error("restore requires a trusted SHA passed independently")
        restore(args.dir, args.trusted_sha256)


if __name__ == "__main__":
    main()
