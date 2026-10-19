"""Añade el diagnóstico de cuerpo y cola (CLA-20261018-015) a README, INFORME y CLAUDE.md."""
import os

def rw(p, fn):
    s = open(p, encoding="utf-8", newline="").read()
    crlf = "\r\n" in s
    s2 = fn(s.replace("\r\n", "\n"))
    if crlf:
        s2 = s2.replace("\n", "\r\n")
    open(p + ".tmp_claude", "w", encoding="utf-8", newline="").write(s2)
    os.replace(p + ".tmp_claude", p)

def rep1(s, a, b):
    assert s.count(a) == 1, a[:70]
    return s.replace(a, b)

README = "Hackaton/Semana 1/Modelos_claude/README.md"
BUL = ("- `diagnostico_cuerpo_cola.py` compara el orden de los candidatos enviados en 2024 con y sin el percentil superior de T0, reescalando cada uno por ramo con su factor óptimo dentro del subconjunto. Con todas las filas el orden local (S21, S22, H, A_G, S09b) es casi el inverso del público (A_G 0,12908, S09b 0,12889, H 0,12886, S21 0,12874); sin el p99,5 queda S22, S09b, A_G, H y S21, más parecido al público. Son cuatro puntos y recortar por la etiqueta no es una regla de puntuación válida: es un diagnóstico, calculado después de fijar S22 (`experimentos/diag_cuerpo_cola_publicos.json`, CLA-20261018-015).\n")
rw(README, lambda s: s.rstrip("\n") + "\n" + BUL)

INFORME = "Hackaton/Semana 1/Evaluacion_integral_claude/INFORME.md"
PAR = ("\n\nDespués de fijar S22 se comparó el orden de los candidatos enviados en el cuerpo de la distribución de 2024 (`diagnostico_cuerpo_cola.py`): sin el percentil superior de T0 y con cada candidato reescalado por ramo a su factor óptimo, para que pese la forma y no el nivel. Con todas las filas el orden local es S21, S22, H, A_G y S09b, casi el inverso del público; sin el p99,5 es S22 (0,11168), S09b (0,11160), A_G (0,11143), H (0,10996) y S21 (0,10968), y sin el p99 S09b, A_G, S22, H y S21. El público se parece más al orden del cuerpo que al de la distribución completa, lo que apoya la lectura de que la cola de 2024 no se traslada al subconjunto público. Son cuatro puntos y el recorte por la etiqueta no es una regla de puntuación válida, así que queda como indicio.")
rw(INFORME, lambda s: rep1(s, "y en los subconjuntos de 2024 lo esperable sería que S21 quedara por encima de S22 (lo hace en el 80 % al 86 % de los casos).",
                           "y en los subconjuntos de 2024 lo esperable sería que S21 quedara por encima de S22 (lo hace en el 80 % al 86 % de los casos)." + PAR))

CLAUDE = "CLAUDE.md"
rw(CLAUDE, lambda s: rep1(s, "con IDs CLA-20261018-001 a 014 hasta ahora; el siguiente es CLA-20261018-015.",
                          "con IDs CLA-20261018-001 a 015 hasta ahora; el siguiente es CLA-20261018-016."))
rw(CLAUDE, lambda s: rep1(s, "Codex volvió a A_G como ancla principal por instrucción del participante (COD-20261018-050).",
                          "Codex volvió a A_G como ancla principal por instrucción del participante (COD-20261018-050). En el cuerpo de la distribución de 2024 (sin el p99,5 de T0 y con cada candidato reescalado por ramo), el orden local de los enviados se parece al público (S09b y A_G por encima de H y S21) y S22 queda arriba, mientras que con todas las filas el orden es casi el inverso (`diagnostico_cuerpo_cola.py`, CLA-20261018-015; indicio con cuatro puntos)."))
print("ok")
