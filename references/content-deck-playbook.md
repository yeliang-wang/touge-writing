# Content Deck Playbook

Use this reference when the task asks for PPT, courseware, public talk material, a Markdown speaker script, or a full content package.

## Content Positioning

A content deck is not a slide version of generic advice. It is the author's judgment system rendered into a talkable structure.

Default outputs:

- optional long-form article Markdown
- `slide-plan.json`
- WPS-compatible `.pptx`
- per-slide Markdown speaker guide
- contact-sheet preview PNG
- `build-manifest.json`

## Input Triage

Identify:

- Topic: what claim or problem is being explained.
- Audience: programmers, managers, founders, product people, students, or mixed public readers.
- Scene: public talk, internal sharing, courseware, product explainer, or article-to-deck conversion.
- Output depth: short outline, full deck files, article + deck, or speaker script only.
- Evidence boundary: what facts are provided and what must not be invented.

If the user provides a repo or product path, inspect real files before making factual claims. If the user only gives a topic, write from argument and experience-level reasoning, not fake project facts.

## Argument First

Before building slides, define the argument spine:

1. What popular slogan or comfortable misunderstanding is being challenged?
2. What is the real cost, responsibility, or operating constraint behind it?
3. What concrete scene makes the issue visible?
4. What decision rule should the audience take away?
5. What should they do next Monday?

Use this spine to create the article and the deck. Slides should compress the argument, not replace it with empty bullet lists.

## Deck Shapes

### Opinion Talk

Use for technical-career essays, industry commentary, AI hype judgment, and public sharing.

Suggested structure:

1. Cover: one sharp claim.
2. Scene: the real workplace moment behind the topic.
3. Misunderstanding: the fashionable version people repeat.
4. Cost: what the slogan hides.
5. Boundary: what is actually hard.
6. Decision rule: how to judge whether to do it.
7. Action: what to try, stop, or verify.
8. Summary: one sentence the audience can repeat.

### Product Or Project Explainer

Use when the content explains a product, repo, platform, or technical system.

Suggested structure:

1. Cover: what this thing is.
2. Why it exists.
3. Who pays the cost if it is missing.
4. Static boundaries: user, agent, service, runtime, storage, evidence.
5. Dynamic flow: one real request or lifecycle.
6. Tradeoffs: what the design refuses to do.
7. Operating proof: logs, tests, metrics, screenshots, or artifacts.
8. What the audience can reuse.

### Article To Deck

Use when the user provides an existing draft.

Suggested structure:

1. Extract the thesis.
2. Split paragraphs into claims, scenes, costs, counterarguments, and actions.
3. Keep one primary claim per slide.
4. Turn dense paragraphs into oral `talk`, not tiny slide text.
5. Preserve the original stance unless the user asks for rewriting.

## Slide Plan Contract

Create a JSON file with this shape before running `scripts/build_content_deck.py`:

```json
{
  "title": "Deck title",
  "audience": "who this is for",
  "scenario": "public talk | internal sharing | courseware | product explainer",
  "style": "touge",
  "article_markdown": "optional long-form article",
  "slides": [
    {
      "title": "Slide title",
      "subtitle": "Short visible claim",
      "kind": "cover | claim | contrast | bullets | quote | architecture | sequence | lifecycle | summary",
      "points": ["short visible point"],
      "quote": "optional short sentence",
      "nodes": [{"id": "User", "label": "User", "note": "optional"}],
      "edges": [{"from": "User", "to": "Agent", "label": "optional"}],
      "steps": [{"from": "User", "to": "Agent", "label": "optional"}],
      "talk": "One oral paragraph. It should sound like the author explaining the slide to real people."
    }
  ],
  "takeaways": ["what the audience should remember"]
}
```

Required per slide: `title` and `talk`. The builder can render without diagrams, but `kind`, `points`, `nodes`, `edges`, and `steps` improve the visual result.

## Slide Writing Rules

- Visible slide text should be short and concrete.
- Put nuance into `talk`, not crowded text boxes.
- Use `contrast` when the point is "what people think" vs "what actually happens".
- Use `architecture`, `sequence`, or `lifecycle` only for real boundaries or flows.
- Do not add diagrams to every page.
- Avoid fake certainty, fake case studies, and fake metrics.
- For sharp language, make the reasoning carry the sharpness.

## File Generation

When actual files are requested:

```bash
python3 scripts/build_content_deck.py \
  --plan /path/to/slide-plan.json \
  --out /path/to/output-dir \
  --slug optional-slug
```

The script creates:

```text
output/
  <slug>-wps-compatible.pptx
  <slug>-guide.md
  <slug>-article.md      # only when article_markdown exists
  build-manifest.json
preview/
  contact-sheet.png
  slide-01.png
  ...
```

Run a duration estimate when needed:

```bash
python3 scripts/build_content_deck.py \
  --plan /path/to/slide-plan.json \
  --out /path/to/output-dir \
  --estimate-only
```

## Acceptance Check

Before final delivery:

- The deck has a clear position, not just a topic.
- At least one slide shows concrete cost, scene, boundary, or tradeoff.
- The Markdown speaker guide can be read aloud naturally.
- Any factual claim that depends on a real product, repo, person, date, or metric has been verified outside the style system.
- The output does not expose private corpus text or paths.
