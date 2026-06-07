# Evaluation Report

## Scope

This report evaluates five core product scenarios from `evals/tasks.jsonl`:

- long-form writing
- career conversation
- rewrite / de-AI
- reboot reflection
- title generation

The outputs are stored under `evals/outputs/`.

## Automated Style Gate

All five outputs passed `scripts/style_eval.py`.

| Task | Output | Score | Verdict | Pass |
|---|---|---:|---|---|
| write_technical_hype | `write_technical_hype.md` | 13 | close | yes |
| career_reply_age | `career_reply_age.md` | 12 | close | yes |
| rewrite_ai_smell | `rewrite_ai_smell.md` | 11 | close | yes |
| reboot_low_point | `reboot_low_point.md` | 12 | close | yes |
| title_set | `title_set.md` | 14 | strong_match | yes |

## Reviewer Notes

### Strengths

- The system reliably avoids generic AI openings.
- The outputs preserve a direct stance and practical tradeoff framing.
- Career and technical topics sound closest to the corpus.
- The title generator captures question, rebuttal, and responsibility patterns.
- The reboot output is sober and practical instead of motivational.

### Weak Spots

- The deterministic style scorer is still a smoke test, not a true preference model.
- Reboot output needs owner review because personal low-point tone is hard to judge automatically.
- Some sharpness can drift toward formula if every output starts with `别扯了`; future feedback should diversify openings.
- The private retriever helps grounding but does not yet use embeddings, so semantic recall is acceptable but not ideal.

## Current Product Judgment

The package is ready as a public `1.0-rc` repository and local Codex skill.

It should be called `1.0` only after the owner reviews at least 10 real outputs and accepts 8 or more.
