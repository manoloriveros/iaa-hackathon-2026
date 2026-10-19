# Reconstrucción de la base preaudit desde once originales

El productor `rebuild_base.py` genera once tablas en una carpeta nueva. Solo lee los once Parquet originales y `rules.json`. No necesita las capas clean, capfix, refine, dupfix, renaudit o preaudit, ni sus bitácoras o listas de IDs. El comparador es otro programa y se ejecuta después de completar la generación.

## Qué reproduce

ID01 normaliza claves de clientes; EXP01 calcula exposición inclusiva ACT/365 con cuatro decimales; CAP01 divide entre mil las filas de la cohorte histórica; CAT01 aplica los alias de construcción; AGE01 deriva edad cumplida al inicio; DUP01 retiene el representante de ocho dígitos de cada pareja idéntica; REN00 y PRE00 añaden las marcas históricas de auditoría.

CAP01 se calcula sobre capitales originales, antes de cualquier corrección, sin cascada. Las cohortes CAP01, DUP01, REN00 y PRE00 se vuelven a derivar de los originales. Sus conjuntos o parejas tienen que coincidir con las huellas de las decisiones aprobadas. `rules.json` contiene esas huellas, cantidades, algoritmos y metadatos; no contiene listas de identificadores ni valores tomados de preaudit.

La preparación del contrato (`../prepare_base_rebuild_N62.py`) leyó la evidencia histórica para congelar esas huellas. Esa preparación no forma parte de la ejecución del productor. Los once SHA originales también están congelados: cualquier versión de datos distinta hace abortar el proceso, en vez de ampliar silenciosamente una decisión histórica.

La rama retrospectiva de capitales no entra en esta base. Las marcas audit_* siguen excluidas de predictores. REN00 usa continuidad futura al snapshot histórico y PRE00 no acredita cobertura. Ninguna regla convierte una valoración de siniestros en último verdadero, ni identifica reservas insesgadas o IBNER.

## Ejecutar el productor

Requiere Python, pandas, NumPy y PyArrow. La corrida guarda las versiones efectivas. No usa módulos del proyecto ni bibliotecas de ML.

En este equipo, PyArrow está disponible en el lector local del proyecto:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = 'C:/dev/Hakaton/Preparación/.cache/parquet-reader'

& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' rebuild_base.py `
  --raw 'C:/dev/Hakaton/Hackaton/Semana 1/Datos' `
  --rules './rules.json' `
  --out './otra_corrida_nueva'
```

Fuera de este equipo se puede usar un entorno que tenga esas bibliotecas, sin PYTHONPATH especial. Los caminos raw, rules y out son argumentos. La salida debe ser nueva y estar fuera de la carpeta raw. El programa no borra ni sobrescribe corridas existentes.

El recibo `build_receipt.json` conserva hashes antes y después, cohortes comprobadas, recuentos por regla, archivos de entrada leídos, versiones y hashes de salida. El registro de lecturas de datos del productor permite comprobar que no abrió capas de referencia. Es un control del código ejecutado y sus accesos registrados, no una certificación de aislamiento de sistema operativo. `COMPLETE.json` solo aparece cuando terminan las once tablas y sus controles.

## Comparar con la referencia congelada

`reference_contract.json` copia el catálogo preaudit que se tomó como referencia antes de producir. Solo lo consume el comparador, junto con las salidas nuevas. Los caminos de ese catálogo se resuelven contra project-root. Esta separación evita usar la respuesta de referencia para generar los datos.

```powershell
& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' compare_preaudit.py `
  --rebuild './run_v1' `
  --catalog './reference_contract.json' `
  --project-root 'C:/dev/Hakaton' `
  --out './comparison_v1'
```

Se comparan las once tablas, cantidad y orden de filas, orden de columnas, tipos lógicos, posiciones nulas y cada valor. No se aproxima ningún número. La comparación de celdas considera iguales dos NaN en la misma posición y contrasta por separado el mapa de nulos Arrow. Se informan aparte la igualdad completa del esquema/metadatos y la coincidencia de bytes SHA-256 de cada Parquet. Una serialización distinta puede contener exactamente las mismas filas y valores.

El comparador también comprueba que los archivos de referencia y las salidas no cambiaron durante la verificación. Si hay diferencias conserva su informe y termina con código distinto de cero. No cambia los datos para hacerlos coincidir.

## Integración y límites

Para integrar el productor en otro paquete bastan el script, rules.json, las dependencias y los once originales correspondientes a sus hashes. El comparador y su contrato son piezas de verificación adicionales. No copiar los datos o las corridas al repositorio de código.

La aceptación de esta tarea es igualdad exacta con la capa histórica preaudit. Eso acredita reconstrucción de esa capa bajo las mismas decisiones, no su idoneidad actuarial, disponibilidad prospectiva o una reconstrucción completa del modelo S30. No se entrenan modelos ni se llama a Kaggle.

Ver `plan.json`, `source_freeze.json` y el informe de cierre para procedencia, autorización humana y resultado real.


## Resultado comprobado

Corrida run_v1 y comparación comparison_v1: once tablas, 7826273 filas y 148424183 celdas; cero diferencias, todos los metadatos y once SHA idénticos. Siete tablas fueron transformadas y cuatro auxiliares se copiaron desde raw. Ver INFORME.md y verification.json. No se reentrenó ni hubo llamadas a Kaggle.
