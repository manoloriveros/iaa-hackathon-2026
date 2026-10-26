"""Registra adversos y continuidad; no termina ni bloquea la misión 0,17."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
spec=importlib.util.spec_from_file_location('statewriter',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
P=R/'registro/semana2_mision017_fase2_actual.json';BASE=R/'privado/semana2/mision017_fase2'
read=w.read;sha=w.sha;rel=w.rel


def main():
    specs=[(3,BASE/'tanda3_20261025_v3','N0',['Q1','Q2','Q3']),
           (4,BASE/'tanda4_marketing_20261025_v1','N3',['R1','R2','R3'])]
    for number,out,ref,names in specs:
        assert (out/'validation_v1/report.json').exists() and not (out/'completion_receipt.json').exists()
        validation=read(out/'validation_v1/report.json');assert len(validation['replays'])==15
        assert not any(x['exploratory_pass'] for x in validation['comparisons'].values())
    stamp=datetime.now(timezone.utc);local=stamp.astimezone(timezone(timedelta(hours=-5)))
    archive=BASE/'cortes_tandas3_4'/stamp.strftime('%Y%m%dT%H%M%SZ');archive.mkdir(parents=True)
    summaries=[];notes=[]
    for number,out,reference,names in specs:
        report=out/'price_report.json';validation=out/'validation_v1/report.json';v=read(validation)
        summary={'batch':number,'output':rel(out),'status':'completed_exploratory_no_admission',
            'price_report':rel(report),'price_report_sha256':sha(report),'validation':rel(validation),'validation_sha256':sha(validation),
            'reference':reference,'scores':v['scores'],'exploratory_pass':[],'new_price_estimator_fits':3,
            'new_source_reporting_reconstructions':15 if number==3 else 0,'new_emerging_C0_fits':0,'submissions':0}
        summaries.append(summary)
        title=('CatBoost fuente 2021–2024 y mezclas fijas' if number==3 else 'GLM fuente para marketing_segment')
        note=f'\n\n## {title}, {local.date().isoformat()} (Bogotá)\n\nCodex, {stamp.isoformat()}. '
        if number==3:
            note+=('La fuente de2.409.311periodos desarrollados quedó reconstruida con las variables comunes de F2. '
                'Se cotejaron las15CDF de coste maduro, las mezclas por peril y T0 por año con el antecedente de Claude. '
                'Los274siniestros anteriores a la cobertura disponible se preservan para reproducir el uso histórico en la CDF; no se asignan a periodos inventados. '
                'Se entrenaron tres CatBoost conservadores, con600rondas fijas, depth5 y pérdida Tweedie1,5. '
                'La versión inicial de integración falló por el control de orden de multiplicación: la diferencia máxima era2,28e-13CU. '
                'El modelo terminado de autos se conservó y reutilizó porSHA; solo se ajustaron después edificios y contenidos. No hubo un segundo ajuste de autos.\n\n')
        else:
            note+=('La auditoría sin costes de488.180clientes históricos desarrollados mostró asociación entre marketing_segment y credit_band (I=0,99777nats), con12categorías compartidas por los históricos y el test emergente. '
                'Eso motivó un GLM fuente de un efecto comercial, con región/año como nuisance y regularización0,1. Solo se transfirió el efecto comercial; no se inventó credit_band emergente. '
                'Los precios N3 se multiplicaron por el efecto con fuerzas1,0,5,0,25 y se conservaron los totales por ramo/negocio mediante normalizadores de covariables y predicciones, sin etiquetas retenidas. '
                'La asociación de perfiles no demostró una mejora predictiva transportable.\n\n')
        note+='| Variante | D² local | Diferencia | IC95 por componentes | Después de retirar31grupos favorables |\n|---|---:|---:|---|---:|\n'
        for name in names:
            z=v['comparisons'][name];ci=z['bootstrap95']
            note+=f'| {name} | {v["scores"][name]:.6f} | {z["delta"]:+.6f} | [{ci[0]:+.6f}; {ci[1]:+.6f}] | {z["after_remove31_delta"]:+.6f} |\n'
        note+=f'\nReferencia de esta comparación: {reference}={v["scores"][reference]:.6f}. Ninguna variante cumple todos los criterios preinscritos. '
        note+='Se conservan los adversos, B00, F2 y todas las alternativas; no se promueve ni retira ningún modelo por este score.\n\n'
        if number==3:
            note+=('Los15ámbitos reales se reprodujeron con ajuste bloqueado; se verificaron las45condiciones de primer orden de los niveles aprendidos dentro del ámbito. '
                'Los cambios de etiquetas retenidas no alteraron los predictores ni las predicciones reproducidas. '
                'Coste de la tanda:3estimadores fuente,15CDF empíricas reconstruidas para las entradas y48constantes de precio; cero nuevos ajustes de C0 emergente.\n\n')
        else:
            note+=('Los15ámbitos se reprodujeron exactamente y conservaron sus totales; alterar etiquetas no cambió el overlay. '
                'La codificación dispersa se reconstruyó por otro método, el objetivo se cotejó con scikit-learn y las derivadas del GLM con diferencias finitas en los tres ramos. '
                'Coste:3GLM fuente y90normalizadores de cartera que no leen etiquetas; cero nuevas curvas C0 o niveles entrenados en el emergente.\n\n')
        note+=('2024 es desarrollo adaptativo autorizado, no un holdout intacto. El ámbito de fuente incluye2024 para información disponible al inicio de2025; no se afirma un backtest prospectivo de2024. '
            'La incertidumbre de cola, reservas, maestros sin fecha y semántica entre mercados sigue abierta. Los intervalos condicionan en los modelos fuente fijados. '
            'No es revisión profesional independiente. No hubo envíos ni consultas de nuevos scores para decidir estas recetas. La última marca pública conciliada del equipo es0,16033, inferior a0,17.\n\n')
        note+='Evidencia: '+rel(validation)+'.\n'
        notes.append(note)
        doc=R/f'docs/semana2/MISION017_FASE2_TANDA{number}_RESULTADOS.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
        body=out/'forum_resultado.md';body.write_text(note,encoding='utf8')
        p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
            '--id',f'COD-S2-20261025-MISION017-FASE2-TANDA{number}-RESULTADO',
            '--asunto',title+': mejora insuficiente o incierta, sin enviar','--cuerpo',str(body)],
            check=True,capture_output=True,text=True,encoding='utf8')
        summary['forum']=json.loads(p.stdout)
        files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and 'state_cuts' not in p.parts}
        (out/'closure_manifest.json').write_text(json.dumps({'utc':stamp.isoformat(),'files':files},indent=2),encoding='utf8')
        (out/'completion_receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    counters=R/'registro/semana2_contadores_propios_actual.json';counter=read(counters)
    assert 'phase2_2024_tanda3' not in counter and 'phase2_2024_tanda4' not in counter
    w.update(counters,{'as_of_utc':stamp.isoformat(),'cumulative_price_base_fits':counter['cumulative_price_base_fits']+6,
        'cumulative_closed_form_constants':counter['cumulative_closed_form_constants']+48,
        'supplementary_reporting_peril_fits_since_counter_start':counter['supplementary_reporting_peril_fits_since_counter_start']+15,
        'phase2_2024_tanda3':{'source_price_fits':3,'motor_reused_not_refitted':True,'empirical_source_cost_CDF_reconstructions':15,
            'new_target_C0_fits':0,'closed_form_price_levels':48,'source_cost_mixtures_reconstructed':3,'receipt':summaries[0]},
        'phase2_2024_tanda4':{'source_GLM_fits':3,'new_C0_fits':0,'new_target_label_fitted_levels':0,
            'covariate_only_portfolio_normalizers':90,'source_year_initialization_values_not_independent_models':12,'receipt':summaries[1]},
        'latest_phase2_index':rel(P)},archive)
    next_unit=('Revisar las unidades y el papel de written_premium en la fuente desarrollada y el emergente, sin confundir prima cobrada con objetivo de riesgo. '
        'La hipótesis siguiente es un GLM fuente de información tarifaria residual, con prima anual correctamente tratada, frente al padre de F2; '
        'los intentos anteriores T1wp/T3wp dividían prima por exposición y el M3 propio usó la prima como offset dominante. '
        'Primero comprobar la unidad en fuente y condiciones por año/negocio/exposición; no declarar todavía que una nueva receta esté implementada o admitida. '
        'Si queda una necesidad concreta, congelar variables, código, criterio y coste y publicar antes del ajuste. '
        'Reutilizar las75curvas por ámbito y los datos fuente cerrados; no repetir CatBoost, marketing, sus replays o sus remuestreos con fuentes iguales. '
        'Mantener2024abierto por autorización humana, B00, F2 y alternativas, y conservar cupos. Ningún trabajo propio sigue en ejecución.')
    phase=read(P);completed=phase.get('completed_batches',[])
    if not completed:
        completed=[{'batch':1,'validation':'Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/tanda1_20261025_v2/validation_v1/report.json'},
                   {'batch':2,'validation':'Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/tanda2_20261025_v1/validation_v1/report.json'}]
    completed+=summaries
    w.update(P,{'utc':stamp.isoformat(),'status':'active','current_batch':summaries[1],'previous_batch':summaries[0],
        'completed_batches':completed,'active_execution':None,'active_jobs':[],'next_unit':next_unit,
        'new_price_fits':18,'new_C0_fits':105,'new_emerging_C0_fits':75,'new_source_C0_fits':30,
        'new_closed_form_levels':159,'new_covariate_only_portfolio_normalizers':90,'new_submissions':0,
        'marketing_admission_report':rel(BASE/'admisibilidad_campos_comunes_v1/report.json'),
        '2024_open':True,'2024_closed':False,'goal_achieved':False},archive)
    w.update(ROOT/'Preparación/ESTADO_PROYECTO.json',{'week_2_mission017_phase2_20261025':{
        'status':'active','phase':rel(P),'current_batch':summaries[1],'2024_open':True,'2024_closed':False,
        'active_jobs':[],'goal_achieved':False,'next_unit':next_unit},'week_2_mission017_phase2_execution':None},archive)
    combined=''.join(notes)+'\n\nSiguiente unidad vigente: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,combined,archive)
    print(json.dumps({'goal_status':'active','batches_closed':[3,4],'new_source_price_fits':6,'phase_price_fits':18,
        'source_C0_reconstructions':15,'target_C0_refits':0,'new_submissions':0,'active_jobs':[],
        '2024_open':True,'goal_achieved':False,'forum_ids':[x['forum']['id'] for x in summaries]}))


if __name__=='__main__':main()
