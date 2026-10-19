import os, re
def rw(p, fn):
    s = open(p, encoding="utf-8", newline="").read(); crlf = "\r\n" in s
    s2 = fn(s.replace("\r\n", "\n"))
    if crlf: s2 = s2.replace("\n", "\r\n")
    open(p + ".tmp_claude", "w", encoding="utf-8", newline="").write(s2); os.replace(p + ".tmp_claude", p)
def rep1(s, a, b):
    assert s.count(a) == 1, a[:70]
    return s.replace(a, b)
# DECISIONES: Cierre D87 en CRLF
p = "Preparación/DECISIONES.md"
d = open(p, "rb").read(); assert b"## Cierre D87" not in d
body = open("Hackaton/Semana 1/Modelos_claude/foro/Cierre_D87_DECISIONES.md", encoding="utf-8").read().strip("\n").replace("\r\n", "\n").replace("\n", "\r\n")
sep = b"\r\n" if d.endswith(b"\n") else b"\r\n\r\n"
open(p + ".tmp_claude", "wb").write(d + sep + body.encode("utf-8") + b"\r\n"); os.replace(p + ".tmp_claude", p)
# README
R = "Hackaton/Semana 1/Modelos_claude/README.md"
rw(R, lambda s: rep1(s, "- En curso: dos semillas más de la frecuencia CatBoost por peligro de autos (`CFS_motor_s45`, luego CFSS6_motor con cuatro semillas en V24 y seis en 2025), adoptadas sin mirar el resultado (CLA-20261018-021).",
                     "- Dos semillas más de la frecuencia CatBoost por peligro de autos (`CFS_motor_s45`) dan en V24 0,08861, igual que las anteriores; con cuatro semillas en V24 la mezcla cambia +0,00000 en el agregado (`experimentos/robustez_s22_semillas_v24.json`). Sin efecto: no hay archivo nuevo (CLA-20261018-022, cierre de D87).\n- La línea B de Claude entregó S30 (S22 con severidad con tendencia en autos y edificios y pesos de cuerpo en contenidos), que obtuvo 0,12996 en el público (D88, CLB-20261018-002 y 003)."))
# INFORME
I = "Hackaton/Semana 1/Evaluacion_integral_claude/INFORME.md"
rw(I, lambda s: rep1(s, "La lectura posible, sin medir, es que la cola de 2024 está más cargada de reserva de caso que la de 2023, y un modelo que la descuenta gana en un año y pierde en el otro.",
                     "La lectura posible, sin medir, es que la cola de 2024 está más cargada de reserva de caso que la de 2023, y un modelo que la descuenta gana en un año y pierde en el otro. Dos semillas más en la frecuencia CatBoost de autos no cambian la mezcla (+0,00000 en V24). La línea B de Claude partió de S22 con severidad con tendencia y pesos de cuerpo en contenidos (S30) y obtuvo 0,12996 en el público; la diferencia con S22 y con 0,13 está dentro del ruido del subconjunto."))
# CLAUDE.md
C = "CLAUDE.md"
rw(C, lambda s: rep1(s, "| S22_claude_propio | Claude | 0,13774 | 0,12988 | S21 sin forma de hogar (D86); primer puesto público al enviarlo (D87) |",
                     "| S22_claude_propio | Claude | 0,13774 | 0,12988 | S21 sin forma de hogar (D86); primer puesto público al enviarlo (D87) |\n| S30_claude_b | Claude, línea B | 0,13788 | 0,12996 | S22 con severidad con tendencia y pesos de cuerpo en contenidos (D88); primer puesto público al enviarlo |"))
rw(C, lambda s: rep1(s, "con IDs CLA-20261018-001 a 021 hasta ahora; el siguiente es CLA-20261018-022.",
                     "con IDs CLA-20261018-001 a 022 hasta ahora; el siguiente es CLA-20261018-023."))
rw(C, lambda s: rep1(s, "D87 es lo último de Claude y la próxima libre es D88;",
                     "D87 y su cierre son lo último de la línea principal, D88 es de la línea B y la próxima libre es D89;"))
rw(C, lambda s: rep1(s, "y el tercer motor de frecuencia (LightGBM por peligro de profundidad intermedia con severidad GLM): en hogar ninguna combinación mejora V23 y V24 a la vez y en autos sube el agregado +0,00003 y +0,00004 (D85 y cierre de D86).",
                     "el tercer motor de frecuencia (LightGBM por peligro de profundidad intermedia con severidad GLM): en hogar ninguna combinación mejora V23 y V24 a la vez y en autos sube el agregado +0,00003 y +0,00004 (D85 y cierre de D86), y sobre S22 las relatividades de severidad acotadas al p99,5 (efecto en el redondeo), los LightGBM de hogar con tope y recargo uniforme (dividen los cortes) y dos semillas más en la frecuencia CatBoost de autos (+0,00000 en V24) (D87 y su cierre)."))
print("ok")
