"""Semantic metric receipts from frozen inputs. No fitting or ledger operations.

Prepared in isolation by Codex. Importing this module never reads project data.
The caller must supply a frozen manifest; real confirmation remains unauthorized.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np

SCHEMA = "S2-METRIC-BINDING-v1"
RECEIPT = "S2-METRIC-RECEIPT-v1"
SCORER = {
    "name": "total-unit-tweedie-D2", "power": 1.5, "weight": "exactly-one",
    "null": "weighted-mean-recomputed-per-bootstrap-portfolio",
    "quantile": "linear", "rng": "numpy-PCG64-integers-v1",
    "influence": "descending-group-loss-improvement-ties-lexicographic-id",
}
KEY = ("market", "line", "row_id")
ABS_TOL = 1e-12
REL_TOL = 1e-10


class BindingError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BindingError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "Duplicate JSON key: " + k)
            result[k] = v
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(BindingError("Nonfinite JSON: " + x)))


def finite(value, label):
    require(type(value) in (int, float) and math.isfinite(value), "Missing finite number: " + label)
    return float(value)


def artifact(spec, root):
    require(isinstance(spec, dict) and set(spec) == {"path", "sha256"}, "Artifact requires exact path/sha256")
    require(isinstance(spec["path"], str) and spec["path"], "Empty artifact path")
    root = Path(root).resolve()
    path = (root / spec["path"]).resolve()
    require(path.is_relative_to(root) and path.is_file(), "Artifact outside root or missing")
    require(sha(path) == spec["sha256"], "Artifact SHA mismatch: " + spec["path"])
    return path


def table(spec, root):
    path = artifact(spec, root)
    if path.suffix.lower() == ".parquet":
        # Optional adapter for future real runs, not exercised against actual
        # project rows by this isolated correction or its synthetic tests.
        import pyarrow.parquet as pq
        rows = pq.read_table(path).to_pylist()
    else:
        value = read_json(path)
        require(isinstance(value, dict) and set(value) == {"rows"}, "Expected canonical rows object")
        rows = value["rows"]
    require(isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows), "Empty/invalid rows")
    return rows


def key(row):
    result = tuple(row.get(k) for k in KEY)
    require(all(isinstance(k, str) and k for k in result), "Invalid namespaced row key")
    return result


def indexed(rows):
    result = {}
    for row in rows:
        k = key(row)
        require(k not in result, "Duplicate row key")
        result[k] = row
    return result


def ordered(rows):
    keys = [key(row) for row in rows]
    require(keys == sorted(set(keys)), "Rows must be unique and in canonical key order")
    return keys


def close(actual, expected, path="metrics"):
    """Check shape and values; never use supplied floating values for decisions."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), "Missing/extra keys: " + path)
        for k, value in expected.items():
            close(actual[k], value, path + "." + k)
    elif type(expected) in (float, int):
        value = finite(actual, path)
        if type(expected) is int:
            require(type(actual) is int and actual == expected, "Integer differs: " + path)
        else:
            require(math.isclose(value, expected, abs_tol=ABS_TOL, rel_tol=REL_TOL), "Value differs: " + path)
    else:
        require(type(actual) is type(expected) and actual == expected, "Value differs: " + path)


def bindings(manifest, policy, root):
    require(manifest.get("policy_id") == policy["id"], "Manifest policy differs")
    common = manifest.get("common", {})
    require(set(common) == set(policy["common_artifact_roles"]), "Common artifact roles differ")
    for spec in common.values():
        artifact(spec, root)
    require(sha(artifact(common["scorer"], root)) == sha(Path(__file__)), "Scorer is not executed implementation")
    for name, spec in policy["base_manifest"].items():
        require(common.get(name) == spec, "Frozen base source differs: " + name)
    mb = manifest.get("metric_binding", {})
    require(set(mb) == {"schema", "temporal_rows", "cold_rows", "level_rows", "draw_plan"}
            and mb.get("schema") == SCHEMA, "Missing/invalid metric binding schema")
    for name in ["temporal_rows", "cold_rows", "level_rows", "draw_plan"]:
        artifact(mb[name], root)
    return common, mb


