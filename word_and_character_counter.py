import json

# ===== CONFIG =====
JSON_FILE = "qfo_words_and_characthers_counter.json"
Q = 30  # number of characters to show for QFO's preview
# ==================

def count_words(text):
    return len(text.split())

def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    idx = 0  # global index across all prompts
    for prompt_source, sentences in data.items():
        for sentence in sentences:
            num_chars = len(sentence)
            num_words = count_words(sentence)
            preview = sentence[:Q]  # QFO's characters
            print(f"{idx}.")
            print(f"   Prompt Source: {prompt_source}")
            print(f"   Characters: {num_chars}")
            print(f"   Words: {num_words}")
            print(f"   Preview ({Q} chars): {preview}")
            print("-" * 50)
            idx += 1

if __name__ == "__main__":
    main()