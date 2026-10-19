## Décima ronda, 18 de octubre a media tarde: resultado público de S21 y variante robusta S22

Con autorización del participante (N30), Codex envió H y S21. H obtuvo 0,12886 y S21 0,12874 en el público, por debajo de A_G (0,12908) y de S09b (0,12889) (COD-20261018-049). En V24, S21 superaba a S09b en +0,00255 y lo hacía en el 99,6 % de los subconjuntos del 30 % de los clientes, así que la inversión no se parece al ruido de muestreo de clientes de 2024.

### Diagnóstico sin etiquetas de 2025

- Nivel. S21 predice para 2025 un 2,4 % más que S09b (214,3 frente a 209,2 millones de CU). Mover todo S21 un 2,4 % cambia el D² agregado entre −0,00031 y +0,00015 en V24 y −0,00008 en V23, muy lejos de las 0,0027 de la inversión.
- Forma y nivel. `diagnostico_forma_nivel.py` mide el cociente entre el total con forma y sin ella en cada corte: autos 1,011, 1,010 y 1,013 (V23, V24 y 2025), edificios 1,079, 1,083 y 1,080, contenidos 1,034, 1,034 y 1,031. La forma no desplaza el nivel de 2025 respecto de los cortes donde se ajusta el factor (`experimentos/diag_forma_nivel_s21.json`).
- Cola. Frente a S09b, sin el 0,1 % superior de las filas, S21 queda en −0,00103 en V23 (edificios −0,00335, contenidos −0,00186) y +0,00036 en V24. La misma mezcla sin la forma de hogar gana a S09b en los tres ramos y los dos cortes con y sin ese 0,1 % (`experimentos/robustez_s21_sin_forma_hogar.json`).

### S22_claude_propio

`S22_claude_propio.csv` (SHA-256 `c21a02e14de4a89f892604239b7cfd9ac4e95ea7d175460a25ba806a5a3541b0`, nota `../Envios/S22_claude_entrega_codex.json`) es S21 con la forma solo en autos: mismos componentes, pesos, regla de nivel y factor de año siguiente. Total 211.689.735,38 CU; tasas 2025 por unidad de exposición 594,5, 492,1 y 125,7. `reproducir_mezcla.py` lo repite en el equipo con el SHA-256 idéntico (`experimentos/reproduccion_s22_equipo.json`).

| Ramo | V23 / V24 frente a S09b | Sin el 0,1 % superior | V23 / V24 frente a S21 | Sin el 0,1 % superior |
| --- | ---: | ---: | ---: | ---: |
| Autos | +0,00095 / +0,00283 | +0,00075 / +0,00099 | 0 / 0 | 0 / 0 |
| Edificios | +0,00197 / +0,00114 | +0,00136 / +0,00170 | −0,00153 / −0,00089 | +0,00471 / +0,00146 |
| Contenidos | +0,00328 / +0,00340 | +0,00112 / +0,00074 | −0,00016 / −0,00010 | +0,00298 / +0,00160 |
| Agregado | +0,00164 / +0,00222 | +0,00097 / +0,00114 | −0,00054 / −0,00033 | +0,00200 / +0,00077 |

En 2024, frente a A_G gana +0,00165 (IC95 por cliente [+0,00052; +0,00308]) y sigue por encima con la reserva × 0,75 (+0,00156) y × 1,25 (+0,00173); frente a H queda en +0,00048 ([−0,00041; +0,00138]), +0,00069 y +0,00030, y en edificios por debajo de H (−0,00030 nominal, −0,00087 con +25 %). En los subconjuntos del 30 % de 2024, S21 supera a S22 en el 86,4 % de los casos en V23 y el 79,8 % en V24: si 2025 se comportara como 2024, lo esperable sería que S21 quedara por encima. Sin la forma, el factor de año siguiente deja el total de edificios por debajo del observado en V23 (cociente observado/predicho 1,080, frente a 1,001 con forma; `experimentos/medias_por_ramo_s22.json`), porque el factor que minimiza la devianza Tweedie no coincide con el que iguala totales cuando las predicciones quedan concentradas.

La lectura del resultado público de S22 quedó fijada antes de cualquier envío (CLA-20261018-012): si supera a S21, es coherente con que la forma de hogar no se traslada a 2025; si queda igual o por debajo, la inversión viene de otra parte y la forma no se cambia solo por eso.
