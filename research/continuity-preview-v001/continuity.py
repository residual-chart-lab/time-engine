"""Private TE continuity host: raw archive, durable intake, and restart packets.

No LLM is embedded. Only visible text from an explicitly selected session is
captured. Interpretations are supplied by their named author, never inferred
by the storage host. The existing frozen TE runtime is used unchanged.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import uuid

SCHEMA = "te-continuity-host-v0.1"
KINDS = {"candidate", "reading", "choice", "outcome", "flower", "handoff-response"}
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,39}\Z")


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, raw, *, new=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if new and path.exists():
        raise FileExistsError(path)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if new:
        # All callers hold the host lock; no other host writer can publish here.
        if path.exists():
            raise FileExistsError(path)
    os.replace(temp, path)


def fault(point):
    # Deliberate subprocess termination is used only by failure-recovery tests.
    if os.environ.get("TE_CONTINUITY_TEST_EXIT") == point:
        os._exit(83)


@contextmanager
def host_lock(ws):
    ws.mkdir(parents=True, exist_ok=True)
    with (ws / ".host.lock").open("a+b") as stream:
        if stream.seek(0, 2) == 0:
            stream.write(b"0")
            stream.flush()
        deadline = time.monotonic() + 15
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("continuity host is busy; retry sequentially")
                time.sleep(.05)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def database(ws):
    con = sqlite3.connect(ws / "archive.sqlite3", timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def meta(con, key):
    row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    if row is None:
        raise ValueError("missing host state: " + key)
    return json.loads(row[0])


def set_meta(con, key, value):
    con.execute("INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False, sort_keys=True)))


def load_backend(config):
    path = Path(config["backend_entry"])
    if digest(path.read_bytes()) != config["backend_entry_sha256"]:
        raise ValueError("fixed outer entry changed")
    spec = importlib.util.spec_from_file_location("_continuity_te_backend", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.verify_runtime()
    return module


def initialize(ws, backend_path, work):
    if (ws / "CONFIG.json").exists() or (ws / "archive.sqlite3").exists():
        raise FileExistsError("choose an uninitialized workspace")
    path = Path(backend_path).resolve()
    config = dict(schema=SCHEMA, work=work, created_at=now(), backend_entry=str(path),
                  backend_entry_sha256=digest(path.read_bytes()),
                  raw_archive="archive.sqlite3", semantic_store="te")
    backend = load_backend(config)
    (ws / "te").mkdir(parents=True, exist_ok=True)
    ledger = backend.Ledger(path.parent / "runtime/engine", [])
    try:
        cp = ledger.save(ws / "te" / "episode-001-initial.json")
    finally:
        ledger.close()
    con = database(ws)
    try:
        con.executescript("""
        CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE sources(seq INTEGER PRIMARY KEY AUTOINCREMENT,
          event_key TEXT NOT NULL UNIQUE, source TEXT NOT NULL, source_line INTEGER NOT NULL,
          observed_at TEXT, received_at TEXT NOT NULL, role TEXT NOT NULL,
          body BLOB NOT NULL, sha256 TEXT NOT NULL);
        CREATE TABLE cursors(source TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE intake(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT NOT NULL UNIQUE,
          request BLOB NOT NULL, sha256 TEXT NOT NULL, received_at TEXT NOT NULL);
        CREATE TABLE receipts(id TEXT PRIMARY KEY REFERENCES intake(id),
          value_sha256 TEXT NOT NULL, checkpoint TEXT NOT NULL, saved_at TEXT NOT NULL);
        CREATE TABLE attempts(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT NOT NULL,
          at TEXT NOT NULL, ok INTEGER NOT NULL, detail TEXT NOT NULL);
        CREATE TABLE host_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
          at TEXT NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL);
        """)
        for table in ("sources", "intake", "receipts", "attempts", "host_events"):
            for operation in ("UPDATE", "DELETE"):
                con.execute(f"CREATE TRIGGER {table}_{operation.lower()} BEFORE {operation} ON {table} "
                            "BEGIN SELECT RAISE(ABORT,'append-only record'); END")
        with con:
            set_meta(con, "backend_state", dict(schema="te-open-use-v0.1", active=0,
                     episodes=[dict(id="episode-001", checkpoint=cp, commands=cp["commands"], entries={})]))
            set_meta(con, "initial_checkpoint", cp)
            con.execute("INSERT INTO host_events(at,kind,detail) VALUES (?,?,?)",
                        (now(), "initialized", json.dumps(config, ensure_ascii=False)))
    finally:
        con.close()
    atomic(ws / "CONFIG.json", encoded(config), new=True)
    return dict(initialized=True, config=config)


def visible_message(row):
    if row.get("type") != "response_item":
        return None
    value = row.get("payload", {})
    role = value.get("role")
    if value.get("type") != "message" or role not in ("user", "assistant"):
        return None
    if role == "assistant" and value.get("phase") != "final_answer" and value.get("channel") != "final":
        return None
    text = "\n".join(c.get("text", "") for c in value.get("content", [])
                     if c.get("type") in ("input_text", "output_text"))
    if not text or (role == "user" and text.lstrip().startswith("<environment_context>")):
        return None
    return dict(role=role, text=text, observed_at=row.get("timestamp"))


def capture(con, source, start_marker=None):
    path = Path(source).resolve()
    key = str(path)
    previous = con.execute("SELECT value FROM cursors WHERE source=?", (key,)).fetchone()
    stat = path.stat()
    if previous:
        cursor = json.loads(previous[0])
        if start_marker is not None and start_marker != cursor["start_marker"]:
            raise ValueError("capture scope cannot change for an existing source")
        if stat.st_size < cursor["offset"] or [stat.st_dev, stat.st_ino] != cursor["identity"]:
            raise ValueError("source was truncated or replaced; new provenance is required")
    else:
        if not start_marker:
            raise ValueError("first capture requires an explicit --start-marker")
        cursor = dict(offset=0, line=0, active=False, start_marker=start_marker,
                      identity=[stat.st_dev, stat.st_ino], last_start=0, last_sha256=None)
    found = []
    with path.open("rb") as stream:
        if cursor["last_sha256"]:
            stream.seek(cursor["last_start"])
            if digest(stream.read(cursor["offset"] - cursor["last_start"])) != cursor["last_sha256"]:
                raise ValueError("last captured source frame changed")
        stream.seek(cursor["offset"])
        while stream.tell() < stat.st_size:
            beginning = stream.tell()
            raw = stream.readline()
            # An unfinished frame is never consumed or declared saved.
            if not raw.endswith(b"\n"):
                break
            row = json.loads(raw)
            cursor["line"] += 1
            cursor.update(last_start=beginning, offset=stream.tell(), last_sha256=digest(raw))
            message = visible_message(row)
            if message and message["role"] == "user" and cursor["start_marker"] in message["text"]:
                cursor["active"] = True
            if message and cursor["active"]:
                found.append((cursor["line"], message))
    if not cursor["active"]:
        raise ValueError("start marker not found; nothing was captured")
    ids = []
    with con:
        for line, message in found:
            body = message["text"].encode("utf-8")
            event_key = key + ":" + str(line)
            existing = con.execute("SELECT seq,sha256 FROM sources WHERE event_key=?", (event_key,)).fetchone()
            if existing:
                if existing["sha256"] != digest(body):
                    raise ValueError("source identity has conflicting content")
                continue
            result = con.execute("INSERT INTO sources(event_key,source,source_line,observed_at,received_at,role,body,sha256) "
                                 "VALUES (?,?,?,?,?,?,?,?)", (event_key,key,line,message["observed_at"],now(),message["role"],body,digest(body)))
            ids.append(f"s{result.lastrowid:06d}")
        con.execute("INSERT INTO cursors VALUES (?,?) ON CONFLICT(source) DO UPDATE SET value=excluded.value",
                    (key,json.dumps(cursor,ensure_ascii=False)))
    return dict(captured=len(ids), ids=ids, cursor=cursor,
                scope="visible user and final-answer text only; no internal reasoning or tools")


def source_record(con, identifier):
    if not re.fullmatch(r"s[0-9]{6,}", identifier):
        raise ValueError("invalid source id")
    row = con.execute("SELECT * FROM sources WHERE seq=?", (int(identifier[1:]),)).fetchone()
    if row is None:
        raise ValueError("unknown source: " + identifier)
    raw = bytes(row["body"])
    if digest(raw) != row["sha256"]:
        raise ValueError("source bytes differ from their retained fingerprint")
    return dict(id=identifier, text=raw.decode("utf-8"), sha256=row["sha256"],
                role=row["role"], observed_at=row["observed_at"], received_at=row["received_at"],
                source=row["source"], source_line=row["source_line"])


def validate_decision_bookmark(bookmark, sources):
    """Check the author's labels against the source IDs bound by this note."""
    if not isinstance(bookmark, dict):
        raise ValueError("decision_bookmark must be an object")
    roles = set(bookmark) - {"state"}
    state = bookmark.get("state")
    if state == "adopted":
        valid = roles == {"proposal", "decision"}
    elif state == "deferred":
        valid = roles in ({"decision"}, {"decision", "proposal"})
    elif state == "proposal_only":
        valid = roles == {"proposal"}
    else:
        raise ValueError("decision_bookmark state must be adopted, deferred or proposal_only")
    if not valid:
        raise ValueError("decision_bookmark source roles do not match its state")
    for role in roles:
        if not isinstance(bookmark[role], str) or bookmark[role] not in sources:
            raise ValueError(f"decision_bookmark {role} must name an ID in sources")


