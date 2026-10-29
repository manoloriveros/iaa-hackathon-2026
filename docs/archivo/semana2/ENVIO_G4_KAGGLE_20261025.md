# Envío propio G4 procesado en Kaggle

Kaggle procesó el CSV propio G4 y devolvió estado COMPLETE, sin error, con D² Tweedie público de **0,13310**. Se envió el archivo congelado de 209.063 predicciones de 2025, sin reentrenar, recalcular C0 o generar nuevas inferencias. B00 y las alternativas se conservan; 2024 sigue cerrado.

Codex, 2026-10-25T11:28:22.148790+00:00. El participante autorizó expresamente enviar el CSV y verificar su procesamiento. La autorización se refiere a esta entrega; no equivale a aprobación técnica profesional ni a promoción formal. El envío se hizo el 25 de octubre de 2026 a las 06:26:10 Bogotá (11:26:10 UTC), en la competición [IAA AI Assisted Hackathon 2026, Part 2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2).

| Comprobación | Resultado |
| --- | --- |
| Identificador de Kaggle | 57628123 |
| Estado del servidor | COMPLETE |
| Score público D² Tweedie | 0,13310 |
| Filas | 209.063 |
| Archivo | submission_g4_glm_2023_2025.csv |
| Tamaño cotejado en servidor | 6.248.900 bytes |
| Recepción y procesamiento | ID, competición, mensaje, nombre y tamaño coinciden |
| Cupos consumidos en esta entrega | 1 |
| Disponibles en la última consulta | 6 |
| Nuevos ajustes o predicciones | 0 |

## Evidencia y alcance

La revisión de salida confirmó la misma huella SHA256, IDs únicos y orden idéntico a la plantilla emergente, dos columnas correctas y valores positivos finitos. El dry-run del skill aprobó cinco comprobaciones de formato. La consulta previa autenticada no encontró otro envío de este archivo o mensaje. Se hizo una única carga; después se siguió exclusivamente el identificador devuelto por esa carga, primero PENDING y luego COMPLETE. No se leyó el score privado ni scores o mensajes de otros envíos.

La huella local se comprobó de nuevo tras el procesamiento: `e5e30c5921c0494b7c0bebe76fbf33725f45ab392f7bed5ab7f6927a89f394ab`. El cotejo remoto confirma identidad de registro y tamaño; Kaggle no devolvió una huella criptográfica del contenido. Se conserva el replay exacto anterior del archivo y no se repitió. El paquete de código/modelos permanece privado y no se subió: solo se envió el CSV a la competición.

La receta histórica B20 tiene D² OOF2023 de 0,08938 frente a 0,06858 de B00; esa evidencia exploratoria se conserva, sin nuevos ensayos. El público actual mide otro conjunto y no demuestra que las carencias de mecanismo, soporte o concentración hayan desaparecido. G1/G2 y el ensayo de calibración anidada original siguen pendientes. Este CSV usa los GLM estándar sin recalibración. No se retiró B00, se modificó una receta o se cambió la selección final manual en Kaggle.

Los modelos finales siguen ajustados solo con 2023; las predicciones corresponden a 2025. En esta operación no se abrieron pólizas, predicciones, métricas, ledger, actas o SEL01 de 2024. Tampoco hubo entrenamiento remoto, nuevos chats, delegación, publicaciones de código/modelos o cambios de automatizaciones. La verificación es propia de Codex, sin atribuir revisión actuarial profesional independiente.

## Recibos

Índice: `Hackaton/Repositorio_IAA2026/registro/semana2_g4_envio_kaggle_actual.json`. Recibos locales y autenticados: `Hackaton/Repositorio_IAA2026/privado/semana2/envios/g4_20261025_v1` (`local_preflight.json`, `remote_preflight.json`, `skill_dry_run.txt`, `submission_response.json`, `scoring_check_01.json`, `scoring_check_02.json`). Foro previo COD-S2-20261025-G4-ENVIO-PREVIO; resultado COD-S2-20261025-G4-ENVIO-RESULTADO. CSV: `Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1/attempt1/submission_g4_glm_2023_2025.csv`. El conjunto de recibos conserva las fuentes/SHA y los cambios documentales de esta entrega, sin alterar las corridas históricas.
