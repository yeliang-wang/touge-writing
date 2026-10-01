# Writing project · v2.2

This repository provides shared author expression, WeChat article writing and novel writing. Codex owns execution and external MCP connections. Keep private works in the explicitly selected local workspace (recommended `~/.touge-writing/workspace`); public source is methods, templates, scripts and reviewed style abstractions.

## Choose the task
- WeChat/public-account/single article: read `.agents/skills/touge-wechat-writing/SKILL.md`.
- Novel/book/serial/chapter: read `.agents/skills/touge-novel-writing/SKILL.md`, then resolve the work through the selected workspace’s `catalog.json`. Always pass the same explicit `--workspace`; CLI omission retains the legacy cwd/workspace default. Check for existing legacy works before initializing an empty external location; honor an already confirmed destination without asking again.
- Existing auxiliary requests (conversation, reboot, decks, product Q&A): use root `SKILL.md` routing.
- The author profile is `shared/author-expression/PROFILE.md`. A book's characters and facts never become global style rules.

## Preserve work
Use registered current versions and explicit author decisions, not the highest-looking filename, newest mtime, or conversation recollection. `archives/` is historical evidence, not current instructions. Source files, accepted texts and historical plans are immutable; create another version. Plan inheritance records are historical facts and do not silently follow the newest book plan.

Review authorization already given in the conversation remains valid. Do not ask again for the same action. For a requested continuation, follow that work's current review/draft stage; migration authorization does not mean permission to rewrite its chapters.

Product upgrades and releases validate capabilities and migration integrity, not a manuscript's content. Restoring a saved chapter-review stage verifies recovery only; it is not an instruction to perform that review. Use synthetic materials for new writing evaluations. Review or resolve a real work's facts, plot, prose or chapter plans only in a separate writing task after release. Earlier test observations are not release blockers or author-approved editorial decisions.

## Methods and task records
Read only applicable versioned cards in `capabilities/registry.json`. An active run overrides legacy next-chapter advice; it snapshots task inputs, author expression, Skill, lifecycle and selected methods. Trial completion is not manuscript acceptance. `版本记录/revisions.json` alone owns content acceptance; lifecycle events own task execution; state files are derived.

Materials are explicitly scoped. Source identity, read coverage, factual confidence and fiction authorization are separate. A timeline display chapter number does not establish chapter identity. Resolve facts only within the authorized writing task; product upgrades preserve the work.

## External tools
MCP connects external services; it is not the writing runtime. Use host tools only when the task requires them. Keep credentials in the host's approved credential mechanism, never in repository/workspace files or output. Maintain concrete remote IDs and receipts privately. Read remote state before updates and verify afterwards; an ambiguous request must be reconciled before retrying. A local final draft does not imply public publishing.

For v2.2, retain the explicit v2.0 scope: WeChat establishes capability and setup guidance only; account connection and live operations are excluded from acceptance by the user's explicit scope revision. Tencent Docs retains real read/write evidence. Revalidate existing receipts when the protocol is unchanged, and state that they are historical; changes to connection, target resolution, write or readback require affected live checks. Mark untested operations honestly.

## Validation
Run `python3 -m unittest discover -s tests -v`, `python3 scripts/preflight_check.py`, and `python3 scripts/acceptance.py --workspace "$HOME/.touge-writing/workspace"` (or the explicitly selected private path). Full acceptance includes migration and historical external evidence; local unit tests alone cannot release v2.2.0. Public installs use `acceptance.py --public-only`; v2.2 results and legacy regression are separate, and historical v2.0/v2.1 evidence must not be overwritten. Do not copy private fixtures into public tests. Keep existing auxiliary capabilities compatible.

## Collaboration and storage
Each collaborator owns a private workspace. Use the work’s collaboration agreement for selected cloud documents, responsibility and confirmation authority. A cloud edit is not accepted content. Reuse content registration and actual decision records; no workspace synchronization or automatic merge. One designated editor integrates changes; pre-read, reconcile conflicts and verify writes. No application-level encryption is implemented: confidentiality requires suitable local storage and access control, including backups. Do not claim encryption or multi-account live validation without evidence.
