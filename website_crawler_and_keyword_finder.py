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


def check_keywords(text: str, keywords: list) -> list:
    found = []
    lower_text = text.lower()
    for kw in keywords:
        if kw.lower() in lower_text:
            found.append(kw)
    return found


def crawl_site(
    start_url: str,
    keywords: list,
    *,
    visited: set,
    max_pages: int = 5,
    timeout: int = 10,
) -> list:
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
            text = soup.get_text(" ", strip=True)
            found = check_keywords(text, keywords)
            if found:
                results.append({
                    "url": url,
                    "keywords_found": found
                })

            links = get_links(start_url, html)
            queue.extend(links)
            pages_checked += 1

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    return results


def run(config: dict, output_dir: Path) -> None:
    """Run website crawler + keyword finder: read URLs and keywords from config, write matches to output_dir."""
    paths = config.get("paths_resolved", {})
    keywords_path = paths.get("keywords", "keywords_tacto_from_hyperniche.json")
    urls_path = paths.get("urls_by_group", "geo_prompt_answers.json")
    opts = config.get("website_crawler_and_keyword_finder", {})
    max_pages = opts.get("max_pages_per_site", 5)
    timeout = opts.get("timeout", 10)

    keywords_data = load_json(keywords_path)
    websites_data = load_json(urls_path)
    keywords = list(set(
        keywords_data.get("keywords_clean", []) +
        keywords_data.get("keywords_transliterated", [])
    ))
    visited = set()
    all_results = {}

    for audit_name, urls in websites_data.items():
        print(f"\n=== Crawling audit: {audit_name} ===")
        audit_results = []
        for url in urls:
            print(f"Crawling {url}...")
            results = crawl_site(
                url,
                keywords,
                visited=visited,
                max_pages=max_pages,
                timeout=timeout,
            )
            audit_results.extend(results)
        all_results[audit_name] = audit_results

    out_path = output_dir / "website_crawler_keyword_finder.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nCrawling finished. Results saved to {out_path}")


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
