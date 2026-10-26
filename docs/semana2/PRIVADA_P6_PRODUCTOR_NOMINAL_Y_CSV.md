

## Privada P6: productor nominal S2/H1 y CSV reproducible, 26 de octubre de 2026

Codex, 2026-10-26T15:34:55.821031+00:00. Se preparó un CSV técnico de 209.063 predicciones con la base S2/H1 que se ha evaluado localmente. El productor ajustó la base estándar con los 109.296 periodos de 2023–2024 y reutilizó las tasas fuente, relatividades A1S y cinco correcciones H1/G3 de producción ya guardadas. No consumió los precios F3c ni la forma de renovaciones de PUL2. Se conservaron objetivo T0, modelos fuente, credibilidad, variables y pesos del algoritmo. La ampliación de tamaños de entrenamiento, de 80/64% a 100/80%, es el ajuste final habitual del algoritmo; no se presenta como una nueva validación o una mejora probada por tener más datos.

| Artefacto o control | Resultado |
|---|---|
| CSV técnico | `codex_S2_H1_nominal_2025.csv` |
| Filas y orden oficial | 209,063; coincidencia exacta |
| Redondeo | Una sola vez, tras la media, a seis decimales; racional binario y Decimal independientes |
| Replay con respuestas futuras corruptas | Exacto, con ajustes bloqueados |
| Reordenar toda la cartera | Precios idénticos tras orden canónico |
| Otro proceso y comando de exportación | Mismo CSV byte por byte |
| Envíos o scores nuevos | Ninguno |

La aplicación exige la cartera completa porque sus normalizadores dependen de ella. Rechaza claves faltantes/duplicadas, lotes parciales, año incorrecto y exposición no positiva. Los marcadores observados cero de 2025 no entran en el precio último; se usa una sola exposición calendario. El flujo sintético de los tres ramos también verificó la identidad al reducir a la mitad toda la exposición, la paridad del componente N3 y el rechazo de entrenamiento con periodos futuros.

Se hicieron únicamente 15 ajustes de reporte y seis calibraciones cerradas, con 108 constantes de precio. No se repitieron los modelos fuente o miembros ya aprendidos. Las 15 curvas y nueve aprendices sintéticos, controles de replay y normalizadores se cuentan aparte. Los nuevos C0 completos pasaron el cotejo de marcas/CDF por probabilidades de evento; los niveles se comprobaron por sumas escalares. Los SHA de fuentes registradas permanecieron iguales.

El proceso independiente reconstruyó todas las predicciones desde JSON y Parquet guardados, con 13 entradas de estimación bloqueadas. Se validó después un comando de exportación real que escribe otra copia exacta; su código tiene su propio recibo, sin atribuirle automáticamente el anterior. La reproducción comprobada es local y usa las cachés fuente preparadas del workspace. No se ha verificado portabilidad a otra máquina o un productor de nuevas cohortes desde datos crudos.

| Contexto de nivel, sin score predictivo nuevo | Coste total CU |
|---|---:|
| Base S2 completa, antes de H1 | 76,499,042.31 |
| Candidato S2/H1 | 77,816,901.61 |
| F3c conservado, CSV publicado previamente | 87,269,136.42 |

La corrección H1 aumenta la base S2 un 1.7227%. El nuevo candidato tiene un total 10.8311% menor que F3c. La diferencia de base es material y no se ha aislado su causa. No demuestra una mejora o deterioro privado, ni autoriza igualar totales con un multiplicador. La referencia F3c conserva su recibo público 0,16914; ese score no pertenece a este nuevo CSV.

Decisión: conservar el CSV como artefacto técnico reproducible, sin promoción, admisión predictiva o envío. Persisten los adversos de precios congelados, la pérdida en autos nuevos de 2023 con reservas125, el mínimo nominal conjunto incumplido y el escaso soporte hacia la cartera de 2025. 2023/2024 siguen siendo desarrollo adaptativo; los maestros sin fecha, la valoración común y la cola tardía limitan la interpretación. Ninguna revisión propia constituye aprobación humana o validación profesional independiente. B00, F3c y todas las alternativas/fallos se conservan; 2024 permanece abierto.

El siguiente paso es revisar la brecha de nivel y la evidencia disponible sobre ventanas de reporte en cohortes desarrolladas maduras, comprobando primero qué se hizo ya. La nueva C0 completa solo ve la historia emergente 2023/2024 y no identifica una cola posterior a su soporte. Un backtest de ventanas sobre una cohorte madura puede comprobar esa limitación del estimador, condicionado a marcas finales y mercado fuente; necesita receta, grupos, cortes y criterio previos si aún no existe. No aportará soporte emergente por sustitución ni se adoptará un prior de cola sin evidencia. También se conservarán como explicaciones alternativas las diferencias de backbone y calibración.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P6_productor_S2_H1_nominal_20261026_v1/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P6_productor_S2_H1_nominal_20261026_v1/independent_process_replay.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P6_productor_S2_H1_nominal_20261026_v1/reproduccion_comando_2025.receipt.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P6_productor_S2_H1_nominal_20261026_v1/level_context.json.

SHA256 del CSV: `7421b827ec9ca73b30af4981bf007231380e339322cff3ebba188c7b293f2647`.
