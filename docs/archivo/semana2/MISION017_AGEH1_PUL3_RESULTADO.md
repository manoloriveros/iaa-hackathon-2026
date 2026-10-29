

## AGEH1/PUL3: la edad NB vuelve a fallar, 26 de octubre de 2026

Codex, 2026-10-26T09:37:46.103721+00:00. Se completaron los 15 GLM preinscritos con el motor de edad sin cambios, cinco bandas y K300, ahora sobre H1. La conexión nueva cotejó ámbitos, ancestros y replay H1 separado en entrenamiento/retenido; no se mezclaron precios OOF de otros folds. No se repitió la suite del optimizador sin cambios: su código/fixture se comprobaron por hash; se probaron las rutas nuevas sin ajustar.

Incremento NB frente a H1/PUL2: -0.00029138; IC95 pareado [-0.00061445, -0.00005511]. Empeora en los cinco folds y los dos años; fallan todas las guardas NB. Sensibilidad ponderada del incremento NB: -0.00392090. Proxy A1 original de 2024 para edad NB sola: -0.00093797; el proxy de razón completa es +0.00228386. El segundo es positivo por otros componentes y no rescata el daño NB. Los proxies no son F3c corregido completo y el ESS sigue siendo insuficiente.

PUL3 combinado: D² 0.13939708, diferencia frente a G3 +0.00229715; conserva la concentración y empeora una celda. REN permaneció exactamente PUL2. Ninguna ganancia REN se usa para aprobar la edad. Se conserva PUL3 como adverso, sin elegir nuevas bandas o K.

Los 15 ajustes pasaron objetivo/onehot/gradiente/Hessiano independientes, problema numérico idéntico bajo etiquetas retenidas alteradas y replay exacto con optimizador bloqueado. Coste real: 15 GLM nuevos, cero modelos fuente, C0, kappas, inferencias fuente, precios finales o envíos. Los coeficientes y dos interceptos de cada GLM son parámetros dentro de esos modelos, no nuevas constantes cerradas independientes para sumarlas otra vez.

La siguiente unidad preparará un prototipo concreto PUL2 de 2025 respecto de F3c, sin edad ni más ajuste, para verificar el flujo real y medir cambios de nivel/cartera. No implica superar post31, admisión estadística o permiso nuevo de envío. Se distinguirá la media de cinco miembros de la validación OOF de un solo ámbito y la transferencia a F3c del comparador local G3. Antes de inferir se registrarán fórmula, normalización, fuentes y coste; el productor no tendrá una vía de upload.

B00, F3c 0,16914, PUL2 y todos los adversos conservados.2024 abierto y adaptativo. Ningún cupo consumido; meta pública 0,17 activa. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/edad_H1_PUL3_20261026_v1/report.json.
