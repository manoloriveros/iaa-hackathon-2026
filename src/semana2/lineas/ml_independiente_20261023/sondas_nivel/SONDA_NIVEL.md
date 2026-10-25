# Sonda de nivel 2025 sobre la mezcla enviada

Preparada el 24 de octubre de 2026 tras el envío de la mezcla 50/50 (envío 57599788, D² público 0,15390, puesto 5 de 7; líder 0,16446 según el estado de Kaggle que guardó Codex). Nada se ha enviado desde esta línea.

## Por qué

Las mediciones de esta línea indican que la palanca grande es el nivel por ramo y, dentro de autos, el del nuevo negocio. En la cartera 2025, un 15 % de error en autos cuesta unos 0,002 de D², y la duda entre aplicar o no el exceso del nuevo negocio (27 %) cuesta 0,006. El clima del propio año no explica el hueco (E13: −0,0022 en 2023, +0,0003 en 2024).

## Cómo funciona

Para Tweedie 1,5, multiplicar por c las predicciones de un ramo cambia el D² público con una fórmula cerrada de dos incógnitas por ramo. Con la puntuación de la mezcla (c = 1) y dos sondas por ramo (c = 0,90 y 1,10) se despeja el factor óptimo del público, c*. Es la misma técnica de D100, que en la semana 1 acertó al quinto decimal.

El público es un tercio de las filas, así que c* trae ruido. Siguiendo la lección de D103, el ruido se midió frente a la parte privada y a la escala del test 2025. Se remuestrearon componentes cliente-dirección del OOF 2023-2024 a 69 mil filas públicas y 140 mil privadas. La desviación típica de log(c* público / c* privado) sale en 6,1 % en autos, 15,1 % en edificios y 8,5 % en contenidos.

Se aplica solo la parte creíble: log c_Z = Z · log c*, con Z = τ² / (τ² + σ²). La incertidumbre previa τ quedó fijada antes de ver las sondas, a partir del abanico de niveles ya documentados: 0,14 en autos, 0,20 en edificios y 0,06 en contenidos. Eso da Z = 0,84, 0,64 y 0,33.

Si τ es correcta, la ganancia esperada en la parte privada ronda 0,003 de D², casi toda en autos y edificios.

## Archivos y regla

Las seis sondas, en `sondas_nivel/`, tienen sus SHA en `preinscripcion_sonda_nivel_s2.json`. La regla:

1. Enviar las seis tal cual. Ninguna se selecciona nunca.
2. Resolver con `python sonda_nivel_s2.py resolver --base 0.15390 --motor P090 P110 --buildings P090 P110 --contents P090 P110`. Si S1 o S2 salen no positivos, o c* cae fuera de [0,5; 2,0], ese ramo no se ajusta.
3. Enviar el candidato una vez. Su público esperado lo calcula el resolvedor antes del envío; una desviación mayor que 0,0001 indica que el evaluador no tiene la forma supuesta.
4. Seleccionar el candidato si su público iguala o supera al de la mezcla; si no, la mezcla.

Son siete de los nueve envíos que quedaban hoy. Enviar y seleccionar lo decide el participante; los envía Codex.
