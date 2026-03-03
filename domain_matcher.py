import json
from pathlib import Path
from urllib.parse import urlparse

# ====== CONFIG (defaults when run standalone) ======
# ====================


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def run(config: dict, output_dir: Path) -> None:
    """Run domain matcher: read URLs and target domains from config, write matches to output_dir."""
    paths = config.get("paths_resolved", {})
    urls_path = paths.get("urls_by_group")
    if not urls_path:
        raise FileNotFoundError("config paths_resolved must contain urls_by_group")
    target_domains_path = paths.get("target_domains", "target_domains.json")

    with open(urls_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(target_domains_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        TARGET_DOMAINS = set(d.lower() for d in raw)
    else:
        TARGET_DOMAINS = set(str(v).lower() for v in raw.values()) if isinstance(raw, dict) else set(raw)

    matches = []
    for key, url_list in data.items():
        for index, url in enumerate(url_list):
            domain = extract_domain(url)
            for target in TARGET_DOMAINS:
                t = target[4:] if target.startswith("www.") else target
                if domain == target or domain == t or domain.endswith("." + t):
                    matches.append({
                        "index": index,
                        "audit": key,
                        "domain": domain,
                        "url": url,
                    })
                    break

    out_path = output_dir / "domain_matcher.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)

    print(f"Found {len(matches)} matches. Output: {out_path}")


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