def verify_release_review(policy, root, selector_path):
    """Pre-opening evidence pinned by the adoption index, never by the batch.

    A mutable workspace operator can edit an index; this is version binding,
    not a cryptographic identity or a substitute for human review.
    """
    release = policy.get("_metric_binding_release")
    require(isinstance(release, dict) and set(release) == {"review", "bindings"},
            "Separate pre-opening review not adopted")
    expected = release["bindings"]
    require(isinstance(expected, dict) and set(expected) == {
        "selector", "metric_engine", "independent_checker", "test_suite", "policy"},
        "Incomplete pre-opening version bindings")
    for spec in expected.values():
        artifact(spec, root)
    require(sha(selector_path) == expected["selector"]["sha256"], "Reviewed selector version differs")
    require(sha(Path(__file__)) == expected["metric_engine"]["sha256"], "Reviewed metric engine differs")
    require(policy["_sha256"] == expected["policy"]["sha256"], "Reviewed policy version differs")
    actual_policy = read_json(artifact(expected["policy"], root))
    require(canonical_sha(actual_policy) == canonical_sha({k:v for k,v in policy.items() if not k.startswith("_")}),
            "Policy values differ from reviewed bytes")
    review = read_json(artifact(release["review"], root))
    require(review.get("schema") == "S2-METRIC-RELEASE-REVIEW-v1"
            and review.get("scope") == "synthetic_preopening_only"
            and review.get("result") == "pass" and review.get("confirmation_opened") is False,
            "Review is not a passing synthetic pre-opening review")
    require(review.get("bindings") == expected, "Review version bindings differ")
    coverage = review.get("coverage", {})
    for name in ["independent_oracle", "tampered_receipt_rejected",
                 "coordinated_values_recomputed", "preopening_fail_closed"]:
        require(coverage.get(name) is True, "Missing separate review coverage: " + name)
    return release["review"].copy()


