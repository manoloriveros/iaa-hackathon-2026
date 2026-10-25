## 38. Semana 2: línea ML independiente de Claude (corte 24 de octubre, 15:30 UTC; 10:30 America/Bogota)

El 23 de octubre a las 21:30 de Bogotá el participante abrió una sesión de Claude (Proyecto IAA) con este encargo: «tu vas a trabajar de forma independiente a los otros esfuerzos que estamos haciendo, analiza la información de la primera y la segunda semana, los datos, y monta modelos de predicción de maching learnig, no pares hasta tener el modelo completo, validado y bien calibrado... toma tú todas las desiciones que consideres necesarias siempre y cuando no afectes los otros chats... tienes libertad de probar nuevas cosas, usar transformers, y las mejores tecnicas de entrenamiento de IA, incluso fine tuning». La sesión se interrumpió entre las 03:40 y las 12:20 UTC del 24 y el participante repitió el encargo; el entorno conservó todo.

Carpeta `Hackaton/Semana 2/Claude/ml_independiente_20261023/` (README, `INFORME.md` con diez figuras, `PREINSCRIPCION.md` SHA cf3e5d97…ff7e escrita a las 02:45 UTC antes de ajustar nada, `experimentos.jsonl` con E01-E08, N01, A01-A04, `lista_congelada.json` de las 14:19 UTC, `manifiesto.json`, `codigo/` con `verificar_informe.py`, 81 de 81 cifras también en el equipo). CSV por fila, OOF de DEV/HOLD/PCV y modelos en `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/`. Foro CLA-S2-20261024-015. Todo el código es propio, desde los 20 Parquet originales con SHA comprobado; no usa predicciones, factores ni código de otras líneas.

Lo que dejó:

- Etiqueta T0 (27.997.991,57 CU, igual a la de Codex) y completitud de reporte por fila ponderada por coste, por ramo y peligro, estimada en la cohorte 2021 del desarrollado (2024 emergente: 0,8027 autos, 0,9423 edificios, 0,9636 contenidos).
- Catorce modelos y tres mezclas con DEV (OOF 2023 por cliente), HOLD (2024 abierto una vez, 14:36 UTC) y PCV (2023-2024, solo para calibrar producción). Gana T2b, LightGBM Tweedie 1,5 entrenado en el desarrollado con el esquema común, transferido con un nivel por ramo: D² 0,1233 en DEV y 0,1253 en HOLD con la calibración final, frente a 0,0631/0,0732 de la tasa por ramo y 0,0896/0,0989 del mejor LightGBM solo emergente.
- FT-Transformer con Tweedie y desplazamiento: preentrenado en el desarrollado y ajustado en el emergente supera al entrenado desde cero en +0,0335 (DEV) y +0,0387 (HOLD), sin alcanzar al LightGBM transferido. Ajuste fino por boosting (T3), red residual tipo CANN (N3) y mezclas empatan dentro del ruido; modelo conjunto (T4), por peligro (T6) y GLM de adaptación (T5) son adversos.
- HOLD tumbó la tendencia del desarrollado (−0,0016 con C1) y el ajuste de nuevo negocio con K = 200 (+0,0031 en 2023, −0,0017 en 2024; exceso de nuevo negocio de autos 1,55 en 2023 y 1,00 en 2024). Desviaciones A03 y A04 declaradas después de abrir 2024.
- Producción sin enviar: `prediccion_2025_mlind.csv`, SHA d261388c7e4d5dcc…, 70.822.703 CU (autos 43,2 M, edificios 22,1 M, contenidos 5,5 M). Sensibilidades: ajuste de nuevo negocio 82,7 M, tendencia 76,8 M, preinscrita 89,7 M, T2c sin historia 70,1 M. Prima comercial de las 20 referencias con el nivel de balance.
- Revisión por subagente (sin errores; avisos recogidos) y respuesta medida a la auditoría de Codex (S2-AUD-MLIND-C0-SCOPE: efecto ≤ 0,0001 en D²; agrupación cliente-dirección: sin canal de fuga en T2b), `respuesta_auditoria_codex.json`.

Avisos para retomar:

- Esta línea no cambia la selección común ni la producción designada (sección 37); es una segunda estimación independiente con la misma conclusión de fondo.
- La incertidumbre que más pesa es el nivel del nuevo negocio de autos (77 % de la cartera 2025).
- `occupation` es la variable con más ganancia de T2b; en hogar puede ser en parte sobreajuste categórico. La ablación queda pendiente.
- La nube de Claude conserva en /home/claude/ml las bases y modelos; se pierde si el contenedor se recicla.
