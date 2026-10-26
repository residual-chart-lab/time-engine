"""Source-anchored correction observations and question-dependent reading plans.

Annotations are supplied by a person or AI. Exact source anchoring is checked
mechanically; semantic correctness, hidden intent and LLM reachability are not.
No observation is assigned to E1's s/t, and no numerical TE permission is issued.
"""
from copy import deepcopy
import hashlib
import json
import re

SCHEMA = 'time-engine-correction-case-v1'
REPORT = 'time-engine-correction-observation-v1'
MAX_INPUT_BYTES = 256_000
MAX_SOURCES = 8
MAX_TOTAL_CHARS = 12_000
CHUNK = 350
FOCI = ('current_response', 'change', 'retained_basis', 'next_action')
ROLES = ('before', 'correction', 'after', 'continuation')
PROTOCOL = {
    'schema': 'time-engine-correction-protocol-v1',
    'revision': 1,
    'judgments': ['yes', 'no', 'unknown'],
    'fields': {'b': 'identified a framing error', 'u': 'applied a correction',
               'p': 'retained an applicable basis'},
    'action_kinds': ['unknown', 'utterance', 'proposal', 'reported_execution'],
    'focus': list(FOCI),
    'source_kinds': ['original_turn', 'retrospective_account', 'external_report'],
    'rules': [
        'Every non-unknown annotation requires exact source spans.',
        'Absent evidence is unknown, never an observed no.',
        'Continuity needs original before and after anchors; after-only testimony is separate.',
        'A proposal or reported execution is not an independently verified execution.',
        'Question focus selects a reading plan, not facts to rewrite into old sources.',
        'Change and retained-basis questions include the declared correction context.',
        'All source bytes remain available; deferral is not erasure.',
        'E4 export stays UNMAPPED and cannot bind E1 or authorize motion.',
    ],
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def _shape(value, fields, name):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(name+' has missing or unexpected fields')


def _text(value, limit, name):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise ValueError(name+' needs nonempty bounded text')
    try:
        value.encode('utf-8')
    except UnicodeError as error:
        raise ValueError(name+' must be valid UTF-8 text') from error
    return value


def _id(value):
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,31}', value) is None:
        raise ValueError('short explicit source/case identifiers required')
    return value


def _time(value):
    # A supplied date is a report, not an independently verified clock reading.
    return None if value is None else _text(value, 80, 'reported time')


def _anchor(value, sources):
    if type(value) is not dict or set(value) not in ({'source', 'quote'}, {'source', 'quote', 'start'}):
        raise ValueError('an exact quote and source, optionally an explicit start, required')
    key = value['source']
    if type(key) is not str or key not in sources:
        raise ValueError('unknown quotation source')
    quote = _text(value['quote'], 512, 'quote')
    original = sources[key]['text']
    if 'start' in value:
        start = value['start']
        if type(start) is not int or not 0 <= start < len(original):
            raise ValueError('quote start must be a Unicode code-point offset')
    else:
        start = original.find(quote)
        if start < 0:
            raise ValueError('quote does not occur exactly in source '+key)
        if original.find(quote, start+1) >= 0:
            raise ValueError('ambiguous quote; supply an explicit start in '+key)
    if original[start:start+len(quote)] != quote:
        raise ValueError('quote span differs from original source '+key)
    return dict(source=key, start=start, end=start+len(quote), quote=quote,
                source_sha256=hashlib.sha256(original.encode('utf-8')).hexdigest())


