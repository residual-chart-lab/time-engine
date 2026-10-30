"""Experimental clock coordinates and C-relative routes over an unchanged E4.

All route annotations are caller declarations, stored as ordinary E4 records.
No text-to-number map, subjective-duration measure, or new E1 permit is issued.
"""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import calendar
import hashlib
import json
import re

SCHEMA = 'time-engine-woven-time-prototype-v0.1'


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def clock_coordinate(value):
    """A fixed-offset civil-calendar chart; phase never substitutes for cycle id."""
    if value is None:
        return None
    if (type(value) is not str or re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value) is None):
        raise ValueError('explicit date, time and UTC offset required, or null')
    # datetime accepts some malformed offsets by normalizing them. Reject those.
    if value[-1] != 'Z' and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise ValueError('invalid UTC offset')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    utc = dt.astimezone(timezone.utc)
    second = Fraction(dt.microsecond, 1_000_000)
    minute = (dt.second + second) / 60
    hour = (dt.minute + minute) / 60
    day = (dt.hour + hour) / 24
    month = (dt.day - 1 + day) / calendar.monthrange(dt.year, dt.month)[1]
    # Equal angular month panels: this phase is not elapsed SI time / year.
    year = (dt.month - 1 + month) / 12
    ids = [str(dt.year), dt.strftime('%Y-%m'), dt.strftime('%Y-%m-%d'),
           dt.strftime('%Y-%m-%dT%H'), dt.strftime('%Y-%m-%dT%H:%M'),
           dt.strftime('%Y-%m-%dT%H:%M:%S')]
    offset = dt.strftime('%z')
    delta = utc - datetime(1, 1, 1, tzinfo=timezone.utc)
    return dict(original=value, utc=utc.isoformat(), offset=offset,
                instant_us=(delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds,
                chart='fixed-offset-nested-civil-calendar-v1',
                cycles=[dict(scale=scale, cycle_id=cycle + offset,
                             phase=[p.numerator, p.denominator])
                        for scale, cycle, p in zip(
                            ('year', 'month', 'day', 'hour', 'minute', 'second'),
                            ids, (year, month, day, hour, minute, second))])


def _id(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', value):
        raise ValueError('bounded explicit id required')
    return value


def _shape(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError('complete fields required: ' + ', '.join(keys))


def _validate(session, meta):
    state = session.episode.status()
    events = {e['id']: e for e in state['events']}
    goals = {g['id']: g for g in state['goals']}
    if type(meta) is not dict or meta.get('schema') != SCHEMA:
        raise ValueError('supported weave annotation required')
    kind = meta.get('kind')
    if kind == 'passage':
        _shape(meta, ('schema', 'kind', 'event', 'clock', 'boundary'))
        if meta['event'] not in events:
            raise ValueError('passage must reference an already stored source event')
        clock_coordinate(meta['clock'])
        if type(meta['boundary']) is not bool:
            raise ValueError('explicit caller-declared boundary flag required')
    elif kind == 'step':
        _shape(meta, ('schema', 'kind', 'goal', 'from', 'to'))
        if meta['from'] not in events or meta['to'] not in events or meta['from'] == meta['to']:
            raise ValueError('two distinct stored source events required')
        if meta['goal'] not in goals:
            raise ValueError('stored goal required')
        refs = {e['id'] for e in session.episode.recall(meta['goal'])['events']}
        if not {meta['from'], meta['to']} <= refs:
            raise ValueError('step sources must belong to its declared goal')
    elif kind == 'thread':
        _shape(meta, ('schema', 'kind', 'goal', 'start', 'end'))
        if meta['goal'] not in goals or meta['start'] not in events:
            raise ValueError('stored goal and start event required')
        if meta['end'] is not None and meta['end'] not in events:
            raise ValueError('stored end event or null required')
        refs = {e['id'] for e in session.episode.recall(meta['goal'])['events']}
        if meta['start'] not in refs or (meta['end'] is not None and meta['end'] not in refs):
            raise ValueError('thread endpoints must belong to its declared goal')
    else:
        raise ValueError('passage, step or thread annotation required')


def annotate(session, key, meta, note):
    """Validate before the existing transactional Recollection writer is called."""
    _id(key)
    _validate(session, meta)
    if type(note) is not str or not note.strip() or len(note) > 4096:
        raise ValueError('explicit bounded explanation required')
    # Annotation time is the E4 receipt sequence, never an invented event date.
    return session.apply(dict(op='record', id=key, origin='reported_in_session',
                              source=encode(meta).decode().rstrip('\n'), text=note))


def passage(session, key, event, note, clock=None, boundary=False):
    return annotate(session, key, dict(schema=SCHEMA, kind='passage',
                    event=event, clock=clock, boundary=boundary), note)


def step(session, key, goal, before, after, note):
    return annotate(session, key, dict(schema=SCHEMA, kind='step',
                    goal=goal, **{'from': before, 'to': after}), note)


def thread(session, key, goal, start, end, note):
    return annotate(session, key, dict(schema=SCHEMA, kind='thread',
                    goal=goal, start=start, end=end), note)


def _reachable(start, adjacency):
    seen, pending = set(), [start]
    while pending:
        node = pending.pop()
        if node not in seen:
            seen.add(node)
            pending.extend(adjacency.get(node, ()))
    return seen


def view(session, thread_id, horizon=None, resolution='all'):
    """Read all declared start-to-end routes within C's source scope.

    The existing verified E4 provides journal provenance. A route is an explicit
    retrospective reading, not a certified causal necessity or Flower closure.
    """
    _id(thread_id)
    state = session.episode.status()
    maximum = state['accepted_commands']
    horizon = maximum if horizon is None else horizon
    if type(horizon) is not int or not 0 <= horizon <= maximum:
        raise ValueError('recorded horizon required')
    if resolution not in ('all', 'boundaries'):
        raise ValueError('all or boundaries resolution required')
    # Snapshot comes from the supplied live/restored E4 object, not unverified JSON.
    checkpoint, _ = session.snapshot()
    rows = json.loads(checkpoint)['journal'][:horizon]
    annotations = []
    for row in rows:
        cmd = row['command']
        if cmd['op'] != 'record':
            continue
        try:
            meta = json.loads(cmd['source'])
        except (ValueError, TypeError):
            continue
        if type(meta) is dict and meta.get('schema') == SCHEMA:
            # Recheck shape and references when reading imported annotations.
            _validate(session, meta)
            refs = [meta[k] for k in ('event', 'from', 'to', 'start', 'end')
                    if k in meta and meta[k] is not None]
            source_events = {e['id']: e for e in state['events']}
            if any(source_events[k]['seq'] >= row['seq'] for k in refs):
                raise ValueError('annotation refers to a source not yet stored when declared')
            if 'goal' in meta:
                goal = next(g for g in state['goals'] if g['id'] == meta['goal'])
                if goal['seq'] >= row['seq']:
                    raise ValueError('goal was not stored when the annotation was declared')
                prior_refs = {e['id'] for e in session.episode.recall(meta['goal'], row['seq'] - 1)['events']}
                if not set(refs) <= prior_refs:
                    raise ValueError('source was not in this goal when the annotation was declared')
            annotations.append(dict(id=cmd['id'], declared_at=row['seq'],
                                    note=cmd['text'], **deepcopy(meta)))
    found = [a for a in annotations if a['id'] == thread_id and a['kind'] == 'thread']
    if len(found) != 1:
        raise ValueError('thread was not declared by this horizon')
    strand = found[0]
    recalled = session.episode.recall(strand['goal'], horizon)
    if recalled['goal']['seq'] >= strand['declared_at']:
        raise ValueError('thread goal must precede its declaration')
    events = {e['id']: e for e in recalled['events']}
    if strand['start'] not in events or (strand['end'] is not None and strand['end'] not in events):
        raise ValueError('thread endpoints were not in this goal at this horizon')
    links = [a for a in annotations if a['kind'] == 'step' and a['goal'] == strand['goal']
             and a['from'] in events and a['to'] in events]
    adjacency, reverse = {}, {}
    for a in links:
        adjacency.setdefault(a['from'], set()).add(a['to'])
        reverse.setdefault(a['to'], set()).add(a['from'])
    forward = _reachable(strand['start'], adjacency)
    end = strand['end']
    connected = end is not None and end in forward
    selected = forward & _reachable(end, reverse) if connected else forward
    selected_links = [a for a in links if a['from'] in selected and a['to'] in selected]
    # A new visit requires a distinct event id; cycles may not erase visit order.
    incoming = {k: len(reverse.get(k, set()) & selected) for k in selected}
    ready = deque(sorted((k for k, n in incoming.items() if n == 0), key=lambda k: events[k]['seq']))
    ordered = []
    while ready:
        node = ready.popleft()
        ordered.append(node)
        for nxt in sorted(adjacency.get(node, set()) & selected, key=lambda k: events[k]['seq']):
            incoming[nxt] -= 1
            if incoming[nxt] == 0:
                ready.append(nxt)
    if len(ordered) != len(selected):
        raise ValueError('declared route has a cycle; record distinct visits')
    # Multiple annotations never overwrite each other, even for the same event.
    marks = [a for a in annotations if a['kind'] == 'passage' and a['event'] in selected]
    boundary_ids = {a['event'] for a in marks if a['boundary']}
    visible = set(ordered) if resolution == 'all' else boundary_ids | {strand['start'], end}
    source_refs = [dict(id=k, receipt_seq=events[k]['seq'], origin=events[k]['origin'],
                       stored_text_sha256=hashlib.sha256(events[k]['text'].encode()).hexdigest())
                   for k in ordered]
    result = dict(schema=SCHEMA + '-view', thread=strand, as_of=horizon, resolution=resolution,
                  goal=recalled['goal'], route_status='CONNECTED' if connected else 'OPEN' if end is None else 'GAP',
                  source_refs=source_refs, steps=selected_links, passages=marks,
                  clock_annotations=[dict(annotation=a['id'], event=a['event'],
                                          basis='caller_report', declared_at=a['declared_at'],
                                          coordinate=clock_coordinate(a['clock'])) for a in marks],
                  visible_events=[k for k in ordered if k in visible],
                  latent_events=[k for k in ordered if k not in visible],
                  boundary_events=[k for k in ordered if k in boundary_ids],
                  reading_basis='caller_declared_routes', flower_closure='NOT_CERTIFIED',
                  subjective_duration=None, e1_permit_issued=False)
    result['route_sha256'] = sha(dict(goal=recalled['goal'], sources=source_refs, steps=selected_links))
    return result


def read_plan(session, woven_view, recalled):
    """Use the unchanged recollection reader, scoped to this route's originals."""
    rebuilt = view(session, woven_view['thread']['id'], woven_view['as_of'], woven_view['resolution'])
    if sha(rebuilt) != sha(woven_view):
        raise ValueError('view differs from its recorded horizon')
    ticket = recalled['ticket']
    # Rebuild the historical packet through the existing reader's verifier.
    actual = session.call(ticket['cue'], ticket['selection'], ticket['as_of'])
    if actual != recalled or recalled['packet']['status'] != 'MATCH':
        raise ValueError('matched historical recollection packet required')
    if (recalled['packet']['goal']['id'] != woven_view['goal']['id']
            or ticket['as_of'] != woven_view['as_of']):
        raise ValueError('same C and historical horizon required')
    available = {r['id'] for r in recalled['packet']['references']}
    selected = [r['id'] for r in woven_view['source_refs']]
    if not set(selected) <= available:
        raise ValueError('route sources must be in this recollection packet')
    return [dict(op='read', ticket=deepcopy(ticket), event=k) for k in selected]