def prepare(manifest, policy, root, a, b, _allow_self=False):
    common, mb = bindings(manifest, policy, root)
    models = manifest.get("models", [])
    ids = [m.get("id") for m in models]
    require(len(ids) == len(set(ids)) and a in ids and b in ids
            and (ids.index(a) > ids.index(b) or (_allow_self and a == b)), "Invalid/oriented pair")
    model_specs = {m["id"]: m.get("artifacts", {}) for m in models}
    for name in [a, b]:
        require(set(model_specs[name]) == set(policy["model_artifact_roles"]) | {"level_predictions"},
                "Model needs frozen level predictions and all registered roles")
        for spec in model_specs[name].values():
            artifact(spec, root)
    raw = indexed(table(common["target"], root))
    partitions = indexed(table(common["partitions"], root))
    expected = sorted(k for k, r in raw.items() if r.get("year") == 2024 and r.get("is_test") is False)
    test = sorted(k for k, r in raw.items() if r.get("year") == 2025 and r.get("is_test") is True)
    require(expected and test, "No complete temporal/test source keys")
    views = {}
    for name in ["temporal", "cold", "level"]:
        rows = table(mb[name + "_rows"], root)
        keys = ordered(rows)
        require(keys == (test if name == "level" else expected), "View omits/adds source rows: " + name)
        if name != "level":
            for r in rows:
                k = key(r); source = raw[k]; part = partitions.get(k, {})
                require(finite(r.get("target"), "target") == finite(source.get("T0"), "source.T0"), "Target differs from frozen T0")
                require(finite(r.get("weight"), "weight") == 1., "Primary policy is unweighted")
                require(isinstance(r.get("group_id"), str) and r["group_id"]
                        and r["group_id"] == part.get("group_id"), "Group differs from frozen partitions")
                seen = part.get("customer_seen_prior_year_same_line")
                require(type(seen) is bool, "Missing source customer status")
                require(r.get("customer_status") == ("renewal" if seen else "new_customer"), "Customer segment differs")
                if name == "temporal":
                    expected_y = {"reserve075": source.get("T1_reserve075"),
                                  "reserve125": source.get("T1_reserve125"),
                                  "late_cost05": source.get("T0"), "late_cost10": source.get("T0")}
                    require(set(r.get("scenario_targets", {})) == set(policy["safeguards"]["scenarios"]), "Scenario target keys differ")
                    for scenario, value in expected_y.items():
                        require(finite(r["scenario_targets"][scenario], scenario) == finite(value, "source." + scenario),
                                "Scenario target differs from frozen source")
        predictions = {}
        role = {"temporal": "temporal_predictions", "cold": "cold_start_predictions", "level": "level_predictions"}[name]
        for mid in [a, b]:
            pr = table(model_specs[mid][role], root)
            require(ordered(pr) == keys, "Prediction key/order mismatch")
            require(all(finite(r.get("prediction"), "prediction") > 0 for r in pr), "Nonpositive prediction")
            if name == "temporal":
                for r in pr:
                    require(set(r.get("scenario_predictions", {})) == set(policy["safeguards"]["scenarios"]), "Prediction scenarios differ")
                    require(all(finite(v, "scenario prediction") > 0 for v in r["scenario_predictions"].values()), "Invalid scenario prediction")
            predictions[mid] = pr
        views[name] = (rows, predictions)
    groups = sorted({r["group_id"] for r in views["temporal"][0]})
    require(len(groups) >= 2 and groups == sorted({r["group_id"] for r in views["cold"][0]}), "Bootstrap group universes differ")
    plan = read_json(artifact(mb["draw_plan"], root))
    conf = policy["confirmation"]
    require(set(plan) == {"schema", "algorithm", "seed", "replicates", "ordered_group_ids", "stream_sha256"}, "Draw plan keys differ")
    require(plan["schema"] == "S2-DRAW-PLAN-v1" and plan["algorithm"] == SCORER["rng"], "Unsupported draw algorithm")
    require(type(plan["seed"]) is int and plan["seed"] == conf["bootstrap_seed"], "Draw seed differs")
    require(type(plan["replicates"]) is int and plan["replicates"] == conf["bootstrap_replicates"], "Draw count differs")
    require(plan["ordered_group_ids"] == groups, "Draw group order differs")
    return views, groups, plan


def preflight(manifest, policy, root):
    """Validate source coverage, values, schemas and draws, without any score.

    Frozen prediction values are inspected for validity but no loss, interval,
    diagnostic or model selection statistic is computed by this function.
    """
    ids = [m["id"] for m in manifest["models"]]
    require(ids, "Empty roster")
    prepared = prepare(manifest, policy, root, ids[0], ids[0], _allow_self=True)
    for mid in ids[1:]:
        prepare(manifest, policy, root, mid, ids[0])
    _, groups, plan = prepared
    require(draw_digest(groups, plan["seed"], plan["replicates"]) == plan["stream_sha256"],
            "Preflight draw stream differs")
    return {"scope": "structure_and_draws_only_no_model_metrics", "models": ids}


def deviance(y, mu):
    # Algebraically identical to the expanded Tweedie1.5 expression, without
    # subtracting three near-equal terms when y ~= mu. Rationalizing the root
    # difference also avoids cancellation in sqrt(y)-sqrt(mu).
    difference = (y - mu) / (np.sqrt(y) + np.sqrt(mu))
    return 4. * difference * (difference / np.sqrt(mu))


