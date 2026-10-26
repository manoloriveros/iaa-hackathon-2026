"""Comprueba solo la nueva barrera de envío; no repite el transporte anterior."""
from pathlib import Path
from datetime import datetime, timezone
from contextlib import redirect_stdout
import ast
import importlib.util
import io
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/entrega_H1_investigacion_20261026_v1'
sp=importlib.util.spec_from_file_location('private_priority_H1_entry',R/'herramientas/enviar_H1_investigacion.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);sys.stdout.reconfigure(encoding='utf8')


def main():
    archives=sorted(OUT.glob('prioridad_privada_*'));assert len(archives)==1;archive=archives[0]
    target=archive/'private_priority_guard_test.json';assert not target.exists()
    previous=archive/'enviar_H1_pre_prioridad_privada.py'
    def bodies(path):
        tree=ast.parse(path.read_text(encoding='utf8'))
        return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    old=bodies(previous);new=bodies(Path(m.__file__))
    retained=['source','save','api','matching','limits_dict','send_once','check_remote']
    assert all(old[n]==new[n] for n in retained)
    calls={'api':0,'source':0}
    def reject_api():calls['api']+=1;raise AssertionError('API must not be initialized while deferred')
    def reject_source():calls['source']+=1;raise AssertionError('Old admission cannot release new transport')
    saved_api,saved_source=m.api,m.source;m.api=reject_api;m.source=reject_source
    saved_argv=sys.argv;sys.argv=[str(m.__file__),'submit']
    output=io.StringIO()
    try:
        with redirect_stdout(output):m.main()
    finally:
        m.api,m.source=saved_api,saved_source;sys.argv=saved_argv
    result=json.loads(output.getvalue())
    assert result['status']=='held_for_private_generalization_review' and result['new_submissions']==0
    assert calls=={'api':0,'source':0}
    # The archived conditional admission pins the previous transport: a future
    # release needs a newly reviewed version, not just flipping the hold flag.
    try:m.source()
    except AssertionError:pass
    else:raise AssertionError('Old admission should not authorize changed transport')
    fixture=archive/'guard_fixtures';fixture.mkdir()
    fake_repo=fixture/'repo';(fake_repo/'registro').mkdir(parents=True)
    fake_policy=fixture/'policy.json';fake_policy.write_text('{}',encoding='utf8')
    fake_gate=fake_repo/'registro/semana2_control_entregas_codex_actual.json'
    saved_root,saved_repo=m.ROOT,m.R;m.ROOT=fixture;m.R=fake_repo
    failures=[]
    try:
        try:m.current_delivery_gate()
        except FileNotFoundError:failures.append('missing_control_fail_closed')
        else:raise AssertionError('Missing control accepted')
        for name,allow,checksum in [('bad_boolean','false',m.sha(fake_policy)),('tampered_policy',False,'0'*64)]:
            fake_gate.write_text(json.dumps({'author':'Codex','allow_new_submission':allow,
                                            'policy':'policy.json','policy_sha256':checksum}),encoding='utf8')
            try:m.current_delivery_gate()
            except AssertionError:failures.append(name+'_fail_closed')
            else:raise AssertionError('Invalid control accepted')
    finally:m.ROOT,m.R=saved_root,saved_repo
    receipt={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'all_passed':True,
             'new_guard_actual_main_held_before_source_and_authentication':True,'actual_main_result':result,
             'API_calls':calls['api'],'new_submissions':0,'old_admission_cannot_authorize_changed_transport':True,
             'unchanged_transport_core_AST_functions':retained,'previous14core_tests_not_repeated':True,
             'new_fail_closed_checks':failures,'current_transport_sha256':m.sha(Path(m.__file__)),
             'archived_transport_sha256':m.sha(previous),'test_code_sha256':m.sha(Path(__file__)),
             'scope':'Changed entry gate only; prior transport evidence is retained, not recertified as a new full suite.'}
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=True))


if __name__=='__main__':main()
