"""Fija fuentes/columnas y contratos antes de materializar valores de2023."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import entradas_g4_2023 as core
RUN=REPO/'privado/semana2/entradas_g4_2023/ingreso_20261024_v1'
PLAN=REPO/'registro/semana2_g4_entradas2023_plan_v1.json'
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    assert not PLAN.exists();RUN.mkdir(parents=True,exist_ok=False)
    coverage=REPO/'privado/semana2/desarrollo2023/coberturas_20261024T011932Z_14b50ca9'
    dev6=REPO/'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b'
    specs={}
    definitions=[]
    for line in ['motor','buildings','contents']:
        cols=core.META+(['period_start','period_end','exposure','x_new_business'] if line=='buildings' else [])
        definitions.append((line,coverage,'inputs_2023/'+line+'.parquet',cols,'prepared'))
    definitions += [('static',dev6,'inputs_2023/buildings.parquet',core.META+['period_start','period_end','exposure']+core.STATIC+['T0'],'prepared'),
        ('raw',dev6,'inputs_2023/raw_buildings.parquet',['row_id','policy_id','customer_id','address_id','period_start','period_end','exposure','sum_insured','written_premium','new_business','accidental_damage_cover'],'raw_periods'),
        ('claims',coverage,'inputs_2023/claims_buildings.parquet',core.KEY+['claim_id','policy_id','year','fold','group_id','included_in_T0','loss_date','report_date','peril','T0_cents'],'prepared')]
    proofs=[]
    for name,folder,subpath,cols,kind in definitions:
        p=folder/subpath;metadata=core.footer_proof(p,cols,kind)
        man=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        expected=next(x['sha256'] for x in man['files'] if x['path'].replace('\\','/')==subpath)
        assert core.sha(p)==expected,'Historical source changed: '+subpath
        specs[name]={'path':rel(p),'sha256':expected,'columns':cols,'kind':kind,'historical_manifest':rel(folder/'manifest.json')}
        proofs.append({'source':name,**metadata})
    frozen=[]
    for p in [REPO/'src/semana2/entradas_g4_2023.py',REPO/'src/semana2/ambitos_c0_b20_2023.py',REPO/'herramientas/preparar_entradas_g4_2023.py',REPO/'herramientas/probar_adaptador_entradas_g4_2023.py']:
        q=RUN/'preregistered_sources'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
        frozen.append({'path':rel(p),'sha256':core.sha(p),'snapshot':rel(q)})
    plan={'id':'S2-G4-ENTRADAS2023-v1-20261024','author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'authorization_literal':'Prepara el adaptador y las entradas estrictas de2023 para G4,sin ajustar modelos ni recalcular C0. Conserva B00,deja trazabilidad y bloqueos en foro y mantén2024cerrado.',
        'scope':'Prepare existing emerging2023 building base inputs and global three-line memberships only; no fitting,prediction,scoring,C0 estimation or new information claim.',
        'sources':specs,'frozen_code':frozen,'forum_prior':'COD-S2-20261024-061',
        'reader_contract':'Pinned SHA and row-group min=max2023(or raw period dates2023),false test when supplied,explicit columns before decode. Missing/mixed statistics fail closed.',
        'output':'Separate metadata,unlearned periods,targets,claims and capital-audit files by saved fold; five outer and ten unique inner file lists. No C0 or learned features copied.',
        'capital':'Keep original sum insured and written premium in audit-only table. No x_log_sum_insured produced until exact-scope frozen parameters exist. Application helper never estimates them.',
        'target':'Preserve observed T0; integer-cent comparison against inherited included claims only checks the new copies,no revaluation,claim deletion or target correction.',
        'temporal':'Loss/policy cohort2023; report dates through original valuation2024-12-31 are follow-up of those occurrences,not opening2024 policy cohort.',
        'scope_contract':'Only allowed fold data files are opened for learning inputs; protected fold metadata retained,protected values absent. Training signature excludes protected payload hashes.',
        'validation':['new-reader year/hash/path rejection before decoding','component/key integrity without new folds','new-copy T0/claim reconciliation','all15scope file lists disjoint','one outer and one inner scope with protected-file opens forbidden','no-capital/wrong-scope rejection and pure synthetic application','model/C0 fit and model load/network entrypoints blocked'],
        'no_old_diagnostics':['support/concentration','calibration/score','climate','reserve/tail sensitivity','original exposure reconciliation','C0/GLM suites'],
        'all_fit_calls':0,'C0_values_created':0,'new_predictions':0,'new_scores':0,'new_features_admitted':False,
        'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_closed':True,'promotion':False,'professional_independent_validation':False}
    PLAN.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (RUN/'plan_snapshot.json').write_bytes(PLAN.read_bytes());(RUN/'preregistration_footer_proofs.json').write_text(json.dumps(proofs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=RUN/'forum_061_pre.md';body.write_text('''Codex, preinscripción de ingreso G4 solicitado: entradas reales existentes de2023 y adaptador sin modelos,C0 o inferencias. Plan: registro/semana2_g4_entradas2023_plan_v1.json. Se verificaron solo footers/SHA de seis fuentes ya recortadas2023 antes de decodificar valores. No se llama a productores multiaño ni se abre2024/test/ledger/actas/SEL01.

Fuentes: pertenencias de tres ramos de la auditoría de coberturas2023; seis características estáticas,T0 y capital/premium raw de entradas base dev6; notificaciones heredadas de edificios2023. Lectura con SHA fijado,whitelist de columnas y estadísticas de ámbito por grupo de filas; sin prueba de año se rechaza antes de decodificar. No se leen columnas C0,predicciones,curvas,imputaciones o correcciones de capital exteriores.

Salidas privadas por fold: periodos sin aprendizaje,objetivos observados,notificaciones incluidas y capital/premium separado para auditoría; metadatos de pertenencia globales y15ámbitos lógicos. Folds/componentes originales conservados,sin resorteo. T0 solo se concilia en centavos contra los siniestros heredados para verificar estas copias,no se revalúa. El reporte tardío de una ocurrencia2023 puede ser de2024 según valoración original; no es abrir cohorte2024.

Dependencia explícita: CAPS2-01 aprendía referencias por ámbito. No se copia x_log_sum_insured exterior a interiores ni se usan medias/umbrales aprendidos de otro fold. Capital original y prima quedan en tabla de auditoría,fuera de los seis predictores no aprendidos. La séptima variable necesita parámetros futuros del mismo ámbito; la función de aplicación no los estima y rechaza ausencia/otro ámbito. No se etiqueta dato real como fixture para forzar entrada al módulo sintético.

Validación nueva del ingreso: año mixto/hash alterado/rutas de modelo o score rechazados antes de lectura; claves/componentes; listas de archivos de cinco exteriores y diez interiores; dos lectores de ámbito que prohíben abrir valores protegidos; aplicación de capital con parámetros ficticios fijos. Se bloquean fit de modelos,C0,cargas de estimadores y red durante preparación. No se repiten diagnósticos de soporte,clima,reservas,exposición o desempeño.

B00/alternativas,T0/C0/folds/modelos/contadores conservados. G1/G2 y objetos internos aprendidos siguen pendientes; esta preparación no autoriza entrenamiento,envío o promoción. Sin contactos externos,otros chats,delegación o programación. Ventana nocturna cerrada. Autor Codex,revisión técnica propia,sin aprobación humana o validación profesional independiente.
''',encoding='utf-8')
    out=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',plan['forum_prior'],'--asunto','G4: preinscripción del adaptador y entradas2023 sin ajuste ni recálculo C0','--cuerpo',str(body)],capture_output=True,text=True)
    assert out.returncode==0,out.stderr;(RUN/'forum_prior_receipt.json').write_text(out.stdout,encoding='utf-8')
    print(json.dumps({'plan':rel(PLAN),'sha256':core.sha(PLAN),'sources':len(specs),'forum_prior':plan['forum_prior'],'rows_decoded':0},ensure_ascii=True))

if __name__=='__main__':main()