def gain(y, pa, pb, w):
    y = np.asarray(y, dtype=float); pa = np.asarray(pa, dtype=float); pb = np.asarray(pb, dtype=float); w = np.asarray(w, dtype=float)
    require(np.isfinite(y).all() and (y >= 0).all() and np.isfinite(w).all() and (w > 0).all(), "Invalid target/weights")
    mean = float(np.dot(w, y) / w.sum())
    require(mean > 0, "Null mean is zero")
    denominator = float(np.dot(w, deviance(y, np.full(len(y), mean))))
    require(math.isfinite(denominator) and denominator > 0, "Null deviance degenerate")
    return float(np.dot(w, deviance(y, pb) - deviance(y, pa)) / denominator)


def arrays(view, a, b):
    rows, predictions = view
    return (np.array([r["target"] for r in rows], dtype=float),
            np.array([r["prediction"] for r in predictions[a]], dtype=float),
            np.array([r["prediction"] for r in predictions[b]], dtype=float),
            np.array([r["weight"] for r in rows], dtype=float))


def draw_digest(groups, seed, replicates):
    rng = np.random.Generator(np.random.PCG64(seed)); h = hashlib.sha256()
    for _ in range(replicates):
        sample = rng.integers(0, len(groups), size=len(groups), dtype=np.uint32)
        h.update(sample.astype("<u4", copy=False).tobytes())
    return h.hexdigest()


def bootstrap(views, groups, plan, a, b):
    group_map = {g: i for i, g in enumerate(groups)}
    aggregates = []
    for name in ["temporal", "cold"]:
        y, pa, pb, w = arrays(views[name], a, b)
        idx = np.array([group_map[r["group_id"]] for r in views[name][0]])
        agg = np.array([np.bincount(idx, weights=z, minlength=len(groups))
                        for z in [w, w*y, w*np.sqrt(y), w*(deviance(y, pb)-deviance(y, pa))]])
        aggregates.append(agg)
    rng = np.random.Generator(np.random.PCG64(plan["seed"])); h = hashlib.sha256()
    results = np.empty((2, plan["replicates"]))
    for i in range(plan["replicates"]):
        sample = rng.integers(0, len(groups), size=len(groups), dtype=np.uint32)
        h.update(sample.astype("<u4", copy=False).tobytes())
        counts = np.bincount(sample, minlength=len(groups))
        for v, agg in enumerate(aggregates):
            sw, sy, sr, difference = agg @ counts
            mean = sy / sw
            require(mean > 0, "Degenerate bootstrap target")
            first = sy / math.sqrt(mean)
            second = sw * math.sqrt(mean)
            denominator = 4. * (first + second - 2. * sr)
            scale = abs(first) + abs(second) + 2. * abs(sr)
            require(math.isfinite(denominator) and denominator > 0
                    and denominator > 64. * np.finfo(float).eps * scale,
                    "Degenerate or ill-conditioned bootstrap null; no metric issued")
            results[v, i] = difference / denominator
    digest = h.hexdigest()
    require(digest == plan["stream_sha256"], "Draw stream digest differs")
    require(np.isfinite(results).all(), "Nonfinite bootstrap result")
    return results, digest


