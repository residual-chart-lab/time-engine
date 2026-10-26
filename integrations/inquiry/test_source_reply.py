import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy

import source_reply as api
from event_bridge import Episode
from test_step_session import ROOT, RAW, SHA, DIGEST
from test_correction_observer import fixture, retrospective_case

REQ=dict(target='retained_basis',question='Show the annotated basis across the correction with its original sources.')
NOW=dict(target='current_response',question='What does the current supplied response say?')


def ledger():
    return Episode.receive(RAW,SHA,DIGEST)


def fresh(omitted=(),case=None):
    value=api.bundle(case or fixture(),omitted)
    return api.Session(value,ledger())


def choose(session,kind='answer',style='account_first'):
    plan=next(p for p in session.status()['plans'] if p['kind']==kind and (kind!='answer' or p['style']==style))
    session.apply(dict(op='choose',plan=plan['id']))
    return plan


def execute(session,kind='answer'):
    choose(session,kind)
    session.apply(dict(op='resolve'))
    return session.apply(dict(op='advance',permit=session.status()['permit']))['result']


class SourceReplyTests(unittest.TestCase):
    def test_same_current_observation_different_future_answers_and_actual_operations(self):
        full=fresh();projected=fresh(('before',))
        self.assertEqual(full.available['texts']['after'],projected.available['texts']['after'])
        for s in (full,projected):s.apply(dict(op='bind',requirement=NOW))
        self.assertEqual([p['fingerprint'] for p in full.status()['admissible_answers']],
                         [p['fingerprint'] for p in projected.status()['admissible_answers']])
        for s in (full,projected):s.apply(dict(op='bind',requirement=REQ))
        self.assertEqual(len(full.status()['admissible_answers']),2)
        self.assertEqual(projected.status()['admissible_answers'],[])
        answer=execute(full);ask=execute(projected,'ask')
        self.assertTrue(answer['certificate']['contract_satisfied'])
        self.assertFalse(ask['certificate']['contract_satisfied'])
        self.assertIn('I distinguish established claims',answer['reply']['body'])
        self.assertIn('訂正前の原文',ask['reply']['body'])
        self.assertEqual(full.status()['phase'],projected.status()['phase'])
        self.assertEqual(full.status()['phase'],'CLOSED')
        self.assertFalse(full.status()['semantic_certification'])
        self.assertEqual(full.status()['e4_math_phase'],'UNBOUND')

    def test_independent_source_coverage_oracle_for_every_packet_subset(self):
        case=fixture();whole=api.bundle(case);model=whole['model'];ids=[s['id'] for s in case['sources']]
        source={s['id']:s for s in case['sources']}
        before=[a for a in case['observations']['p']['evidence'] if a['source'] in case['roles']['before']
                and source[a['source']]['kind']=='original_turn']
        after=[a for a in case['observations']['p']['evidence'] if a['source'] in case['roles']['after']
               and source[a['source']]['kind']=='original_turn']
        correction=[k for k in case['roles']['correction'] if source[k]['kind']=='original_turn']
        checked=0
        for n in range(len(ids)+1):
            for subset in combinations(ids,n):
                visible=set(subset);texts={k:source[k]['text'] for k in subset};p=api.packet(model,texts)
                for req in (NOW,REQ):
                    if req['target']=='current_response':
                        count=2*sum(a['source'] in visible and a['source'] in case['roles']['after']
                                    for a in case['observations']['u']['evidence'])
                    else:
                        count=2*sum(b['source'] in visible and a['source'] in visible and c in visible
                                    for b in before for a in after for c in correction)
                    plans=api.plans(model,p,req)
                    self.assertEqual(sum(r['kind']=='answer' for r in plans),count)
                    for plan in plans:
                        if plan['kind']=='answer':
                            reply,_,_=api.materialize(model,p,req,plan,{})
                            self.assertTrue(api.verify_reply(model,p,req,reply))
                    checked+=1
        self.assertEqual(checked,32)

    def test_bundle_key_order_does_not_change_execution_or_checkpoint(self):
        value=api.bundle(fixture())
        wire=json.loads(api.obs.encode(value))
        a=api.Session(value,ledger());b=api.Session(wire,ledger())
        self.assertEqual(a.snapshot(),b.snapshot())
        for s in (a,b):
            s.apply(dict(op='bind',requirement=REQ));execute(s)
        self.assertEqual(a.snapshot(),b.snapshot())
        raw,trusted=a.snapshot()
        self.assertEqual(api.Session.restore(value,ledger(),raw,trusted).snapshot(),(raw,trusted))

    def test_blind_omission_and_restoration_controls(self):
        case=fixture();full=api.bundle(case);blind=api.bundle(case,('continuation',))
        witness=lambda b:sorted(p['fingerprint'] for p in api.plans(b['model'],b['packet'],REQ) if p['kind']=='answer')
        self.assertEqual(witness(full),witness(blind))
        omitted=api.bundle(case,('before',))
        restored=api.packet(omitted['model'],dict(omitted['packet']['texts'],before=full['packet']['texts']['before']))
        self.assertEqual(restored,full['packet'])
        self.assertEqual(witness(full),witness(dict(model=omitted['model'],packet=restored)))

    def test_omitted_source_body_and_quote_are_not_smuggled_through_model(self):
        case=fixture();value=api.bundle(case,('before',))
        encoded=api.obs.encode(value).decode()
        self.assertNotIn(case['sources'][0]['text'],encoded)
        self.assertNotIn(case['observations']['p']['evidence'][0]['quote'],encoded)

    def test_requirement_change_invalidates_permission_but_reuses_valid_spans(self):
        s=fresh();s.apply(dict(op='bind',requirement=REQ));choose(s);s.apply(dict(op='resolve'))
        old=s.status()['permit'];reads=s.status()['span_reads']
        s.apply(dict(op='bind',requirement=NOW))
        before=s.snapshot()
        with self.assertRaises(ValueError):s.apply(dict(op='advance',permit=old))
        self.assertEqual(s.snapshot(),before)
        result=execute(s)
        self.assertTrue(result['certificate']['contract_satisfied'])
        self.assertEqual(s.status()['span_reads'],reads+1) # current u differs from the retained-p span.
        self.assertEqual(result['reply']['requirement'],api.digest(NOW))

    def test_missing_source_arrives_after_question_without_rewriting_closed_history(self):
        s=fresh(('before',));s.apply(dict(op='bind',requirement=REQ));asked=execute(s,'ask')
        prior=deepcopy(s.closed);prefix=json.loads(s.ledger.snapshot()[0])['journal']
        text=api.bundle(fixture())['packet']['texts']['before']
        s.apply(dict(op='supply',source='before',text=text))
        self.assertEqual(s.status()['phase'],'UNBOUND')
        with self.assertRaises(ValueError):s.apply(dict(op='choose',plan='stale-plan'))
        s.apply(dict(op='bind',requirement=REQ));answered=execute(s)
        self.assertTrue(answered['certificate']['contract_satisfied'])
        self.assertFalse(asked['certificate']['contract_satisfied'])
        self.assertEqual(s.closed[0],prior[0])
        self.assertEqual(json.loads(s.ledger.snapshot()[0])['journal'][:len(prefix)],prefix)
        self.assertEqual(s.status()['closed_responses'],2)

    def test_source_arrival_before_execution_invalidates_old_preparation(self):
        s=fresh(('before',));s.apply(dict(op='bind',requirement=REQ));choose(s,'ask');s.apply(dict(op='resolve'))
        old=s.status()['permit']
        s.apply(dict(op='supply',source='before',text=api.bundle(fixture())['packet']['texts']['before']))
        self.assertIsNone(s.status()['permit']);self.assertEqual(s.status()['phase'],'BOUND')
        with self.assertRaises(ValueError):s.apply(dict(op='advance',permit=old))
        self.assertTrue(execute(s)['certificate']['contract_satisfied'])

    def test_plans_from_another_packet_or_request_are_not_permissions(self):
        a=fresh();b=fresh(('before',));a.apply(dict(op='bind',requirement=REQ));b.apply(dict(op='bind',requirement=REQ))
        forbidden=a.status()['admissible_answers'][0]['id'];before=b.snapshot()
        with self.assertRaises(ValueError):b.apply(dict(op='choose',plan=forbidden))
        self.assertEqual(b.snapshot(),before)
        a.apply(dict(op='bind',requirement=NOW))
        with self.assertRaises(ValueError):a.apply(dict(op='choose',plan=forbidden))

    def test_unknown_or_retrospective_annotation_never_certifies_continuity(self):
        for case in (retrospective_case(),fixture()):
            if case['id']=='synthetic-correction':case['observations']['p']['judgment']='unknown'
            s=fresh(case=case);s.apply(dict(op='bind',requirement=REQ))
            self.assertEqual(s.status()['admissible_answers'],[])
            allowed={p['kind'] for p in s.status()['plans']}
            self.assertIn('defer',allowed)
            self.assertFalse(execute(s,'defer')['certificate']['contract_satisfied'])

    def test_review_reads_real_available_source_without_claiming_answer_success(self):
        s=fresh();s.apply(dict(op='bind',requirement=REQ));result=execute(s,'review')
        self.assertIn('I require physical proof',result['reply']['body'])
        self.assertFalse(result['certificate']['contract_satisfied'])

    def test_terminal_verifier_rejects_tampered_scope_body_guards_and_source_bytes(self):
        s=fresh();s.apply(dict(op='bind',requirement=REQ));reply=execute(s)['reply']
        variants=[]
        for key,value in [('body','unsupported answer'),('contract_satisfied',False),('semantic_certification',True),
                          ('requirement','0'*64),('packet','0'*64)]:
            changed=deepcopy(reply);changed[key]=value;variants.append(changed)
        changed=deepcopy(reply);changed['citations'][0]['quote']='invented';variants.append(changed)
        for changed in variants:
            with self.assertRaises(ValueError):api.verify_reply(s.model,s.available,REQ,changed)
        altered=deepcopy(s.available);altered['texts']['before']='Changed outside the cited span. '+altered['texts']['before']
        with self.assertRaises(ValueError):api.verify_reply(s.model,altered,REQ,reply)

    def test_checkpoints_before_and_after_execution_restore_exactly_and_continue(self):
        s=fresh();s.apply(dict(op='bind',requirement=REQ));choose(s);s.apply(dict(op='resolve'))
        for phase in ('READY','CLOSED'):
            raw,sha=s.snapshot()
            r=api.Session.restore(s.initial,ledger(),raw,sha)
            self.assertEqual(r.snapshot(),(raw,sha));self.assertEqual(r.status(),s.status())
            if phase=='READY':s.apply(dict(op='advance',permit=s.status()['permit']))
            else:
                r.apply(dict(op='bind',requirement=NOW))
                self.assertTrue(execute(r)['certificate']['contract_satisfied'])

    def test_checkpoint_tampering_and_forged_source_arrival_are_rejected(self):
        s=fresh(('before',));s.apply(dict(op='bind',requirement=REQ));execute(s,'ask')
        doc=json.loads(s.snapshot()[0])
        for field in ('phase','reads'):
            bad=deepcopy(doc);bad[field]='forged';raw=api.obs.encode(bad)
            with self.assertRaises(ValueError):api.Session.restore(s.initial,ledger(),raw,hashlib.sha256(raw).hexdigest())
        before=s.snapshot()
        for key,text in [('before','invented'),('after',s.available['texts']['after']),('not-declared','new')]:
            with self.assertRaises(ValueError):s.apply(dict(op='supply',source=key,text=text))
            self.assertEqual(s.snapshot(),before)

    def test_e4_budget_failure_is_atomic_and_last_checkpoint_still_restores(self):
        s=fresh();s.apply(dict(op='bind',requirement=REQ));last=s.snapshot()
        failed=False
        for index in range(40):
            try:s.apply(dict(op='bind',requirement=dict(REQ,question='rebind '+str(index))))
            except ValueError:
                failed=True;break
            last=s.snapshot()
        self.assertTrue(failed);self.assertEqual(s.snapshot(),last)
        self.assertEqual(api.Session.restore(s.initial,ledger(),*last).snapshot(),last)

    def test_external_cli_compile_choose_execute_checkpoint_and_resume(self):
        work=ROOT/'.work';work.mkdir(exist_ok=True)
        cli=[sys.executable,'-I','-B',str(ROOT/'run_source_reply.py')]
        with tempfile.TemporaryDirectory(dir=work) as name:
            out=Path(name);case=out/'case.json';case.write_bytes(api.obs.encode(fixture()))
            compiled=out/'packets'
            subprocess.run(cli+['compile','--case',str(case),'--output-dir',str(compiled)],capture_output=True,check=True,timeout=30)
            raw=(compiled/'without-before.bundle.json').read_bytes();value=json.loads(raw)
            args=cli+['run','--bundle',str(compiled/'without-before.bundle.json'),'--trusted-sha256',hashlib.sha256(raw).hexdigest()]
            p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
            def send(command):
                p.stdin.write(json.dumps(command)+'\n');p.stdin.flush()
                reply=json.loads(p.stdout.readline());self.assertTrue(reply['ok'],reply);return reply
            try:
                self.assertTrue(json.loads(p.stdout.readline())['ok'])
                r=send(dict(op='bind',requirement=REQ))
                plan=next(r for r in r['status']['plans'] if r['kind']=='ask')
                send(dict(op='choose',plan=plan['id']));r=send(dict(op='resolve'))
                r=send(dict(op='advance',permit=r['status']['permit']))
                self.assertEqual(r['result']['reply']['operation']['kind'],'ask')
                checkpoint=out/'closed.json';saved=send(dict(op='save',path=str(checkpoint)))
                send(dict(op='quit'));p.communicate(timeout=20);self.assertEqual(p.returncode,0)
                resumed=subprocess.run(args+['--resume',str(checkpoint),'--trusted-resume-sha256',saved['sha256']],
                                       input='{"op":"status"}\n{"op":"quit"}\n',capture_output=True,text=True,check=True,timeout=30)
                self.assertEqual(json.loads(resumed.stdout.splitlines()[0])['status']['phase'],'CLOSED')
            finally:
                if p.poll() is None:p.kill();p.communicate()


if __name__=='__main__':unittest.main()

