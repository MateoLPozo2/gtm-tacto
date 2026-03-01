import json
import requests
from bs4 import BeautifulSoup
import re

# ===== CONFIG =====
JSON_FILE = "geo_prompt_answers.json"
TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (compatible; TextCrawler/1.0)"
# ==================

HEADERS = {
    "User-Agent": USER_AGENT
}

sentence_splitter = re.compile(r'(?<=[.!?])\s+')

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_sentences(text: str):
    return sentence_splitter.split(text)

def fetch_page(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None

def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # remove non-content tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return clean_text(text)

def analyze_text(text: str):
    sentences = split_sentences(text)

    sentence_data = []
    total_words = 0
    total_chars = len(text)

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        words = len(s.split())
        chars = len(s)

        if words > 0:
            sentence_data.append({
                "sentence": s,
                "words": words,
                "characters": chars
            })
            total_words += words

    sentence_count = len(sentence_data)

    avg_words = total_words / sentence_count if sentence_count > 0 else 0
    avg_chars = sum(s["characters"] for s in sentence_data) / sentence_count if sentence_count > 0 else 0

    return {
        "total_characters": total_chars,
        "total_words": total_words,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": round(avg_words, 2),
        "avg_chars_per_sentence": round(avg_chars, 2),
        "sentences": sentence_data
    }

def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    global_index = 0

    for prompt_source, urls in data.items():
        print(f"\n==============================")
        print(f"PROMPT SOURCE: {prompt_source}")
        print(f"==============================\n")

        for url in urls:
            print(f"URL: {url}")

            html = fetch_page(url)
            if not html:
                print("   ❌ Failed to fetch page\n")
                continue

            text = extract_text_from_html(html)
            analysis = analyze_text(text)

            print(f"   Total Characters (page): {analysis['total_characters']}")
            print(f"   Total Words (page): {analysis['total_words']}")
            print(f"   Sentence Count: {analysis['sentence_count']}")
            print(f"   Avg Words / Sentence: {analysis['avg_words_per_sentence']}")
            print(f"   Avg Chars / Sentence: {analysis['avg_chars_per_sentence']}")
            print("   --- Sentence Analysis ---")

            for s in analysis["sentences"]:
                print(f"   {global_index}.")
                print(f"      Words: {s['words']}")
                print(f"      Characters: {s['characters']}")
                print(f"      Sentence: {s['sentence'][:120]}{'...' if len(s['sentence']) > 120 else ''}")
                global_index += 1

            print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    main()