## 34. Validación nocturna independiente de las partes 1 y 2 y apertura única de 2024 (corte 24 de octubre, 02:15 UTC; 23 de octubre, 21:15 America/Bogota)

A las 18:15 de Bogotá el participante pidió en otra sesión de Claude (Cowork) retomar las dos partes y validarlo todo «de forma exhaustiva», con avances programados cada hora, empezando por modelos estándar y complicándolos solo si fuera estrictamente necesario, y añadió: «mantén tu evaluación independiente a las anteriores». Respondió también a las preguntas de arranque: abrir 2024 una sola vez con SEL01, auditar la parte 1 con una escalera simple sin tocar S41, avances cada hora y revisores independientes (subagentes) autorizados. Carpeta `Hackaton/Semana 2/Claude/validacion_nocturna_20261023/` (INFORME.md, BITACORA.md, código, cinco figuras, salidas agregadas, informes de los revisores rev1 a rev3, verificador de 82 cifras sin fallos, manifiesto de 62 archivos). Las producciones de 2025 están en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/`, sin enviar. Registro en DECISIONES.md (S2-PUERTA2024-CLAUDE-20261024) y en la clave `week_2_nightly_validation_claude_20261024`; aportes CLA-S2-20261024-005 (preinscripción), 006 (acta) y 009 (cierre del primer bloque).

Todo el código es nuevo, escrito desde los originales comprobados por SHA, y las cifras previas solo se compararon al final. La base emergente coincide con la de Codex: 609 exposiciones corregidas, T0 de 27.997.991,57 CU, 36 siniestros de prehistoria y 349 capitales entre mil. La del desarrollado coincide con D42, D47, D59, D66 y D67. Decisiones nuevas, cada una con su prueba:

- VAR-N1: quitar seis variables de marketing sin señal (χ²/gl entre 0,15 y 2,1 en el desarrollado).
- CON-N1: WOD = t/w = timber y MIX = non_standard, por las proporciones de los dos mercados.
- MM-N1: quitar `make_model` del GBM (el D² interno de autos sube de 0,0743 a 0,0845).
- Mes de inicio en las relatividades, porque la mitad del efecto del nuevo negocio es calendario (rev1).

Escalera de desarrollo 2023, OOF con folds propios por cliente:

| Modelo | D² |
| --- | --- |
| Tasa por ramo | 0,068 |
| GLM solo emergente | 0,080 |
| GBM solo emergente | 0,083 |
| A1: relatividades de un LightGBM Tweedie del desarrollado (esquema común) × nivel emergente por ramo, 3 parámetros | 0,1213 |

Región, nuevo negocio emergente, clima persistente y nivel Tweedie no mejoran de forma robusta.

La frecuencia del nuevo negocio es la misma en los dos mercados (1,13–1,17 y 1,15–1,19), y en 2024 el nuevo negocio queda calibrado bajo A1 (razón 0,98): respaldo independiente de NB-CRED-01.

Apertura única de 2024: 00:55:37 UTC, lista congelada R0/A1/A2. D² de 0,0728, 0,1214 y 0,1175. A1 − R0 = +0,0486, con intervalo del 99,17 % de [+0,0265; +0,0733]. A1 pasa escenarios, segmentos e influencia, pero falla la salvaguarda de cliente nuevo (+0,0131, límite del 95 % en −0,0105), así que el titular es R0. Rev2 lo reprodujo todo y midió que esa salvaguarda pasaría solo el 26 % de las veces con el efecto observado.

Producciones sin enviar:

| Archivo | Total | SHA |
| --- | --- | --- |
| R0_2025.csv | 61,20 M CU | 928865e5… |
| A1_2025.csv | 67,15 M | 4a9f7fc0… |
| A1T_2025.csv | 72,40 M | 4ba0cc34… |

A1T es A1 con la tendencia del desarrollado (+4,6 %, +6,4 % y +3,6 % anual) durante 1,5 años. Rev3 estima niveles independientes más altos que A1 (601, 475 y 103 frente a 521, 432 y 94 CU por año). Su sospecha de que A1 no llevaba IBNR era errónea: el último implícito en 2023–24 es 17,76 M frente a 15,86 M de T0, porque la renovación abarata con la edad de la cartera.

El incendio de edificios (49 siniestros en 2023 frente a 21 en 2024, sin efecto año en el desarrollado) domina la incertidumbre del nivel.

La prima comercial de las 20 referencias sale con P = [R(1 + 0,12 hogar) + 85e]/(0,49 o 0,69). Se corrigió la sensibilidad por póliza en C00314425 y B00250679.

Parte 1, escalera en V24 (mismo T0 que S30):

| Modelo | D² |
| --- | --- |
| Tasa por ramo | 0,0736 |
| GLM | 0,1193 |
| Un GBM con F0 | 0,1290 |
| GBM con F0 + historia de la póliza | 0,1313 |
| S30 | 0,1379 |

S30 aportaba +0,0066 [+0,0048; +0,0086] sobre el mejor GBM único: complejidad justificada. El IBNR de autos 2024 con Lynden-Bell diario queda un 2,7 % por debajo del de D67.

Avisos para retomar:

- Decisiones del participante:
  - Enmendar o no la salvaguarda de cliente nuevo de SEL01. Con la enmienda, A1 promueve con la evidencia ya obtenida.
  - Nivel 2025: A1, A1T o una sonda con el ruido medido frente a la parte privada. Las desviaciones típicas estimadas son 0,054, 0,16 y 0,095 en logaritmo por ramo.
- 2024 ya no es una confirmación intacta para el proyecto: todo análisis posterior sobre ese año es exploratorio.
- Por la incidencia de Kaggle (sección 33), hoy no se puede enviar.
- Antes de publicar, comprobar el último CLA-S2-* (esta sesión usó 005, 006 y 009).
- La nube de Claude conserva en `/home/claude/noche/` los datos copiados, las bases y los modelos; se pierde si el contenedor se recicla.
