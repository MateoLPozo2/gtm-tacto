import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

MAX_PAGES_PER_SITE = 5
TIMEOUT = 10
EXCLUDE_BRAND = ["tacto", "TACTO", "https://tacto.ai"]  # all variants will be lowercased

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

def crawl_site(start_url, brand_name):
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
            text = soup.get_text(" ", strip=True).lower()

            # check if brand is present, but exclude tacto
            if brand_name.lower() in text and not any(excl in text for excl in EXCLUDE_BRAND):
                results.append(url)

            links = get_links(start_url, html)
            queue.extend(links)
            pages_checked += 1

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    return results

def main():
    websites_data = load_json("geo_prompt_answers.json")
    brand_name = input("Enter the brand name to search for (excluding Tacto): ").strip()
    
    if not brand_name:
        print("You must enter a brand name!")
        return

    all_results = {}

    for audit_name, urls in websites_data.items():
        print(f"\n=== Crawling audit: {audit_name} ===")
        audit_results = []
        for url in urls:
            print(f"Crawling {url}...")
            found_urls = crawl_site(url, brand_name)
            audit_results.extend(found_urls)
        all_results[audit_name] = audit_results

    # save output
    output_file = f"brand_results_{brand_name.replace(' ', '_')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nSearch finished. Results saved to {output_file}")

if __name__ == "__main__":
    main()