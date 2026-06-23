#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import re
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
SLIDE_CX, SLIDE_CY = 12192000, 6858000
FONT_REG = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_MONO = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

C = {
    "bg": "#111318",
    "panel": "#1A1D24",
    "panel2": "#20242D",
    "line": "#3A404D",
    "muted": "#A7AFBD",
    "text": "#F3F5F7",
    "red": "#F45B69",
    "amber": "#F2B84B",
    "green": "#58C27D",
    "blue": "#69A8F5",
    "cyan": "#49C6D8",
    "white": "#FFFFFF",
}


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value).strip("-").lower()
    return value[:80] or "touge-content-deck"


def font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_MONO if mono else FONT_REG, size=size)


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return (*hex_to_rgb(color), alpha)


def wrap(draw: ImageDraw.ImageDraw, value: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for para in str(value).split("\n"):
        cur = ""
        for ch in para:
            test = cur + ch
            if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int = 24,
         color: str = "text", max_width: int | None = None, line_gap: int = 8,
         anchor: str | None = None, mono: bool = False) -> int:
    fnt = font(size, mono)
    fill = C.get(color, color)
    x, y = xy
    if anchor:
        draw.text((x, y), str(value), font=fnt, fill=fill, anchor=anchor)
        return y + size
    lines = wrap(draw, str(value), fnt, max_width) if max_width else str(value).split("\n")
    yy = y
    for line in lines:
        draw.text((x, yy), line, font=fnt, fill=fill)
        yy += size + line_gap
    return yy


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = "panel",
            outline: str = "line", radius: int = 8, width: int = 2) -> None:
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=rgba(C.get(fill, fill)),
        outline=C.get(outline, outline),
        width=width,
    )


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int],
          color: str = "line", width: int = 3) -> None:
    draw.line((start, end), fill=C[color], width=width)
    x1, y1 = start
    x2, y2 = end
    angle = math.atan2(y2 - y1, x2 - x1)
    for da in (2.55, -2.55):
        x = x2 + 12 * math.cos(angle + da)
        y = y2 + 12 * math.sin(angle + da)
        draw.line((x2, y2, x, y), fill=C[color], width=width)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def node(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str,
         sub: str = "", color: str = "cyan") -> None:
    rounded(draw, box, "panel2", color, 7)
    x1, y1, x2, y2 = box
    text(draw, ((x1 + x2) // 2, y1 + 24), title, 18, color, anchor="mm")
    if sub:
        text(draw, (x1 + 14, y1 + 48), sub, 13, "muted", max_width=x2 - x1 - 28, line_gap=4)


def draw_header(draw: ImageDraw.ImageDraw, idx: int, title: str, subtitle: str) -> None:
    text(draw, (54, 36), f"{idx:02d}", 16, "red")
    text(draw, (106, 30), title, 31, "text", max_width=900, line_gap=3)
    if subtitle:
        text(draw, (106, 82), subtitle, 17, "muted", max_width=980, line_gap=4)


def draw_footer(draw: ImageDraw.ImageDraw, idx: int, total: int, label: str) -> None:
    text(draw, (48, 678), f"{label} / content deck", 12, "#6F7785")
    text(draw, (1230, 678), f"{idx}/{total}", 12, "#6F7785", anchor="ra")


def draw_bullets(draw: ImageDraw.ImageDraw, points: list[str], x: int, y: int, w: int) -> None:
    for i, point in enumerate(points[:6]):
        yy = y + i * 67
        draw.ellipse((x, yy + 10, x + 11, yy + 21), fill=C["red"])
        text(draw, (x + 30, yy), point, 23, "text", max_width=w - 30, line_gap=5)


def draw_contrast(draw: ImageDraw.ImageDraw, spec: dict) -> None:
    left = spec.get("left") or spec.get("misunderstanding") or "大家以为"
    right = spec.get("right") or spec.get("reality") or "真正的问题"
    rounded(draw, (78, 185, 600, 575), "panel", "amber", 10)
    rounded(draw, (680, 185, 1202, 575), "panel", "red", 10)
    text(draw, (112, 220), "表面说法", 22, "amber")
    text(draw, (112, 270), left, 31, "text", max_width=430, line_gap=10)
    text(draw, (714, 220), "真实代价", 22, "red")
    text(draw, (714, 270), right, 31, "text", max_width=430, line_gap=10)


def draw_sequence(draw: ImageDraw.ImageDraw, steps: list[dict]) -> None:
    actors: list[str] = []
    for step in steps:
        for key in ("from", "to"):
            name = str(step.get(key, "")).strip()
            if name and name not in actors:
                actors.append(name)
    actors = actors[:6] or ["User", "Agent", "Runtime", "Output"]
    xs = [80 + i * (1120 // max(1, len(actors) - 1)) for i in range(len(actors))]
    for x, actor in zip(xs, actors):
        rounded(draw, (x - 70, 158, x + 70, 203), "panel2", "cyan", 6)
        text(draw, (x, 181), actor, 14, "text", anchor="mm")
        draw.line((x, 203, x, 610), fill=C["line"], width=2)
    y = 245
    colors = ["red", "blue", "green", "amber", "cyan"]
    for i, step in enumerate(steps[:8]):
        src = actors.index(step.get("from")) if step.get("from") in actors else 0
        dst = actors.index(step.get("to")) if step.get("to") in actors else min(1, len(actors) - 1)
        color = colors[i % len(colors)]
        arrow(draw, (xs[src], y), (xs[dst], y), color, 3)
        text(draw, ((xs[src] + xs[dst]) // 2, y - 25), str(step.get("label", ""))[:36], 14, color, anchor="mm")
        y += 56


def draw_architecture(draw: ImageDraw.ImageDraw, nodes: list[dict], edges: list[dict]) -> None:
    if not nodes:
        nodes = [
            {"id": "Input", "label": "Input", "note": "topic/material"},
            {"id": "Judgment", "label": "Judgment", "note": "position/cost"},
            {"id": "Draft", "label": "Draft", "note": "article/script"},
            {"id": "Deck", "label": "Deck", "note": "pptx/md"},
        ]
        edges = [{"from": nodes[i]["id"], "to": nodes[i + 1]["id"]} for i in range(len(nodes) - 1)]
    positions: dict[str, tuple[int, int, int, int]] = {}
    colors = ["red", "blue", "green", "amber", "cyan"]
    for i, n in enumerate(nodes[:8]):
        x = 80 + (i % 4) * 290
        y = 190 + (i // 4) * 190
        positions[n["id"]] = (x, y, x + 210, y + 95)
        node(draw, positions[n["id"]], n.get("label", n["id"]), n.get("note", ""), colors[i % len(colors)])
    for e in edges[:10]:
        if e.get("from") in positions and e.get("to") in positions:
            a = positions[e["from"]]
            b = positions[e["to"]]
            arrow(draw, (a[2], (a[1] + a[3]) // 2), (b[0], (b[1] + b[3]) // 2), "line", 2)


def draw_slide(spec: dict, idx: int, total: int, deck_title: str) -> Image.Image:
    img = Image.new("RGB", (W, H), hex_to_rgb(C["bg"]))
    draw = ImageDraw.Draw(img)
    title = spec.get("title", f"Slide {idx}")
    subtitle = spec.get("subtitle", "")
    kind = spec.get("kind", "bullets")

    if idx == 1 or kind == "cover":
        text(draw, (76, 94), title, 54, "text", max_width=980, line_gap=9)
        if subtitle:
            text(draw, (80, 184), subtitle, 29, "muted", max_width=900, line_gap=8)
        rounded(draw, (82, 430, 650, 560), "panel", "red", 10)
        text(draw, (116, 458), "这页先把话说清楚", 21, "red")
        claim = spec.get("claim") or spec.get("quote") or "不是把内容做成 PPT，而是把判断讲到别人听得懂。"
        text(draw, (116, 496), claim, 27, "text", max_width=480, line_gap=8)
        node(draw, (810, 175, 1035, 265), "立场", "先有判断", "red")
        node(draw, (920, 365, 1145, 455), "交付", "文章 / PPT / 讲稿", "green")
        arrow(draw, (920, 265), (1035, 365), "green", 4)
        draw_footer(draw, idx, total, deck_title)
        return img

    draw_header(draw, idx, title, subtitle)
    points = spec.get("points") or []
    if kind == "contrast":
        draw_contrast(draw, spec)
    elif kind == "sequence":
        draw_sequence(draw, spec.get("steps", []))
    elif kind in {"architecture", "modules"}:
        draw_architecture(draw, spec.get("nodes", []), spec.get("edges", []))
    elif kind == "lifecycle":
        steps = points or [s.get("label", "") for s in spec.get("steps", [])]
        for i, label in enumerate(steps[:6]):
            x = 74 + i * 195
            node(draw, (x, 265, x + 140, 345), label, "", "green" if i < 4 else "amber")
            if i < min(len(steps), 6) - 1:
                arrow(draw, (x + 140, 305), (x + 195, 305), "line", 2)
    elif kind in {"claim", "quote"}:
        claim = spec.get("quote") or spec.get("claim") or (points[0] if points else title)
        text(draw, (92, 205), claim, 45, "red", max_width=1000, line_gap=12)
        if len(points) > 1:
            draw_bullets(draw, points[1:], 125, 405, 980)
    elif kind == "summary":
        text(draw, (90, 190), spec.get("claim", title), 42, "red", max_width=960, line_gap=10)
        draw_bullets(draw, points, 120, 360, 1000)
    else:
        draw_bullets(draw, points or [spec.get("talk", "")[:90]], 100, 185, 1060)
    draw_footer(draw, idx, total, deck_title)
    return img


def rels(items: list[tuple[str, str, str]]) -> str:
    body = "\n".join(f'<Relationship Id="{rid}" Type="{typ}" Target="{target}"/>' for rid, typ, target in items)
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n{body}\n</Relationships>'


def content_types(count: int) -> str:
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ] + [
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, count + 1)
    ]
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
        *overrides,
        '</Types>',
    ])


def presentation_xml(count: int) -> str:
    slds = "\n".join(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, count + 1))
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{count + 1}"/></p:sldMasterIdLst><p:sldIdLst>{slds}</p:sldIdLst><p:sldSz cx="{SLIDE_CX}" cy="{SLIDE_CY}" type="wide"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle/></p:presentation>'''


def slide_xml(idx: int) -> str:
    name = html.escape(f"slide-{idx:02d}.png")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="111318"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr><p:pic><p:nvPicPr><p:cNvPr id="{idx + 1}" name="{name}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_CX}" cy="{SLIDE_CY}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'''


def static_parts(work: Path, count: int, title: str) -> None:
    write(work / "[Content_Types].xml", content_types(count))
    write(work / "_rels/.rels", rels([
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "ppt/presentation.xml"),
        ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
        ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties", "docProps/app.xml"),
    ]))
    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    esc_title = html.escape(title)
    write(work / "docProps/core.xml", f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{esc_title}</dc:title><dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>''')
    write(work / "docProps/app.xml", f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Codex content deck builder</Application><PresentationFormat>16:9</PresentationFormat><Slides>{count}</Slides></Properties>''')
    write(work / "ppt/presentation.xml", presentation_xml(count))
    pres_rels = [(f"rId{i}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", f"slides/slide{i}.xml") for i in range(1, count + 1)]
    pres_rels.append((f"rId{count + 1}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "slideMasters/slideMaster1.xml"))
    write(work / "ppt/_rels/presentation.xml.rels", rels(pres_rels))
    write(work / "ppt/slideMasters/slideMaster1.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>''')
    write(work / "ppt/slideMasters/_rels/slideMaster1.xml.rels", rels([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml")]))
    write(work / "ppt/slideLayouts/slideLayout1.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>''')
    write(work / "ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "../slideMasters/slideMaster1.xml")]))


def build_contact_sheet(paths: list[Path], contact: Path) -> None:
    thumbs = [Image.open(p).resize((384, 216)) for p in paths]
    sheet = Image.new("RGB", (384 * 3, 256 * math.ceil(len(thumbs) / 3)), "white")
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(thumbs):
        x = (i % 3) * 384
        y = (i // 3) * 256
        sheet.paste(im, (x, y))
        d.text((x + 8, y + 222), f"Slide {i + 1:02d}", fill=(20, 20, 20), font=font(12))
    contact.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact)


def create_markdown(plan: dict, md: Path) -> None:
    title = plan.get("title", "Content Deck")
    parts = [
        f"# {title} 口述稿",
        "",
        "这份稿子配合 PPT 使用。每一页只承担一个判断，细节放在口述里展开。",
        "",
    ]
    for i, slide in enumerate(plan.get("slides", []), start=1):
        parts += [f"## {i}. {slide.get('title', f'Slide {i}')}", "", slide.get("talk", ""), ""]
    takeaways = plan.get("takeaways") or plan.get("benefits") or []
    if takeaways:
        parts += ["## 听众最后应该带走什么", ""]
        for i, item in enumerate(takeaways, start=1):
            parts += [f"{i}. {item}", ""]
    write(md, "\n".join(parts))


def estimate_duration(plan: dict) -> dict:
    text_parts = [slide.get("talk", "") for slide in plan.get("slides", [])]
    if plan.get("article_markdown"):
        text_parts.append(plan["article_markdown"])
    clean = re.sub(r"[`*_#>\-|\s]", "", "\n".join(text_parts))
    chars = len(clean)
    return {
        "totalNonWhitespaceChars": chars,
        "estimatedMinutes": {
            "tight": round(chars / 230 * 1.10, 1),
            "recommended": round(chars / 200 * 1.20, 1),
            "deep": round(chars / 180 * 1.25, 1),
        },
    }


def build(plan_path: Path, out_dir: Path, slug_arg: str = "") -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    slides = plan.get("slides", [])
    if not slides:
        raise SystemExit("slide plan contains no slides")

    slug = slugify(slug_arg or plan.get("title", "touge-content-deck"))
    preview = out_dir / "preview"
    output = out_dir / "output"
    work = out_dir / "wps-pptx-work"
    for d in [preview, output, work]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    title = plan.get("title", "Content Deck")
    pngs: list[Path] = []
    for idx, slide in enumerate(slides, start=1):
        img = draw_slide(slide, idx, len(slides), title)
        path = preview / f"slide-{idx:02d}.png"
        img.save(path)
        pngs.append(path)

    contact = preview / "contact-sheet.png"
    build_contact_sheet(pngs, contact)

    pptx = output / f"{slug}-wps-compatible.pptx"
    guide = output / f"{slug}-guide.md"
    article = output / f"{slug}-article.md"
    create_markdown(plan, guide)
    article_path = ""
    if plan.get("article_markdown"):
        write(article, f"# {title}\n\n{plan['article_markdown'].strip()}\n")
        article_path = str(article)

    static_parts(work, len(pngs), title)
    media = work / "ppt/media"
    media.mkdir(parents=True, exist_ok=True)
    for idx, png in enumerate(pngs, start=1):
        shutil.copyfile(png, media / f"image{idx}.png")
        write(work / f"ppt/slides/slide{idx}.xml", slide_xml(idx))
        write(work / f"ppt/slides/_rels/slide{idx}.xml.rels", rels([
            ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", f"../media/image{idx}.png"),
            ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
        ]))

    with zipfile.ZipFile(pptx, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(work.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(work).as_posix())

    manifest = {
        "pptx": str(pptx),
        "guide": str(guide),
        "article": article_path,
        "contactSheet": str(contact),
        "slideCount": len(slides),
        "wpsMode": "full-slide-png",
        "plan": str(plan_path),
        "duration": estimate_duration(plan),
    }
    write(output / "build-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Touge-style WPS-compatible PPTX and Markdown speaker guide.")
    parser.add_argument("--plan", required=True, help="slide-plan.json")
    parser.add_argument("--out", required=True, help="output workspace directory")
    parser.add_argument("--slug", default="", help="output filename slug")
    parser.add_argument("--estimate-only", action="store_true", help="print duration estimate without rendering files")
    args = parser.parse_args()

    plan_path = Path(args.plan).expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if args.estimate_only:
        print(json.dumps(estimate_duration(plan), ensure_ascii=False, indent=2))
        return

    manifest = build(plan_path, Path(args.out).expanduser().resolve(), args.slug)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
