"""Execute a source-backed reply, ask for a missing source, then continue.

The driver has the archived original and supplies it only after the recipient
has actually emitted its request. No unobserved source is recovered by prediction.
This is a deterministic execution example, not an independent AI behavior study.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
CLI=[sys.executable,'-I','-B',str(ROOT/'run_source_reply.py')]


def enc(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,indent=2)+'\n').encode()


class Peer:
    def __init__(self,path,sha,resume=None,trusted=None):
        args=CLI+['run','--bundle',str(path),'--trusted-sha256',sha]
        if resume:args+=['--resume',str(resume),'--trusted-resume-sha256',trusted]
        self.p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                text=True,encoding='utf-8')
        self.trace=[];self.receive(None)

    def receive(self,command):
        line=self.p.stdout.readline()
        if not line:raise RuntimeError(self.p.stderr.read())
        reply=json.loads(line);self.trace.append(dict(command=command,response=reply))
        if not reply['ok']:raise RuntimeError(reply)
        return reply

    def send(self,command):
        self.p.stdin.write(json.dumps(command,ensure_ascii=True)+'\n');self.p.stdin.flush()
        return self.receive(command)

    def finish(self):
        self.send(dict(op='quit'));_,error=self.p.communicate(timeout=30)
        if self.p.returncode:raise RuntimeError(error)

    def execute(self,kind,style='account_first'):
        state=self.send(dict(op='status'))['status']
        plan=next(p for p in state['plans'] if p['kind']==kind and (kind!='answer' or p['style']==style))
        self.send(dict(op='choose',plan=plan['id']))
        ready=self.send(dict(op='resolve'))
        return self.send(dict(op='advance',permit=ready['status']['permit']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=False,exist_ok=False)
    case_path=ROOT/'examples/source-reply-case.json'
    requirement=json.loads((ROOT/'examples/source-reply-requirement.json').read_bytes())
    case=json.loads(case_path.read_bytes())
    packets=out/'packets'
    compiled=subprocess.run(CLI+['compile','--case',str(case_path),'--output-dir',str(packets)],
                            capture_output=True,text=True,check=True,timeout=30)
    manifest=json.loads(compiled.stdout)['manifest']
    peers=[];summary={}
    try:
        for variant in ('retained','without-before','current-only','blind-control'):
            path=packets/(variant+'.bundle.json');meta=manifest['files'][path.name]
            peer=Peer(path,meta['sha256']);peers.append(peer)
            now=peer.send(dict(op='bind',requirement=dict(target='current_response',question='現在の記録は何と答えていますか。')))
            bound=peer.send(dict(op='bind',requirement=requirement))
            choices=bound['status']['admissible_answers']
            summary[variant]=dict(current_answer_count=len(now['status']['admissible_answers']),
                                  current_fingerprints=[p['fingerprint'] for p in now['status']['admissible_answers']],
                                  future_answer_count=len(choices),
                                  future_fingerprints=[p['fingerprint'] for p in choices])
            if variant!='current-only':
                emitted=peer.execute('answer' if choices else 'ask')
                summary[variant]['result']=emitted['result']
                saved=peer.send(dict(op='save',path=str(out/(variant+'-closed.json'))))
                summary[variant]['checkpoint_sha256']=saved['sha256']
                assert hashlib.sha256((out/(variant+'-closed.json')).read_bytes()).hexdigest()==saved['sha256']
            peer.finish()
            (out/(variant+'-trace.json')).write_bytes(enc(peer.trace))

        missing=out/'without-before-closed.json'
        resumed=Peer(packets/'without-before.bundle.json',manifest['files']['without-before.bundle.json']['sha256'],
                     missing,summary['without-before']['checkpoint_sha256']);peers.append(resumed)
        # This arrival is an explicit external input from the archived source.
        body=next(s['text'] for s in case['sources'] if s['id']=='before')
        resumed.send(dict(op='supply',source='before',text=body))
        rebound=resumed.send(dict(op='bind',requirement=requirement))
        supplied=resumed.execute('answer')
        saved=resumed.send(dict(op='save',path=str(out/'after-arrival-closed.json')))
        resumed.finish()
        (out/'after-arrival-trace.json').write_bytes(enc(resumed.trace))
        summary['after-arrival']=dict(future_answer_count=len(rebound['status']['admissible_answers']),
                                       result=supplied['result'],checkpoint_sha256=saved['sha256'])
        assert summary['retained']['current_fingerprints']==summary['without-before']['current_fingerprints']
        assert summary['retained']['future_answer_count']==2
        assert summary['without-before']['future_answer_count']==0
        assert summary['current-only']['future_answer_count']==0
        assert summary['retained']['future_fingerprints']==summary['blind-control']['future_fingerprints']
        assert summary['retained']['result']['reply']==summary['after-arrival']['result']['reply']
        initial=json.loads(missing.read_bytes())
        final=json.loads((out/'after-arrival-closed.json').read_bytes())
        assert initial['closed'][0]==final['closed'][0]
        (out/'retained-response.txt').write_bytes((summary['retained']['result']['reply']['body']+'\n').encode())
        (out/'missing-source-question.txt').write_bytes((summary['without-before']['result']['reply']['body']+'\n').encode())
        result=dict(schema='time-engine-source-reply-example-v1',contract=manifest['contract'],requirement=requirement,
                    variants=summary,same_current_observation=True,blind_control_same_answers=True,
                    closed_request_preserved_after_arrival=True,restored_reply_matches_retained=True,
                    driver_policy='answer if a certified recipe is available, otherwise ask; fixed account_first style',
                    ai_behavior_effect_measured=False,semantic_certification=False)
        (out/'RESULT.json').write_bytes(enc(result))
        print(json.dumps(dict(ok=True,output_dir=str(out),same_current_observation=True,
                              answer_counts={key:v['future_answer_count'] for key,v in summary.items()},
                              response_after_arrival_matches=True)))
    finally:
        for peer in peers:
            if peer.p.poll() is None:peer.p.kill();peer.p.communicate()


if __name__=='__main__':main()

