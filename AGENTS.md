# Writing project

This repository provides shared author expression, WeChat article writing and novel writing. Codex owns execution and external MCP connections. Keep private works under `workspace/`; public source is methods, templates, scripts and reviewed style abstractions.

## Choose the task
- WeChat/public-account/single article: read `.agents/skills/touge-wechat-writing/SKILL.md`.
- Novel/book/serial/chapter: read `.agents/skills/touge-novel-writing/SKILL.md`, then resolve the work through `workspace/catalog.json`.
- Existing auxiliary requests (conversation, reboot, decks, product Q&A): use root `SKILL.md` routing.
- The author profile is `shared/author-expression/PROFILE.md`. A book's characters and facts never become global style rules.

## Preserve work
Use registered current versions and explicit author decisions, not the highest-looking filename, newest mtime, or conversation recollection. `archives/` is historical evidence, not current instructions. Source files, accepted texts and historical plans are immutable; create another version. Plan inheritance records are historical facts and do not silently follow the newest book plan.

Review authorization already given in the conversation remains valid. Do not ask again for the same action. For a requested continuation, follow that work's current review/draft stage; migration authorization does not mean permission to rewrite its chapters.

Product upgrades and releases validate capabilities and migration integrity, not a manuscript's content. Restoring a saved chapter-review stage verifies recovery only; it is not an instruction to perform that review. Use synthetic materials for new writing evaluations. Review or resolve a real work's facts, plot, prose or chapter plans only in a separate writing task after release. Earlier test observations are not release blockers or author-approved editorial decisions.

## External tools
MCP connects external services; it is not the writing runtime. Use host tools only when the task requires them. Keep credentials in the host's approved credential mechanism, never in repository/workspace files or output. Maintain concrete remote IDs and receipts privately. Read remote state before updates and verify afterwards; an ambiguous request must be reconciled before retrying. A local final draft does not imply public publishing.

For v2.0, WeChat establishes capability and setup guidance only; account connection and live operations are excluded from acceptance by the user's explicit scope revision. Tencent Docs retains real read/write acceptance. Mark untested operations honestly.

## Validation
Run `python3 -m unittest discover -s tests -v`, `python3 scripts/preflight_check.py`, and `python3 scripts/acceptance.py --workspace workspace`. Full acceptance includes external evidence; local unit tests alone cannot release v2.0.0. Do not copy private fixtures into public tests. Keep existing auxiliary capabilities compatible.
