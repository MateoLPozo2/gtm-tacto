"""
Content briefing generator: reads quality_content.json and produces a structured
JSON briefing that answers:
  - Which domains appear most frequently? (from across_audits.per_domain_summary)
  - What actionable implications for brand content strategy? (narrative section)

Uses only existing fields from quality_content.json; does not create calculated
values or modify naming of objects.
"""
import json
from pathlib import Path


def run(config: dict, output_dir: Path) -> None:
    """Read quality_content.json from output_dir and write content_briefing.json."""
    qc_path = output_dir / "quality_content.json"
    if not qc_path.exists():
        raise FileNotFoundError(
            f"quality_content.json not found in {output_dir}. "
            "Run option 6 (Quality Content) first."
        )

    with open(qc_path, "r", encoding="utf-8") as f:
        qc = json.load(f)

    across = qc.get("across_audits", {})
    per_domain_summary = across.get("per_domain_summary", [])
    meta = qc.get("meta", {})

    # Use only existing fields; no new calculated values
    # Domains by frequency: same objects (excluding mean_qc_score), sorted by total_url_count or total_visibility (desc)
    def _url_count(d: dict) -> int:
        return d.get("total_url_count") or d.get("total_visibility") or 0

    def _domain_obj_without_qc(d: dict) -> dict:
        out = {k: v for k, v in d.items() if k != "mean_qc_score"}
        return out

    domains_by_frequency = [
        _domain_obj_without_qc(d)
        for d in sorted(per_domain_summary, key=_url_count, reverse=True)
    ]

    # Implications: narrative bullets referencing top domains (no new numeric fields)
    top_by_frequency = domains_by_frequency[:5]
    implications = [
        "Review and analyze content from the domains that appear most frequently across audits to identify structural or stylistic patterns.",
        "Compare mean_content_complexity (avg words per sentence) across domains to prioritize which content to emulate.",
    ]
    if top_by_frequency:
        domain_list = ", ".join(d.get("domain", "") for d in top_by_frequency)
        implications.append(
            f"High-frequency domains in this run: {domain_list}. Consider reviewing their content structure."
        )

    briefing = {
        "domains_by_frequency": domains_by_frequency,
        "implications_for_brand_content_strategy": implications,
        "meta": {
            "source": "quality_content.json",
            "qc_meta": meta,
        },
    }

    out_path = output_dir / "content_briefing.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(briefing, f, indent=2, ensure_ascii=False)

    print(f"Content briefing written to {out_path}")


def main() -> None:
    from pathlib import Path

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    data_dir = config.get("data_dir", ".")
    base = Path(__file__).resolve().parent / data_dir
    config["paths_resolved"] = {
        k: str((base / v).resolve())
        for k, v in config.get("paths", {}).items()
        if v
    }
    output_dir = Path("output") / "run_standalone"
    output_dir.mkdir(parents=True, exist_ok=True)
    run(config, output_dir)


if __name__ == "__main__":
    main()
