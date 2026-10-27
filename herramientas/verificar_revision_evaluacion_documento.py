"""Comprueba la reutilizacion de sorteos y las fuentes sin ajustar o remuestrear."""
import importlib.util
from pathlib import Path
import json
import hashlib
import sys

R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('document_review_fixed_outputs',R/'herramientas/auditar_evaluacion_documento.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
np=m.np;pd=m.pd


def main():
    plan=m.w.read(m.PLAN);m.guard(plan);p=np.load(m.OUT/'policy_bootstrap.npz');draws=p['delta'];segments=list(p['segments'])
    error=0.;sources={};files={}
    for vi,view in enumerate(m.VIEWS):
        path=m.ACTIVE/f'bootstrap_{view}.npz';pack=np.load(path);sources[m.w.rel(path)]=m.w.sha(path)
        for j,name in enumerate(pack['segments']):
            ours=draws[:,segments.index(name),vi,0]-draws[:,segments.index(name),vi,1]
            expected=pack['scores'][:,j,1]-pack['scores'][:,j,0]
            error=max(error,float(np.max(np.abs(ours-expected))))
        path=m.ACTIVE/f'composition_bootstrap_{view}.npz';pack=np.load(path);sources[m.w.rel(path)]=m.w.sha(path)
        for j,name in enumerate(['mix2025_global','mix2025_new_business']):
            ours=draws[:,segments.index(name),vi,0]-draws[:,segments.index(name),vi,1]
            error=max(error,float(np.max(np.abs(ours-pack['delta'][:,j]))))
        f=pd.read_parquet(m.OUT/f'policy_{view}.parquet');nb=f.new_business.to_numpy(bool)
        assert np.array_equal(f.DOC_R1.to_numpy()[nb],f.baseline.to_numpy()[nb])
        assert np.array_equal(f.DOC_R1.to_numpy()[~nb],f.full.to_numpy()[~nb])
    assert error<2e-12,error
    for folder,name in [(m.PARENT,'fuentes.json'),(m.ACTIVE,'sources.json')]:
        records=m.w.read(folder/name);assert isinstance(records,list)
        for record in records:
            path=Path(record['path']);path=path if path.is_absolute() else m.ROOT/path
            if str(path) not in files:
                digest=hashlib.sha256()
                with path.open('rb') as handle:
                    for block in iter(lambda:handle.read(8*1024*1024),b''):digest.update(block)
                files[str(path)]=digest.hexdigest()
            assert files[str(path)]==record['sha256'],str(path)
    post=m.ACTIVE/'post_verification.json';data=m.w.read(post)
    assert data['all_passed'] and all(data['checks'].values())
    assert data['verifier_sha256']==m.w.sha(R/'herramientas/revisar_ampliacion_f3c.py')
    assert m.w.sha(m.F3C)==m.F3CSHA;m.guard(plan)
    m.dump(m.OUT/'policy_verification.json',{'author':'Codex','utc':m.utc(),
        'all_original10000bootstrap_differences_reconstructed_all3views_and_composition':True,
        'max_reconstruction_error':error,'serialized_NB_and_renewal_quotes_exact':True,
        'all_current_declared_source_file_hashes_match':True,'unique_source_files_checked':len(files),
        'owner_post_verification_sha256':m.w.sha(post),'original_bootstrap_sources':sources,
        'verifier_sha256':m.w.sha(Path(__file__)),'new_fits':0,'new_resampling':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'verified':True,'original10000draw_reconstruction_error':error,'source_files':len(files),'new_fits':0,'new_resampling':0}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');main()
