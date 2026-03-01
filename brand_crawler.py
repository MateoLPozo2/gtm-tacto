import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path


def load_json(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_links(base_url: str, html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"])
        if urlparse(url).netloc == urlparse(base_url).netloc:
            links.append(url)
    return links


def crawl_site(
    start_url: str,
    brand_name: str,
    *,
    visited: set,
    max_pages: int = 5,
    timeout: int = 10,
    exclude_brand: list | None = None,
) -> list:
    exclude_brand = exclude_brand or []
    queue = [start_url]
    pages_checked = 0
    results = []

    while queue and pages_checked < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            r = requests.get(url, timeout=timeout)
            if "text/html" not in r.headers.get("Content-Type", ""):
                continue

            html = r.text
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True).lower()

            if brand_name.lower() in text and not any(excl.lower() in text for excl in exclude_brand):
                results.append(url)

            links = get_links(start_url, html)
            queue.extend(links)
            pages_checked += 1

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    return results


def run(
    config: dict,
    output_dir: Path,
    brand_name: str | None = None,
) -> None:
    """Run brand crawler: crawl URLs from config, check for brand (exclude list from config), write to output_dir."""
    if not brand_name:
        brand_name = input("Enter the brand name to search for (excluding Tacto): ").strip()
    if not brand_name:
        raise ValueError("Brand name is required")

    paths = config.get("paths_resolved", {})
    urls_path = paths.get("urls_by_group", "geo_prompt_answers.json")
    opts = config.get("brand_crawler", {})
    max_pages = opts.get("max_pages_per_site", 5)
    timeout = opts.get("timeout", 10)
    exclude_brand = opts.get("exclude_brand", ["tacto", "TACTO", "https://tacto.ai"])

    websites_data = load_json(urls_path)
    visited = set()
    all_results = {}

    for audit_name, urls in websites_data.items():
        print(f"\n=== Crawling audit: {audit_name} ===")
        audit_results = []
        for url in urls:
            print(f"Crawling {url}...")
            found_urls = crawl_site(
                url,
                brand_name,
                visited=visited,
                max_pages=max_pages,
                timeout=timeout,
                exclude_brand=exclude_brand,
            )
            audit_results.extend(found_urls)
        all_results[audit_name] = audit_results

    brand_slug = brand_name.replace(" ", "_")
    output_file = output_dir / f"brand_crawler_{brand_slug}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nSearch finished. Results saved to {output_file}")


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
