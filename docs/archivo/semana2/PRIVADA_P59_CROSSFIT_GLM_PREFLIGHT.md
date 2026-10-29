# P59: flujo completo de calibración fuera del grupo

Codex, 2026-10-27T03:00:52.289789+00:00. Se comprobó el flujo numérico sintético de reporte, cuotas, base y GLMen dos particiones exteriores, con las cinco interiores en cada una. Todos los controles adversos conservaron objetos y predicciones; la serialización final fue exacta.

El GLM aprende de una predicción base por fila que excluyó su grupo, y se aplica sobre la base exterior completa. Cada curva/cuota/base interior tiene sus propios grupos permitidos: no se reutilizan objetos exteriores con ancestros protegidos. Los precios y qheredados se eliminaron antes del enlace interior; contaminar esos campos no cambió el canónico. El diseño sigue la idea estándar de [stacking con predicciones cruzadas](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html), sin prometer una ganancia.

Fixture:132CDFprimarias y132adversas,36bases/36adversas (72+72componentes y48+48etapas residuales),6GLM/6adversos. Real:75enlaces interiores por claves idénticas al soporte guardado, sin repetir esa auditoría o equipararla a credibilidad; cero curvas/precios ajustados o scores reales. Se guardó ahora la partición interior final con semilla5, sin seleccionar por resultados. Los tamaños64%/80%de evaluación y80%/100%de producción conservan la proporción1,25, sin garantía de igualdad de error.

Permanecen fuente2024condicional, maestros sin fecha, qcomún por ramo y cola/reservas.2023/2024son desarrollo adaptativo, no confirmación independiente o mejora privada establecida. B00/F3c/adversos conservados, cero inferencias2025o envíos.

Próximo: P60: register and commit complete cross-fitted P56GLM validation using P59raw canonical data/partitions.25OWNinner reports(275+275CDFs),75+75base learners(150+150components,100+100residual stages),15+15GLMs. Reuse P55outer base ONLYfor outerheldapplication; no source refits, no inherited outerq/base in innertrain. Preserve ALLoriginal gates, convergence and own conditional-transfer requirement. Freeze final production innerhashseed5, no mean5models or public tuning.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P59_crossfit_preflight_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P59_crossfit_preflight_20261027/synthetic.json.
