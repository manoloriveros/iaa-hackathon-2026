"""Tarea 7 (cierre): D² total de 3 líneas en 2025 = 0,438·ΔD²_motor + 0,181·ΔD²_contents (conversión de I_t7_2025).
Normal aproximada: var = var(verdad, del bootstrap K300: (p95-p05)/3,29) + var(evaluación 2025, analítica).
Paquete del autor en motor: mezcla 50/50 entre prev/occ reales (K300_boot) y ruido (ruido=1)."""
import json
import numpy as np
from scipy.stats import norm
r = json.load(open("/home/claude/m017/revision/I_t7_2025.json"))
cv = r["factor_conversion_D2_linea_a_D2_total"]


def comp(key, modo="K300_boot", esc="T3_verdad=f_aplicado"):
    b = r[key][f"boot_verdad_{modo}"]
    sd_t = (b["p95"] - b["p05"]) / 3.29
    sd_e = r[key]["escenarios"][esc]["all"]["sd_eval"]
    return b["gan_media"], np.sqrt(sd_t ** 2 + sd_e ** 2)


def total(mot, con):
    m = cv["motor"] * mot[0] + cv["contents"] * con[0]
    s = np.sqrt((cv["motor"] * mot[1]) ** 2 + (cv["contents"] * con[1]) ** 2)
    return m, s, norm.cdf(-m / s)


out = {}
paq = {"recomendado: motor gender + contents gender+wfh+seg": (comp("motor|gender"), comp("contents|autor (gender+wfh+seg)")),
       "conservador: motor gender + contents gender+wfh": (comp("motor|gender"), comp("contents|gender+wfh")),
       "autor si prev/occ reales": (comp("motor|autor (gender+prev+occ)"), comp("contents|autor (gender+wfh+seg)")),
       "autor si prev/occ ruido": (comp("motor|autor (gender+prev+occ)", "ruido=1"), comp("contents|autor (gender+wfh+seg)"))}
for k, (a, b) in paq.items():
    m, s, p = total(a, b)
    out[k] = dict(gan_total_bp=round(m * 1e4, 1), sd_bp=round(s * 1e4, 1), P_empeora=round(float(p), 3),
                  motor_linea_bp=round(a[0] * 1e4, 1), contents_linea_bp=round(b[0] * 1e4, 1))
# mezcla 50/50 para el autor (Monte Carlo)
rng = np.random.default_rng(1)
k1, k2 = out["autor si prev/occ reales"], out["autor si prev/occ ruido"]
x = np.where(rng.random(200000) < .5, rng.normal(k1["gan_total_bp"], k1["sd_bp"], 200000), rng.normal(k2["gan_total_bp"], k2["sd_bp"], 200000))
out["autor mezcla 50/50"] = dict(gan_total_bp=round(float(x.mean()), 1), P_empeora=round(float((x < 0).mean()), 3))
print(json.dumps(out, indent=1))
json.dump(out, open("/home/claude/m017/revision/I_t7c_total.json", "w"), indent=1)