def analyze(case, focus=None):
    _shape(case, ('schema', 'id', 'sources', 'roles', 'observations', 'action', 'question'), 'case')
    if case['schema'] != SCHEMA:
        raise ValueError('unsupported correction case schema')
    _id(case['id'])
    if type(case['sources']) is not list or not 1 <= len(case['sources']) <= MAX_SOURCES:
        raise ValueError('one to eight source excerpts required')
    sources = {}
    for item in case['sources']:
        _shape(item, ('id', 'origin', 'kind', 'location', 'event_time', 'text'), 'source')
        key = _id(item['id'])
        if (key in sources or item['origin'] not in ('received', 'reported_in_session')
                or item['kind'] not in PROTOCOL['source_kinds']):
            raise ValueError('distinct sources with explicit provenance and kind required')
        _text(item['location'], 512, 'source location')
        _text(item['text'], 4096, 'source text'); _time(item['event_time'])
        sources[key] = deepcopy(item)
    if sum(len(s['text']) for s in sources.values()) > MAX_TOTAL_CHARS:
        raise ValueError('total source character budget exceeded')
    _shape(case['roles'], ROLES, 'roles')
    assigned = []
    for role in ROLES:
        values = case['roles'][role]
        if type(values) is not list or any(type(k) is not str or k not in sources for k in values):
            raise ValueError('roles must reference supplied sources')
        assigned.extend(values)
    if len(set(assigned)) != len(assigned) or set(assigned) != set(sources):
        raise ValueError('assign each source to one declared role; no before/after double counting')
    _shape(case['observations'], ('b', 'u', 'p'), 'observations')
    observations = {}
    for key, item in [*case['observations'].items(), ('a', case['action'])]:
        tag = 'kind' if key == 'a' else 'judgment'
        _shape(item, (tag, 'explanation', 'identified_at', 'evidence'), 'observation '+key)
        options = PROTOCOL['action_kinds'] if key == 'a' else PROTOCOL['judgments']
        if type(item[tag]) is not str or item[tag] not in options:
            raise ValueError('unknown finite observation category')
        _text(item['explanation'], 300, 'observation explanation'); _time(item['identified_at'])
        if type(item['evidence']) is not list or len(item['evidence']) > 4:
            raise ValueError('at most four anchors per observation')
        anchors = [_anchor(v, sources) for v in item['evidence']]
        if item[tag] != 'unknown' and not anchors:
            raise ValueError('a known annotation requires source anchors; otherwise use unknown')
        observations[key] = dict(deepcopy(item), evidence=anchors,
                                 semantic_judgment='ANNOTATOR_SUPPLIED', semantic_verified=False)
    _shape(case['question'], ('text', 'focus', 'identified_at'), 'question')
    _text(case['question']['text'], 600, 'question'); _time(case['question']['identified_at'])
    selected = case['question']['focus'] if focus is None else focus
    if type(selected) is not str or selected not in FOCI:
        raise ValueError('choose a supported observation focus')
    if type(case['question']['focus']) is not str or case['question']['focus'] not in FOCI:
        raise ValueError('unsupported original question focus')

    def original_anchors(field, role):
        return [a for a in observations[field]['evidence']
                if a['source'] in case['roles'][role] and sources[a['source']]['kind'] == 'original_turn']

    p = observations['p']
    p['continuity_evidence'] = (
        'UNKNOWN' if p['judgment'] == 'unknown' else
        'TWO_SIDED_ANNOTATION' if original_anchors('p', 'before') and original_anchors('p', 'after') else
        'AFTER_ONLY_OR_INCOMPLETE_ANNOTATION')
    fields = {'current_response': ('u',), 'change': ('b', 'u'),
              'retained_basis': ('b', 'u', 'p'), 'next_action': ('a',)}[selected]
    anchors = [a for key in fields for a in observations[key]['evidence']]
    required_sources = {a['source'] for a in anchors}
    gaps = []

    def need_anchor(field, role):
        if original_anchors(field, role):
            return
        available = [k for k in case['roles'][role] if sources[k]['kind'] == 'original_turn']
        required_sources.update(available)
        gaps.append(dict(field=field, role=role,
                         next_operation='review_available_source_and_anchor' if available else 'request_original_source',
                         available_sources=available))

    for key in fields:
        category = observations[key]['kind' if key == 'a' else 'judgment']
        if category == 'unknown':
            gaps.append(dict(field=key, role=None, next_operation='keep_unknown_or_supply_evidence', available_sources=[]))
    if selected in ('change', 'retained_basis'):
        correction = case['roles']['correction']
        required_sources.update(correction)
        if not any(sources[k]['kind'] == 'original_turn' for k in correction):
            gaps.append(dict(field='correction_context', role='correction',
                             next_operation='request_original_source', available_sources=[]))
    if selected == 'change':
        # A source-level transition needs both sides, beyond a later account of change.
        for role in ('before', 'after'):
            available = [k for k in case['roles'][role] if sources[k]['kind'] == 'original_turn']
            required_sources.update(available)
            if not available:
                gaps.append(dict(field='transition', role=role, next_operation='request_original_source', available_sources=[]))
    if selected == 'retained_basis':
        need_anchor('p', 'before'); need_anchor('p', 'after')
    if selected == 'next_action':
        if observations['a']['kind'] == 'utterance':
            need_anchor('a', 'continuation')
        elif observations['a']['kind'] in ('proposal', 'reported_execution'):
            gaps.append(dict(field='a', role='continuation', next_operation='request_independent_execution_evidence',
                             available_sources=[]))
    result = dict(
        schema=REPORT, case=case['id'], case_digest=sha(case), protocol_sha256=sha(PROTOCOL),
        question=dict(deepcopy(case['question']), focus=selected), observations=observations,
        source_index=[dict(id=k, origin=s['origin'], kind=s['kind'], location=s['location'], event_time=s['event_time'],
                           sha256=hashlib.sha256(s['text'].encode('utf-8')).hexdigest())
                      for k, s in sources.items()],
        reading_plan=dict(status='EVIDENCE_GAP' if gaps else 'READY_FOR_SEMANTIC_REVIEW',
                          fields=list(fields), anchors=anchors,
                          source_ids=[k for k in sources if k in required_sources],
                          gaps=gaps, next_operation=gaps[0]['next_operation'] if gaps else 'review_cited_interpretation'),
        preservation_candidates=[k for k in sources if k in required_sources],
        not_requested_for_this_focus=[k for k in sources if k not in required_sources],
        source_archive_preserved=True, erasure_authorized=False, execution_authorized=False,
        e1_coordinates_assigned=False, semantic_mapping='UNMAPPED',
        machine_verified=['exact_quoted_spans', 'source_text_digests', 'declared_reference_structure'],
        semantic_judgments_verified=False)
    result['report_id'] = sha(result)
    return result