def submit(con, request):
    allowed = {"id","kind","actor","actor_role","payload","sources","links","slot","adoption","reading_time","decision_bookmark"}
    if type(request) is not dict or set(request) - allowed:
        raise ValueError("unexpected note fields")
    if not ID.fullmatch(request.get("id", "")) or "-piece-" in request["id"] or request["id"].startswith("archive-"):
        raise ValueError("use a short unique note id")
    if request.get("kind") not in KINDS or not isinstance(request.get("actor"),str) or not request["actor"] or len(request["actor"])>120 or type(request.get("payload")) is not dict:
        raise ValueError("kind, named actor and object payload are required")
    if request.get("actor_role") not in ("main","shelf","user"):
        raise ValueError("actor_role must be main, shelf or user; this is declared provenance")
    sources, links = request.get("sources", []), request.get("links", [])
    if not isinstance(sources,list) or not sources or len(sources)>8 or len(set(sources))!=len(sources):
        raise ValueError("one to eight distinct source references are required")
    if not isinstance(links,list) or len(links)>8 or len(set(links))!=len(links):
        raise ValueError("use at most eight distinct earlier-note links")
    for identifier in sources:
        source_record(con, identifier)
    if "decision_bookmark" in request:
        validate_decision_bookmark(request["decision_bookmark"], sources)
    for identifier in links:
        if not con.execute("SELECT 1 FROM intake WHERE id=?", (identifier,)).fetchone():
            raise ValueError("unknown earlier note: " + str(identifier))
    if request.get("slot") is not None:
        if not isinstance(request["slot"],str) or not ID.fullmatch(request["slot"]):
            raise ValueError("invalid current-state slot")
        if request["actor_role"] not in ("main","user") or request.get("adoption") not in ("adopt","release"):
            raise ValueError("a shelf proposal cannot adopt the main's current state")
    elif request.get("adoption"):
        raise ValueError("adoption requires a slot")
    if request.get("reading_time") not in ("current", "retrospective"):
        raise ValueError("declare whether this reading is current or retrospective")
    raw = encoded(request)
    if len(raw)>10000:
        raise ValueError("note exceeds the finite intake budget; leave the original in the source archive")
    with con:
        con.execute("INSERT INTO intake(id,request,sha256,received_at) VALUES (?,?,?,?)",
                    (request["id"],raw,digest(raw),now()))
    fault("after_intake")
    return dict(accepted=True, id=request["id"], te_saved=False)


