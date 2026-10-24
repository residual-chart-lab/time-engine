"""Focused E2 request/recovery and P0 negative acceptance audit."""
from pathlib import Path
from unittest.mock import patch
import sys,json,hashlib,subprocess,importlib.util
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import step_session as api
RAW=(ROOT/'integrations/inquiry/E1-entry.record.json').read_bytes()
SHA=hashlib.sha256(RAW).hexdigest()
DIGEST=json.loads(RAW)['entry_digest']
OUT=Path(__file__).parent
REQ=dict(context='mixed',strengths=['1/1024','1/1024'],frame='split')
CHOICE=dict(op='choose',v='1',u='0',word='HHHSUT')
def receive():return api.Session.receive(RAW,SHA,DIGEST)
def encoded(value):
 raw=(json.dumps(value,separators=(',',':'))+'\n').encode();return raw,hashlib.sha256(raw).hexdigest()

s=receive();rows=[]
for label,req,expected in [('mixed',REQ,'READY'),('outside',dict(REQ,context='outside_chart'),'REJECTED'),('zero',dict(REQ,context='zero_head'),'REJECTED'),('restricted',dict(REQ,domain=['0','0']),'REJECTED'),('mixed_return',REQ,'READY')]:
 s.apply(dict(op='bind',requirement=req));assert s.state.plan is None and s.state.action is None
 before=s.snapshot()
 try:s.apply(dict(op='advance'))
 except ValueError:pass
 else:raise AssertionError('bind retained prior permission')
 assert s.snapshot()==before
 s.apply(CHOICE);status=s.apply(dict(op='resolve'));assert status['phase']==expected
 rows.append(dict(label=label,phase=status['phase'],action=s.state.action.status,work=status['last_resolution_work']))
 if expected=='REJECTED':
  before=s.snapshot()
  try:s.apply(dict(op='advance'))
  except ValueError:pass
  else:raise AssertionError('rejected request executed')
  assert s.snapshot()==before
assert rows[-1]['work']['total_exact_queries']==0
s.apply(dict(op='advance'));raw,sha=s.snapshot()
restored=api.Session.restore(receive().entry,raw,sha)
assert restored.snapshot()==(raw,sha) and restored.status()==s.status()
for _ in range(3):restored.apply(dict(op='advance'))
assert restored.status()['certified']

bad=[]
for label in ('request','journal','reads','graph','cache'):
 doc=json.loads(raw)
 if label=='request':doc['current']['scope']['last_strength']='0'
 elif label=='journal':doc['journal'][0]['requirement']['context']='main'
 elif label=='reads':doc['numerical_reads']+=1
 elif label=='graph':doc['current']['graph']['nodes'].append({'tuple':[]})
 else:doc['current']['cache'][0][2]='0'
 forged,h=encoded(doc)
 try:api.Session.restore(receive().entry,forged,h)
 except (ValueError,TypeError) as exc:bad.append(dict(name=label,rejected=True,error=str(exc)))
 else:raise AssertionError(label+' forgery accepted')

# Demonstrate a sub-byte-limit malformed command after real first closure.
# Its nesting should be rejected without terminating the live local session.
args=[sys.executable,'-I',str(ROOT/'run_time_engine.py'),'--entry',str(ROOT/'integrations/inquiry/E1-entry.record.json'),'--trusted-sha256',SHA,'--expected-entry-digest',DIGEST]
prefix=[dict(op='bind',requirement=REQ),CHOICE,dict(op='resolve'),dict(op='advance')]
deep='{"op":"status","extra":'+'['*1100+'0'+']'*1100+'}'
assert len(deep.encode())<api.MAX_COMMAND_BYTES
commands='\n'.join(map(json.dumps,prefix))+'\n'+deep+'\n'+json.dumps(dict(op='status'))+'\n'+json.dumps(dict(op='quit'))+'\n'
result=subprocess.run(args,input=commands,text=True,capture_output=True)
output=[json.loads(x) for x in result.stdout.splitlines()]
deep_result=dict(bytes=len(deep.encode()),limit=api.MAX_COMMAND_BYTES,returncode=result.returncode,
 last_output_phase=output[-1]['status']['phase'],recursion_error='RecursionError' in result.stderr,
 continued_after_error=any(x.get('ok') is False for x in output) and output[-1].get('event')=='quit')
(OUT/'deep-command.stderr.txt').write_text(result.stderr)

# Candidate validation must reject changed and extra files; restore both.
package=ROOT/'.work/astra-p0-unpacked/time-engine-p0'
spec=importlib.util.spec_from_file_location('p0_verify',package/'verify_package.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
p=package/'README.md';original=p.read_bytes();negative=[]
try:
 p.write_bytes(original+b'\nchanged\n')
 try:v.verify(package)
 except ValueError:negative.append('changed_file_rejected')
 else:raise AssertionError('changed file accepted')
finally:p.write_bytes(original)
p=package/'unexpected.txt'
try:
 p.write_text('extra')
 try:v.verify(package)
 except ValueError:negative.append('extra_file_rejected')
 else:raise AssertionError('extra file accepted')
finally:p.unlink()
assert v.verify(package)['passed']
report=dict(pinned_commit='f60fad90fcadaccf438c29a2f1a21bbf532dfea3',request_transitions=rows,
 restored_changed_requests_exactly=True,completed_certified=True,tampered_checkpoints=bad,
 nested_command=deep_result,package_negatives=negative)
(OUT/'observed.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
