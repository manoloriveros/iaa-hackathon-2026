# Revisión independiente de la sonda por ramo × nuevo negocio (subagente de IA, 25-10-2026)

Revisor: subagente general de Claude, sin contexto previo, con acceso al código y a las salidas. Es una revisión de IA, no una revisión profesional humana. Lo que sigue es un resumen fiel de su informe, traducido.

Veredicto: nada bloqueante. Los cinco archivos de sonda son correctos y se pueden enviar, y la regla es sólida. Recomienda enviar F primero y corregir dos puntos del resolutor (2 y 3) antes de usarlo.

Lo que comprobó:

1. Álgebra. Con Tweedie 1,5, Σdev = constante + 4c^(−1/2)·Σyμ^(−1/2) + 4c^(1/2)·Σμ^(1/2), y eso separa la puntuación por celdas. La ecuación del resolutor para a_s es exacta (en 2024 coincide con 4Σyμ^(−1/2)/N con un error relativo de 1e−14). Es correcto usar D2(F) observado y g = 1,187658, y deducir motor_1 de βA − Σ a_s. El redondeo de la sonda global mueve βA ±0,0014, y eso cambia log c* de motor_1 en 0,005 como mucho.
2. La aproximación de b_s. En 4.000 tercios al azar del μ de 2025, la cuota de Σμ^(1/2) de cada celda se desvía con una desviación típica entre 0,4 % (motor_1) y 1,3 % (buildings_0). Ese error llega a c*_s multiplicado por |1 − 1,301/c*_s| ≈ 0,066 cerca de c* = 1,22, así que queda por debajo de 0,001 en log c*. El redondeo de las puntuaciones añade como mucho 0,005 (contents_0).
3. Los cinco CSV pasan todos los controles: filas, orden y número (209.063) iguales a F; filas sin escalar idénticas a F byte a byte; filas escaladas iguales a F×1,2 con un error de 4e−7 como mucho; recuentos por celda correctos; valores positivos y finitos; saltos LF; SHA-256 iguales a la preinscripción.
4. Recuperación de c*_s. Con `--prueba`, el mayor error de log es 0,026 (buildings_1, con c* = 0,50). En su propia prueba (μ real de 2025, siniestralidades de 2023 y 2024, particiones nuevas y redondeo a cinco decimales, 150 réplicas por año), c*_s acierta el óptimo público con una desviación típica de 0,008 o menos (máximo 0,03), y ningún a_s salió ≤ 0.

Hallazgos a corregir, todos aplicados:

- Orden de envío: nada obligaba a enviar F primero, y si F para, se pierden las cinco sondas. Corregido: la preinscripción fija enviar F primero y las sondas solo si F encaja.
- Puntuaciones sin atar a archivos. Corregido: el resolutor acepta las puntuaciones por nombre de archivo o por recibo con SHA-256, y rechaza nombres de celda.
- a_s ≤ 0 se dejaba en g sin avisar. Corregido: el modelo implica a_s > 0, así que ahora detiene el resolutor.
- La parada de 0,7 usaba c*_s sin contraer y en el escenario sin desviación saltaba en el 0,7–5 % de las réplicas, casi siempre por buildings_0. Corregido: la parada es max(0,7; 3σ_s).
- El σ de las celdas de nuevo negocio descansa en pocos datos: entre 1.507 y 3.915 filas de origen, con 35 a 348 siniestros, cada una repetida entre 17 y 27 veces. En su remuestreo por filas, el σ coincide con el de diseno.json con un margen de un 25 % en casi todas las celdas, salvo motor_1 de 2023 (0,12 frente a 0,067). Corregido de forma conservadora: Z usa el mayor σ de los dos años (`sigma_por_pool.json`; motor_1 0,0786, Z 0,866). Los dos cálculos no coinciden del todo y no se adopta el 0,12, que viene de otro método; queda declarado.

Menores:

- La parada 1 era asimétrica en el borde. Corregido: ahora compara el intervalo de redondeo de la puntuación observada con el intervalo previsto [0,1594743; 0,1594849].
- diseno.json no guardaba la composición por año. Ahora `sigma_por_pool.json` guarda la composición, las repeticiones, los NaN y los siniestros de origen.
- `--prueba` usa la mezcla de 2024, donde motor_1 es pequeña, y reescribe con el mismo contenido las salidas de evaluar_final. Está documentado.
- La previa sortea la verdad con el mismo τ que fija Z y seis celdas independientes, lo que favorece a ramo × nuevo negocio. Declarado en el informe y en la preinscripción.

Ramo × nuevo negocio frente a ramo, según el revisor: en diseno.json, +0,0013 y +0,0015 con la previa, +0,0000 (2024) y +0,0065 (2023) como el año, y −0,0001 y −0,0002 sin desviación. En sus corridas pareadas sobre el μ de 2025: −0,0003 y −0,0004 sin desviación, y +0,0009 y +0,0013 con la previa. La elección solo se sostiene si se cree que el nuevo negocio y la renovación se separan alrededor de 0,2 en log por celda; con diez envíos por día, el coste es aceptable.