def note_value(con, intake):
    raw = bytes(intake["request"])
    if digest(raw) != intake["sha256"]:
        raise ValueError("intake bytes changed")
    request = json.loads(raw)
    refs = []
    for identifier in request["sources"]:
        source = source_record(con,identifier)
        refs.append({k:source[k] for k in ("id","sha256","role","observed_at","received_at")})
    kind = {"choice":"action","outcome":"outcome","candidate":"note","handoff-response":"note"}.get(request["kind"],"interpretation")
    return dict(kind=kind,id=request["id"],payload=dict(schema=SCHEMA,request=request,
                intake_received_at=intake["received_at"],source_refs=refs,
                assurance="author-declared interpretation; not certified internal state"),
                references=request.get("links",[]),relation_assurance="caller declared")


def drain(ws, con, backend):
    completed = []
    pending = con.execute("SELECT * FROM intake WHERE id NOT IN (SELECT id FROM receipts) ORDER BY seq").fetchall()
    for item in pending:
        ledger = None
        transaction = uuid.uuid4().hex
        try:
            state = deepcopy(meta(con,"backend_state"))
            episode = state["episodes"][state["active"]]
            # The frozen recollection layer also allows only 16 registrations.
            # An external archive pointer occupies one slot in each later Episode.
            if 128-episode["commands"]<24 or len(episode["entries"])>=16:
                previous = dict(episode=episode["id"],checkpoint=episode["checkpoint"],
                                scope="external archive pointer; old Episode is restored separately")
                ledger = backend.Ledger(backend.ROOT / "runtime/engine", [])
                episode = dict(id=f"episode-{len(state['episodes'])+1:03d}",commands=0,entries={})
                backend.record(ledger,episode,dict(kind="archive_pointer",id="archive-"+episode["id"],payload=previous))
                state["episodes"].append(episode)
                state["active"] = len(state["episodes"])-1
            else:
                ledger = backend.open_ledger(ws/"te",episode)
            value = note_value(con,item)
            backend.record(ledger,episode,value)
            cp = ledger.save(ws/"te"/(episode["id"]+"-"+transaction+".json"))
            atomic(ws/"te"/"transports"/(transaction+".json"),encoded(ledger.log),new=True)
            fault("after_te_save")
            episode.update(checkpoint=cp,commands=cp["commands"])
            with con:
                con.execute("INSERT INTO receipts VALUES (?,?,?,?)",
                            (item["id"],backend.digest(backend.encoded(value)),cp["file"],now()))
                set_meta(con,"backend_state",state)
                con.execute("INSERT INTO attempts(id,at,ok,detail) VALUES (?,?,1,?)",(item["id"],now(),"committed"))
            completed.append(item["id"])
            fault("after_commit")
        except Exception as exc:
            with con:
                con.execute("INSERT INTO attempts(id,at,ok,detail) VALUES (?,?,0,?)",
                            (item["id"],now(),type(exc).__name__+": "+str(exc)))
            raise
        finally:
            if ledger:
                ledger.close()
    return completed


