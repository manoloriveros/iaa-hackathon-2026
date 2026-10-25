"""Fija ejecución real autorizada antes de estimar referencias de capital."""
from pathlib import Path
from datetime import datetime, timezone
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import entradas_g4_2023 as ingress
RUN=REPO/'privado/semana2/capital_real_g4_2023/produccion_20261024_v1'
PLAN=REPO/'registro/semana2_g4_capital_real_plan_v1.json'
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    assert not PLAN.exists();RUN.mkdir(parents=True,exist_ok=False)
    prior=REPO/'registro/semana2_g4_productor_capital_actual.json';idx=json.loads(prior.read_text(encoding='utf-8'))
    assert idx['producer_receipt_connection_synthetic_verified'] and idx['contract_checks']==63
    prepared=json.loads((REPO/'registro/semana2_g4_entradas2023_actual.json').read_text(encoding='utf-8'))['input_manifest']
    assert ingress.sha(ROOT/prepared['path'])==prepared['sha256']
    frozen=[]
    for name in ['src/semana2/productor_capital_g4_2023.py','src/semana2/conexion_g4_2023.py','src/semana2/entradas_g4_2023.py',
        'src/semana2/ambitos_c0_b20_2023.py','herramientas/generar_capital_real_g4_2023.py','registro/semana2_g4_capital_contrato_v2.json']:
        p=REPO/name;q=RUN/'preregistered_sources'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
        frozen.append({'path':rel(p),'sha256':ingress.sha(p),'snapshot':rel(q)})
    plan={'id':'S2-G4-CAPITAL-REAL2023-v1-20261024','author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'forum_prior':'COD-S2-20261024-067','input_manifest':prepared,'frozen_code':frozen,
        'authorization_literal':'Genera los parámetros de capital por ámbito con entradas reales2023 y valida conexión a G4,sin ajustar modelos ni recalcular C0;conserva B00,deja resultados en foro y mantén2024cerrado.Prepara CSV para Kaggle.',
        'recipe':'CAPS2-01-SCOPE-v2 and G4-INPUT-CONNECTION-2023-v2 unchanged; same five saved outer folds and ten unique inner pairs.',
        'criteria':['15exact-scope parameter artifacts and15base feature views with original period/target membership',
            'producer and independent reference read metadata/capital only; protected value files never opened in each scope',
            'normal bounds versus Decimal absolute error<=1e-12; corrected log versus Decimal/math.log error<=1e-12 and identical missing decisions',
            'population receipt replay agrees with permitted raw capital; no fallback,band change or row deletion',
            'all model/preprocessor fit,predict,C0 fit/apply,model load and network entrypoints blocked'],
        'budgets':{'real_capital_parameter_artifacts':15,'real_feature_views':15,'model_fits':0,'C0_calls':0,'predictions':0,'scores':0},
        'previous_synthetic_verification':idx['validation'],'synthetic_suite_rerun':False,
        'kaggle_preparation':'Separate reuse/preflight of existing2025CSV only if provenance compatible; not a G4 trained prediction,not promotion or upload. No2024ledger/actas/SEL01.',
        'B00_preserved':True,'2024_closed':True,'G4_full_flow_not_closed_by_this_work':True}
    PLAN.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(RUN/'plan_snapshot.json').write_bytes(PLAN.read_bytes())
    body=RUN/'forum_067_pre.md';body.write_text('''Codex,preinscripción de producción real de capital solicitada tras066. Plan: registro/semana2_g4_capital_real_plan_v1.json. Mismo productor/contrato v2,regla CAPS2-01 y folds2023 ya verificados;no se repite suite sintética.

Quince ámbitos (5exteriores,10pares interiores): producir límites solo desde capital/prima permitidos,guardar población/recibo/artefacto,reproducirlos por la conexión G4 y conservar quince vistas privadas de predictores. Sin eliminar periodos o siniestros,modificar T0/exposición/folds,usar referencias exteriores en interiores o crear fallback. Comparación independiente con Decimal de límites y con Decimal/math.log de capital corregido,tolerancia absoluta1e-12 y decisiones de ausencias idénticas; discrepancias bloquean y se archivan sin retocar límites.

Lecturas solo de entradas ya estrictas2023 y sus proyecciones declaradas. Se prohíbe abrir valores protegidos en cada ámbito. Fit/predict de modelos y preprocesadores,C0 fit/apply,cargas de estimadores y red bloqueados. Presupuesto15parámetros/15vistas,0modelos/C0/inferencias/scores. El avance es conexión real de entradas base,no flujo de aprendizaje completo ni G1/G2 resueltos.

El participante también pide CSV para Kaggle. Su preparación se separa: revisar predicciones2025ya existentes con trazabilidad compatible y contrato de archivo,sin presentar estos parámetros como modelo G4 entrenado o promover por scores. No subir o puntuar bajo esta preparación,ni abrir2024/ledger/actas/SEL01. Si no hay un CSV compatible,se documentará el faltante concreto. B00 y alternativas conservados. Autor Codex,verificación propia exploratoria;sin aprobación humana inventada,delegación,otros chats,publicación,remoto o automatizaciones;ventana nocturna cerrada.
''',encoding='utf-8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',plan['forum_prior'],
        '--asunto','G4: producción real de capital2023 por ámbito y preparación separada del CSV,preinscripción','--cuerpo',str(body)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr;(RUN/'forum_prior_receipt.json').write_text(p.stdout,encoding='utf-8')
    print(json.dumps({'plan':rel(PLAN),'forum_prior':plan['forum_prior'],'frozen_files':len(frozen),'real_parameter_artifacts':0},ensure_ascii=True))

if __name__=='__main__':main()
