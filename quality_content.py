"""
Quality Content (QC) module: computes visibility (geo appearance count per domain/audit),
content complexity (avg words per sentence from crawler analyzer), and a correlation-based
QC score per domain, per audit, and across audits. Uses minimum data thresholds and
smoothed normalization to avoid meaningless values on small datasets.
"""
import json
import math
from pathlib import Path
from collections import defaultdict

from domain_matcher import extract_domain

# Defaults: only compute correlation/normalized QC when enough data points
MIN_POINTS_FOR_CORRELATION = 3
MIN_POINTS_FOR_NORMALIZATION = 2
EPSILON = 0.01


def _pearson(x: list[float], y: list[float], min_points: int = 2) -> float | None:
    """Pearson correlation between x and y. Returns None if n < min_points or zero variance."""
    n = len(x)
    if n != len(y) or n < min_points:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    sx = sum((xi - mx) ** 2 for xi in x)
    sy = sum((yi - my) ** 2 for yi in y)
    if sx == 0 or sy == 0:
        return None
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    r = cov / math.sqrt(sx * sy)
    return round(r, 4)


def _minmax_normalize(values: list[float], epsilon: float = 0.0) -> list[float]:
    """Min-max normalize to [0, 1]. With epsilon > 0, use smoothed normalization."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    if epsilon > 0:
        return [round((v - lo + epsilon) / (hi - lo + 2 * epsilon), 4) for v in values]
    return [(v - lo) / (hi - lo) for v in values]


def _smoothed_qc_score(norm_vis: float, norm_comp: float, epsilon: float) -> float:
    """QC = ((norm_vis + ε) * (norm_comp + ε)) / (1 + ε). Keeps score in (0, 1] range."""
    return round(((norm_vis + epsilon) * (norm_comp + epsilon)) / (1 + epsilon), 4)


def _pearson_to_pct(r: float) -> float:
    """Map Pearson correlation r in [-1, 1] to percentage 0-100: (r + 1) / 2 * 100."""
    return round((r + 1) / 2 * 100, 2)


def run(config: dict, output_dir: Path) -> None:
    """Compute QC scores from urls_by_group (visibility) and website_crawler_analyzer.json (content complexity)."""
    paths = config.get("paths_resolved", {})
    urls_path = paths.get("urls_by_group")
    if not urls_path:
        raise FileNotFoundError("config paths_resolved must contain urls_by_group")
    analyzer_path = output_dir / "website_crawler_analyzer.json"
    if not analyzer_path.exists():
        raise FileNotFoundError(
            f"website_crawler_analyzer.json not found in {output_dir}. "
            "Run option 4 (Website crawler + content analyzer) first."
        )

    opts = config.get("quality_content", {})
    min_corr = opts.get("min_points_correlation", MIN_POINTS_FOR_CORRELATION)
    min_norm = opts.get("min_points_normalization", MIN_POINTS_FOR_NORMALIZATION)
    epsilon = opts.get("epsilon", EPSILON)

    with open(urls_path, "r", encoding="utf-8") as f:
        geo_data = json.load(f)

    # 1. Visibility per (audit, domain): count of URLs
    visibility: dict[tuple[str, str], int] = defaultdict(int)
    for audit, url_list in geo_data.items():
        for url in url_list:
            domain = extract_domain(url)
            visibility[(audit, domain)] += 1

    # 2. Content complexity from analyzer: group by (audit, domain), mean avg_words_per_sentence
    with open(analyzer_path, "r", encoding="utf-8") as f:
        analyzer_data = json.load(f)

    complexity_by_key: dict[tuple[str, str], tuple[float, int]] = {}
    for item in analyzer_data:
        audit = item.get("prompt_source", "")
        url = item.get("url", "")
        domain = extract_domain(url)
        avg = item.get("avg_words_per_sentence")
        if avg is None:
            continue
        key = (audit, domain)
        if key not in complexity_by_key:
            complexity_by_key[key] = (0.0, 0)
        total, count = complexity_by_key[key]
        complexity_by_key[key] = (total + avg, count + 1)
    for key in complexity_by_key:
        total, count = complexity_by_key[key]
        complexity_by_key[key] = (round(total / count, 2), count)

    # 3. Join: all (audit, domain) from visibility; add content_complexity and url_count
    rows: list[dict] = []
    all_vis: list[int] = []
    all_comp: list[float] = []
    for (audit, domain), vis in visibility.items():
        comp_val, url_count = complexity_by_key.get((audit, domain), (None, 0))
        row = {
            "audit": audit,
            "domain": domain,
            "content_complexity": comp_val,
            "url_count": url_count,
        }
        rows.append(row)
        if comp_val is not None:
            all_vis.append(url_count)
            all_comp.append(comp_val)

    # 4. Smoothed min-max normalize and QC score only when enough data points
    if len(all_vis) >= min_norm and len(all_comp) >= min_norm:
        norm_vis_list = _minmax_normalize(all_vis, epsilon=epsilon)
        norm_comp_list = _minmax_normalize(all_comp, epsilon=epsilon)
        idx = 0
        for row in rows:
            if row["content_complexity"] is not None:
                nv = norm_vis_list[idx]
                nc = norm_comp_list[idx]
                raw_qc = _smoothed_qc_score(nv, nc, epsilon)
                row["qc_score"] = round(raw_qc * 100, 2)
                idx += 1
            else:
                row["qc_score"] = None
    else:
        for row in rows:
            row["qc_score"] = None

    # 5. Per-audit: quality_content_score (correlation when >= min_corr) + domains as object
    per_audit: dict = {}
    for audit in geo_data:
        audit_rows = [r for r in rows if r["audit"] == audit]
        vis_for_r = [r["url_count"] for r in audit_rows if r["content_complexity"] is not None]
        comp_for_r = [r["content_complexity"] for r in audit_rows if r["content_complexity"] is not None]
        pearson_r = _pearson(vis_for_r, comp_for_r, min_points=min_corr) if len(vis_for_r) >= min_corr else None
        quality_content_score = _pearson_to_pct(pearson_r) if pearson_r is not None else None
        domains_obj: dict = {}
        for r in audit_rows:
            domains_obj[r["domain"]] = {
                "url_count": r["url_count"],
                "avg_sentence_length": round(r["content_complexity"], 2) if r["content_complexity"] is not None else None,
            }
        per_audit[audit] = {
            "quality_content_score": quality_content_score,
            "domains": domains_obj,
        }

    # 6. Across audits: global correlation only when threshold met + per-domain summary
    global_pearson = _pearson(all_vis, all_comp, min_points=min_corr) if len(all_vis) >= min_corr else None
    global_corr = _pearson_to_pct(global_pearson) if global_pearson is not None else None
    domain_agg: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        domain_agg[r["domain"]].append(r)
    per_domain_summary = []
    for domain, domain_rows in sorted(domain_agg.items()):
        total_url_count = sum(r["url_count"] for r in domain_rows)
        comps = [r["content_complexity"] for r in domain_rows if r["content_complexity"] is not None]
        mean_comp = round(sum(comps) / len(comps), 2) if comps else None
        qc_scores = [r["qc_score"] for r in domain_rows if r["qc_score"] is not None]
        mean_qc = round(sum(qc_scores) / len(qc_scores), 2) if qc_scores else None
        per_domain_summary.append({
            "domain": domain,
            "total_url_count": total_url_count,
            "mean_content_complexity": mean_comp,
            "mean_qc_score": mean_qc,
        })

    out = {
        "per_domain_audit": rows,
        "per_audit": per_audit,
        "across_audits": {
            "global_correlation_visibility_complexity": global_corr,
            "per_domain_summary": per_domain_summary,
        },
        "meta": {
            "normalization": "minmax_smoothed",
            "qc_formula": "((normalized_visibility + epsilon) * (normalized_complexity + epsilon)) / (1 + epsilon)",
            "scores_as_percentage": "All QC scores (qc_score, mean_qc_score, quality_content_score, global_correlation) are in 0-100%.",
            "quality_content_score_formula": "(Pearson_r + 1) / 2 * 100",
            "epsilon": epsilon,
            "min_points_correlation": min_corr,
            "min_points_normalization": min_norm,
        },
    }

    out_path = output_dir / "quality_content.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"QC score written to {out_path} (global correlation: {global_corr})")


def main():
    from pathlib import Path
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    data_dir = config.get("data_dir", ".")
    base = Path(__file__).resolve().parent / data_dir
    config["paths_resolved"] = {k: str((base / v).resolve()) for k, v in config.get("paths", {}).items() if v}
    output_dir = Path("output") / "run_standalone"
    output_dir.mkdir(parents=True, exist_ok=True)
    run(config, output_dir)


if __name__ == "__main__":
    main()
