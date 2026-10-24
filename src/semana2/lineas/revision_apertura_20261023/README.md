# Revisión de la apertura de semana 2

Claude, 23 de octubre de 2026. Evidencia del aporte [CLA-S2-20261023-001](../../Foro/FORO.md), que responde a COD-S2-20261023-001 y a los aportes de Codex hasta COD-S2-20261023-009. El participante pidió revisar la apertura de Codex: comprobar por cuenta propia las cifras del diagnóstico desde los Parquet, revisar el plan y el calendario y responder en el foro, sin entrenar ni aplicar correcciones.

La revisión es descriptiva. No ajusta modelos, no cambia datos y no guarda nada por fila: todo lo que hay aquí son agregados. Las comparaciones entre mercados son brutas y no separan composición de nivel. Es trabajo de IA, sin revisión humana.

## Qué contiene

| Archivo | Contenido |
| --- | --- |
| `revisar_apertura.py` | Recalcula todo desde los originales con código propio y escribe la evidencia, las tablas, las figuras y el manifiesto |
| `figuras.py` | Dibuja las tres figuras a partir de `evidencia.json` y `tablas/` |
| `evidencia.json` | Las cifras de los datos originales, agrupadas por tema: integridad, escala, exposición, siniestros, nuevo negocio, historia, capital, peculiaridades del generador, clima, mercados, relatividades y prima comercial |
| `tablas/` | Seis CSV: agregados por mercado, ramo y año; frecuencia y severidad por peligro; razones entre mercados; retrasos de reporte con la prueba KS; relatividades one-way; curvas de frecuencia por clima |
| `diagnostico_desarrollo2023.py` | Lee las predicciones fuera de muestra y el diagnóstico de ajuste de la tanda de 2023 de Codex (`dev_20261023T173828Z_7efe46fc`) y las matrices F0 (`f0_ultimo_20261023T170841Z_82038766`), comprueba sus SHA contra los manifiestos de esas corridas y recalcula métricas sin cargar modelos ni ajustar |
| `desarrollo2023_diagnostico.json` | Resultado del anterior: D² reproducidos, D² con balance dentro del ajuste, A/E por nuevo negocio y renovación, D² ponderado a la mezcla de 2025 y comprobaciones de F0 |
| `fig1_peligros_mercados.png` | Frecuencia y severidad emergente frente a desarrollada por peligro, ocurrencias de 2023 |
| `fig2_lo_que_se_traslada.png` | Relatividades one-way y medianas de retraso de reporte en los dos mercados |
| `fig3_nuevo_negocio_nivel.png` | Peso del nuevo negocio por año y efecto de su relatividad sobre el nivel de 2025 |
| `aporte_CLA-S2-20261023-001.md` | Cuerpo del aporte tal como se anexó al foro |
| `cifras_aporte.json` y `verificar_aporte.py` | Cada cifra del aporte con su ruta en una de las dos evidencias; el verificador comprueba que el texto la cita bien |
| `verificacion_aporte.json` | Resultado del verificador, con las huellas de las evidencias y del aporte |
| `manifiesto.json` | SHA-256 de las entradas, los scripts y las salidas de la corrida principal |

## Cómo repetirlo

Desde `C:/dev/Hakaton`, con el Python del laboratorio (necesita pandas, pyarrow, scipy y matplotlib):

```powershell
$py = 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe'
$dir = 'Hackaton/Semana 2/Claude/revision_apertura_20261023'
& $py "$dir/revisar_apertura.py" --out "$dir/repeticion"
& $py "$dir/diagnostico_desarrollo2023.py" --out "$dir/repeticion/desarrollo2023_diagnostico.json"
& $py "$dir/verificar_aporte.py"
```

Sin argumentos de datos, `revisar_apertura.py` lee `Hackaton/Semana 2/Datos/emerging` y `Hackaton/Semana 1/Datos`, y compara sus SHA-256 con `Codex/fuentes/download_manifest.json` y con el manifiesto oficial de semana 1 (`Preparación/artifacts/verification/iaa_launch_20261016/data_manifest.json`). Si alguna huella no coincide, se detiene sin calcular. Con `--sin-figuras` no necesita matplotlib. `diagnostico_desarrollo2023.py` hace lo mismo con los manifiestos de las corridas de Codex. El verificador lee las evidencias de esta carpeta.

La corrida original se hizo en la nube de Claude con Python 3.13.17, pandas 3.0.5, numpy 2.5.3, pyarrow 26.0.0, scipy 1.18.1 y matplotlib 3.11.2, y tardó unos 100 segundos. Repetida en la misma nube, dio las tablas idénticas byte a byte y la misma evidencia salvo la hora. Los D² reproducidos de la tanda de 2023 coinciden con `sklearn.metrics.d2_tweedie_score`.

## Definiciones que conviene tener presentes

- La etiqueta T0 de esta revisión es diagnóstica: suma de `incurred_to_date − recoveries` de los siniestros no rechazados asignados a la fila por póliza y fecha de ocurrencia. No sustituye a la base del proyecto.
- La exposición de todos los cálculos es días inclusivos / 365. En el desarrollado se excluyen las 604 copias DUP01 (los `claim_id` de once caracteres) y se rellenan con ceros los `customer_id` de autos (ID01) para unir clientes.
- Las bandas de edad del desarrollado se construyen con los mismos cortes que el emergente (17–24, 25–34, 35–49, 50–64, 65+).
- La cola de reporte del desarrollado se mide en las ocurrencias de 2021 y 2022, observadas al 31-12-2024 entre dos y cuatro años: cuota del conteo y del incurrido neto reportados después de 365, 730 y 1.095 días.
- La sensibilidad al clima de 2025 aplica a la exposición del test la frecuencia emergente de 2023–2024 por tramos de una sola variable, primero con el clima de 2024 de cada dirección y después con el de 2025. Es un orden de magnitud, no un modelo candidato.
- El balance dentro del ajuste multiplica las predicciones fuera de muestra de cada nodo (receta, ramo y fold) por el A/E de sus propias filas de ajuste, tomado de `fit_vs_oof.json`. La ponderación a la mezcla de 2025 multiplica las filas de nuevo negocio y de renovación de cada ramo para que su exposición pese lo mismo que en el test. El «nivel observado de cada ramo» usa el A/E fuera de muestra y solo sirve como cota diagnóstica.
