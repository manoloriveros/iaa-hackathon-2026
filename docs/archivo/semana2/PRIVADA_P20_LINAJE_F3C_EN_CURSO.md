# P20: procedencia de F3c, revisión aún parcial

Codex, 2026-10-26T19:00:32.871270+00:00. La revisión de código concreta por qué el replay anterior del CSV no certifica el aprendizaje completo del F3c entregado. No se han ajustado modelos, cargado modelos para inferencia, recalculado C0, puntuado o enviado archivos.

El constructor F3c carga el prefijo de F3b y aplica sus factores FAC y razones Rf al CSV final_creible. F3b aprende esos factores residuales sobre el conjunto de DEV23_T2b y HOLD24_T2b; esa es una operación de producción con ambos años, no una estimación que excluya cada grupo retenido. F2 también aprende conjuntamente sus factores de NCB y siniestros previos. Esto no invalida ajustar el modelo final con todos los datos disponibles: impide presentar las mismas correcciones estimadas con ambos años como validación externa de esos años.

La dependencia lib26.py carga literalmente /home/claude/m017/f3_eval.py. No se localizó ese archivo entre los sueltos de Hackaton ni en los tres paquetes exp26 de esta línea (151,54y4entradas). Los bytes de F3b/lib26 del primer paquete coinciden con las copias locales inspeccionadas. El snapshot de F3c tampoco contiene construir_F3b.py en su ruta relativa inmediata; la copia disponible está en el paquete anterior. Falta cerrar el mapa de dependencias y las definiciones exactas de sets/objetivo/exposición/enlace antes de ejecutar un replay fiel. La búsqueda no cubre todavía todos los archivos comprimidos del proyecto.

La función de factores cuenta siniestros positivos, aplica credibilidad n/(n+300)y conserva el total de precios de cada celda al aplicar una etapa. No se encontró un fallo de contar filas como siniestros. Las razones Rf se calculan a partir de cuatro series y sus etiquetas locales. El constructor de final_creible contiene niveles y forma derivados de consultas públicas históricas; no se hacen sondas nuevas en esta revisión.

El replay fuente T2b existente y sus modelos guardados son reutilizables según su recibo, con fuente desarrollada hasta2024. Ese recibo todavía reclama la calibración/enlace de observación con grupos destino protegidos. No se vuelve a inferir ni repetir ese replay. La admisión de F3c ya declaraba ausente el replay histórico completo de C1/F3c: el chequeo correcto del CSV era una representación reconstruida desde sus salidas.

El productor original sigue fuera del repositorio común y no se acredita su sello de versión completo. Esta carencia debe cerrarse antes de un futuro envío, sin atribuir al commit de evaluaciones P17–P19 la reproducción de F3c ni reescribir su autoría. El envío pasado precedió al protocolo de versionado de esa tarde.

Siguiente paso acotado: inspeccionar nombres de miembros de los paquetes originales restantes de MLind/código fuente identificados por sus manifiestos. Si la dependencia no se recupera, especificar una reconstrucción autocontenida con nombre y diferencias explícitos; no llamarla reproducción fiel por igualar un CSV. Cualquier ajuste posterior necesita receta completa, comparador y costes preinscritos.

B00/F3c/todas las alternativas permanecen.2024está abierto adaptativo. No hay evidencia nueva de mejora privada ni revisión profesional independiente. Recibo estático: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P20_linaje_F3c_20261026/discovery_receipt.json.
