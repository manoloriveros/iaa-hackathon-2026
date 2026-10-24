"""Criterios y registro de bandas antes de leer resultados por celda."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    pp = REPO/'registro/semana2_b20_bandas_calibracion_plan_v1.json'
    assert not pp.exists(), 'Plan existente: conciliar antes de repetir'
    np = REPO/'registro/semana2_continuidad_nocturna.json'
    raw = np.read_bytes()
    night = read(np)
    assert night['current_unit'] is None, 'Unidad concurrente: conciliar primero'
    ridge = ROOT/read(REPO/'registro/semana2_glm_ridge_actual.json')['run']
    parent = ROOT/read(ridge/'plan_snapshot.json')['input_run']
    producer = REPO/'src/semana2/revisar_calibracion_b20_bandas2023.py'
    sources = [producer, ridge/'oof_2023.parquet', ridge/'report.json', ridge/'verification.json',
               ridge/'plan_snapshot.json', REPO/'registro/semana2_contadores_propios_actual.json']
    sources += sorted((ridge/'models').glob('*/bundle.joblib'))
    sources += sorted((parent/'inputs_2023').glob('*.parquet'))
    plan = {
        'id': 'S2-B20-BANDAS-CALIBRACION2023-v1-20261024', 'author': 'Codex', 'registered_utc': datetime.now(timezone.utc).isoformat(),
        'authorization_literal': 'Continúa con la revisión de calibración de B20 por bandas de riesgo fijadas en ajuste, usando artefactos guardados y sin reentrenar. Registra decisiones y resultados, mantén 2024 y test cerrados y añade complejidad solo con evidencia.',
        'hypothesis': 'Nearunit aggregate A/E may conceal systematicrisk-band or business imbalance and costly sparsegroups. Examine heldout observedT0 against fixedC0 predictions; no recalibration or newmodel is assumed necessary.',
        'ridge_run': rel(ridge), 'frame_source': rel(parent), 'producer': rel(producer), 'producer_sha256': sha(producer),
        'output_run': 'Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/b20_bandas_calibracion_20261024_v1',
        'band_definition': 'Exactly5nominalannualrate bands perline/model-fold. Replay B20 saved estimator on owntraining rows only. Cuts are empiricalinverseCDF q=.2,.4,.6,.8,0-basedindex ceil(n*k/5)-1 with exactintegerarithmetic. Band1 r<=c1,then(c1,c2]...,band5 r>c4. Keep repeatedcuts/emptybands; never split ties byID or heldoutlabels.',
        'comparison': 'Assign heldout periods using savedOOF B20annualrates and corresponding fit-only cuts. Both B20 andB19 use identical B20 bands/rows, not separate model-selected populations. Observedexpected prediction is originalC0*rate, not annualrate alone.',
        'readout': 'Line, line-fold, line-business byband:O/E from sums, OminusE, rows/groups/positiveperiods/positivegroups, nominal/effectiveexposure, largestcost-group share, concentrationequivalent groups and outoftraining-range counts. Keepzero/emptycells undefined whenE=0. Report fivefold dispersion and support without significance claims.',
        'uncertainty': 'No newbootstrap or Waldcoverageclaim. Fold ranges overlap and cells share components. Costconcentration-equivalent count is a concentrationdescription, not inferential effective samplesize. These reused2023diagnostics do not certify ultimate adequacy or freshvalidation.',
        'training_readout': 'Training rate replay is inference only,200376rows counting4appearances of each originalperiod acrossfits. Traininginterceptscore sqrt(mu)-T0/sqrt(mu) is checked; its zero optimum does not force aggregate A/E=1. All fitmethods blocked.',
        'acceptance': '15frozenB20estimators, no fit calls; training/heldout graphdisjoint; exact originalOOF prices,T0,C0 and50094unique2023heldoutrows; cutpoints/ranks fromfitrates only; independent manualexp rate replay, Python orderstatistics/bisect and mathfsum dictionary cellconservation. Targets poisoned cannot changeedges. Native source/duplicate guards fail before work.',
        'resources': 'CPU2threads,0newfits,15trainingrate replays,0newmodelrecipes,0bootstrap,0testprices/2024/ledger/remote/submissions/delegation. Do not repeat original GLM or attribution suites.',
        'decision_rule': 'KeepB00/B01-B20. No OOF-derived normalization, isotonic mapping, alpha, feature/interactions, perband modelrouting or promotion. A bandA/E deviation is diagnostic, not a factor toapply. Added complexity requires a distinct documented necessity and new preregistration.',
        'scope': 'Only2023;2024/test/actas/scores/SEL01/ledgerclosed. Prior external2024subject exposure disclosed andunused; no completeblindness claim.',
        'frozen_sources': [{'path': rel(x), 'sha256': sha(x)} for x in sources],
        'forum_prior': 'COD-S2-20261024-B20-BANDS-PRE', 'forum_result': 'COD-S2-20261024-B20-BANDS-RESULT',
        'IAA': 'Purpose/limits ProfessionalConsiderations3.1, ownreview Governance2.8, data/modelDocumentation2-3; no professionalcertification.'
    }
    dump(pp, plan)
    body = 'Por instrucción humana, plan S2-B20-BANDAS-CALIBRACION2023-v1-20261024 antes del cálculo. Se revisa si A/E agregado cercano a uno esconde desequilibrio por riesgo/negocio y pocos componentes costosos; no se presume necesidad de recalibrar o complejizar. Solo modelos B20 y OOF2023 guardados, mismos T0/C0 y cincofolds.\n\nQuintiles de tasa anual nominal de B20 por ramo/fold, calculados exclusivamente con replay del modelo guardado en sus filas de ajuste: cortes inversaCDF20/40/60/80%, índice ceil(n*k/5)-1. Se mantiene exactamente cinco bandas, incluidos empates y vacíos, con frontera superior inclusiva y sin usarID para desempatar. Aplicar a tasas OOF de B20. B19 se lee sobre idénticas bandas y filas B20; no se comparan cohortes diferentes. Ninguna etiqueta retenida fija cortes.\n\nSe conservan por ramo/fold/negocio/banda sumas O/E, diferencias, exposición, periodos y grupos positivos, concentración de coste y extrapolación fuera del rango del ajuste. No media de cocientes o exposición aplicada dos veces. Los replay de ajuste suman200.376apariciones, no200.376periodos independientes. No intervalos falsamente independientes de cincofolds ni bootstrap nuevo. El intercepto Tweedie no obliga a A/E uno.\n\nComprobar cortes con ordenación/bisect separados, tasas con exp(Xbeta) y ajustes bloqueados, sumas con math.fsum/diccionarios, fuentes conSHA, guardas de año/target/claves y falta de influencia de target sobre cortes. Cero entrenamiento, nueva receta/modelo, normalización OOF, isotónica, búsqueda de alpha o enrutamiento por banda. B00 y B01–B20 conservados.2024/test/ledger cerrados; exposición previa del título declarada sin uso. Ventana/otrasautomatizaciones intactas, sin remoto/envío/delegación/mensajes externos.\n\nConfiguración registro/semana2_b20_bandas_calibracion_plan_v1.json; productor src/semana2/revisar_calibracion_b20_bandas2023.py. Fuentes de B20 y entradas2023 de B19 guardadas; se infiere en ajuste con los quinceestimadores sin llamar fit. Revisión propia, no profesional independiente.\n'
    (REPO/'registro/COD-S2-20261024-B20-BANDS-PRE_cuerpo.md').write_text(body, encoding='utf-8')
    assert np.read_bytes() == raw
    night['current_unit'] = {'id': plan['id'], 'plan': rel(pp), 'status': 'preregistered_before_training_only_bands', 'forum_prior': plan['forum_prior']}
    night['updated_utc'] = plan['registered_utc']
    dump(np, night)
    print(json.dumps({'plan': rel(pp), 'sources': len(sources), 'sha256': sha(pp), 'new_fits': 0}))


if __name__ == '__main__':
    main()
