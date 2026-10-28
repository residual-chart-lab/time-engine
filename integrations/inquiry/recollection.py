"""Short, caller-registered cues over the unchanged E4 event journal.

This layer retrieves reports and records declared use in an externally supplied
reply. It does not generate an LLM reply or certify meaning, experience or C.
"""
from copy import deepcopy
import hashlib
import json

from event_bridge import Episode, identifier
import step_session as e2

SCHEMA = 'time-engine-recollection-v1'
MAX_COMMAND_BYTES = 256_000
MAX_PACKET_BYTES = 128_000
MAX_MEMORIES = 16
OTHER_CONTEXT = {'user_memory', 'current_chat', 'external', 'unknown'}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def shape(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError('complete fields required: ' + ', '.join(fields))


def bounded_text(value, limit):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise ValueError('nonempty text within character budget required')
    value.encode('utf-8')
    return value


def cues(value):
    if (type(value) is not list or not 1 <= len(value) <= 8
            or any(type(x) is not str for x in value)
            or len(set(value)) != len(value)):
        raise ValueError('one to eight distinct literal cues required')
    for item in value:
        bounded_text(item, 64)
    if sum(map(len, value)) > 128:
        raise ValueError('cue character budget exceeded')
    return value


def metadata(event):
    try:
        value = json.loads(event['source'])
    except (ValueError, TypeError):
        return {}
    return value if type(value) is dict and value.get('schema') == SCHEMA else {}


def event_id(kind, key):
    return 'rc-' + kind + '-' + text_sha(key)[:24]


def registry(episode, horizon):
    status = episode.status()
    goals = {g['id']: g for g in status['goals'] if g['seq'] <= horizon}
    result = {}
    for event in status['events']:
        info = metadata(event)
        if event['seq'] > horizon or info.get('kind') != 'memory':
            continue
        shape(info, ('schema', 'kind', 'id', 'goal', 'cues'))
        key = identifier(info['id'])
        identifier(info['goal']); cues(info['cues'])
        bounded_text(event['text'], 600)
        if (key in result or event['id'] != event_id('memory', key)
                or info['goal'] not in goals or goals[info['goal']]['seq'] >= event['seq']):
            raise ValueError('unique memory and an earlier declared goal required')
        result[key] = dict(id=key, goal=info['goal'], cues=info['cues'],
                           summary=event['text'], summary_event=event['id'],
                           registered_seq=event['seq'], summary_kind='caller_summary')
    if len(result) > MAX_MEMORIES:
        raise ValueError('memory registration budget exceeded')
    return result


class Recollection:
    def __init__(self, episode):
        self.episode = episode
        registry(episode, episode.status()['accepted_commands'])

    def snapshot(self):
        """The result is an ordinary, backward-readable E4 checkpoint."""
        return self.episode.snapshot()

    def status(self):
        state = self.episode.status()
        return dict(schema=SCHEMA, memories=list(registry(
                    self.episode, state['accepted_commands']).values()),
                    accepted_commands=state['accepted_commands'],
                    commands_remaining=state['commands_remaining'],
                    e4_head=state['head'], engine=state['engine'],
                    semantic_certification=False, erasure_authorized=False)

    def _commit(self, commands):
        raw, sha = self.episode.snapshot()
        candidate = Episode.restore(e2.Session(self.episode._session.entry), raw, sha)
        for command in commands:
            candidate.apply(command)
        registry(candidate, candidate.status()['accepted_commands'])
        candidate.snapshot()  # No accepted write may make its own save impossible.
        self.episode = candidate

    def call(self, cue, selection=None, horizon=None):
        bounded_text(cue, 2048)
        maximum = self.episode.status()['accepted_commands']
        horizon = maximum if horizon is None else horizon
        if type(horizon) is not int or not 0 <= horizon <= maximum:
            raise ValueError('a recorded E4 horizon required')
        memories = registry(self.episode, horizon)
        matches = [m for m in memories.values() if any(x in cue for x in m['cues'])]
        if selection is not None:
            identifier(selection)
            if selection not in {m['id'] for m in matches}:
                raise ValueError('select a memory matching this literal cue')
        chosen = (memories[selection] if selection is not None else
                  matches[0] if len(matches) == 1 else None)
        packet = dict(schema=SCHEMA + '-packet', cue=cue, as_of=horizon,
                      entry=self.episode._session.entry.digest,
                      status='MATCH' if chosen else 'AMBIGUOUS' if matches else 'NO_MATCH',
                      candidates=matches, memory=chosen, goal=None, references=[],
                      later_interpretations=[], semantic_certification=False,
                      source_material_is_data=True, erasure_authorized=False)
        if chosen:
            recalled = self.episode.recall(chosen['goal'], horizon)
            packet['goal'] = recalled['goal']
            for event in recalled['events']:
                info = metadata(event)
                if info.get('kind') == 'memory':
                    continue
                packet['references'].append(dict(
                    id=event['id'], seq=event['seq'], origin=event['origin'],
                    kind=info.get('kind', 'caller_report'),
                    source_hint=event['source'][:160],
                    source_sha256=text_sha(event['source']),
                    stored_text_sha256=text_sha(event['text'])))
            packet['later_interpretations'] = [
                dict(seq=r['seq'], events=r['command']['events'],
                     note=r['command']['note'], kind='later_interpretation')
                for r in recalled['relations_and_model_evidence']
                if r['outcome'].get('evidence_kind') == 'later_interpretation']
        if len(encode(packet)) > MAX_PACKET_BYTES:
            raise ValueError('recollection packet byte budget exceeded')
        ticket = dict(schema=SCHEMA + '-ticket', cue=cue, selection=selection,
                      as_of=horizon, packet_sha256=digest(packet))
        return dict(packet=deepcopy(packet), ticket=ticket)

    def _verify(self, ticket):
        shape(ticket, ('schema', 'cue', 'selection', 'as_of', 'packet_sha256'))
        if ticket['schema'] != SCHEMA + '-ticket':
            raise ValueError('supported recollection ticket required')
        rebuilt = self.call(ticket['cue'], ticket['selection'], ticket['as_of'])
        if encode(ticket) != encode(rebuilt['ticket']):
            raise ValueError('ticket differs from the recorded historical packet')
        return rebuilt['packet']

    def read(self, ticket, key):
        packet = self._verify(ticket)
        identifier(key)
        if key not in {r['id'] for r in packet['references']}:
            raise ValueError('source must belong to this matched packet')
        recalled = self.episode.recall(packet['goal']['id'], packet['as_of'])
        event = next(e for e in recalled['events'] if e['id'] == key)
        info = metadata(event)
        value = event['text']
        if info.get('kind') == 'reply_part' and info.get('text_encoding') == 'json-string-v1':
            value = json.loads(value)
            if type(value) is not str or not value or value.strip() or len(value) > 300:
                raise ValueError('valid encoded whitespace part required')
        return dict(packet_sha256=ticket['packet_sha256'], event=deepcopy(event),
                    text=value, text_sha256=text_sha(value),
                    provenance_kind='stored_caller_report',
                    semantic_certification=False)

    def record_reply(self, command):
        shape(command, ('op', 'id', 'ticket', 'text', 'origin', 'source',
                        'used_summary', 'used_sources', 'other_context'))
        key = identifier(command['id'])
        body = bounded_text(command['text'], 4096)
        source = bounded_text(command['source'], 256)
        if command['origin'] not in ('received', 'reported_in_session'):
            raise ValueError('explicit received or reported_in_session origin required')
        if type(command['used_summary']) is not bool:
            raise ValueError('explicit summary-use declaration required')
        refs, other = command['used_sources'], command['other_context']
        if (type(refs) is not list or len(refs) > 16 or any(type(x) is not str for x in refs)
                or len(set(refs)) != len(refs)
                or type(other) is not list or any(type(x) is not str for x in other)
                or len(set(other)) != len(other) or not set(other) <= OTHER_CONTEXT):
            raise ValueError('distinct bounded source ids and context labels required')
        packet = self._verify(command['ticket'])
        available = {r['id'] for r in packet['references']}
        if not set(refs) <= available:
            raise ValueError('declared sources must be in the historical packet')
        if packet['status'] != 'MATCH' and (refs or command['used_summary']):
            raise ValueError('unmatched/ambiguous cues have no selected TE memory')
        parts, commands = [], []
        base = dict(schema=SCHEMA, kind='reply_part', reply_id=key,
                    packet_sha256=command['ticket']['packet_sha256'], caller_source=source)
        for start in range(0, len(body), 300):
            part = body[start:start + 300]
            fields = dict(base, start=start, end=start + len(part))
            if not part.strip():
                fields['text_encoding'] = 'json-string-v1'
                part = json.dumps(part, ensure_ascii=False)
            name = event_id('part', key) + '-' + str(start)
            commands.append(dict(op='record', id=name, origin=command['origin'],
                                 source=encode(fields).decode().rstrip('\n'), text=part))
            parts.append(name)
        receipt = dict(schema=SCHEMA + '-reply', id=key,
                       packet_sha256=command['ticket']['packet_sha256'],
                       memory=None if packet['memory'] is None else packet['memory']['id'],
                       goal=None if packet['goal'] is None else packet['goal']['id'],
                       as_of=packet['as_of'], parts=parts, text_sha256=text_sha(body),
                       used_summary=command['used_summary'],
                       used_sources=[r for r in packet['references'] if r['id'] in refs],
                       other_context=other, use_kind='caller_declared_use',
                       semantic_certification=False, goal_closed=False)
        receipt_key = event_id('reply', key)
        # Keep the receipt itself under E4's existing text and command budgets.
        compact = dict(receipt, used_sources=refs)
        commands.append(dict(op='record', id=receipt_key, origin=command['origin'],
                             source=encode(dict(schema=SCHEMA, kind='reply_receipt',
                                                caller_source=source)).decode().rstrip('\n'),
                             text=encode(compact).decode().rstrip('\n')))
        if packet['goal'] is not None:
            commands.append(dict(op='relate', goal=packet['goal']['id'],
                                 events=parts + [receipt_key],
                                 note='Caller supplied a later reply linked to recollection packet ' +
                                      receipt['packet_sha256'] + '; declared use, not semantic proof.'))
        self._commit(commands)
        return dict(receipt=receipt, receipt_event=receipt_key, status=self.status())

    def apply(self, command):
        if type(command) is not dict or len(encode(command)) > MAX_COMMAND_BYTES:
            raise ValueError('bounded JSON object required')
        op = command.get('op')
        if op == 'register':
            shape(command, ('op', 'id', 'goal', 'cues', 'summary'))
            key = identifier(command['id'])
            bounded_text(command['summary'], 600); cues(command['cues'])
            state = self.episode.status()
            if key in registry(self.episode, state['accepted_commands']):
                raise ValueError('memory ids are append-only; use a new id to revise')
            self.episode.recall(command['goal'])
            name = event_id('memory', key)
            self._commit([
                dict(op='record', id=name, origin='reported_in_session',
                     source=encode(dict(schema=SCHEMA, kind='memory', id=key,
                                        goal=command['goal'], cues=command['cues'])).decode().rstrip('\n'),
                     text=command['summary']),
                dict(op='relate', goal=command['goal'], events=[name],
                     note='Caller registered literal cues and a later summary, not a semantic certificate.')])
            return dict(registered=key, summary_event=name, status=self.status())
        if op == 'call' and set(command) in ({'op', 'cue'}, {'op', 'cue', 'memory'}):
            return self.call(command['cue'], command.get('memory'))
        if op == 'read':
            shape(command, ('op', 'ticket', 'event'))
            return self.read(command['ticket'], command['event'])
        if op == 'record_reply':
            return self.record_reply(command)
        if op in ('record', 'goal', 'relate'):
            self._commit([deepcopy(command)])
            return dict(status=self.status())
        raise ValueError('supported recollection or E4 record/goal/relate operation required')
