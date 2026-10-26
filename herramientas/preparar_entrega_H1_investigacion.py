"""Entrega de investigación separada de la promoción formal del modelo H1."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';OUT=BASE/'entrega_H1_investigacion_20261026_v1'
PROTOTYPE=BASE/'H1_solo_prototipo_20261026_v1';TRANSFER=BASE/'transferencia_H1_solo_20261026_v1'
POLICY=R/'registro/semana2_mision017_H1_revision_entrega_v1.json'
sys.stdout.reconfigure(encoding='utf8')


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m


send=load('H1_delivery_transport',R/'herramientas/enviar_H1_investigacion.py')
w=load('H1_delivery_state_tools',R/'herramientas/registrar_avance_mision017_fase2.py')


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def prepare():
    assert not OUT.exists() and not POLICY.exists();OUT.mkdir()
    report=w.read(PROTOTYPE/'report.json');transfer=w.read(TRANSFER/'report.json')
    spec=report['CSV'];assert spec['sha256']==send.SHA
    files=[Path(__file__),Path(send.__file__),ROOT/spec['path'],PROTOTYPE/'report.json',TRANSFER/'report.json',
           BASE/'enlace_HET_20261026_v1/report.json',PROTOTYPE/'member_prices_2025.parquet',
           R/'registro/semana2_politica_desarrollo2024_v2.json',R/'registro/semana2_politica_seleccion_v1.json',
           BASE/'entrega_F3c_investigacion_20261026_v1/public_receipt.json',
           ROOT/'.agents/skills/kaggle/scripts/kaggle_skill.py',
           ROOT/'.agents/skills/kaggle/modules/competitions/scripts/competition_submit.py',
           ROOT/'.agents/skills/kaggle/modules/competitions/scripts/competition_validate.py',
           ROOT/'Hackaton/Repositorio_IAA2026/privado/semana2/envios/g4_20261025_v1/official_sample_format.csv']
    policy={'id':'S2-MISION017-H1-RESEARCH-DELIVERY-v1','author_decision':'Codex','utc':datetime.now(timezone.utc).isoformat(),
            'status':'research_delivery_review_before_copy_dryrun_and_any_upload',
            'human_authorization_in_thread':['Dale, envía el CSV propio a Kaggle, verifica que se procese y deja el resultado en el foro.',
                                             'continua de manera automática hasta que finalices, no me preguntes más y tomas todas las decisiones que consideres necesarias',
                                             '2024 no tiene que estar bloqueado, usa todo lo que tenemos y necesites que nos lleve a mejorar significativamente el modelo'],
            'authority':'Existing direct participant requests and autonomy; this decision is Codex research judgment, not a new human signoff or orders from another AI.',
            'candidate':'F3c times own savedH1/G3, five fixed price members arithmetic mean. No REN FSp shape, new models, C0, level or calibration weights.',
            'source_recipe_author':'Claude for F3c base; Codex for H1 correction, validation, composition and transport',
            'CSV_source':spec,'message':send.MESSAGE,
            'hypothesis':'A source-only risk-weighted observation link removes a reproducible global-peril-mixture distortion and may improve the full F3c delivered model without adding capacity or unstable REN shape.',
            'support':{'source_safe_bases':{n:{k:a[k] for k in ['delta','bootstrap95','post31_delta','worst_cell_delta','direction_coherence']} for n,a in transfer['source_safe_bases'].items()},
                       'A1_2024_conditional_proxy':{k:transfer['conditional_A1_2024']['A1'][k] for k in ['delta','bootstrap95','post31_delta']},
                       'all_six_scenario_pooled_lower95_and_post31_positive':all(a['bootstrap95'][0]>0 and a['post31_delta']>0 for a in report['scenarios'].values())},
            'failed_or_unresolved_gates_preserved':{'phase2_formal_minimum_gain002_failed':True,
                                                  'reserve075_revaluation_motorNB2023_delta':-.004903875592920979,
                                                  'tail010_motorNB2023_delta':-.00426495479819371,
                                                  'full_historic_F3c_replay_available':False,'nested_future_ensemble_validation_available':False,
                                                  'weighted2025_ESS_gate_passed':False,'2024_pristine_holdout':False},
            'why_research_exception':'Consistent positive source-safe transfer, no concentration reversal after31groups, positive aggregate reserve/tail sensitivity and a simpler mechanism justify at most one measured research step. These do not establish all formal safeguards, full F3c gain or public0.17. Existing gates remain failed; PUL2 was not chosen despite its larger local point score.',
            'scope':'One research submission only when fresh quota permits; no promotion, retirement, final selection, extra probes, public level search or fallback upload.',
            'limits':report['limits']+['This is an adaptive public experiment, not independent confirmation or a guaranteed public improvement'],
            'required_before_upload':['Unchanged source/copy SHA and report hashes','Official skill dryrun5checks pass',
                                      'Fault-injected real transport flow without network, no blind retries',
                                      'Separate conditional research admission recorded in forum','Actual current quota>=1 and exact duplicate reconciliation',
                                      'Exclusive durable intent before at most1APIPOST; read and bind processed public receipt'],
            'budget':{'max_new_submissions':1,'new_fits':0,'new_C0_fits':0,'new_source_inference':0,'new_predictions':0},
            'formal_promotion':False,'promotion_gates_passed':False,'no_manual_final_selection':True,
            'B00_all_alternatives_preserved':True,'2024_open':True,'goal_achieved':False,
            'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(POLICY,policy)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro la revisión de una entrega de investigación H1, separada de la promoción formal y bajo la autorización directa ya dada para enviar y decidir sin nuevas preguntas. '
                    'Se preparará una copia exacta del CSV H1, dry run oficial y transporte de un único envío con control de duplicados y respuesta incierta. '
                    'La evidencia a favor es transferencia positiva en S0/S1/S2, concentración post31 positiva y sensibilidad agregada positiva en seis escenarios; '
                    'no se escoge PUL2 por su score local mayor. Permanecen el mínimo formal0,002 incumplido, deterioros NB bajo reservas/cola, replay F3c completo ausente, '
                    'validación anidada ausente y ESS insuficiente. Un resultado público no cambiará esos fallos. '
                    'La autorización anterior permite decidir una excepción de investigación; no se inventa aprobación humana o validación profesional. '
                    'Cero ajustes, C0, inferencias o predicciones nuevas; máximo un envío solo con cupo actual. Los prototipos históricos no se reescriben. '
                    'B00/F3c y alternativas intactos,2024abierto. Política: '+w.rel(POLICY)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-MISION017-H1-ENTREGA-PREVIO',
                        '--asunto','Revisión H1 de investigación: máximo un envío, sin promoción formal',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'policy_sha256':w.sha(POLICY),'forum':json.loads(res.stdout)})
    target=OUT/'codex_H1_observation_2025.csv';shutil.copyfile(ROOT/spec['path'],target)
    assert w.sha(target)==spec['sha256'] and target.stat().st_size==spec['bytes']
    copy=dict(spec,path=w.rel(target));dump(OUT/'copy_receipt.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
                                                                 'CSV':copy,'source':spec,'byte_identical':True,'new_predictions':0,'new_submissions':0})
    print(json.dumps({'prepared_copy':copy,'registration':json.loads(res.stdout),'new_submissions':0}))


def dryrun():
    assert not (OUT/'dryrun_receipt.json').exists()
    policy=w.read(POLICY);copy=w.read(OUT/'copy_receipt.json');spec=copy['CSV']
    assert w.sha(POLICY)==w.read(OUT/'registration.json')['policy_sha256']
    assert all(w.sha(ROOT/p)==h for p,h in policy['sources'].items())
    temp=OUT/'dryrun_tmp';temp.mkdir(exist_ok=True);env=dict(os.environ,TEMP=str(temp),TMP=str(temp),PYTHONIOENCODING='utf-8')
    sample=ROOT/'Hackaton/Repositorio_IAA2026/privado/semana2/envios/g4_20261025_v1/official_sample_format.csv'
    command=[str(ROOT/'Preparación/.venv-kaggle/Scripts/python.exe'),str(ROOT/'.agents/skills/kaggle/scripts/kaggle_skill.py'),
             'submit',send.SLUG,str(ROOT/spec['path']),'-m',send.MESSAGE,'--sample',str(sample)]
    assert '--yes' not in command
    res=subprocess.run(command,check=False,capture_output=True,text=True,encoding='utf8',env=env)
    log=OUT/'official_skill_dryrun.txt';log.write_text(res.stdout+res.stderr,encoding='utf8')
    assert res.returncode==0 and 'file check:  all 5 passed' in res.stdout and 'Dry run. Nothing was sent to Kaggle.' in res.stdout
    assert w.sha(ROOT/spec['path'])==spec['sha256']
    dump(OUT/'dryrun_receipt.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'CSV':spec,
                                  'official_skill_dryrun_all5passed':True,'receipt':w.rel(log),'receipt_sha256':w.sha(log),
                                  'official_sample':w.rel(sample),'official_sample_sha256':w.sha(sample),'no_yes_flag':True,
                                  'new_submissions':0,'workspace_temp_only_for_this_process':True})
    print(res.stdout)


def admit():
    assert not (OUT/'admission.json').exists()
    policy=w.read(POLICY);copy=w.read(OUT/'copy_receipt.json');dry=w.read(OUT/'dryrun_receipt.json');test=w.read(OUT/'transport_selftest.json')
    assert w.sha(POLICY)==w.read(OUT/'registration.json')['policy_sha256'] and copy['byte_identical']
    assert dry['official_skill_dryrun_all5passed'] and test['all_passed'] and test['network_calls']==0
    assert test['transport_code_sha256']==w.sha(Path(send.__file__))
    assert all(w.sha(ROOT/p)==h for p,h in policy['sources'].items())
    a={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'CSV':copy['CSV'],
       'research_submission_only':True,'formal_promotion':False,'promotion_gates_passed':False,
       'explicit_research_exception':True,'max_new_submissions':1,'execution_condition':'Fresh actual quota>=1, no duplicate and exclusive durable start. Not an immediate upload order from a prototype.',
       'no_final_selection':True,'human_authorization':'Prior direct submit request, ongoing autonomy and explicit2024opening. Codex research decision; no new human signoff.',
       'policy':w.rel(POLICY),'policy_sha256':w.sha(POLICY),'submission_code_sha256':w.sha(Path(send.__file__)),
       'dryrun_receipt_sha256':w.sha(OUT/'dryrun_receipt.json'),'transport_test_sha256':w.sha(OUT/'transport_selftest.json'),
       'source_report_hashes':{w.rel(p):w.sha(p) for p in [PROTOTYPE/'report.json',TRANSFER/'report.json',BASE/'enlace_HET_20261026_v1/report.json']},
       'failed_or_unresolved_gates_preserved':policy['failed_or_unresolved_gates_preserved'],
       'new_fits':0,'new_C0_fits':0,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    body=OUT/'forum_admission.md'
    body.write_text('Codex. Decisión explícita de investigación para un único CSV H1, SHA '+send.SHA+'. La copia y el dry run oficial de cinco controles pasaron; '
                    'el transporte real se probó con clientes sintéticos sin red para cuota cero, duplicados, respuesta incierta, reentrada, recibo pendiente/completo, '
                    'ref incorrecta, mensaje/tamaño y score privado inaccesible. La decisión usa la autorización directa previa y no inventa nueva aprobación humana. '
                    'Solo podrá hacerse un POST tras respuesta actual de cuota>=1 y conciliación de duplicados; sin reintentos ciegos o selección final. '
                    'Es excepción de investigación: los fallos de ganancia formal, reservas/cola NB, replay F3c completo, validación anidada y ESS permanecen. '
                    'No se afirma score0,17 ni promoción. B00/F3c y alternativas se conservan;2024abierto. Evidencia: '+w.rel(POLICY)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-MISION017-H1-ADMISION-INVESTIGACION',
                        '--asunto','H1: excepción de investigación condicionada a cupo, sin promoción formal',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    a['forum']=json.loads(res.stdout);dump(OUT/'admission.json',a)
    verified_spec,verified_path=send.source();assert verified_spec==copy['CSV'] and w.sha(verified_path)==send.SHA
    print(json.dumps({'conditional_research_admission':True,'max_submissions':1,'formal_promotion':False,'forum':a['forum']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','dryrun','admit']);args=parser.parse_args()
    {'prepare':prepare,'dryrun':dryrun,'admit':admit}[args.mode]()
