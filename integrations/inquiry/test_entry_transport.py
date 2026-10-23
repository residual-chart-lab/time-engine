import unittest,json,hashlib,tempfile,subprocess,sys
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
import entry_transport as wire

ROOT=Path(__file__).resolve().parents[2]


def blocked():
    stack=ExitStack()
    for module,name in ((wire.a,'register'),(wire.incremental,'register'),(wire.adaptive,'register'),(wire.m,'register'),(wire.b,'register'),(wire.prior.previous,'begin'),(wire.prior.te,'prepare')):
        stack.enter_context(patch.object(module,name,side_effect=AssertionError('past generator forbidden')))
    return stack


def changed(value):
    raw=(json.dumps(value,separators=(',',':'))+'\n').encode()
    return raw,hashlib.sha256(raw).hexdigest()


class EntryTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry=wire.a.register();cls.raw,cls.sha=wire.dumps(cls.entry);cls.digest=cls.entry.digest

    def test_erasure_and_restoration_entries_preserve_their_exact_state(self):
        for modes in (('erase','keep'),('restore','restore')):
            entry=wire.a.register(modes);raw,h=wire.dumps(entry)
            with blocked():received=wire.loads(raw,h,entry.digest)
            self.assertEqual(received.base.engine,entry.base.engine)
            self.assertEqual(wire.session.archives(received),wire.session.archives(entry))

    def test_archive_is_entry_only_and_preserves_original_numbers(self):
        doc=json.loads(self.raw)
        self.assertEqual(set(doc),{'schema','model','entry_digest','graph','numbers'})
        self.assertEqual(doc['numbers'],wire.session.archives(self.entry))

    def test_import_issues_a_valid_entry_without_any_past_generator(self):
        with blocked():received=wire.loads(self.raw,self.sha,self.digest)
        wire.a.verify_entry(received);self.assertEqual(received.base.engine,self.entry.base.engine)
        self.assertEqual(wire.session.archives(received),wire.session.archives(self.entry))

    def test_external_hash_and_expected_identity_are_required(self):
        with self.assertRaises(ValueError):wire.loads(self.raw,'0'*64,self.digest)
        with self.assertRaises(ValueError):wire.loads(self.raw,self.sha,'0'*64)
        with self.assertRaises(ValueError):wire.loads(self.raw+b' ',self.sha,self.digest)

    def test_modified_original_number_archive_does_not_issue_authority(self):
        doc=json.loads(self.raw);doc['numbers']['base']='00';raw,h=changed(doc)
        registries=(wire.m._ISSUED,wire.adaptive._ISSUED,wire.incremental._ISSUED,wire.a._ISSUED);before=tuple(map(len,registries))
        with self.assertRaises(ValueError):wire.loads(raw,h,self.digest)
        self.assertEqual(tuple(map(len,registries)),before)

    def test_changed_model_is_rejected(self):
        doc=json.loads(self.raw);doc['model']='other-model';raw,h=changed(doc)
        with self.assertRaises(ValueError):wire.loads(raw,h,self.digest)

    def test_swapping_the_two_source_histories_is_rejected(self):
        doc=json.loads(self.raw);root=doc['graph']['nodes'][doc['graph']['root']['ref']]['tuple'];root[0],root[1]=root[1],root[0]
        raw,h=changed(doc)
        with self.assertRaises(ValueError):wire.loads(raw,h,self.digest)

    def test_unused_graph_nodes_are_not_silently_accepted(self):
        doc=json.loads(self.raw);doc['graph']['nodes'].append({'tuple':[]});raw,h=changed(doc)
        with self.assertRaises(ValueError):wire.loads(raw,h,self.digest)

    def test_save_and_load_enforce_the_same_graph_and_byte_budgets(self):
        with patch.object(wire,'MAX_NODES',1):
            with self.assertRaises(ValueError):wire.dumps(self.entry)
            with self.assertRaises(ValueError):wire.loads(self.raw,self.sha,self.digest)
        with patch.object(wire,'MAX_BYTES',1):
            with self.assertRaises(ValueError):wire.dumps(self.entry)
            with self.assertRaises(ValueError):wire.loads(self.raw,self.sha,self.digest)

    def test_new_observation_values_require_a_session_checkpoint(self):
        entry=wire.loads(self.raw,self.sha,self.digest)
        entry.derived.register('already-read',0,(0,0),'diagnostic')
        with self.assertRaises(ValueError):wire.dumps(entry)

    def test_fresh_process_receives_runs_and_replays_three_flowers_without_generators(self):
        code=r'''
import sys,json,hashlib
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'integrations/inquiry'))
import entry_transport as w
import three_flower_session as live
import rr69_study as study
with ExitStack() as stack:
 for module,name in ((w.a,'register'),(w.incremental,'register'),(w.adaptive,'register'),(w.m,'register'),(w.b,'register'),(w.prior.previous,'begin'),(w.prior.te,'prepare')):
  stack.enter_context(patch.object(module,name,side_effect=AssertionError('past generator forbidden')))
 raw=Path(sys.argv[2]).read_bytes();e=w.loads(raw,sys.argv[3],sys.argv[4]);scope=study.scope(e,'mixed',('1/1024','1/1024'),'split')
 ready=live.resolve(live.choose(live.start(e,scope),1,0,'HHHSUT'))[0];done=live.finish(ready)
 actual,h=live.dumps(done);saved=json.loads(actual);reference=json.loads((root/'integrations/inquiry/RR69-mixed-connected.record.json').read_bytes())
 assert w.checkpoint.unpack(saved.pop('graph'))==w.checkpoint.unpack(reference.pop('graph'))
 assert saved==reference
 second=w.loads(raw,sys.argv[3],sys.argv[4]);resumed=live.loads(actual,h,second,study.scope(second,'mixed',('1/1024','1/1024'),'split'))
 assert resumed.certified
 print(json.dumps(dict(certified=done.certified,stock=len(done.engine.stock),full_physical_history_matches_RR69=True,receiver_checkpoint_replays=True,past_generators_called=0)))
'''
        temporary_root=ROOT/'.work/e1-tests';temporary_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as temp:
            assert Path(temp).resolve().is_relative_to(temporary_root.resolve())
            path=Path(temp)/'entry.json';path.write_bytes(self.raw)
            result=subprocess.run([sys.executable,'-c',code,str(ROOT),str(path),self.sha,self.digest],text=True,capture_output=True,check=True)
        report=json.loads(result.stdout)
        type(self).fresh_report=report
        self.assertEqual(report,dict(certified=True,stock=9,full_physical_history_matches_RR69=True,receiver_checkpoint_replays=True,past_generators_called=0))

if __name__=='__main__':unittest.main()
