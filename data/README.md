# Data directory

JSON input files for the Tacto scripts. Paths in `config.json` are relative to this folder (via `data_dir`).

- **qfo_words_and_characthers_counter.json** — Prompt source → list of sentences (QFO/query analyzer).
- **geo_prompt_answers.json** — Group/audit name → list of URLs (brand crawler, domain matcher, crawler analyzer, keyword finder).
- **keywords_tacto_from_hyperniche.json** — `keywords_clean` and `keywords_transliterated` (keyword finder).
- **target_domains.json** — List of domain strings (domain matcher).
- **brand_list.json** — Optional list of brand names (brand matcher).
