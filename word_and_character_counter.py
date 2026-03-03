import json
from pathlib import Path

# ===== CONFIG (defaults when run standalone) =====
JSON_FILE = "qfo_words_and_characthers_counter.json"
# ==================


def count_words(text: str) -> int:
    return len(text.split())


def run(config: dict, output_dir: Path) -> None:
    """Run QFO/query analyzer: read sentences from config path, write structured JSON to output_dir."""
    paths = config.get("paths_resolved", {})
    input_path = paths.get("qfo_sentences", JSON_FILE)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    index = 0
    for prompt_source, sentences in data.items():
        for sentence in sentences:
            num_chars = len(sentence)
            num_words = count_words(sentence)
            results.append({
                "index": index,
                "audit": prompt_source,
                "words": num_words,
                "character": num_chars,
            })
            index += 1

    out_path = output_dir / "word_and_character_counter.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


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
    print(f"Output written to {output_dir / 'word_and_character_counter.json'}")


if __name__ == "__main__":
    main()