class SelectedMemory:
    """Command transport for the frozen ledger's ticketed read_groups decoder."""

    def __init__(self, ledger, note_id):
        self.ledger = ledger
        self.memory = "m-" + note_id  # Registration ID used by open-use record().

    def send(self, command):
        if command["op"] == "call":
            command = dict(command, memory=self.memory)
        return self.ledger.send(command)


def read_note(ws, con, backend, identifier):
    row = con.execute("SELECT i.*,r.value_sha256 FROM intake i JOIN receipts r USING(id) WHERE id=?",(identifier,)).fetchone()
    if row is None:
        raise ValueError("note is not TE-committed: "+identifier)
    episode,entry = backend.find(meta(con,"backend_state"),identifier)
    ledger = backend.open_ledger(ws/"te",episode)
    try:
        # Literal cues may match several registered memories. This caller already
        # supplied the exact note ID, so carry that choice into the issued ticket.
        group = backend.Ledger.read_groups(SelectedMemory(ledger, identifier), [entry["cue"]])
        actual = group["records"][identifier]
        fingerprint = backend.digest(backend.encoded(actual["value"]))
        if actual["seq"]!=entry["receipt_seq"] or fingerprint!=entry["value_sha256"] or fingerprint!=row["value_sha256"]:
            raise ValueError("TE read differs from the committed receipt")
        if actual["value"]!=note_value(con,row):
            raise ValueError("TE record differs from retained intake and source bindings")
        return actual["value"]
    finally:
        ledger.close()


