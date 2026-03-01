import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# -------- CONFIG --------
MAX_PAGES_PER_SITE = 5
TIMEOUT = 10
# ------------------------

visited = set()

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"])
        if urlparse(url).netloc == urlparse(base_url).netloc:
            links.append(url)
    return links

def check_keywords(text, keywords):
    found = []
    lower_text = text.lower()
    for kw in keywords:
        if kw.lower() in lower_text:
            found.append(kw)
    return found

def crawl_site(start_url, keywords):
    queue = [start_url]
    pages_checked = 0
    results = []

    while queue and pages_checked < MAX_PAGES_PER_SITE:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            r = requests.get(url, timeout=TIMEOUT)
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

def main():
    keywords_data = load_json("keywords_tacto_from_hyperniche.json")
    websites_data = load_json("geo_prompt_answers.json")

    # combine clean + transliterated keywords
    keywords = list(set(keywords_data.get("keywords_clean", []) +
                        keywords_data.get("keywords_transliterated", [])))

    all_results = {}

    for audit_name, urls in websites_data.items():
        print(f"\n=== Crawling audit: {audit_name} ===")
        audit_results = []
        for url in urls:
            print(f"Crawling {url}...")
            results = crawl_site(url, keywords)
            audit_results.extend(results)
        all_results[audit_name] = audit_results

    # save output
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("\nCrawling finished. Results saved to results.json")

if __name__ == "__main__":
    main()