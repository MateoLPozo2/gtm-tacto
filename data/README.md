# Data directory

Input files for the Tacto scripts. Paths in `config.json` are relative to this folder (via `data_dir`). All files listed here are **inputs**; script outputs are written to timestamped run directories under `output/`.

| File | Structure | Consumed by |
|------|-----------|-------------|
| **geo_prompt_answers.json** | Audit name → list of cited URLs | Brand crawler, domain matcher, website crawler analyzer, website crawler + keyword finder, quality content |
| **qfo_words_and_characthers_counter.json** | Prompt source → list of sentences | Word & character counter (QFO/query analyzer) |
| **keywords_tacto_from_hyperniche.json** | `keywords_clean`, `keywords_transliterated` (arrays of strings) | Website crawler + keyword finder |
| **target_domains.json** | List of domain strings (or dict of domain values) | Domain matcher |
| **brand_list.json** | Optional list of brand names | Brand crawler (optional; used to suggest a brand when running the brand matcher) |

See project root **SCOPE_AND_CAPABILITIES.md** for full script inputs, outputs, and scope.
