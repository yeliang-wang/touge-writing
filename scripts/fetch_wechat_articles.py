#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from lxml import etree, html as lxml_html


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


def slugify(value: str, limit: int = 72) -> str:
    value = re.sub(r"\s+", "-", value.strip().lower())
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff._-]+", "", value)
    value = value.strip("-._")
    return (value[:limit] or "untitled")


def load_records(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [r for r in data["records"] if r.get("record_type") == "article_standard" and r.get("standard_url")]


def fetch_url(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read()


def text_content(node) -> str:
    text = "".join(node.itertext())
    text = html.unescape(text)
    text = re.sub(r"\u00a0", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def cleanup_tree(root):
    for bad in root.xpath(".//script|.//style|.//noscript|.//iframe"):
        parent = bad.getparent()
        if parent is not None:
            parent.remove(bad)
    return root


def node_to_markdown(node) -> str:
    if isinstance(node.tag, str):
        try:
            tag = etree.QName(node).localname.lower()
        except ValueError:
            tag = node.tag.split(":")[-1].lower()
    else:
        tag = ""
    if tag in {"script", "style", "noscript", "iframe"}:
        return ""

    if tag == "br":
        return "\n"

    if tag == "img":
        src = node.get("data-src") or node.get("src") or ""
        alt = node.get("alt") or ""
        return f"\n![{alt}]({src})\n" if src else ""

    if tag == "a":
        label = text_content(node)
        href = node.get("href") or ""
        if href and label:
            return f"[{label}]({href})"
        return label

    parts = []
    if node.text:
        parts.append(html.unescape(node.text))
    for child in node:
        parts.append(node_to_markdown(child))
        if child.tail:
            parts.append(html.unescape(child.tail))
    body = "".join(parts)

    block_tags = {
        "p",
        "section",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "blockquote",
        "ul",
        "ol",
        "li",
    }
    if tag in {"h1", "h2", "h3"}:
        level = {"h1": "#", "h2": "##", "h3": "###"}[tag]
        body = f"\n{level} {body.strip()}\n"
    elif tag == "li":
        body = "\n- " + body.strip()
    elif tag == "blockquote":
        lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
        body = "\n" + "\n".join("> " + line for line in lines) + "\n"
    elif tag in block_tags:
        body = "\n" + body.strip() + "\n"
    return body


def extract_article(html_bytes: bytes, record: dict):
    parser = lxml_html.HTMLParser(encoding="utf-8")
    root = lxml_html.fromstring(html_bytes, parser=parser)
    title = (
        root.xpath("string(//h1[contains(@class, 'rich_media_title')])").strip()
        or root.xpath("string(//meta[@property='og:title']/@content)").strip()
        or record.get("title", "")
    )
    author = root.xpath("string(//*[@id='js_name'])").strip()
    account = root.xpath("string(//*[@id='js_name'])").strip()
    publish_time = (
        root.xpath("string(//*[@id='publish_time'])").strip()
        or record.get("publish_date", "")
    )
    content_nodes = root.xpath("//*[@id='js_content']")
    content_node = cleanup_tree(content_nodes[0]) if content_nodes else None
    plain_text = text_content(content_node) if content_node is not None else ""
    md_body = node_to_markdown(content_node) if content_node is not None else ""
    md_body = re.sub(r"[ \t]+\n", "\n", md_body)
    md_body = re.sub(r"\n{3,}", "\n\n", md_body).strip()
    cover = (
        root.xpath("string(//meta[@property='og:image']/@content)").strip()
        or record.get("cover_url", "")
    )
    return {
        "title": title,
        "author": author,
        "account": account,
        "publish_time": publish_time,
        "url": record.get("standard_url"),
        "cover_url": cover,
        "plain_text": plain_text,
        "markdown": md_body,
        "word_count": len(re.sub(r"\s+", "", plain_text)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-json", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.6)
    args = parser.parse_args()

    index_path = Path(args.index_json)
    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "raw_html"
    md_dir = out_dir / "markdown"
    raw_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(index_path)
    if args.limit:
        records = records[: args.limit]

    manifest = []
    errors = []

    for i, record in enumerate(records, start=1):
        title = record.get("title") or f"article-{record.get('list_index')}"
        digest = hashlib.sha1(record["standard_url"].encode("utf-8")).hexdigest()[:10]
        stem = f"{int(record.get('list_index', i)):03d}-{slugify(title)}-{digest}"
        raw_path = raw_dir / f"{stem}.html"
        md_path = md_dir / f"{stem}.md"
        meta_path = md_dir / f"{stem}.json"
        try:
            if raw_path.exists():
                html_bytes = raw_path.read_bytes()
            else:
                html_bytes = fetch_url(record["standard_url"])
                raw_path.write_bytes(html_bytes)
                time.sleep(args.sleep)
            article = extract_article(html_bytes, record)
            frontmatter = {
                "title": article["title"],
                "url": article["url"],
                "publish_time": article["publish_time"],
                "source_publish_date": record.get("publish_date"),
                "list_index": record.get("list_index"),
                "word_count": article["word_count"],
                "readers": record.get("metrics", {}).get("readers"),
                "likes": record.get("metrics", {}).get("likes"),
                "shares": record.get("metrics", {}).get("shares"),
                "comments": record.get("metrics", {}).get("comments"),
                "is_original": record.get("is_original"),
            }
            md_text = "---\n" + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in frontmatter.items()) + "\n---\n\n"
            md_text += f"# {article['title']}\n\n{article['markdown']}\n"
            md_path.write_text(md_text, encoding="utf-8")
            meta = {**frontmatter, "raw_html": str(raw_path), "markdown": str(md_path), "cover_url": article["cover_url"]}
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest.append(meta)
            print(f"[{i}/{len(records)}] OK {title}", flush=True)
        except (urllib.error.URLError, TimeoutError, ValueError, etree.ParserError, OSError) as exc:
            err = {
                "list_index": record.get("list_index"),
                "title": title,
                "url": record.get("standard_url"),
                "error": repr(exc),
            }
            errors.append(err)
            print(f"[{i}/{len(records)}] ERR {title}: {exc}", flush=True)

    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": len(manifest), "errors": len(errors), "out_dir": str(out_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
