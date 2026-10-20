from pathlib import Path
import hashlib,json

# Deliberately imports no TE model, trajectory, root solver or success test.
root=Path(__file__).resolve().parents[2]
manifest=dict(schema='time-engine-rr61-independent-C-inputs-v1',date='2026-10-20',
    parent_commit='66038def4c18859bc2268f8832286f6c1243fc62',
    construction='x=k/4 for every integer k=-4,...,8; plus the explicitly labelled blind-channel control x=1/3',
    future_target=['1','0','0','0'],future_inherited=['-1','0','0','0'],
    future_frames=[dict(name=f'grid-{k}',x=f'{k}/4',role='independent fixed grid') for k in range(-4,9)]
        +[dict(name='blind-current-frame',x='1/3',role='zero-channel control')],
    control_domain=['-64','64'],
    histories=[dict(name='erase',mode='erase',contact=1,gain='1'),
               dict(name='keep',mode='keep',contact=1,gain='1'),
               dict(name='restore',mode='restore',contact=1,gain='1'),
               dict(name='large-history-control',mode='keep',contact=1,gain=str(2**24))],
    word_family='all finite primitive first-return H/S words: equal H and S counts and more H than S at each proper prefix',
    free_execution_words=['HS','HHHSSS','HHSHSS'],negative_even_word='HHSS',
    success_paths_used_to_construct_C=False,
    comparison='backward residual-aware pullback versus forward affine reachable-interval calculation; same histories, C, domain and words')
path=root/'.work/rr61-local/inputs.generated.json'
path.parent.mkdir(parents=True,exist_ok=True)
raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
path.write_bytes(raw)
print(json.dumps(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),requirements=len(manifest['future_frames']))))
