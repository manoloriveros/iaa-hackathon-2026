"""Documenta el resultado público de S22 y las pruebas posteriores (D87) en README, INFORME y CLAUDE.md."""
import os

def rw(p, fn):
    s = open(p, encoding="utf-8", newline="").read(); crlf = "\r\n" in s
    s2 = fn(s.replace("\r\n", "\n"))
    if crlf: s2 = s2.replace("\n", "\r\n")
    open(p + ".tmp_claude", "w", encoding="utf-8", newline="").write(s2); os.replace(p + ".tmp_claude", p)

def rep1(s, a, b):
    assert s.count(a) == 1, a[:70]
    return s.replace(a, b)

README = "Hackaton/Semana 1/Modelos_claude/README.md"
SEC = """
## Undécima ronda, 18 de octubre al final de la tarde: S22 en el público y pruebas sobre S22

El participante decidió probar S22 y Codex lo envió (ref 57370117, archivo neutral `S22_riesgo_ultimo.csv`, mismo SHA-256): 0,12988 en el público, primer puesto al momento de la consulta, +0,00080 frente a A_G y +0,00114 frente a S21 (COD-20261018-084). Según la lectura fijada antes del envío (CLA-20261018-012), es coherente con que la forma de hogar no se traslada a 2025. El participante pidió seguir mejorando S22; cada prueba se fijó en el foro antes de calcularla.

| Prueba sobre S22 | V23 / V24, todas las filas | V23 / V24, sin el 0,1 % superior | Decisión |
| --- | ---: | ---: | --- |
| Sin forma en autos | −0,00024 / −0,00047 | −0,00017 / −0,00012 | La forma de autos se queda (`experimentos/robustez_s22_sin_forma_autos.json`) |
| Relatividades de severidad acotadas al p99,5 (`--tope=0.995`) | −0,00001 / −0,00001 | +0,00001 / +0,00004 | Efecto en el redondeo; no justifica un envío |
| Lo anterior más LightGBM de hogar con tope y recargo uniforme | −0,00020 / +0,00023 | +0,00006 / +0,00009 | No llega al mínimo: no hay S23 |

- `severidad_cfs.py` y `severidad_cfs3.py` aceptan `--tope=q`: la severidad por fila (y_p / n_p en filas con siniestro, sin ponderar por n) se acota al cuantil q del peligro en el entrenamiento del corte solo para estimar las pendientes; sin la opción los componentes se reproducen exactamente. La severidad media base no cambia, pero el total de 2025 sí cambia un poco después de la regla s17 (+0,003 % en autos, −0,066 % en edificios y −0,054 % en contenidos), como señaló Codex (COD-20261018-086).
- Los LightGBM de hogar con tope (`experimentos/s23_pruebas/cfg_hogar_tope.json`: 142.260 CU en edificios y 28.359,5 en contenidos, p99,5 de T0 positivo de 2021-2022, con el mismo mecanismo `cap` que autos) mejoran edificios en V24 (0,11257 → 0,11444) y lo empeoran en V23 (0,1143 → 0,11298). El recargo es un factor multiplicativo, total del entrenamiento entre total acotado (1,046 y 1,017 en 2021-2022).
- En curso: dos semillas más de la frecuencia CatBoost por peligro de autos (`CFS_motor_s45`, luego CFSS6_motor con cuatro semillas en V24 y seis en 2025), adoptadas sin mirar el resultado (CLA-20261018-021).
"""
rw(README, lambda s: s.rstrip("\n") + "\n" + SEC)

INFORME = "Hackaton/Semana 1/Evaluacion_integral_claude/INFORME.md"
SEC2 = """
### 4.11 S22 en el público y pruebas posteriores

S22 se envió por decisión del participante y obtuvo 0,12988 en el público, por encima de A_G (0,12908), S09b (0,12889), H (0,12886) y S21 (0,12874). El orden de los cinco en el público coincide en lo esencial con el orden en el cuerpo de la distribución de 2024 de la sección 4.10, y no con el de la distribución completa; sigue siendo un indicio con cinco puntos.

Sobre S22 se probaron tres cambios, cada uno fijado antes de calcularlo. Quitar la forma de autos empeora autos con y sin la cola, así que esa forma se queda: a diferencia de la de hogar, su ganancia no depende de los siniestros grandes. Estimar las relatividades de severidad con la severidad por fila acotada al p99,5 de cada peligro casi no cambia la mezcla (−0,00001 con todas las filas, hasta +0,00004 sin el 0,1 % superior). Entrenar los LightGBM de hogar con la etiqueta acotada y un recargo multiplicativo uniforme mejora edificios en 2024 y lo empeora en 2023; la combinación no llega al mínimo fijado y no se adopta. La lectura posible, sin medir, es que la cola de 2024 está más cargada de reserva de caso que la de 2023, y un modelo que la descuenta gana en un año y pierde en el otro.
"""
def f_inf(s):
    k = s.index("\n## 5. Límites")
    assert "### 4.11" not in s
    return s[:k] + "\n" + SEC2.strip("\n") + "\n" + s[k:]
rw(INFORME, f_inf)
rw(INFORME, lambda s: rep1(s, "En el público S21 obtuvo 0,12874, por debajo de S09b;",
                           "En el público S21 obtuvo 0,12874, por debajo de S09b, y S22 obtuvo 0,12988, el mejor resultado público al cierre de la tarde (sección 4.11);"))

CLAUDE = "CLAUDE.md"
rw(CLAUDE, lambda s: rep1(s, "| S21_claude_propio | Claude | 0,13807 | 0,12874 | Línea propia (D85); ensayo N30, por debajo de S09b pese a +0,00255 en V24 |",
                          "| S21_claude_propio | Claude | 0,13807 | 0,12874 | Línea propia (D85); ensayo N30, por debajo de S09b pese a +0,00255 en V24 |\n| S22_claude_propio | Claude | 0,13774 | 0,12988 | S21 sin forma de hogar (D86); primer puesto público al enviarlo (D87) |"))
rw(CLAUDE, lambda s: rep1(s, "con IDs CLA-20261018-001 a 017 hasta ahora; el siguiente es CLA-20261018-018.",
                          "con IDs CLA-20261018-001 a 021 hasta ahora; el siguiente es CLA-20261018-022. Una segunda sesión de Claude (línea B, abierta por el participante a las 14:36) escribe con IDs CLB- desde `Modelos_claude_b/` y numera sus candidatos desde S30; las dos líneas no tocan las corridas de la otra."))
rw(CLAUDE, lambda s: rep1(s, "D86 y su cierre son lo último de Claude y la próxima libre es D87;",
                          "D87 es lo último de Claude y la próxima libre es D88;"))
rw(CLAUDE, lambda s: rep1(s, "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 16:30 America/Bogota)",
                          "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 17:30 America/Bogota)"))
rw(CLAUDE, lambda s: rep1(s, "Corte de esta memoria: 18 de octubre de 2026, 16:30 America/Bogota en la sección 13;",
                          "Corte de esta memoria: 18 de octubre de 2026, 17:30 America/Bogota en la sección 13;"))
rw(CLAUDE, lambda s: rep1(s, "(tercer motor adverso también en autos; Codex retiene S22 por H2).",
                          "(tercer motor adverso también en autos; Codex retiene S22 por H2); la decimocuarta (17:30) añade S22 en el público (0,12988, primer puesto) y D87."))
print("ok")
