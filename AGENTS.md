# Writing project · v2.4.2

This repository provides shared author expression, WeChat article writing and novel writing. Codex owns execution and external MCP connections. Keep private works in the explicitly selected local workspace (recommended `~/.touge-writing/workspace`); public source is methods, templates, scripts and reviewed style abstractions.

The public capability project is `touge-writing`. A private `touge-writing-workspace` can contain multiple novels and WeChat articles in one catalog; do not treat its name as a single work identity. Select the work by stable project ID. Separate repositories when collaborators need different access scopes, since Git access exposes every committed work and its history.

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

Resolve the work's `rules_file` and optional `rules_manifest` for the target and task mode, then read the actual rule text and sources. Plans record inherited versions, concrete application and authorized exceptions. Reviews cover applicable rule IDs with artifact hashes, locations and reasons; a snapshot or valid coverage schema does not prove understanding. A review-only task can complete with manuscript `needs_revision`; saving a candidate does not certify quality or acceptance. Small edits may use lightweight checks without a run. See `docs/rules.md`; do not fabricate retrospective coverage for old versions.

## External tools
MCP connects external services; it is not the writing runtime. Use host tools only when the task requires them. Keep credentials in the host's approved credential mechanism, never in repository/workspace files or output. Maintain concrete remote IDs and receipts privately. Read remote state before updates and verify afterwards; an ambiguous request must be reconciled before retrying. A local final draft does not imply public publishing.

For v2.4, retain the explicit v2.0 scope: WeChat establishes capability and setup guidance only; account connection and live operations are excluded from acceptance by the user's explicit scope revision. Tencent Docs retains real read/write evidence. Revalidate existing receipts when the protocol is unchanged, and state that they are historical; changes to connection, target resolution, write or readback require affected live checks. Mark untested operations honestly.

## Validation
Run `python3 -m unittest discover -s tests -v`, `python3 scripts/preflight_check.py`, and `python3 scripts/acceptance.py --workspace "$HOME/.touge-writing/workspace"` (or the explicitly selected private path). Public installs use `acceptance.py --public-only`. v2.4 D01–D06 acceptance separates public behavior, private rule dependencies and historical protection, independent Skill behavior, and release/remote clone evidence; local unit tests alone cannot release the current v2.4 patch. Use the exact VERSION configuration and separate output directory; preserve v2.4.0 and earlier acceptance results and state which checks were newly executed versus historical integrity checks. Do not copy private fixtures into public tests. Product validation does not authorize manuscript edits. Keep existing auxiliary capabilities compatible.

## Collaboration and storage
The public capability repository and each private work/team workspace are independent Git roots. Share only the work and dependencies covered by its collaboration agreement; Git repository access exposes all committed files and history. One designated editor integrates and registers formal versions sequentially. Contributors write in separate local process copies from a known common commit, then submit selected candidate packages with git_collaboration.py; never merge or renumber personal run/lifecycle event chains into the formal chain. Verify the package and current base before integration. A Git commit, PR merge or cloud edit is not accepted content: reuse content registration and actual author decisions. Git/GitHub CLI suffices; Tencent Docs is optional import/export or historical reading, not a mandatory final store. No automatic manuscript merge or distributed lock is implemented. Private repository permissions do not provide author-key-only end-to-end encryption; protect local storage and backups separately. Do not claim encryption or real multi-account validation without evidence.

## Expansion, rhythm and milestones
Use the current versioned scene, reflection and editorial cards for new tasks; retained run pins keep their original cards. Expand from attributable material while preserving the authorized event chain. Paragraphs follow action, speaker and emotional turns, without universal length quotas. Work-specific requirements and authorized exceptions remain in the private work. A draft milestone confirmation binds the existing revision ID and content hash to the actual author decision, remains draft, and does not create duplicate prose registrations or rewrite historical reviews.
