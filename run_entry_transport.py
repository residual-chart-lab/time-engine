"""Create or receive the fixed E1 entry; no distribution service is involved."""
from pathlib import Path
import sys,argparse,json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import entry_transport as wire


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('export','receive','run'))
    parser.add_argument('--entry',type=Path,required=True);parser.add_argument('--trusted-sha256');parser.add_argument('--expected-entry-digest')
    args=parser.parse_args()
    if args.command=='export':
        if args.entry.exists():parser.error('export requires a new file path')
        entry=wire.a.register();raw,h=wire.dumps(entry)
        args.entry.parent.mkdir(parents=True,exist_ok=True)
        with args.entry.open('xb') as f:f.write(raw)
        print(json.dumps(dict(schema=wire.SCHEMA,model=wire.MODEL,entry_digest=entry.digest,sha256=h,bytes=len(raw))));return
    if args.trusted_sha256 is None or args.expected_entry_digest is None:parser.error('receive/run need externally retained --trusted-sha256 and --expected-entry-digest')
    entry=wire.loads(args.entry.read_bytes(),args.trusted_sha256,args.expected_entry_digest)
    if args.command=='receive':
        print(json.dumps(dict(entry_digest=entry.digest,stock=len(entry.base.engine.stock),new_requirement_bound=False)));return
    import three_flower_session as live
    import rr69_study as study
    scope=study.scope(entry,'mixed',('1/1024','1/1024'),'split')
    current=live.resolve(live.choose(live.start(entry,scope),1,0,'HHHSUT'))[0];done=live.finish(current)
    print(json.dumps(dict(entry_digest=entry.digest,phase=done.phase,certified=done.certified,stock=len(done.engine.stock))))

if __name__=='__main__':main()
