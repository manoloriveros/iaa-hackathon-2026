"""Regenera tabla y comparaciones desde una captura, sin entrenar ni consultar Kaggle."""
import json
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def compare(candidate, reference):
    """Comparación válida cuando ambos scores comparten evaluación y denominador."""
    a, b = Decimal(candidate), Decimal(reference)
    if not a.is_finite() or not b.is_finite() or a > 1 or b >= 1:
        raise ValueError("Scores finitos; candidato <= 1 y referencia < 1")
    with localcontext() as context:
        context.prec = 28
        gap = a - b
        return {
            "delta_D2": str(gap),
            "relative_deviance_reduction_pct": str(100 * gap / (1 - b)),
            "candidate_deviance_over_reference": str((1 - a) / (1 - b)),
        }


def main():
    source = json.loads((ROOT / "captura.json").read_text(encoding="utf-8"))
    rows = source["rows"]
    glm = next(r for r in rows if r["name"] == "sandbox_2_basic_glm.csv")
    leader = rows[0]
    calculations = []
    table = [
        "| Puesto visible | Equipo o archivo | D² público | Envíos | Último visible | Brecha hasta RiskForge | D² − GLM | Reducción de desviación frente al GLM |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        result = compare(row["score_displayed"], glm["score_displayed"])
        result["name"] = row["name"]
        result["gap_to_visible_leader"] = str(Decimal(leader["score_displayed"]) - Decimal(row["score_displayed"]))
        result["normalized_deviance"] = str(1 - Decimal(row["score_displayed"]))
        calculations.append(result)
        rank = row["rank_displayed"] if row["rank_displayed"] is not None else "Referencia (sin puesto)"
        table.append(
            f'| {rank} | {row["name"]} | {row["score_displayed"]} | {row["entries_displayed"]} | '
            f'{row["last_displayed"]} | {Decimal(result["gap_to_visible_leader"]):.5f} | '
            f'{Decimal(result["delta_D2"]):+.5f} | {Decimal(result["relative_deviance_reduction_pct"]):+.4f}% |'
        )
    output = {"source": "captura.json", "arithmetic": "Decimal, 28 significant digits", "scores_are_rounded": True, "same_evaluation_assumed": True, "comparisons_vs_glm": calculations,
              "leader_vs_average_cost": compare(leader["score_displayed"], rows[3]["score_displayed"]),
              "glm_vs_average_cost": compare(glm["score_displayed"], rows[3]["score_displayed"])}
    (ROOT / "calculos.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    template = (ROOT / "metodos.md").read_text(encoding="utf-8")
    (ROOT / "TABLA_Y_CALCULOS.md").write_text(template.replace("{{TABLA}}", "\n".join(table)), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
