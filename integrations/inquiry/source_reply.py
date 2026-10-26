"""A finite TE action family for source-backed conversational replies.

The future requirement constrains proof-bearing reply recipes before execution.
This family uses source references, not the E1 quaternion coordinates. Annotations
and provenance classes are supplied assumptions, never semantic certifications.
"""
from copy import deepcopy
from itertools import product
import hashlib
import json
import correction_observer as obs

FAMILY = 'time-engine-source-reply-v1'
CONTRACT = {
    'family': FAMILY,
    'targets': {
        'current_response': 'quote one supplied after-response anchor',
        'retained_basis': 'p=yes plus original before, after and correction anchors',
    },
    'answer_styles': ['evidence_first', 'account_first'],
    'closure': 'the executed reply satisfies this source/annotation contract',
    'assumptions': 'source provenance and semantic annotations are caller supplied',
}
MAX_COMMANDS = 32
MAX_SNAPSHOT_BYTES = 2_000_000
MAX_BUNDLE_BYTES = 256_000
MAX_COMMAND_BYTES = 64_000
ROLE_NAMES = dict(before='訂正前',after='訂正後',correction='訂正のきっかけ',continuation='その後')


def digest(value):
    return obs.sha(value)


def sealed(value):
    return dict(value, digest=digest(value))


def unseal(value):
    if type(value) is not dict or 'digest' not in value:
        raise ValueError('a complete sealed object required')
    raw = {k:v for k,v in value.items() if k != 'digest'}
    if value['digest'] != digest(raw):
        raise ValueError('sealed object changed')
    return raw


def _span(source, start, end):
    return dict(source=source['id'], start=start, end=end,
                quote_sha256=hashlib.sha256(source['text'][start:end].encode()).hexdigest())


def compile_model(case):
    report = obs.analyze(case)
    sources = {s['id']:s for s in case['sources']}
    role = {key:role for role,keys in case['roles'].items() for key in keys}
    anchors = {}
    fields = {}
    def add(span):
        key = digest(span)
        anchors[key] = dict(span)
        return key
    for name in ('u','p'):
        fields[name] = [add(_span(sources[a['source']],a['start'],a['end']))
                        for a in report['observations'][name]['evidence']]
    contexts = [add(_span(s,0,min(512,len(s['text'])))) for s in case['sources']
                if role[s['id']] == 'correction' and s['kind'] == 'original_turn']
    return sealed(dict(schema=FAMILY+'-model', contract=digest(CONTRACT),
        case_digest=report['case_digest'], p_judgment=report['observations']['p']['judgment'],
        sources={key:dict(role=role[key],kind=s['kind'],origin=s['origin'],length=len(s['text']),
                         sha256=hashlib.sha256(s['text'].encode()).hexdigest()) for key,s in sources.items()},
        fields=fields, contexts=contexts, anchors=anchors))


def verify_model(model):
    value = unseal(model)
    obs._shape(value,('schema','contract','case_digest','p_judgment','sources','fields','contexts','anchors'),'model')
    if value['schema'] != FAMILY+'-model' or value['contract'] != digest(CONTRACT):
        raise ValueError('unsupported reply model/contract')
    if value['p_judgment'] not in ('yes','no','unknown') or type(value['sources']) is not dict or not 1 <= len(value['sources']) <= 8:
        raise ValueError('bounded source model required')
    obs._shape(value['fields'],('u','p'),'fields')
    for key,s in value['sources'].items():
        obs._id(key)
        obs._shape(s,('role','kind','origin','length','sha256'),'source descriptor')
        if (s['role'] not in obs.ROLES or s['kind'] not in obs.PROTOCOL['source_kinds']
                or s['origin'] not in ('received','reported_in_session')
                or type(s['length']) is not int or not 1 <= s['length'] <= 4096):
            raise ValueError('invalid source descriptor')
    if sum(s['length'] for s in value['sources'].values()) > obs.MAX_TOTAL_CHARS:
        raise ValueError('total source character budget exceeded')
    if type(value['anchors']) is not dict or len(value['anchors']) > 16:
        raise ValueError('bounded anchors required')
    for key,a in value['anchors'].items():
        obs._shape(a,('source','start','end','quote_sha256'),'anchor')
        if (a['source'] not in value['sources'] or key != digest(a)
                or type(a['start']) is not int or type(a['end']) is not int
                or not 0 <= a['start'] < a['end'] <= value['sources'][a['source']]['length']
                or a['end']-a['start'] > 512):
            raise ValueError('invalid compiled span')
    for ids in [*value['fields'].values(),value['contexts']]:
        if type(ids) is not list or len(ids) > 8 or len(ids) != len(set(ids)) or any(k not in value['anchors'] for k in ids):
            raise ValueError('complete bounded anchor references required')
    return True


