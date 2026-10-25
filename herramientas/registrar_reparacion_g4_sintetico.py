from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1'
OLD=REPO/'registro/semana2_g4_flujo_sintetico_plan_v1.json'
NEW=REPO/'registro/semana2_g4_flujo_sintetico_plan_v2_reparacion.json'
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not NEW.exists()
    plan=json.loads(OLD.read_text(encoding='utf-8'))
    plan.update(id='S2-G4-FLUJO-SINTETICO2023-v2-REPARACION-20261024',utc=datetime.now(timezone.utc).isoformat(),
        previous_plan={'path':rel(OLD),'sha256':sha(OLD)},original_forum_prior=plan['forum_prior'],forum_prior='COD-S2-20261024-G4-FLOW-REPAIR1')
    plan['implementation_repairs']=[
        {'failure':'Protected payload changed canonical cache hash though all numeric learned state was identical.',
         'cause':'astype(str) formats datetime64 as date but object/Timestamp with time after adversarial dtype promotion.',
         'repair':'Explicit ISO normalization of selected training loss/report dates and integer cents before hashing; no protected values enter.'},
        {'failure':'Joint numerical reference returned ABNORMAL near exact solution with tiny negative deviance.',
         'cause':'Subtractive cancellation in equivalent deviance formula near y=mu.',
         'repair':'Use algebraically identical nonnegative4*(sqrt(y)-sqrt(mu))^2/sqrt(mu). Solver,seed,parameters,tolerances and acceptance unchanged.'}]
    plan['preserved_attempts']=['attempt1_verification.json','attempt1_test_output.txt','attempt1_sources','attempt1_failure_investigation.json']
    plan['repair_investigation_work']={'synthetic_scoped_fits':2,'joint_reference_diagnostics':3,'competition_rows':0}
    plan['resources']['cumulative_repair_ceiling']={'scope_attempts':180,'successful_GLM_and_C0_fits_each':120,'calibration_calls':80,'wall_seconds':600,
        'reason':'Explicitly accounts for failed/cache attempts plus focused investigation and corrected full integration. Each executable attempt retains original120scope-attempt ceiling; no change to technical acceptance.'}
    frozen=[]
    for item in plan['frozen_sources']:
        p=ROOT/item['path'];q=RUN/'repair1_frozen_sources'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
        frozen.append({'path':rel(p),'sha256':sha(p),'snapshot':rel(q)})
    plan['frozen_sources']=frozen
    NEW.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(RUN/'repair1_plan_snapshot.json').write_bytes(NEW.read_bytes())
    fp=RUN/'forum_repair1.md';fp.write_text('''Codex, reparación documentada del flujo G4 sintético tras el intento1:9pruebas,3fallos,0errores. Se conservan recibo,salida y fuentes del intento. No hubo lecturas del concurso o red.

La investigación mínima ajustó solo dos ámbitos sintéticos y localizó el fallo de invariancia exclusivamente en training_content_sha256: datos de ajuste idénticos se representaban como fecha o Timestamp con hora al cambiar el dtype de columnas protegidas. Se normalizan explícitamente fechas ISO y centavos enteros seleccionados antes de calcular la clave; no se cambian curvas,coeficientes o criterios para esconder influencia. El segundo fallo es cancelación de la devianza cerca de la solución exacta: la referencia numérica devolvía un valor negativo del orden de1e-15 y parada anormal. Se usa la identidad no negativa4*(sqrt(y)-sqrt(mu))²/sqrt(mu),con el mismo objetivo,solver,tolerancias y fixture.

Enmienda de implementación congelada antes de repetir la integración: registro/semana2_g4_flujo_sintetico_plan_v2_reparacion.json. Misma semilla20261024,misma receta y criterios. Se explicita presupuesto acumulado de reparación:180intentos de ámbito,120ajustes sintéticos GLM/C0 cada uno,80calibradores y600s; cada intento ejecutable mantiene su límite original de120ámbitos. La diferencia contabiliza cachés/fallos/investigación, no una búsqueda predictiva. Se repite la integración afectada por cambios de hash y objetivo numérico; no suites históricas ni diagnósticos reales.

B00/alternativas y2024cerrado. Cero entrenamiento,inferencia o scores con datos del concurso. G1/G2 no resueltos. Sin envíos o promoción; alcance de software sintético únicamente. La corrección no constituye aprobación humana o revisión profesional independiente.
''',encoding='utf-8')
    out=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',plan['forum_prior'],'--asunto','G4 sintético: fallos conservados y reparación de hash/estabilidad numérica preinscrita','--cuerpo',str(fp)],capture_output=True,text=True)
    assert out.returncode==0,out.stderr
    (RUN/'forum_repair1_receipt.json').write_text(out.stdout,encoding='utf-8')
    print(json.dumps({'repair_plan':rel(NEW),'sha256':sha(NEW),'forum_prior':plan['forum_prior'],'technical_criteria_changed':False},ensure_ascii=True))

if __name__=='__main__':main()