def compute_metrics(a, b, manifest, policy, root):
    views, groups, plan = prepare(manifest, policy, root, a, b)
    rows, predictions = views["temporal"]
    y, pa, pb, w = arrays(views["temporal"], a, b)
    yc, pac, pbc, wc = arrays(views["cold"], a, b)
    samples, digest = bootstrap(views, groups, plan, a, b)
    conf = policy["confirmation"]; q = conf["bootstrap_lower_quantile"]
    metrics = {"primary": {"delta": gain(y, pa, pb, w),
                           "lower": float(np.quantile(samples[0], q, method="linear")),
                           "upper": float(np.quantile(samples[0], 1-q, method="linear")),
                           "bootstrap": {**{k: conf[k] for k in ["bootstrap_replicates", "bootstrap_seed", "bootstrap_method", "bonferroni_family_size_fixed"]},
                                         "lower_quantile": q}},
               "cold_start": {"delta": gain(yc, pac, pbc, wc), "lower95": float(np.quantile(samples[1], .025, method="linear"))},
               "scenarios": {}, "segments": {}, "influence": {}, "level_changes": {}}
    for scenario in policy["safeguards"]["scenarios"]:
        sy = [r["scenario_targets"][scenario] for r in rows]
        sa = [r["scenario_predictions"][scenario] for r in predictions[a]]
        sb = [r["scenario_predictions"][scenario] for r in predictions[b]]
        metrics["scenarios"][scenario] = gain(sy, sa, sb, w)
    for segment in policy["safeguards"]["segments"]:
        mask = np.array([r["line"] == segment or r["customer_status"] == segment for r in rows])
        require(mask.any(), "Empty required segment: " + segment)
        metrics["segments"][segment] = gain(y[mask], pa[mask], pb[mask], w[mask])
    difference = deviance(y, pb) - deviance(y, pa)
    group_map = {g:i for i,g in enumerate(groups)}
    group_index = np.array([group_map[r["group_id"]] for r in rows])
    group_sums = np.bincount(group_index, weights=difference, minlength=len(groups))
    contributions = dict(zip(groups, group_sums.tolist()))
    removed = min(len(groups)-1, max(5, math.ceil(.001*len(groups))))
    top = set(sorted(groups, key=lambda g: (-contributions[g], g))[:removed])
    mask = np.array([r["group_id"] not in top for r in rows])
    metrics["influence"] = {"n_groups": len(groups), "removed": removed,
                            "delta_without_top": gain(y[mask], pa[mask], pb[mask], w[mask])}
    level_rows, level_predictions = views["level"]
    for line in policy["safeguards"]["lines"]:
        ix = [i for i, r in enumerate(level_rows) if r["line"] == line]
        require(ix, "Empty level line")
        la = math.fsum(level_predictions[a][i]["prediction"] for i in ix)
        lb = math.fsum(level_predictions[b][i]["prediction"] for i in ix)
        metrics["level_changes"][line] = {"relative_change": la/lb-1.}
    return metrics, digest


def make_receipt(pair_ids, manifest, policy, root):
    a, b = pair_ids
    metrics, digest = compute_metrics(a, b, manifest, policy, root)
    models = {m["id"]: m["artifacts"] for m in manifest["models"]}
    return {"schema": RECEIPT, "policy_id": policy["id"], "policy_sha256": policy["_sha256"],
            "policy_semantic_sha256": canonical_sha({k: v for k, v in policy.items() if not k.startswith("_")}),
            "manifest_semantic_sha256": canonical_sha(manifest), "pair": {"a": a, "b": b},
            "bindings": {"common": copy.deepcopy(manifest["common"]),
                         "models": {a: copy.deepcopy(models[a]), b: copy.deepcopy(models[b])},
                         "metric_binding": copy.deepcopy(manifest["metric_binding"])},
            "scorer_contract": SCORER.copy(), "draws_stream_sha256": digest, "metrics": metrics}


def verify_receipt(pair, manifest, policy, root):
    """Return recomputed metrics, so tolerance never changes a gate boundary."""
    require(isinstance(manifest, dict), "Frozen manifest required")
    receipt = read_json(artifact(pair.get("metric_receipt"), root))
    expected = make_receipt((pair.get("a"), pair.get("b")), manifest, policy, root)
    close(receipt, expected, "receipt")
    supplied = {k: pair.get(k) for k in expected["metrics"]}
    # Explanations/evidence are separate policy controls, not metric results.
    supplied["level_changes"] = {line: {"relative_change": supplied["level_changes"].get(line, {}).get("relative_change")}
                                 for line in expected["metrics"]["level_changes"]} if isinstance(supplied["level_changes"], dict) else None
    close(supplied, expected["metrics"], "pair")
    return expected["metrics"]
