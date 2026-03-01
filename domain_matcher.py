import json
from urllib.parse import urlparse

# ====== CONFIG ======
JSON_FILE = "geo_prompt_answers.json"

# Domains you want to match
TARGET_DOMAINS = {
  "blog.pleo.io",
  "www.ifs.com",
  "www.gep.com",
  "precoro.com",
  "www.yeeflow.com",
  "www.weproc.com",
  "onfinity.io",
  "en.wikipedia.org",
  "www.prodot.de",
  "www.reddit.com",
  "www.cflowapps.com",
  "www.ispnext.com",
  "www.wirtschaftsforum.de",
  "www.business-on.de",
  "www.sap.com",
  "www.onventis.de",
  "omr.com",
  "www.tacto.ai",
  "agicap.com",
  "mind-logistik.de",
  "de.ivalua.com",
  "www.g2.com",
  "spendmatters.com",
  "learning.sap.com",
  "www.valantic.com",
  "www.jaggaer.com",
  "www.mittelstand-heute.com"
}
# ====================

def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = []

    for key, url_list in data.items():
        for i, url in enumerate(url_list):
            domain = extract_domain(url)

            for target in TARGET_DOMAINS:
                if domain == target or domain.endswith("." + target):
                    matches.append({
                        "group": key,
                        "index": i,
                        "url": url,
                        "domain": domain,
                    })

    print(f"\nFound {len(matches)} matches:\n")

    for m in matches:
        print(f"Group: {m['group']}")
        print(f"Index: {m['index']}")
        print(f"Domain: {m['domain']}")
        print(f"Source: {m['url']}")
        print("-" * 60)

if __name__ == "__main__":
    main()