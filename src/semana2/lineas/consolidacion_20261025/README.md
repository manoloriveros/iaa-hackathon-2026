# Consolidación del proyecto y post-mortem de la parte 1 (25 de octubre de 2026)

Sesión de Claude (Proyecto IAA) a pedido de Manuel: consolidar las dos semanas, diagnosticar, elegir la ruta y dejar un plan hasta el cierre. El documento completo, con diagramas y el plan por días, está en Claude Docs: «Hackathon IAA 2026: consolidado del proyecto y plan de trabajo» (https://claude.ai/artifact/YNjr2fLGE5s1Uez7og1Vqd).

## Post-mortem de la parte 1

`postmortem_parte1.py` lee la consulta viva de Kaggle que Codex guardó el 23 de octubre (`Repositorio_IAA2026/privado/resultados_privados_parte1_20261023/consulta_viva_envios.json`) y escribe `postmortem_parte1.json`. Solo usa la biblioteca estándar; se repite con `python3 postmortem_parte1.py` desde esta carpeta.

- Correlación de rangos con el privado en los diez candidatos de estructura: V24 local 0,94; público 0,61. Entre los ocho mejores: 0,88 y 0,24.
- Óptimo de nivel por ramo (sondas S40 sobre S30): público 0,977 / 1,075 / 1,084; privado 0,939 / 1,003 / 1,007. Los desvíos caen a 0,8, 1,0 y 1,4 desviaciones típicas del ruido corregido de D103.
- La forma cerrada reproduce el privado observado de S41 (0,13864) y S42 (0,13863). Con el óptimo público pleno el privado habría sido 0,13844; con el óptimo privado, 0,13890 (todavía 0,00033 por debajo del primero, 0,13923).

Lectura: para elegir estructura, la validación local predijo el privado mucho mejor que el tablero público; el nivel medido en el público solo sirve cuando la señal supera con holgura al ruido, y la credibilidad de D100 protegió el privado.

## Decisiones de la consolidación

Estructura por validación local, nunca por el público; nivel por el público solo con señal clara y credibilidad preinscrita; final de la parte 2 = mezcla robusta 50/50 llevada a los totales por celda de la sonda ramo × nuevo negocio (respaldo: mezcla robusta × 1,1877), congelado el lunes 26; del 27 al 29, informe, video y código de las dos partes. Una sola línea de producción. Ver la sección 47 de `CLAUDE.md`.

Verificación de IA, no revisión profesional humana.