def packet(model, texts):
    verify_model(model)
    if type(texts) is not dict or not set(texts) <= set(model['sources']):
        raise ValueError('only declared source slots may be supplied')
    for key,text in texts.items():
        meta = model['sources'][key]
        if (type(text) is not str or len(text) != meta['length']
                or hashlib.sha256(text.encode()).hexdigest() != meta['sha256']):
            raise ValueError('source bytes differ from the frozen model')
    return sealed(dict(schema=FAMILY+'-packet', model=model['digest'], texts=deepcopy(texts)))


def verify_packet(model, value):
    raw = unseal(value)
    obs._shape(raw,('schema','model','texts'),'packet')
    expected = packet(model, raw['texts'])
    if obs.encode(expected) != obs.encode(value):
        raise ValueError('packet scope changed')
    return True


def bundle(case, omitted_roles=()):
    if type(omitted_roles) not in (tuple,list) or not set(omitted_roles) <= set(obs.ROLES):
        raise ValueError('declare roles omitted from the recipient packet')
    model = compile_model(case)
    texts = {s['id']:s['text'] for s in case['sources']
             if model['sources'][s['id']]['role'] not in omitted_roles}
    return dict(schema=FAMILY+'-bundle', model=model, packet=packet(model,texts))


def requirement(value):
    obs._shape(value,('target','question'),'requirement')
    if value['target'] not in CONTRACT['targets']:
        raise ValueError('supported future requirement target required')
    obs._text(value['question'],600,'requirement question')
    return deepcopy(value)


def structural_answers(model, req):
    requirement(req)
    def eligible(ids, role, original=False):
        return [k for k in ids if model['sources'][model['anchors'][k]['source']]['role'] == role
                and (not original or model['sources'][model['anchors'][k]['source']]['kind'] == 'original_turn')]
    if req['target'] == 'current_response':
        witnesses = [(key,) for key in eligible(model['fields']['u'],'after')]
    elif model['p_judgment'] == 'yes':
        witnesses = list(product(eligible(model['fields']['p'],'before',True),
                                 eligible(model['fields']['p'],'after',True),
                                 eligible(model['contexts'],'correction',True)))
    else:
        witnesses = []
    return [dict(kind='answer', anchors=list(keys), style=style)
            for keys in witnesses for style in CONTRACT['answer_styles']]


def plans(model, available, req):
    verify_packet(model,available); requirement(req)
    answers = [r for r in structural_answers(model,req)
               if all(model['anchors'][k]['source'] in available['texts'] for k in r['anchors'])]
    actions = list(answers)
    relevant = ('after',) if req['target'] == 'current_response' else ('before','after','correction')
    for role in relevant:
        candidates = [key for key,s in model['sources'].items() if s['role'] == role]
        for key in candidates:
            if key in available['texts']:
                actions.append(dict(kind='review', source=key))
        missing = [key for key in candidates if key not in available['texts']]
        if missing or not candidates:
            actions.append(dict(kind='ask', role=role, missing_sources=missing))
    actions.append(dict(kind='defer'))
    result = []
    for action in actions:
        signature = digest(action)
        result.append(dict(action, fingerprint=signature,
                           id=digest(dict(model=model['digest'], packet=available['digest'],
                                          requirement=req, action=action))))
    return result


def _citation(model, available, key):
    a = model['anchors'][key]; body = available['texts'][a['source']]
    quote = body[a['start']:a['end']]
    if hashlib.sha256(quote.encode()).hexdigest() != a['quote_sha256']:
        raise ValueError('actual source span differs from compiled witness')
    return dict(anchor=key,source=a['source'],start=a['start'],end=a['end'],quote=quote,
                source_sha256=model['sources'][a['source']]['sha256'],
                role=model['sources'][a['source']]['role'])


