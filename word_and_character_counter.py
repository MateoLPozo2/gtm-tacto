import json
from pathlib import Path

# ===== CONFIG (defaults when run standalone) =====
JSON_FILE = "qfo_words_and_characthers_counter.json"
Q = 30  # number of characters to show for QFO's preview
# ==================


def count_words(text: str) -> int:
    return len(text.split())


def run(config: dict, output_dir: Path) -> None:
    """Run QFO/query analyzer: read sentences from config path, write structured JSON to output_dir."""
    paths = config.get("paths_resolved", {})
    input_path = paths.get("qfo_sentences", JSON_FILE)
    opts = config.get("word_and_character_counter", {})
    preview_chars = opts.get("preview_chars", Q)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    idx = 0
    for prompt_source, sentences in data.items():
        for sentence in sentences:
            num_chars = len(sentence)
            num_words = count_words(sentence)
            preview = sentence[:preview_chars]
            results.append({
                "index": idx,
                "prompt_source": prompt_source,
                "characters": num_chars,
                "words": num_words,
                "preview": preview,
            })
            idx += 1

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
