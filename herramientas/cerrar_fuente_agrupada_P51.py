"""Cierra los cinco ámbitos fuente guardados; no ajusta, predice ni puntúa."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import math
import sys

R = Path(__file__).resolve().parents[1]; ROOT = R.parents[1]
spec = importlib.util.spec_from_file_location('p51_source_close', R/'herramientas/entrenar_fuente_agrupada_P51.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
w = m.w


def main():
    assert not (m.OUT/'completion_receipt.json').exists()
    current = w.read(m.INDEX); assert current['execution'] is None
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert current['completed_outer_scopes'] == [0, 1, 2, 3, 4]
    assert current['attempted_source_fits'] == current['completed_source_fits'] == 90
    plan = w.read(m.PLAN); assert all(w.sha(ROOT/k) == v for k,v in plan['sources'].items())
    models = {}; outputs = {}; applications = []
    for outer in range(5):
        done_path = m.OUT/f'outer{outer}/completed.json'; done = w.read(done_path)
        assert done['source_fits'] == 18
        for k,v in {**done['outputs'], **done['source_fit_records']}.items(): assert w.sha(ROOT/k) == v
        outputs.update(done['outputs']); outputs[w.rel(done_path)] = w.sha(done_path)
        for record_path in (m.OUT/f'outer{outer}').glob('*/fit_record.json'):
            record = w.read(record_path); model = record_path.parent/'model.txt'
            assert record['plan_sha256'] == w.sha(m.PLAN) and w.sha(model) == record['model_sha256']
            models[w.rel(model)] = record['model_sha256']
        for path in (m.OUT/f'outer{outer}').glob('*_full/application.json'):
            d = w.read(path)
            assert d['reload_and_order_exact'] and d['independent_leaf_sum_max_error'] < 1e-10
            assert math.isclose(d['source_weighted_relative_mean'], 1., rel_tol=1e-12)
            assert d['new2025inference'] == 0
            applications.append({'path': w.rel(path), 'sha256': w.sha(path)})
    assert len(models) == 90 and len(applications) == 45
    now = datetime.now(timezone.utc).isoformat()
    next_unit = 'Register P52complete A1Rtarget comparison with fixed global/cohort/tail/level guards. Pooled failure rejects; pooled pass still requires OWNconditional-transfer reporting/source/target stage before production or upload.'
    text = '# P51: cinco ámbitos de fuente A1R completos\n\nCodex, '+now+'. Se completaron y guardaron los90ajustes previstos,18por ámbito. Los hashes de los modelos y entradas coinciden con la receta congelada. Se conciliaron45recibos de aplicación con recarga y orden exactos, suma independiente de hojas y media relativa fuente1. No se repitieron ajustes, inferencias ni suites.\n\n'
    text += 'Cada ámbito conserva su reporte P50 y tres semillas estándar. El grupo targetretenido se excluye de todo el aprendizaje del ámbito. La validación interna fuente sigue siendo condicional al reporte que incluye toda la fuente; estos recibos no acreditan una mejora en destino.\n\n'
    text += 'Quedan la comparación completa en destino y, solo si supera todas las guardas combinadas, la transferencia condicional con sus propias curvas y árboles. Los90ajustes pertenecen solo a esta etapa; una transferencia posterior puede requerir90más. No hay precios2025nuevos, CSV admitido ni envío. B00/F3c y todas las alternativas se conservan.2024está abierto como desarrollo adaptativo.\n\nPróximo: '+next_unit+'\n'
    m.DOC.write_text(text, encoding='utf8'); body = m.OUT/'forum_cierre.md'; body.write_text(text, encoding='utf8')
    forum = m.prep.post(body, 'COD-S2-20261027-PRIVADA-P51-FUENTE-CIERRE', 'P51: fuente completa, noventa ajustes y evaluación destino pendiente')
    receipt = {'author':'Codex','utc':now,'status':'P51all_source_scopes_complete_target_pending',
        'source_plan':w.rel(m.PLAN),'source_plan_sha256':w.sha(m.PLAN), 'source_fits':90,'scope_count':5,
        'model_hashes':models,'outputs':outputs,'application_receipts':applications,'new_fits':0,'new_inference':0,'new_scores':0,
        'new_submissions':0,'next_unit':next_unit,'forum':forum,'2024_open':True,'goal_achieved':False}
    m.dump(m.OUT/'completion_receipt.json',receipt)
    archive = R/'privado'/('cierre_P51_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    update = {**current,'status':receipt['status'],'completion_receipt':w.rel(m.OUT/'completion_receipt.json'),
        'completion_receipt_sha256':w.sha(m.OUT/'completion_receipt.json'),'forum':forum,'next_unit':next_unit}
    w.update(m.INDEX, update, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P51':update,'next_unit':next_unit}, archive)
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P51':update,'next_unit':next_unit}, archive)
    state_path=ROOT/'Preparación/ESTADO_PROYECTO.json'; own=w.read(state_path)['week_2_mission017_phase2_20261025']
    own.update(private_P51=update,next_unit=next_unit); w.update(state_path,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P51: cierre de fuente por ámbito\n\nCodex, '+now+'.90ajustes/90modelos guardados,5ámbitos/45aplicaciones conciliados. Cierre sin nuevos ajustes o scores; falta evaluación destino completa y transferencia propia antes de admitir. Informe: '+w.rel(m.DOC)+'.\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']: w.append(ROOT/'Preparación'/name,note,archive)
    print(json.dumps({'source_stage_complete':True,'fits':90,'applications':45,'new_fits':0,'forum':forum}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); main()