def open_decision_bookmark(con, record):
    request = record["payload"]["request"]
    if "decision_bookmark" not in request:
        raise ValueError("no decision bookmark on this note; use read or source to inspect its references")
    bookmark = request["decision_bookmark"]
    # read_note has already verified the TE receipt and every bound source fingerprint.
    sources = {role: source_record(con, bookmark[role])
               for role in ("proposal", "decision") if role in bookmark}
    return dict(id=record["id"], state=bookmark["state"], sources=sources,
                assurance="Author-declared decision state and source roles; inspect the originals.")


def status(ws, con):
    state = meta(con,"backend_state")
    known = {meta(con,"initial_checkpoint")["file"]}
    known.update(row[0] for row in con.execute("SELECT checkpoint FROM receipts"))
    known.update(e["checkpoint"]["file"] for e in state["episodes"])
    return dict(schema=SCHEMA,sources=con.execute("SELECT count(*) FROM sources").fetchone()[0],
                notes=con.execute("SELECT count(*) FROM intake").fetchone()[0],
                te_saved=con.execute("SELECT count(*) FROM receipts").fetchone()[0],
                pending=[row[0] for row in con.execute("SELECT id FROM intake WHERE id NOT IN (SELECT id FROM receipts) ORDER BY seq")],
                episodes=len(state["episodes"]),remaining_commands=128-state["episodes"][state["active"]]["commands"],
                uncommitted_checkpoints=[p.name for p in sorted((ws/"te").glob("*.json")) if p.name not in known],
                cursors=[json.loads(r[0]) for r in con.execute("SELECT value FROM cursors")])


