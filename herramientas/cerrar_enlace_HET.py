"""Conserva ambos resultados HET y registra la siguiente pregunta sin ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/enlace_HET_20261026_v1'
sp=importlib.util.spec_from_file_location('HET_closure_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');assert len(report['numeric_controls'])==30
    assert len(list(OUT.glob('learning_*.json')))==30
    c=report['constants_unique'];learned=sum(c[k] for k in ['shape_factors','component_levels','residual_factors','nuisance_levels'])
    assert learned==710
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    proposal_path=R/'registro/semana2_forma_ultima_observacion_propuesta_v0.json';assert not proposal_path.exists()
    proposal={'author':'Codex','utc':stamp.isoformat(),'status':'proposal_only_not_registered_for_price_score',
        'question':'The old RFSobserved-cost ratio conflates ultimate FSp risk shape and peril-completion mismatch. Separate them, preserving all models, weights, cohorts and adverse assays.',
        'identity':'old_RFS_ratio = pure_ultimate_ratio*(q_saved_outer_risk/q_global), where pure_ultimate_ratio=sum(kappa*f*s)/(T2b_annual_raw*calendar_exposure). f already contains calendar exposure once. Verify algebra on pinned inputs before fitting/pricing.',
        'primary':'PUL2: savedH1observedcost prices times pure_ultimate_ratio^w on renewals only, normalized per line/year/REN preservingH1totals. No new source fit,C0,kappa or target calibration.',
        'companion':'PUL1: same ultimate-only shape on savedG3, declared ablation to distinguish observation-link interaction; no post-score switch of winner.',
        'fixed_weights_REN':{'motor':.25,'buildings':.25,'contents':.5},
        'NB':'PUL2NBidenticalH1NB;PUL1NBidenticalG3NB. Do not reintroduce failed NB_FSp changes.',
        'source_of_H1':'Declared secondary ablation of completedHET; now used as an exploratory component by a documented adaptive decision, not promoted or re-tested as independent evidence. H2 remains originalprimary and is retained with its failures.',
        'criterion':'Preserve primary pooleddelta>=.002,lower95>0,>=4positivefolds,bothyears>=0,post31>=0,worstline/year/business>=-.001, plus incremental vsH1 and NBidentity controls. Weighted2025point nonnegative is additional consideration,ESSfailure persists. No formal promotion or automatic upload.',
        'budget_if_registered':{'new_source_fits':0,'new_target_estimator_fits':0,'new_C0_fits':0,'new_kappa_fits':0,
            'new_source_inference':0,'held_prediction_only_normalizers':60,'new_final_test_prices':0,'new_submissions':0},
        'before_price_score':['Verify source/outer C0and kappa memberships and parentH1OOFmapping',
            'Verify exact decomposition and exposure-once math; isolate ultimate ratio from q/T0/reserve/count fields',
            'Synthetic/adverse identity and replay, finitepositivevalues, zero-weightbaseline, independentlog/scalar math',
            'Freeze code/config/cost/criterion and forum comment before creating/scoring new historical prices'],
        '2024_open':True,'B00_F3c_all_alternatives_preserved':True,'goal_achieved':False}
    proposal_path.write_text(json.dumps(proposal,ensure_ascii=False,indent=2),encoding='utf8')
    next_unit='Prepare PUL1/PUL2 from fixed savedG3/H1and cached FSp/kappa: first verify old_RFSratio=pure_ultimate_ratio*(q_outer/q_global), current group ancestry and exposure once. Keep previousweights RENonly; no new C0/models/kappa, no NB_FSp. PrimaryPUL2is a NEW documented adaptive composition, not retrospective H1promotion. Register recipe/controls/cost/forum before any new price or score.2024open;B00/F3c0.16914and quota preserved.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'complete_exploratory_no_admission','primary':'H2',
        'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'results':{name:{k:r[k] for k in ['scores','delta_vs_G3','bootstrap95','gates','weighted2025_sensitivity_delta']} for name,r in report['results'].items()},
        'new_iterative_model_fits':0,'new_closed_price_constants':710,'new_C0_fits':0,'new_kappa_fits':0,
        'new_final_test_prices':0,'new_submissions':0,'formal_admission':False,'submission_allowed':False,
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'next_unit':next_unit,
        'next_proposal':w.rel(proposal_path),'next_proposal_sha256':w.sha(proposal_path)}
    cp=R/'registro/semana2_contadores_propios_actual.json';counter=w.read(cp);assert 'phase2_HET' not in counter
    w.update(cp,{'as_of_utc':stamp.isoformat(),'cumulative_closed_form_constants':counter['cumulative_closed_form_constants']+710,
                 'phase2_HET':{'unique_closed_price_constants':710,'breakdown':c,'control_recomputations_separate':c,
                               'new_iterative_fits':0,'new_C0_fits':0,'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json')}},archive)
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'HET':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(HET=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    index=R/'registro/semana2_enlace_HET_actual.json';assert not index.exists();index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    note='\n\n## HET: enlace por riesgo, resultados y separación de forma última, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se completó el contraste de exposición, conservando T0, modelos fuente, C0, reglas y folds. '
    note+='H2 fue el primario preinscrito (perfil exterior con kappas guardadas); H1 fue la ablation fuente sola. No se intercambian después del resultado.\n\n'
    for name,r in report['results'].items():
        note+=f'{name}: D² {r["scores"][name]:.8f}, diferencia frente a G3 {r["delta_vs_G3"]:+.8f}, IC95 [{r["bootstrap95"][0]:+.8f}, {r["bootstrap95"][1]:+.8f}]. '
        note+='Gana en cinco folds y ambos años. '
        note+=f'Tras retirar los 31 grupos más favorables: {r["post31_delta"]:+.8f}; sensibilidad ponderada de cartera 2025: {r["weighted2025_sensitivity_delta"]:+.8f}, con ESS insuficiente. '
        note+='Fallos: '+', '.join(k for k,v in r['gates'].items() if not v)+'.\n\n'
    note+='Ninguno cumple todos los criterios. H1 solo falla la magnitud mínima; eso no lo convierte en ganador confirmado ni habilita envío. '
    note+='H2 también falla una celda de ramo/año/negocio. No se baja el umbral +0,002 ni se ocultan celdas. '
    note+='Las dos direcciones positivas aportan evidencia exploratoria para revisar la observación antes de más capacidad.\n\n'
    note+='Los 30 flujos pasaron alteración de T0/reservas retenidos, replay exacto con todo el aprendizaje bloqueado, momento/derivada de nivel y aritmética de exposición independientes. '
    note+='El mismo perfil exterior se aplicó a entrenamiento y retenido en su ámbito; no se reutilizaron perfiles de otros folds para aprender. '
    note+='Las pruebas sintéticas incluyeron el adaptador de último de 2025 con enlaces observados cero y exposición calendario una sola vez. '
    note+='Coste: 710 constantes cerradas únicas; controles y normalizadores aparte. Cero ajustes iterativos, curvas, kappas, inferencias fuente, precios finales o envíos.\n\n'
    note+='La siguiente pregunta separa la forma última FSp de la observación. Algebraicamente, la razón RFS antigua incorpora la razón de completitudes además de la forma última. '
    note+='Se preparan PUL1 (forma última pura sobre G3) y PUL2 primario (misma forma sobre H1), con los mismos pesos REN .25/.25/.5, conservando NB exactamente. '
    note+='Es una nueva composición adaptativa propuesta, no adopción retrospectiva de H1; requiere otra receta y comentario antes de producir/puntuar precios. '
    note+='No hay parámetros, árboles o curvas adicionales previstos. El comparador completo F3c histórico sigue sin reproducirse; una ganancia local frente a G3 no prueba mejora del público.\n\n'
    note+='2024 abierto y adaptativo; B00, F3c 0,16914, H2 y todas las alternativas/fallos conservados. Ningún cupo consumido; objetivo 0,17 activo. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+'; propuesta: '+w.rel(proposal_path)+'.\n'
    doc=R/'docs/archivo/semana2/MISION017_HET_RESULTADO.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-HET-RESULTADO','--asunto','HET mejora en cinco folds, aún no cumple todos los criterios',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(index,receipt,archive/'post_forum');w.update(phase,{'HET':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['HET']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_HET_index':w.rel(index),'week_2_mission017_HET_report':w.rel(doc),
        'week_2_mission017_ultimate_shape_proposal':w.rel(proposal_path)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'primary':'H2','results':receipt['results'],'forum':receipt['forum'],'next_unit':next_unit},ensure_ascii=True))


if __name__=='__main__':main()
