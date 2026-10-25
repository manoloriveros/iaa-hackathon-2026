"""Congela consumidor final de2023 y fuentes permitidas antes de ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(REPO/'herramientas'))
import pyarrow.parquet as pq
from semana2 import entradas_g4_2023 as ingress,modelo_final_g4_2023 as core
from entrenar_y_predecir_final_g4_2023 import prove_source
RUN=REPO/'privado/semana2/modelo_final_g4_2023/final_20261024_v1'
PLAN=REPO/'registro/semana2_g4_modelo_final_plan_v1.json'
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    assert not PLAN.exists();RUN.mkdir(parents=True,exist_ok=False)
    recipe= json.loads((REPO/'registro/semana2_g4_modelo_envio_preparacion_v1.json').read_text(encoding='utf-8'))['recipe']
    dev=REPO/'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b'
    cov=REPO/'privado/semana2/desarrollo2023/coberturas_20261024T011932Z_14b50ca9'
    data=ROOT/'Hackaton/Semana 2/Datos/emerging'
    specs={};proof=[]
    def add(name,path,columns,kind,historical_folder=None,subpath=None):
        expected=ingress.sha(path)
        if historical_folder is not None:
            m=json.loads((historical_folder/'manifest.json').read_text(encoding='utf-8'))
            assert expected==next(x['sha256'] for x in m['files'] if x['path'].replace('\\','/')==subpath)
        spec={'path':rel(path),'sha256':expected,'columns':list(dict.fromkeys(columns)),'kind':kind}
        proof.append({'source':name,**prove_source(path,spec)});specs[name]=spec
    for line in core.LINES:
        block=recipe['features_by_line'][line];cover='cover_type' if line=='motor' else 'accidental_damage_cover'
        cols=ingress.META+['period_start','period_end','exposure','T0']+[c for c in block['all'] if c not in ['x_log_sum_insured','x_cover_type']]
        sub=f'inputs_2023/{line}.parquet';add('static_'+line,dev/sub,cols,'prepared',dev,sub)
        add('coverage_'+line,cov/sub,ingress.META+['period_start','period_end','exposure','x_new_business',cover],'prepared',cov,sub)
        sub=f'inputs_2023/claims_{line}.parquet';add('claims_'+line,cov/sub,core.KEY+['claim_id','policy_id','year','fold','group_id','included_in_T0','loss_date','report_date','peril','T0_cents'],'prepared',cov,sub)
        if line!='motor':
            sub=f'inputs_2023/raw_{line}.parquet';add('raw_'+line,dev/sub,['row_id','period_start','period_end','sum_insured','written_premium'],'raw_periods',dev,sub)
        quote=['row_id','policy_id','customer_id','address_id','period_start','period_end','exposure','new_business']
        quote+=['ncb_years','vehicle_age','vehicle_value_group','driver_age_band','cover_type'] if line=='motor' else ['sum_insured','written_premium','accidental_damage_cover']+(['high_value_items'] if line=='contents' else [])
        add('test_'+line,data/f'test_{line}.parquet',quote,'quotes2025')
    add('addresses',data/'addresses.parquet',['address_id','region','property_type','year_built','flood_zone','bedrooms'],'address_master')
    add('sample',data/'sample_submission.parquet',['row_id'],'sample')
    frozen=[]
    for name in ['src/semana2/modelo_final_g4_2023.py','src/semana2/c0_estricto2023.py','src/semana2/ambitos_c0_b20_2023.py',
        'src/semana2/entradas_g4_2023.py','src/semana2/preparar_base.py','herramientas/probar_modelo_final_g4_2023.py','herramientas/entrenar_y_predecir_final_g4_2023.py']:
        p=REPO/name;q=RUN/'preregistered_sources'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes());frozen.append({'path':rel(p),'sha256':ingress.sha(p),'snapshot':rel(q)})
    plan={'id':'G4-GLM23-FINAL-DEPLOYMENT-v1-20261024','author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'forum_prior':'COD-S2-20261024-069','authorization_literal':'continua de manera automática hasta que finalices,no me preguntes más y tomas todas las decisiones que consideres necesarias',
        'authorization_interpretation':'Complete own standard model and Kaggle-ready CSV,including needed full2023 capital/C0/GLM and2025inference.No2024policy learning/scoring,no account upload or final promotion.',
        'scope':core.SCOPE,'reference':'W2-B00','recipe':recipe,'sources':specs,'frozen_code':frozen,
        'target':'Inherited observed netT0; responseT0/C0,weights sqrt(C0),rho1,tail0;future prediction=nominal reconciled2025exposure*rate.',
        'full_scope':'All eligible emerging2023rows,no heldout exclusions. Distinct final deployment object,never an outer-fold artifact renamed.',
        'perils':core.PERILS,'capital_thresholds':core.CAP_LIMIT,'exposure':'Existing deterministic inclusive days/365 rounded4; only declared days-unit/basis360 corrections.',
        'hypothesis':'Standard main-effects GLM already specified in B20 can be fitted in the final all2023scope and replayed without adjustments to generate own2025CSV; no new calibration,climate,trend or ML family.',
        'criteria':['synthetic full chain3branches passes before real fitting; rejects non2023training and outer-capital reuse',
            'source/hash/column and date-footer guards;no quote/master/sample decoders until all3real GLMs fitted',
            'T0/claim integer-cent reconciliation;C0 positive;calendar integration check<=1e-12',
            'GLM convergence maxiter2000,tol1e-6 and penalized gradient<=1e-4',
            'manual exp(Xbeta+intercept) and Tweedie weight identity rtol1e-12/atol1e-9',
            'same trained state before/after2025inference;disk replay all209063rows exact with all fits blocked',
            'CSV209063uniqueIDs exact official sample order,finitepositive values,roundtrip exact;no padding/clipping'],
        'budgets':{'synthetic_GLM_fits':3,'synthetic_reporting_fits':15,'real_GLM_fits':3,'real_reporting_fits':15,'real_frequency_constants':15},
        'validation_policy':'Reuse previous2023OOF evidence;no repeat fold training/bootstrap.No2024opening.Training diagnostics do not measure generalization.',
        'no_adaptive_selection':True,'no_calibration_slope':True,'all_alternatives_preserved':True,'promotion':False,'manual_final_selection':False,
        'submission_sent':False,'external_actions':'None;end at verified ownCSV locally.','professional_independent_validation':False}
    PLAN.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(RUN/'plan_snapshot.json').write_bytes(PLAN.read_bytes())
    (RUN/'source_footer_proofs.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=RUN/'forum_069_pre.md';body.write_text('''Codex,preinscripción del ámbito final propio tras la autorización del participante de continuar automáticamente sin preguntas.Plan:registro/semana2_g4_modelo_final_plan_v1.json.

Se completa el modelo yCSVlocal propios:capital,C0 yGLMfinales ajustados solo en2023,aplicación nominal2025 y replay.No abrir2024políticas,ledger,actas oSEL01;seguimiento de siniestros2023al corte2024-12-31 conserva su papel original.B00/alternativas y adversos históricos permanecen.No promoción o selección final formal,ni envío a cuentaKaggle en esta preparación.

Misma receta estándarB20:GLMTweedie1,5,alpha1,siete efectos por ramo,mediana/escala yOHEsoloajuste.Sin tendencia,clima,credibilidad,calibración de nivel/pendiente o búsqueda de hiperparámetros.Ámbito finaltodo2023distinto de folds:C0rho1/tail0ycapital normal por ramo aprendidos aquí;no renombrar objetos exteriores.ConservarT0yexposición.Cotización2025usaexposición nominal corregida por regla histórica,no completitud observada2023.

Fuentes:proyecciones estrictas2023dev6/coberturas yrawcapital;testoficial emergente2025,maestroestático de direcciones yplantilladeIDs.TodosSHAycolumnasfijados,footers2023/2025antesdedecodificar.Lectores detest/maestro/plantilla bloqueados hasta terminar los3GLMreales.Ningúnproductorhistórico multiaño.

Prueba focal sintética previa3ramos;rechazo2024sintético/ámbito exterior.Capital/C0declaradosporámbitofinal,15curvas por rama/peril en total.Presupuesto3GLMsintéticos+3reales,15curvasreporte sintéticas+15reales y15frecuenciasreales.No repetirOOF/bootstrapde2023.Susresultadospreviosno seconvierten en validación independiente.

Criteriosantesdeajuste:conciliacióncentavos,completitudpositiva,integraciónC0vscalendario<=1e-12;convergencia2000/tol1e-6ygradiente penalizado<=1e-4;predicciónmanualeidentidadpesosrtol1e-12/atol1e-9;estadoaprendidosincambiosalpredecir,replaydiscoexactoconfitsbloqueados yCSV209063IDsenorden,preciospositivosfinitos,sinrellenooclipping.Guardarfallosantesdecualquierreparación,concriteriosintactos.

AutorCodex,verificaciónpropiaexploratoria;no aprobaciónhumana delmodelo o revisiónprofesional independiente.Ventana nocturna cerrada,sin nuevos chats,delegación,publicación,remotooautomatizaciones.
''',encoding='utf-8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',plan['forum_prior'],
        '--asunto','G4: receta finaltodo2023 yCSVpropio2025,preinscripción de ajuste estándar autorizado','--cuerpo',str(body)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr;(RUN/'forum_prior_receipt.json').write_text(p.stdout,encoding='utf-8')
    print(json.dumps({'plan':rel(PLAN),'forum_prior':plan['forum_prior'],'sources':len(specs),'frozen_code':len(frozen),'new_fits':0},ensure_ascii=True))

if __name__=='__main__':main()