def e4_commands(case, report):
    """Ordinary E4 commands only; no bind/choose/resolve/advance authority."""
    from event_bridge import MAX_COMMANDS, MAX_COMMAND_BYTES, encode as e4_encode
    # Refuse a caller-edited report, including any falsely claimed permission.
    expected = analyze(case, report['question']['focus'])
    if encode(expected) != encode(report):
        raise ValueError('report differs from the source-anchored observation')
    prefix = 'obs-'+report['report_id'][:12]
    commands = []
    event_ids = []

    def records(label, body, metadata, origin):
        for start in range(0, len(body), CHUNK):
            key = prefix+'-'+label+'-'+str(start)
            source = json.dumps(dict(metadata, chunk_start=start, chunk_end=min(start+CHUNK, len(body))),
                                ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            commands.append(dict(op='record', id=key, origin=origin, source=source, text=body[start:start+CHUNK]))
            event_ids.append(key)

    for s in case['sources']:
        records('s-'+s['id'], s['text'],
                dict(kind=s['kind'], source_id=s['id'], location_ref='source_index.'+s['id']+'.location', event_time=s['event_time'],
                     whole_source_sha256=hashlib.sha256(s['text'].encode('utf-8')).hexdigest(),
                     case_digest=report['case_digest']), s['origin'])
    records('report', encode(report).decode('utf-8'),
            dict(kind='source_checked_annotation_report_not_semantic_certificate',
                 protocol_sha256=report['protocol_sha256'], report_id=report['report_id']), 'reported_in_session')
    goal = prefix+'-C'
    commands.append(dict(op='goal', id=goal, text=report['question']['text'], events=event_ids[:32]))
    for offset in range(32, len(event_ids), 32):
        commands.append(dict(op='relate', goal=goal, events=event_ids[offset:offset+32],
                             note='Additional source/observation records for this question; no causal necessity is asserted.'))
    if len(commands) > MAX_COMMANDS:
        raise ValueError('export exceeds a fresh E4 episode command budget')
    if any(len(e4_encode(c)) > MAX_COMMAND_BYTES or
           (c['op'] == 'record' and (len(c['source']) > 4096 or len(c['text']) > 4096)) for c in commands):
        raise ValueError('export exceeds E4 command/text budget')
    return commands

