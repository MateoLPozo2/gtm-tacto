import json
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path


sentence_splitter = re.compile(r'(?<=[.!?])\s+')


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_sentences(text: str) -> list:
    return sentence_splitter.split(text)


def fetch_page(url: str, timeout: int = 15, user_agent: str = "Mozilla/5.0 (compatible; TextCrawler/1.0)") -> str | None:
    headers = {"User-Agent": user_agent}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return clean_text(text)


def analyze_text(text: str) -> dict:
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


def run(config: dict, output_dir: Path) -> None:
    """Run website crawler + analyzer: fetch URLs from config, analyze content, write JSON to output_dir."""
    paths = config.get("paths_resolved", {})
    urls_path = paths.get("urls_by_group", "geo_prompt_answers.json")
    opts = config.get("website_crawler_analyzer", {})
    timeout = opts.get("timeout", 15)
    user_agent = opts.get("user_agent", "Mozilla/5.0 (compatible; TextCrawler/1.0)")

    with open(urls_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    global_index = 0

    for prompt_source, urls in data.items():
        for url in urls:
            print(f"URL: {url}")
            html = fetch_page(url, timeout=timeout, user_agent=user_agent)
            if not html:
                print("   Failed to fetch page")
                continue
            text = extract_text_from_html(html)
            analysis = analyze_text(text)
            results.append({
                "url": url,
                "prompt_source": prompt_source,
                "total_characters": analysis["total_characters"],
                "total_words": analysis["total_words"],
                "sentence_count": analysis["sentence_count"],
                "avg_words_per_sentence": analysis["avg_words_per_sentence"],
                "avg_chars_per_sentence": analysis["avg_chars_per_sentence"],
                "sentences": analysis["sentences"],
            })
            global_index += len(analysis["sentences"])

    out_path = output_dir / "website_crawler_analyzer.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Output written to {out_path}")


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