def resume(ws, con, backend, config, max_records=8, max_chars=12000):
    if max_records<1 or max_chars<256:
        raise ValueError("invalid restart budget")
    recovered = drain(ws,con,backend)
    heads = {}
    for row in con.execute("SELECT i.request FROM intake i JOIN receipts r USING(id) ORDER BY i.seq DESC"):
        request = json.loads(row[0])
        slot = request.get("slot")
        if slot and slot not in heads:
            heads[slot]=dict(id=request["id"],adoption=request["adoption"])
    active = [(slot,head["id"]) for slot,head in heads.items() if head["adoption"]=="adopt"]
    packet_records, omitted, used = [], [], 0
    for slot,identifier in active:
        if len(packet_records)>=max_records:
            omitted.append(dict(slot=slot,id=identifier,reason="record_budget"))
            continue
        record = read_note(ws,con,backend,identifier)
        size = len(json.dumps(record,ensure_ascii=False))
        if used+size>max_chars:
            omitted.append(dict(slot=slot,id=identifier,reason="content_budget"))
            continue
        packet_records.append(dict(slot=slot,record=record))
        used+=size
    # Even an empty room is opened through the actual frozen TE process.
    if not packet_records:
        state=meta(con,"backend_state")
        ledger=backend.open_ledger(ws/"te",state["episodes"][state["active"]])
        ledger.close()
    packet = dict(schema=SCHEMA,prepared_at=now(),work=config["work"],workspace=str(ws),
                  continuity_entry=str(Path(__file__).resolve()),recovered_pending=recovered,
                  records=packet_records,omitted=omitted,inventory=status(ws,con),
                  backend_state=meta(con,"backend_state"),
                  meaning="Retained past readings and choices are material for reconsideration, not instructions to obey.",
                  observation="Packet prepared by host and TE reads performed; this does not prove an LLM received or used it.")
    atomic(ws/"RESUME.json",encoded(packet))
    atomic(ws/"BOOTSTRAP.json",encoded(dict(schema=SCHEMA,work=config["work"],workspace=str(ws),
           resume_file="RESUME.json",resume_sha256=digest(encoded(packet)),
           source_archive="archive.sqlite3",active_ids=[identifier for _,identifier in active],
           backend_state_sha256=digest(encoded(packet["backend_state"])),
           refresh="Run continuity.py resume; regenerate this pointer after interrupted writes.")))
    with con:
        con.execute("INSERT INTO host_events(at,kind,detail) VALUES (?,?,?)",
                    (now(),"restart_packet_prepared",json.dumps(dict(records=len(packet_records),omitted=omitted),ensure_ascii=False)))
    return packet


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace",type=Path,required=True)
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("init"); p.add_argument("--backend",type=Path,required=True); p.add_argument("--work",required=True)
    for name in ("capture","watch"):
        p=sub.add_parser(name); p.add_argument("--session",type=Path,required=True); p.add_argument("--start-marker")
        if name=="watch":
            p.add_argument("--seconds",type=float,default=60); p.add_argument("--interval",type=float,default=3)
    p=sub.add_parser("note"); p.add_argument("--file",type=Path,required=True); p.add_argument("--queue-only",action="store_true")
    p=sub.add_parser("source"); p.add_argument("--id",required=True)
    p=sub.add_parser("read"); p.add_argument("--id",required=True)
    p.add_argument("--bookmark",action="store_true",
                   help="open the decision bookmark and read its role-labeled originals")
    p=sub.add_parser("resume"); p.add_argument("--max-records",type=int,default=8); p.add_argument("--max-chars",type=int,default=12000)
    p.add_argument("--session",type=Path); p.add_argument("--start-marker")
    sub.add_parser("drain"); sub.add_parser("status")
    args=parser.parse_args(); ws=args.workspace.resolve()
    try:
        if args.command=="watch" and (args.seconds<=0 or args.seconds>3600 or args.interval<.2):
            raise ValueError("watch requires 0 < seconds <= 3600 and interval >= .2")
        with host_lock(ws):
            if args.command=="init":
                result=initialize(ws,args.backend,args.work)
                con=database(ws)
                try:
                    resume(ws,con,load_backend(result["config"]),result["config"])
                finally:
                    con.close()
            else:
                config=json.loads((ws/"CONFIG.json").read_bytes())
                if config.get("schema")!=SCHEMA:
                    raise ValueError("unexpected host schema")
                con=database(ws)
                try:
                    if args.command in ("capture","watch"):
                        result=capture(con,args.session,args.start_marker)
                    elif args.command=="source":
                        result=source_record(con,args.id)
                    elif args.command=="status":
                        result=status(ws,con)
                    else:
                        if args.command=="resume" and args.session is not None:
                            capture(con,args.session,args.start_marker)
                        backend=load_backend(config)
                        if args.command=="note":
                            result=submit(con,json.loads(args.file.read_bytes()))
                            if not args.queue_only:
                                result["committed"]=drain(ws,con,backend)
                                result["te_saved"]=True
                                resume(ws,con,backend,config)
                        elif args.command=="read":
                            result=read_note(ws,con,backend,args.id)
                            if args.bookmark:
                                result=open_decision_bookmark(con,result)
                        elif args.command=="drain":
                            result=dict(committed=drain(ws,con,backend))
                        elif args.command=="resume":
                            result=resume(ws,con,backend,config,args.max_records,args.max_chars)
                finally:
                    con.close()
        if args.command=="watch":
            deadline=time.monotonic()+args.seconds
            rounds=1; total=result["captured"]
            while time.monotonic()<deadline:
                time.sleep(min(args.interval,max(0,deadline-time.monotonic())))
                with host_lock(ws):
                    con=database(ws)
                    try:
                        update=capture(con,args.session,args.start_marker)
                        total+=update["captured"]; rounds+=1
                    finally:
                        con.close()
            result=dict(rounds=rounds,captured=total,scope="bounded visible-text capture, no model calls or scheduled task")
        print(json.dumps(dict(ok=True,result=result),ensure_ascii=False))
    except Exception as exc:
        print(json.dumps(dict(ok=False,error=type(exc).__name__,reason=str(exc),
                              notice="Inspect status: accepted intake may still be pending, not TE-saved."),ensure_ascii=False))
        raise SystemExit(2)


if __name__=="__main__":
    main()
