"""
Tacto modular controller: single entrypoint that loads config,
creates versioned output dirs, and runs the five modules via a menu.
"""
import json
import sys
from pathlib import Path

# Project root (directory containing main.py and config.json)
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
OUTPUT_ROOT = PROJECT_ROOT / "output"


def load_config() -> dict:
    """Load config.json and resolve paths relative to data_dir."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    data_dir = config.get("data_dir", ".")
    base = PROJECT_ROOT / data_dir
    paths = config.get("paths", {})
    resolved = {}
    for key, value in paths.items():
        if value:
            resolved[key] = str((base / value).resolve())
    config["paths_resolved"] = resolved
    return config


def ensure_output_root() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def create_run_dir() -> Path:
    """Create output/run_YYYYMMDD_HHMMSS/ and return its Path."""
    from datetime import datetime
    ensure_output_root()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_ROOT / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def update_latest(run_dir: Path) -> None:
    """Point output/latest to the given run directory."""
    latest = OUTPUT_ROOT / "latest"
    try:
        if latest.exists():
            latest.unlink()
        latest.symlink_to(run_dir.name)
    except OSError:
        pass


def run_word_and_character_counter(config: dict, output_dir: Path) -> None:
    import word_and_character_counter as m
    m.run(config, output_dir)


def run_brand_crawler(config: dict, output_dir: Path, brand_name: str | None = None) -> None:
    import brand_crawler as m
    m.run(config, output_dir, brand_name=brand_name)


def run_domain_matcher(config: dict, output_dir: Path) -> None:
    import domain_matcher as m
    m.run(config, output_dir)


def run_website_crawler_analyzer(config: dict, output_dir: Path) -> None:
    import website_crawler_analyzer as m
    m.run(config, output_dir)


def run_website_crawler_keyword_finder(config: dict, output_dir: Path) -> None:
    import website_crawler_and_keyword_finder as m
    m.run(config, output_dir)


def menu_loop(config: dict) -> None:
    while True:
        print("\n" + "=" * 50)
        print("Tacto Modular Controller")
        print("=" * 50)
        print("  1) QFO / query analyzer (word & character counter)")
        print("  2) Brand matcher (crawl & check content vs brand list)")
        print("  3) Domain matcher (scan URLs vs target domains)")
        print("  4) Website crawler + content analyzer")
        print("  5) Website crawler + keyword finder")
        print("  6) Run all")
        print("  0) Exit")
        print("=" * 50)
        choice = input("Choice: ").strip()
        if choice == "0":
            print("Bye.")
            return
        if choice not in ("1", "2", "3", "4", "5", "6"):
            print("Invalid option. Enter 0–6.")
            continue

        run_dir = create_run_dir()
        update_latest(run_dir)
        brand_name = None
        if choice == "2":
            paths = config.get("paths_resolved", {})
            brand_list_path = paths.get("brand_list")
            if brand_list_path and Path(brand_list_path).exists():
                try:
                    with open(brand_list_path, "r", encoding="utf-8") as f:
                        brands = json.load(f)
                except (json.JSONDecodeError, OSError):
                    brands = []
                if brands:
                    print("Brands from config:", ", ".join(brands))
                    bn = input("Enter brand name (or one from list): ").strip()
                    brand_name = bn or None
                else:
                    brand_name = input("Enter brand name to search for: ").strip() or None
            else:
                brand_name = input("Enter brand name to search for: ").strip() or None
            if not brand_name:
                print("Brand name required. Skipping.")
                continue

        try:
            if choice == "1":
                run_word_and_character_counter(config, run_dir)
            elif choice == "2":
                run_brand_crawler(config, run_dir, brand_name=brand_name)
            elif choice == "3":
                run_domain_matcher(config, run_dir)
            elif choice == "4":
                run_website_crawler_analyzer(config, run_dir)
            elif choice == "5":
                run_website_crawler_keyword_finder(config, run_dir)
            elif choice == "6":
                run_word_and_character_counter(config, run_dir)
                run_domain_matcher(config, run_dir)
                run_website_crawler_analyzer(config, run_dir)
                run_website_crawler_keyword_finder(config, run_dir)
                bn = input("Run brand matcher? Enter brand name (or leave empty to skip): ").strip()
                if bn:
                    run_brand_crawler(config, run_dir, brand_name=bn)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            raise
        print(f"\nOutput written to: {run_dir}")


def main() -> None:
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    config = load_config()
    ensure_output_root()
    menu_loop(config)


if __name__ == "__main__":
    main()