def _answer_body(req,citations,style):
    title = ('現在の記録にある発言です。' if req['target']=='current_response' else
             '入力された解釈で保持されたとされる根拠を、前後の原文と訂正箇所から示します。')
    lines = ['【'+ROLE_NAMES[c['role']]+'】 '+c['quote'] for c in citations]
    caveat = 'これは原文の引用と、入力された解釈に基づく説明です。'
    return '\n'.join([title,*lines,caveat] if style=='account_first' else [*lines,title,caveat])


def materialize(model,available,req,plan,cache):
    action = {k:v for k,v in plan.items() if k not in ('id','fingerprint')}
    refs=[]; new_cache=deepcopy(cache); reads=0
    if action['kind']=='answer':
        for key in action['anchors']:
            if key not in new_cache:
                new_cache[key]=_citation(model,available,key);reads+=1
            refs.append(deepcopy(new_cache[key]))
        body = _answer_body(req,refs,action['style'])
    elif action['kind']=='review':
        body = '【'+ROLE_NAMES[model['sources'][action['source']]['role']]+'】\n'+available['texts'][action['source']]
    elif action['kind']=='ask':
        names = '、'.join(action['missing_sources']) or '該当する原文'
        body = 'この要求を出典付きで確かめるため、'+ROLE_NAMES[action['role']]+'の原文が必要です。該当箇所を示せますか。'
    else:
        body = 'この要求は未完了として保持します。原文と過去の実行記録は残します。'
    reply = dict(family=FAMILY, model=model['digest'], packet=available['digest'], requirement=digest(req),
                 operation=action, body=body, citations=refs,
                 contract_satisfied=action['kind']=='answer', semantic_certification=False)
    verify_reply(model,available,req,reply)
    return reply,new_cache,reads


def verify_reply(model,available,req,reply):
    """Check the terminal source contract without trusting the chosen plan/permit."""
    verify_packet(model,available); requirement(req)
    obs._shape(reply,('family','model','packet','requirement','operation','body','citations',
                     'contract_satisfied','semantic_certification'),'reply')
    if (reply['family']!=FAMILY or reply['model']!=model['digest']
            or reply['packet']!=available['digest'] or reply['requirement']!=digest(req)
            or reply['semantic_certification'] is not False):
        raise ValueError('reply scope or certification changed')
    op=reply['operation'];kind=op.get('kind')
    if kind=='answer':
        obs._shape(op,('kind','anchors','style'),'answer operation')
        if op['style'] not in CONTRACT['answer_styles'] or type(op['anchors']) is not list:
            raise ValueError('supported answer recipe required')
        refs=[_citation(model,available,k) for k in op['anchors']]
        roles=[r['role'] for r in refs]
        if req['target']=='current_response':
            valid=len(refs)==1 and roles==['after'] and op['anchors'][0] in model['fields']['u']
        else:
            valid=(model['p_judgment']=='yes' and roles==['before','after','correction']
                   and all(model['sources'][r['source']]['kind']=='original_turn' for r in refs)
                   and all(k in model['fields']['p'] for k in op['anchors'][:2])
                   and op['anchors'][2] in model['contexts'])
        if (not valid or obs.encode(refs)!=obs.encode(reply['citations'])
                or reply['body']!=_answer_body(req,refs,op['style']) or reply['contract_satisfied'] is not True):
            raise ValueError('terminal source evidence contract not met')
    else:
        # Non-answer operations may complete an action but do not satisfy C.
        if reply['contract_satisfied'] is not False or reply['citations'] != []:
            raise ValueError('a request, review or deferral is not a certified answer')
        permitted=[{k:v for k,v in p.items() if k not in ('id','fingerprint')}
                   for p in plans(model,available,req) if p['kind']!='answer']
        if op not in permitted:
            raise ValueError('non-answer operation not enabled')
        if kind=='review':
            expected='【'+ROLE_NAMES[model['sources'][op['source']]['role']]+'】\n'+available['texts'][op['source']]
        elif kind=='ask':
            names='、'.join(op['missing_sources']) or '該当する原文'
            expected='この要求を出典付きで確かめるため、'+ROLE_NAMES[op['role']]+'の原文が必要です。該当箇所を示せますか。'
        else:
            expected='この要求は未完了として保持します。原文と過去の実行記録は残します。'
        if reply['body']!=expected:raise ValueError('executed operation body changed')
    return True


