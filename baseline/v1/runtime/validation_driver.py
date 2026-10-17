"""Run the RR54 model and all tests in one process, retaining preview caches."""
from pathlib import Path
import json,sys,time,unittest,hashlib
import three_flower_constraint as model

root=Path(__file__).resolve().parent
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    started=time.monotonic()
    print(json.dumps(dict(stage='main-start')),flush=True)
    result=model.run()
    (root/'three_flower_constraint_result.json').write_text(
        json.dumps(result,default=model.encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(stage='main-finished',groups=result['groups'],seconds=round(time.monotonic()-started,3))),flush=True)
    suite=unittest.defaultTestLoader.discover(str(root),pattern='test_*.py')
    checked=unittest.TextTestRunner(verbosity=1).run(suite)
    if not checked.wasSuccessful():raise SystemExit(1)
    assert checked.testsRun==252,checked.testsRun
    print(json.dumps(dict(stage='tests-finished',tests=checked.testsRun)),flush=True)
    examples=[]
    (root/'macro-occurrences').mkdir(exist_ok=True)
    for index,name in ((0,'first-terminal-frame'),(63,'alternate-terminal-frame')):
        requirement=model.construct_test_requirement(index).requirement
        path=root/'macro-occurrences'/(name+'.record.json')
        if not path.exists():
            occurrence=model.execute_macro(model.select_macro(requirement))
            path.write_text(json.dumps(model.export_macro(occurrence),separators=(',',':'))+'\n',encoding='utf-8')
        record=model.import_macro(json.loads(path.read_text(encoding='utf-8')),requirement)
        assert len(record.actual_records)==3 and record.upper_decoded.outputs[0].level==4
        examples.append(dict(path=path.relative_to(root).as_posix(),bytes=path.stat().st_size,
                             sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    output=dict(passed=True,groups=result['groups'],tests=checked.testsRun,exact_macro_records=len(examples),
                seconds=round(time.monotonic()-started,3),examples=examples)
    (root/'RR54-driver-validation.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output),flush=True)
