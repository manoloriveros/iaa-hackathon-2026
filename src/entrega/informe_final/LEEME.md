# Fuente del informe final, edición del 28 de octubre de 2026

Actualización del cierre: Manuel confirmó expresamente F3c como modelo definitivo de semana 2 después de la comparación completa con F3c-R. Codex actualizó el resumen y el estado final (páginas 1 y 5), conservando predicciones, cifras comerciales y límites. La selección para el concurso no equivale a promoción estadística ni aprobación operativa. Evidencia: `Hackaton/Repositorio_IAA2026/registro/semana2_decision_final_F3c_20261028.json`. La revisión de esta actualización se conserva en `privado/decision_F3c_final_20261028/`.

PDF vigente: `../informe_final_IAA2026_es.pdf`, diez páginas, primeras cinco calificables. F3c, sus predicciones y las veinte referencias comerciales permanecen intactos: 85 CU completos por póliza y total de 20.800,02 CU. Edición documental de Codex sobre fuentes de Claude y evidencia de ambas líneas; voz del participante.

Esta edición explica la combinación por peligro y la transferencia, distingue el modelo de la calibración pública, define la salvaguarda y su excepción posterior al resultado, y presenta limitaciones observadas. Los diagramas conceptuales de páginas 3 y 4 adaptan ideas del panel aportado por el participante. No trasladan sus contadores ni pesos históricos. La narración inglesa limpia está traducida y cotejada; otros materiales ingleses conservan sus cortes. No se midió ahorro de tiempo.

## Reconstrucción y verificación

El PDF procede de `build.py`, `paginas.py`, `anexos.py`, `charts.py`, `style.css`, fuentes y CSV de referencias. Generar HTML con `python -X utf8 -c "import build; build.build()"`; imprimir con `Hackaton/Repositorio_IAA2026/herramientas/renderizar_informe_editorial.cjs`, según su cabecera. No requiere entrenamiento ni tablero. Los HTML individuales `esquema_modelo.html` y `flujo_ia.html` sirven para exportar las figuras vectoriales complementarias.

El texto TeX complementario está sincronizado mediante `../latex/herramientas/html2tex.py`, con dos nuevas figuras PDF vectoriales. No se compiló ni verificó su propia paginación en esta edición; el PDF entregado es el HTML revisado.

Índice: `Hackaton/Repositorio_IAA2026/registro/informe_final_editorial_actual.json`. La corrida `privado/edicion_informe_final/20261028T165110Z/` conserva copia anterior, fuentes, PNG, cotejo numérico y matriz de coherencia con las nueve escenas de `NARRACION_GEMINI_TTS_ES.txt` y su traducción limpia inglesa. El guion y las narraciones no se modifican en esta edición. No se generó audio ni se midió duración grabada. No subir precios por referencia a Git.

Las limitaciones predictivas y profesionales conservan su alcance; la edición no acredita una calificación del jurado ni una aprobación operativa. Los anexos conservan su corte y son idénticos en texto y píxeles a la versión anterior.


## Revisión técnica del 29 de octubre

Se reorganizan las cinco páginas calificables alrededor del problema actuarial, la arquitectura, las decisiones metodológicas, los contrastes y la aplicación comercial. Se retira el glosario inicial; se conserva la consecuencia de la métrica solicitada por el participante. La calibración se describe mediante factores controlados, curva Tweedie y credibilidad, sin ocultar su información pública. La IA se presenta mediante su aporte a controles y correcciones bajo supervisión continua, sin atribuir revisión humana externa. Los anexos conservan las cifras y ajustan el vocabulario. Evidencia editorial: privado/revision_tecnica_informe_20261029. No se entrenan modelos ni se alteran predicciones.