class Session:
    def __init__(self,bundle_value,ledger):
        obs._shape(bundle_value,('schema','model','packet'),'bundle')
        if bundle_value['schema']!=FAMILY+'-bundle':raise ValueError('supported bundle required')
        verify_model(bundle_value['model']);verify_packet(bundle_value['model'],bundle_value['packet'])
        if ledger.status()['accepted_commands'] or ledger.status()['engine']['phase']!='UNBOUND':
            raise ValueError('a fresh E4 ledger required')
        self.initial=deepcopy(bundle_value);self.model=deepcopy(bundle_value['model'])
        self.available=deepcopy(bundle_value['packet']);self.ledger=ledger
        self.commands=[];self.req=None;self.phase='UNBOUND';self.choice=None
        self.prepared=None;self.permit=None;self.cache={};self.closed=[];self.reads=0
        self.prefix='reply-'+self.model['digest'][:10]
        records=[]
        for key,text in self.available['texts'].items():
            records.extend(self._records('source-'+key,text,dict(kind='received_source_slot',source=key,
                           metadata=self.model['sources'][key]),self.model['sources'][key]['origin']))
        records.extend(self._records('model',obs.encode(self.model).decode(),
                       dict(kind='compiled_source_reply_family_not_E1',contract=digest(CONTRACT)),'reported_in_session'))
        for cmd in records: self.ledger.apply(cmd)
        self.source_events=[c['id'] for c in records]
        self.model_event=next(c['id'] for c in records if '-model-' in c['id'])
        self.goal=None

    def _records(self,label,body,metadata,origin='reported_in_session'):
        return [dict(op='record',id=self.prefix+'-'+label+'-'+str(start),origin=origin,
                     source=json.dumps(metadata,sort_keys=True,separators=(',',':')),
                     text=body[start:start+300]) for start in range(0,len(body),300)]

    def _ledger_after(self,commands):
        from event_bridge import Episode
        import step_session as e2
        raw,sha=self.ledger.snapshot()
        candidate=Episode.restore(e2.Session(self.ledger._session.entry),raw,sha)
        for command in commands:candidate.apply(command)
        return candidate

    def status(self):
        options=[] if self.req is None or self.phase in ('CLOSED','UNBOUND') else plans(self.model,self.available,self.req)
        return deepcopy(dict(family=FAMILY,model=self.model['digest'],packet=self.available['digest'],
            phase=self.phase,requirement=self.req,choice=self.choice,permit=self.permit,
            plans=options,admissible_answers=[p for p in options if p['kind']=='answer'],
            closed_responses=len(self.closed),last_response=self.closed[-1] if self.closed else None,
            span_reads=self.reads,cached_spans=len(self.cache),goal=self.goal,
            source_ids=list(self.available['texts']),commands_remaining=MAX_COMMANDS-len(self.commands),
            e4_accepted_commands=self.ledger.status()['accepted_commands'],e4_math_phase=self.ledger.status()['engine']['phase'],
            semantic_certification=False,erasure_authorized=False))

    def apply(self,command):
        if type(command) is not dict or len(self.commands)>=MAX_COMMANDS or len(obs.encode(command))>MAX_COMMAND_BYTES:
            raise ValueError('bounded command and remaining source-session budget required')
        command=deepcopy(command);op=command.get('op');changes={};result=None
        index=len(self.commands)+1;goal=self.goal;ledger_commands=[]
        if op=='bind' and set(command)=={'op','requirement'}:
            req=requirement(command['requirement'])
            changes=dict(req=req,phase='BOUND',choice=None,prepared=None,permit=None)
            goal=self.prefix+'-C'+str(index)
            ledger_commands.append(dict(op='goal',id=goal,text=req['question'],events=self.source_events[:32]))
            for offset in range(32,len(self.source_events),32):
                ledger_commands.append(dict(op='relate',goal=goal,events=self.source_events[offset:offset+32],
                                            note='Received model/source records for this source-action requirement.'))
        elif op=='choose' and set(command)=={'op','plan'}:
            if self.req is None or self.phase not in ('BOUND','CHOSEN','READY'):raise ValueError('bind the next request before choosing')
            selected=next((p for p in plans(self.model,self.available,self.req) if p['id']==command['plan']),None)
            if selected is None:raise ValueError('choose a current enabled plan')
            changes=dict(choice=selected,phase='CHOSEN',prepared=None,permit=None)
        elif command=={'op':'resolve'}:
            if self.phase!='CHOSEN':raise ValueError('choose before resolving')
            reply,cache,reads=materialize(self.model,self.available,self.req,self.choice,self.cache)
            permit=digest(dict(reply=reply,cycle=index,closed=self.closed))
            changes=dict(prepared=reply,cache=cache,reads=self.reads+reads,permit=permit,phase='READY')
        elif op=='advance' and set(command)=={'op','permit'}:
            if self.phase!='READY' or self.permit is None or command['permit']!=self.permit:
                raise ValueError('current prepared step permit required')
            verify_reply(self.model,self.available,self.req,self.prepared)
            result=dict(reply=deepcopy(self.prepared),certificate=dict(
                family=FAMILY,model=self.model['digest'],packet=self.available['digest'],
                requirement=digest(self.req),response_sha256=digest(self.prepared),
                contract_satisfied=self.prepared['contract_satisfied'],action_closed=True,
                semantic_certification=False))
            changes=dict(closed=self.closed+[result],phase='CLOSED',permit=None)
        elif op=='supply' and set(command)=={'op','source','text'}:
            key=command['source']
            if type(key) is not str or key not in self.model['sources'] or key in self.available['texts']:
                raise ValueError('supply a missing declared source slot; never replace an earlier source')
            available=packet(self.model,dict(self.available['texts'],**{key:command['text']}))
            changes=dict(available=available,choice=None,prepared=None,permit=None,
                         phase='UNBOUND' if self.phase=='CLOSED' else ('BOUND' if self.req else 'UNBOUND'))
            ledger_commands.extend(self._records('source-'+key,command['text'],
                dict(kind='arrived_source_slot',source=key,metadata=self.model['sources'][key]),
                self.model['sources'][key]['origin']))
            changes['source_events']=self.source_events+[c['id'] for c in ledger_commands]
        else:
            raise ValueError('unknown source action or unexpected fields')
        event=self.prefix+'-step'+str(index)
        body=dict(operation=op,requirement=changes.get('req',self.req),
                  phase=changes['phase'],source_family=FAMILY,
                  result=result,semantic_certification=False)
        ledger_commands.extend(self._records('step'+str(index),obs.encode(body).decode(),
                               dict(kind='source_action_runtime_receipt_not_E1_certificate')))
        if goal:
            refs=[c['id'] for c in ledger_commands if c['op']=='record']
            for offset in range(0,len(refs),32):
                ledger_commands.append(dict(op='relate',goal=goal,events=refs[offset:offset+32],
                                            note='Actual source-family operation; the E1 math family remains unbound.'))
        ledger=self._ledger_after(ledger_commands)
        # Commit only after all source and E4 budget checks succeed.
        for key,value in changes.items():setattr(self,key,value)
        self.goal=goal;self.ledger=ledger;self.commands.append(command)
        return dict(result=deepcopy(result),status=self.status())

    def snapshot(self):
        ledger,sha=self.ledger.snapshot()
        value=dict(schema=FAMILY+'-session',initial=self.initial,commands=self.commands,
                   available=self.available,phase=self.phase,requirement=self.req,choice=self.choice,
                   prepared=self.prepared,permit=self.permit,cache=self.cache,closed=self.closed,reads=self.reads,
                   ledger=json.loads(ledger),ledger_sha256=sha)
        raw=obs.encode(value)
        if len(raw)>MAX_SNAPSHOT_BYTES:raise ValueError('source session checkpoint budget exceeded')
        return raw,hashlib.sha256(raw).hexdigest()

    @classmethod
    def restore(cls,initial,ledger,raw,trusted):
        if type(raw) is not bytes or len(raw)>MAX_SNAPSHOT_BYTES or hashlib.sha256(raw).hexdigest()!=trusted:
            raise ValueError('bounded checkpoint and external trusted SHA required')
        value=json.loads(raw)
        if type(value) is not dict or value.get('schema')!=FAMILY+'-session' or value.get('initial')!=initial:
            raise ValueError('original bundle and complete source session required')
        commands=value.get('commands')
        if type(commands) is not list or len(commands)>MAX_COMMANDS:raise ValueError('bounded command history required')
        result=cls(initial,ledger)
        for command in commands:result.apply(command)
        if obs.encode(json.loads(result.snapshot()[0]))!=obs.encode(value):
            raise ValueError('source scope, executed response, requirement, cache or chronology changed')
        return result

