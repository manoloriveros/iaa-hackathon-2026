"""Preinscripción finita de trazabilidad; conservar concurrencia y el catálogo activo."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os

ROOT=Path(__file__).resolve().parents[3]; REPO=ROOT/'Hackaton/Repositorio_IAA2026'
NOW=datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()


def main():
    night=REPO/'registro/semana2_continuidad_nocturna.json'
    before=night.read_bytes(); n=json.loads(before.decode('utf-8-sig'))
    identifier='S2-B19-TRAZA2023-v1-20261024'
    assert all(x['id']!=identifier for x in n['completed_units'])
    assert n['confirmation_2024_open'] is False
    base=REPO/'privado/semana2/desarrollo2023/estabilidad_b19_20261024T014815Z_9b2b1803'
    paths=[REPO/'registro/semana2_b19_estabilidad_actual.json',base/'report.json',base/'verification.json',
           base/'oof_group_contributions.parquet',base/'training_group_local_influence.parquet',
           ROOT/'Hackaton/Semana 2/Datos/emerging/claims.parquet',
           REPO/'privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/inputs_2023/claims_2023.parquet',
           ROOT/'Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json',
           REPO/'src/semana2/preparar_base.py',REPO/'src/semana2/trazar_siniestros_b19_2023.py']
    periods=[];rawpol={}
    for line in ['motor','buildings','contents']:
        f=REPO/f'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/inputs_2023/{line}.parquet'
        periods.append(rel(f));paths.append(f)
        f=ROOT/f'Hackaton/Semana 2/Datos/emerging/policies_{line}.parquet';rawpol[line]=rel(f);paths.append(f)
    folder=ROOT/'Hackaton/Semana 2/Codex'
    snapshot=folder/'nocturno_antes_traza_b19.json';snapshot.write_bytes(before)
    for filename,pointer in [('catalogo_antes_traza_b19.json','semana2_desarrollo2023_actual.json'),('contadores_antes_traza_b19.json','semana2_contadores_propios_actual.json')]:
        target=folder/filename
        with target.open('xb') as f:f.write((REPO/'registro'/pointer).read_bytes())
        paths.append(target)
    p={'id':identifier,'author':'Codex','registered_utc':NOW,'path_base':'workspace_root',
       'hypothesis':'The influential B19 components may reflect valid paid losses, open reserves or reporting delays; verify source lineage before proposing another model. No financial adjustment is assumed.',
       'selection':'Union of top5 strictly adverse OOF groups in buildings and motor_new from saved contribution tables, plus top1 absolute local coverage influence in each of10 saved motor/building fits. Stable tie break group_id. At most20 groups. Keep full2023 component acrosslines, accepted and declined original records; no data deletion or new ranking of models.',
       'criteria':'Exact original-versus-saved claim fields and cents, unique loss-date interval within2023, saved group/fold, admitted/repudiated inclusion and per-period T0/reserve identities. Flag closed reserves, late reports>365days, recoveries>paid or missing source; do not repair silently or certify adequacy.',
       'cash_identity':'Reserve=incurred-paid; T0=incurred-recoveries=(paid-recoveries)+reserve, no second subtraction of excess. Money in integer cents. Quarter-cent units for reserve075/125 design calculations, no model scoring or new adopted targets.',
       'time_scope':'Policy/loss year2023 only. Original claims query by selected policy_ids and loss_date in2023; original policy metadata by selected IDs and period_start/end2023. Report dates through fixed valuation2024-12-31 allowed for those2023 losses, not2024 pricing. No other-year prices, test, SEL01 or ledger.',
       'verification':'Independent Decimal cents and Python datetime/dictionary assignment, savedfold/cash conservation, selection reconstructed by a separate loop, expected invalid cache year/identity/date adversaries and one actual CLI tampered-cents source that fails closed. No repeated prior GLM suites/bootstrap.',
       'resources':'One local finite unit up to45min, no fitting/model import/predictions/scores/bootstrap, no remote/submission/delegation/other automation changes.',
       'code':rel(REPO/'src/semana2/trazar_siniestros_b19_2023.py'),
       'claims_2023':rel(paths[6]),'raw_claims':rel(ROOT/'Hackaton/Semana 2/Datos/emerging/claims.parquet'),
       'contributions':rel(base/'oof_group_contributions.parquet'),'influence':rel(base/'training_group_local_influence.parquet'),
       'saved_periods':periods,'raw_policies':rawpol,'valuation_date':'2024-12-31',
       'reference':'W2-B00','all_alternatives_preserved':True,'new_fits':0,'new_scores':0,'new_bootstrap':0,
       'forum_prior':'COD-S2-20261024-038','forum_result':'COD-S2-20261024-039',
       'continuity_registration_mode':'current_unit' if n.get('current_unit') is None else 'parallel_artifact_diagnostic',
       'completed_units_at_start':len(n['completed_units']),'concurrent_unit_at_start':n.get('current_unit'),
       'prior_external2024_subject_exposure_disclosed':True,'complete_blindness_claim_allowed':False,
       'ledger_read':False,'professional_independent_validation':False,
       'frozen_sources':[{'path':rel(x),'sha256':sha(x)} for x in paths]}
    plan=REPO/'registro/semana2_b19_traza2023_plan_v1.json'
    with plan.open('x',encoding='utf-8') as f:json.dump(p,f,ensure_ascii=False,indent=2);f.write('\n')
    body=folder/'traza_b19_2023_preinscripcion.md'
    text='''Respondo al siguiente paso de 037 y al plan nocturno: trazabilidad financiera y temporal de los componentes destacados, sin otra tanda. Antes de calcular se registra `semana2_b19_traza2023_plan_v1.json` con fuentes y SHA, hipótesis, selección, criterio y verificación.

La selección queda fijada como unión de los cinco grupos OOF más adversos de edificios y autos nuevos, y el de mayor influencia absoluta sobre cobertura en cada uno de los diez ajustes guardados de esos ramos; desempate por group_id, máximo 20 componentes. Se revisan sus periodos completos de 2023 y sus siniestros originales, incluidos los rechazados por separado. No se selecciona un modelo, borra un grupo o aprende un factor.

Se cotejarán originales y copia guardada: pagos, incurrido, recuperaciones, reserva derivada, fechas, estado, asignación única y T0/reserva por periodo. Reserva=incurrido−pagado; T0=incurrido−recuperaciones. Los pagos ya son netos de franquicia. Se marcarán reservas en cerrados, recuperaciones superiores a pagos y reportes de más de 365 días, sin corregir o inferir error automáticamente. El estrés de reserva 0,75/1,25 es una identidad de diseño, no un precio, intervalo de adecuación o objetivo adoptado.

Solo pólizas y pérdidas de 2023. Se permiten fechas de reporte hasta la valoración fija del 31 de diciembre de 2024 para esos siniestros; no se abren precios, predicciones, scores, test, SEL01 o ledger de 2024. La exposición previa de un asunto externo sigue declarada, sin usar sus cifras o afirmar ceguera completa. B00 y todas las alternativas se conservan. Cero ajustes, modelos, predicciones, scores o bootstrap nuevos; no repetir las suites de B19. Revisión propia por otro método y flujo adverso real, no profesional independiente.

La discusión pública 752144 conserva el mismo mensaje y tres respuestas que el corte anterior, incluido el reconocimiento del HOST. No hay nuevo archivo de fuente o cotejo de test porque no cambió el contenido; no se envía una prueba. Catálogo y contador actuales se preservan, sin sobrescribir trabajo concurrente o tocar otras automatizaciones.
'''
    with body.open('x',encoding='utf-8') as f:f.write(text)
    entry={'id':identifier,'plan':rel(plan),'status':'preregistered_financial_source_trace_no_fit','forum_preregistration':p['forum_prior']}
    if n.get('current_unit') is None:
        n['current_unit']=entry;n['status']='B19_financial_source_trace_in_progress'
    else:n.setdefault('parallel_artifact_diagnostics',{})[identifier]=entry
    n['updated_utc']=NOW
    tmp=night.with_name(night.name+'.trazab19pre.tmp')
    with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    assert night.read_bytes()==before,'Concurrencia: plan conservado, no sobrescribir índice nocturno'
    os.replace(tmp,night)
    print(json.dumps({'plan':rel(plan),'sha256':sha(plan),'sources':len(paths),'mode':p['continuity_registration_mode'],'prior_completed':len(n['completed_units'])}))


if __name__=='__main__':main()
