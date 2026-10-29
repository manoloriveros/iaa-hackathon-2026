"""Documenta el alcance condicional de datos oficiales sin afirmar vintage prospectivo."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
OUT = R / 'privado/semana2/mision017_fase2/clima2025_auditoria_20261026_v1'
P = R / 'registro/semana2_mision017_fase2_actual.json'
POLICY = R / 'registro/semana2_alcance_covariables_oficiales2025_v3.json'

def main():
    assert not POLICY.exists() and not (OUT / 'completion_receipt.json').exists()
    report = w.read(OUT / 'report.json'); assert report['official_2025_covariate_presence_established']
    assert not report['2025_quote_time_or_forecast_vintage_established'] and report['current_dictionary_same_as_F05']
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    previous = R / 'registro/semana2_politica_desarrollo2024_v2.json'
    policy = {'id': 'S2-COVARIABLES-OFICIALES2025-v3', 'author': 'Codex', 'utc': stamp.isoformat(),
        'human_authorization_literal': '2024 no tiene que estar bloqueado, usa todo lo que tenemos y necesites que nos lleve a mejorar significativamente el modelo',
        'decision_type': 'Implementation scope under ongoing human autonomy, not a new human approval or HOST clarification',
        'prior_policy_preserved': {'path': w.rel(previous), 'sha256': w.sha(previous)},
        'clarification': 'The earlier ban on future realized weather is not interpreted as a ban on official covariates actually supplied for the synthetic2025competition target. Use is conditional/retrospective, never claimed available at quote time. Historical prospective F05 findings remain open.',
        'allowed': ['Read and audit official supplied2025weather, whose full-file bytes match the previously verified official objects',
            'After separate preregistration, test models with same-calendar-year official weather on historical2023/2024 as conditional development',
            'Fit source price models only on labeled historical years through2024; use emerging supplied2025covariates only for conditional test prediction after recipe selection'],
        'not_established': ['Forecast vintage, publication or knowledge before inception', 'Observed vs forecast construction of the indices',
            'Reason for the data page listing weather only through2024 although the Parquets include2025'],
        'limits': ['No external future weather, invented forecasts,2025claim labels or reconstruction of individual hidden labels',
            'No promotion, auto-submission, new source cohort or formal independent validation from covariate availability alone',
            'No rewriting old recipes/rejections or closing S2-VAL-DAT-003 prospectively',
            '2024 stays open as adaptive development; preserve B00, F2, C1 and all alternatives',
            'Keep the one remaining daily slot unless a substantially supported candidate is separately admitted'],
        'evidence': {'report': w.rel(OUT / 'report.json'), 'sha256': w.sha(OUT / 'report.json')},
        'new_fits': 0, 'new_C0_fits': 0, 'new_price_scores': 0, 'new_submissions': 0}
    POLICY.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding='utf8')
    note = '\n\n## Clima de 2025 suministrado oficialmente: presencia y alcance, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Los Parquet oficiales contienen clima de 2025: 136.914 direcciones emergentes y 575.983 desarrolladas, con una fila por dirección/año. '
        'Sus huellas completas coinciden con los originales históricos y con la descarga verificada contra el objeto oficial el 24 de octubre. '
        'No es una actualización nueva de contenido. La página actual, igual a la de F05, enumera solo 2023–2024 para el emergente y 2021–2024 para el desarrollado: '
        'queda registrada la discrepancia, sin inventar su causa ni una aclaración del organizador.\n\n'
        'Las claves climáticas cubren todas las filas de las nueve tablas de pólizas comprobadas, sin duplicados dirección/año o valores numéricos ausentes. '
        'Respecto de la media emergente de 2023–2024, el clima de 2025 tiene, por dirección, aproximadamente 9,61 días más de helada, 127,28 mm menos de lluvia '
        'y 1,31 °C menos de temperatura media. La variación espacial importa: el cambio de temperatura queda fuera del rango de cambios históricos internos '
        'en 56,48 % de las direcciones. Ese rango emergente procede de solo dos años y no equivale al rango de entrenamiento del desarrollado. '
        'Son estadísticas de covariables, no efectos sobre siniestros ni mejora de score.\n\n'
        'Bajo la instrucción de usar la información disponible y la autonomía vigente, se admite estudiar estos valores oficiales como covariables de una predicción '
        'condicional del concurso. No se afirma que fueran conocidos antes de cotizar, que sean pronósticos o que la mera presencia resuelva F05. '
        'Se conserva el hallazgo prospectivo y la política previa; la precisión de alcance queda en un documento nuevo, sin reescribir recetas históricas. '
        'No se usará clima realizado de fuera del concurso ni etiquetas de 2025.\n\n'
        'E13 ya probó sustituir el clima persistente por siete medidas del año, con un tronco desarrollado 2021–2023: −0,00222 en 2023 y +0,00026 en 2024, '
        'con intervalos compatibles con cero. No se repetirá esa receta como si fuera una idea nueva. La siguiente hipótesis es más acotada: '
        'conservar el riesgo base y probar efectos residuales de variaciones climáticas mediante un GLM sencillo con fuente 2021–2024. '
        'Antes se fijará una evaluación cuya composición corresponda a 2025, con pesos derivados únicamente de covariables y sin admitir retroactivamente los modelos fallidos.\n\n'
        'Las medias se verificaron por otro método y los residuos históricos por dirección suman cero. '
        'Cero ajustes, C0, inferencias de modelos de precio, scores nuevos o envíos. El último resultado procesado continúa en 0,16519 y queda un cupo. '
        'La revisión es propia de Codex y no constituye revisión profesional independiente ni aprobación humana nueva.\n\n'
        'Evidencia: ' + w.rel(OUT / 'report.json') + '; alcance: ' + w.rel(POLICY) + '.\n')
    doc = R / 'docs/archivo/semana2/CLIMA2025_OFICIAL_ALCANCE_Y_VARIACION.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-CLIMA2025-ALCANCE', '--asunto',
        'Clima 2025 en archivos oficiales sin cambio de contenido: alcance condicional y revisión de variación', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'covariate_audit_completed_no_predictive_admission',
        'report': w.rel(OUT / 'report.json'), 'report_sha256': w.sha(OUT / 'report.json'),
        'scope_policy': w.rel(POLICY), 'scope_policy_sha256': w.sha(POLICY),
        'weather2025_is_official_existing_content': True, 'prospective_availability_established': False,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0, 'forum': json.loads(p.stdout)}
    (OUT / 'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    next_unit = ('Preparar pesos de evaluación2025 por ramo/negocio/duración, separados por año histórico, exclusivamente con covariables; '
        'medir soporte y ESS antes de un modelo. Congelar la siguiente tanda GLM de clima residual frente a N3, con fuente etiquetada2021–2024 y clima oficial del año. '
        'Mantener el riesgo persistente y distinguir el efecto de anomalías de la incorporación de granizo/heladas/sequedad ausentes en el padre. '
        'No repetir E13 ni rehacer C0. Criterios y presupuesto antes de ajustar o puntuar; no reutilizar la nueva ponderación para promover tandas adversas. '
        'La presencia del clima2025 no prueba capacidad predictiva, disponibilidad prospectiva o la meta0.17. Conservar el último cupo y todos los candidatos.')
    w.update(P, {'utc': stamp.isoformat(), 'official_weather2025_audit': receipt, 'covariate_scope_policy': w.rel(POLICY),
        'next_unit': next_unit, 'active_execution': None, 'active_jobs': [], 'status': 'active',
        '2024_open': True, '2024_closed': False, 'goal_achieved': False,
        'previous_goal_turn_audit': {'classification': 'progress', 'evidence': 'Tanda6 validated and one processed public submission57651126 improved best to.16519; no duplicated upload.'}}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; state = w.read(state_path)
    branch = state['week_2_mission017_phase2_20261025'].copy()
    branch.update(official_weather2025_audit=receipt, covariate_scope_policy=w.rel(POLICY), next_unit=next_unit)
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_official2025_covariate_scope': w.rel(POLICY),
        'week_2_mission017_weather2025_audit': receipt['report'], 'week_2_mission017_weather2025_report': w.rel(doc)}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    print(json.dumps({'goal_status': 'active', 'official_weather2025_scope_recorded': True,
        'prospective_availability_claim': False, 'new_fits': 0, 'new_scores': 0, 'new_submissions': 0,
        'forum_id': receipt['forum']['id']}))

if __name__ == '__main__':
    main()
