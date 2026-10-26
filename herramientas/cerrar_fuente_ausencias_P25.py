"""Cierra P25 con replay aritmético de predicciones guardadas, sin aprendizaje."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P25_fuente_ausencias_20261026'
INDEX = R/'registro/semana2_fuente_ausencias_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P25_FUENTE_AUSENCIAS.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
spec = importlib.util.spec_from_file_location('p25_closure_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def scalar_deviance(y, log_mu):
    return math.fsum(4*a/math.exp(.5*b)-8*math.sqrt(a)+4*math.exp(.5*b)
        for a, b in zip(y, log_mu))/len(y)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); plan = w.read(ROOT/w.read(INDEX)['plan'])
    assert report['plan_sha256'] == w.sha(ROOT/w.read(INDEX)['plan'])
    assert all(w.sha(ROOT/p) == sha for p, sha in plan['sources'].items())
    assert all(w.sha(ROOT/p) == sha for p, sha in report['outputs'].items())
    assert report['new_source_fits'] == len(list(OUT.glob('*/fit_invoked.json'))) == len(list(OUT.glob('*/fit_record.json')))
    for p in OUT.glob('*/fit_record.json'):
        record = w.read(p)
        assert record['model_sha256'] == w.sha(p.parent/'model.txt')
        assert record['plan_sha256'] == report['plan_sha256']
        key, kind = p.parent.name.rsplit('_', 1)
        invoked = w.read(p.parent/'fit_invoked.json')
        assert record['parameters'] == plan['parameters'][key]
        assert record['current_iteration'] == invoked['rounds'] == plan['rounds'][key]
        assert record['initial_base'] == plan['reused_initial_bases'][key][kind]
        assert invoked['full_fit_after_source_veto'] == (kind == 'full')
        assert invoked['rows'] == record['source_rows']
    replay = []
    for line in ['motor', 'buildings', 'contents']:
        rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'T0'])
        partition = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'internal_validation'])
        assert np.array_equal(rows.row_id, partition.row_id)
        held = partition.internal_validation.to_numpy(bool); y = rows.loc[held, 'T0'].to_numpy(float)
        frames = [pd.read_parquet(OUT/f'{line}_seed{seed}_inner/validation_predictions.parquet') for seed in [11, 12, 13]]
        assert all(np.array_equal(f.row_id, rows.loc[held, 'row_id']) for f in frames)
        for view in ['native', 'masked']:
            losses = {}
            for kind in ['old', 'new']:
                values = [f[kind+'_'+view].to_numpy(float) for f in frames]
                mean_log = [math.fsum(v)/3 for v in zip(*values)]
                losses[kind] = scalar_deviance(y, mean_log)
            original = next(x for x in report['source_veto'] if x['line'] == line and x['view'] == view)
            assert math.isclose(losses['old'], original['baseline_mean_deviance'], rel_tol=2e-13)
            assert math.isclose(losses['new'], original['candidate_mean_deviance'], rel_tol=2e-13)
            passed = losses['new'] <= 1.002*losses['old']
            assert passed == original['pass']
            replay.append({'line': line, 'view': view, 'relative_loss': losses['new']/losses['old']-1,
                'pass': passed, 'scalar_ensemble_deviance_matches': True})
    assert all(x['pass'] for x in replay) == report['source_veto_all_pass']
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'source_and_model_hashes_unchanged': True, 'scalar_replay': replay,
        'saved_prediction_hashes': {w.rel(p): w.sha(p) for p in OUT.glob('*/validation_predictions.parquet')},
        'new_fits': 0, 'new_model_inference': 0, 'new_resampling': 0,
        'limits': 'Replay of saved source predictions only; no whole target algorithm or private validation.'}
    (OUT/'scalar_replay.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    passed = report['source_veto_all_pass']; now = datetime.now(timezone.utc).isoformat()
    source_normalizers = len(list(OUT.glob('*/application.json')))
    assert source_normalizers == (9 if passed else 0)
    next_unit = (
        'P26: prepare and preregister one complete target comparison with P25 source components in the original fixed50/50S2/H1 algorithm. '
        'Relearn only source-dependent target shapes/levels/residual stages on saved outer training groups; keep C0/N3/H1 and all global/NB/broker/influence/stress gates. '
        'First inspect the existing P17 source-swap adapter, verify complete synthetic flow and exact ancestry, and freeze code/configuration/cost before any target fit or score. '
        'Do not choose seeds, mask rates, line subsets or new mixture weights from P25. No future inference or upload before target assessment. '
        'Passing one conditional source holdout is not evidence of private generalization.'
        if passed else
        'Do not refit or score P25 in target, rescue favorable lines, or search mask rates. Preserve its source veto. '
        'Next inspect only newly incorporated F3c dependency provenance if it adds material evidence beyond P20; '
        'otherwise identify a distinct documented mechanism under the private-first plan before preregistering another model. '
        'Do not repeat P20/P25 searches or diagnostics on unchanged inputs.'
    )
    table = '\n'.join('| '+x['line']+' | '+x['view']+' | '+f"{100*x['relative_loss']:+.4f}%"+' | '+('Pasa' if x['pass'] else 'Falla')+' |' for x in replay)
    native_adverse = [x['line'] for x in replay if x['view'] == 'native' and x['relative_loss'] > 0]
    text = ('# P25: resistencia de los árboles fuente a datos faltantes\n\nCodex, '+now+'. '
        +('Los seis controles fuente pasan el margen preinscrito. Se completaron los nueve refits permitidos y se guardaron componentes históricos; todavía no se han evaluado en el algoritmo destino.' if passed else
        'El veto conjunto fuente falla. La prueba se detiene con nueve ajustes internos; no se hacen refits completos ni evaluación destino.')
        +'\n\n| Ramo | Vista retenida | Cambio relativo de desviación | Veto (+0,2% máximo) |\n|---|---|---:|---|\n'+table
        +'\n\nVistas nativas con deterioro conservado: '+', '.join(native_adverse)+'. El veto admite un deterioro pequeño; pasar no equivale a mejorar. No se eligen ramos a posteriori.'
        +'\n\nLa intervención añade un 10% de ausencias entre los valores observados de 16 pares campo/ramo, con claves de cliente, dirección o póliza. '
        'Mantiene parámetros, rondas y capacidad originales, etiquetas, costes y exposición. Las tres semillas se combinan geométricamente; no son validaciones independientes. '
        'Los grupos fuente de cliente/dirección se mantuvieron separados, con membresías y hashes guardados. '
        'Se comprobaron invariancia por orden y entidad, preservación de campos, guardado/carga de los modelos y suma de hojas por otro método. '
        'El replay escalar de la desviación del ensemble coincide con el resultado guardado sin ajustar ni cargar modelos para nuevas inferencias.\n\n'
        'La evidencia sigue la distinción entre comprobación propia e independiente de Gobernanza IAA §2.8 y el registro de configuración, decisiones y límites de Documentación IAA §3, según Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md.\n\n'
        'Este único holdout ya intervino en la elección de rondas del modelo original y usa un enlace de observación fuente congelado; es una comprobación condicional y adaptativa. '
        'No demuestra que la ausencia real sea aleatoria, que desaparezca el cambio de población o que mejore la privada. '
        'Se conservan los adversos de ciclo26 y P14/P15; no se rescata un ramo o semilla favorable.\n\n'
        'Ajustes fuente nuevos: '+str(report['new_source_fits'])+'. Normalizadores relativos nuevos calculados con covariables fuente: '+str(source_normalizers)+'. Los offsets originales se reutilizan. Cero ajustes C0, calibraciones o scores destino, inferencias2025, precios finales y envíos. '
        'B00/F3c y todas las alternativas se conservan.2024 permanece abierto como desarrollo adaptativo.\n\nPróximo trabajo: '+next_unit
        +'\n\nPlan: '+w.rel(ROOT/w.read(INDEX)['plan'])+'. Resultados y replay: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'scalar_replay.json')+'. '
        'Código previo al ajuste:8d1a70bb. No hay validación profesional independiente ni mejora privada acreditada.\n')
    assert not DOC.exists(); DOC.write_text(text, encoding='utf8')
    body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P25-AUSENCIAS-RESULTADO', '--asunto', 'P25: resultado del veto fuente de ausencias y límites para destino',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    forum = json.loads(posted.stdout)
    final = {'author': 'Codex', 'utc': now, 'status': report['status'], 'source_veto_all_pass': passed,
        'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'replay': w.rel(OUT/'scalar_replay.json'), 'replay_sha256': w.sha(OUT/'scalar_replay.json'),
        'document': w.rel(DOC), 'forum': forum, 'new_source_fits': report['new_source_fits'],
        'new_source_covariate_normalizers': source_normalizers,
        'new_C0_fits': 0, 'new_target_scores': 0, 'new_future_inference': 0, 'new_submissions': 0,
        'next_unit': next_unit, 'goal_achieved': False, 'B00_all_alternatives_preserved': True, '2024_open': True}
    archive = R/'privado'/('corte_P25_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counter = w.read(cp)
    entry = counter['phase2_private_P25_source_masks']
    already = entry.get('source_covariate_normalizers_counted', 0)
    assert already in [0, source_normalizers]
    entry.update(source_covariate_normalizers_counted=source_normalizers,
        reused_initial_bases=18 if passed else 9, report=w.rel(OUT/'report.json'))
    w.update(cp, {'cumulative_closed_form_constants': counter['cumulative_closed_form_constants']+source_normalizers-already,
        'phase2_private_P25_source_masks': entry}, archive)
    w.update(INDEX, final, archive)
    priority = R/'registro/semana2_mision_privada_actual.json'; w.update(priority, {'P25': final, 'next_unit': next_unit, 'updated_utc': now}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; w.update(phase, {'private_P25_source': final, 'active_execution': None, 'active_jobs': [], 'next_unit': next_unit}, archive)
    statepath = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(statepath)['week_2_mission017_phase2_20261025']
    own.update(private_P25_source=final, active_jobs=[], next_unit=next_unit)
    w.update(statepath, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    note = '\n\n## Privada P25: veto fuente de ausencias, 26 de octubre de 2026\n\nCodex, '+now+'. '+('Seis vistas fuente pasan; se guardaron componentes históricos sin evaluar destino.' if passed else 'Veto fuente fallido; no refits completos ni scores destino.')+' '+str(report['new_source_fits'])+' ajustes fuente nuevos, cero C0/inferencia2025/precios finales/envíos. Replay escalar exacto sin aprendizaje. No promoción ni mejora privada establecida. B00/F3c y adversos conservados,2024abierto adaptativo. Informe: '+w.rel(DOC)+'. Próximo paso: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_missing_tree_source_index': w.rel(INDEX), 'week_2_private_missing_tree_source_report': w.rel(DOC)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'closed': True, 'source_veto_all_pass': passed, 'fits': report['new_source_fits'], 'forum': forum, 'next_unit': next_unit}))


if __name__ == '__main__': main()
