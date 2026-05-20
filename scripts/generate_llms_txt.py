#!/usr/bin/env python3
"""Generate llms.txt and llms-full.txt from MkDocs documentation.

Produces LLM-friendly markdown versions of the documentation:
- llms.txt: Concise index with page descriptions
- llms-full.txt: All documentation concatenated into a single markdown file
"""

import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
MKDOCS_YML = Path(__file__).parent.parent / "mkdocs.yml"

SITE_URL = "https://deepbluecoding.github.io/python-manta/"
SITE_NAME = "Python Manta"
SITE_DESCRIPTION = (
    "Python bindings for the dotabuff/manta Dota 2 replay parser. "
    "Wraps the Go-based manta parser with a Pythonic API, Pydantic models, "
    "and all 272 callbacks for comprehensive replay data extraction."
)


def load_nav():
    try:
        import yaml
        with open(MKDOCS_YML) as f:
            config = yaml.safe_load(f)
        return config.get("nav", [])
    except ImportError:
        pass
    # Fallback: parse nav section from mkdocs.yml without PyYAML
    return _parse_nav_simple()


def _parse_nav_simple():
    text = MKDOCS_YML.read_text()
    lines = text.split("\n")
    nav_lines = []
    in_nav = False
    for line in lines:
        if line.strip() == "nav:" or line.startswith("nav:"):
            in_nav = True
            continue
        if in_nav:
            if line and not line[0].isspace() and line[0] != "-":
                break
            nav_lines.append(line)

    def parse_items(items_lines, base_indent):
        result = []
        i = 0
        while i < len(items_lines):
            line = items_lines[i]
            stripped = line.lstrip()
            if not stripped or not stripped.startswith("- "):
                i += 1
                continue
            indent = len(line) - len(stripped)
            if indent < base_indent:
                break
            if indent > base_indent:
                i += 1
                continue
            entry = stripped[2:].strip()
            if ":" in entry:
                key, value = entry.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value:
                    result.append({key: value})
                else:
                    children_lines = []
                    i += 1
                    while i < len(items_lines):
                        child_line = items_lines[i]
                        child_stripped = child_line.lstrip()
                        child_indent = len(child_line) - len(child_stripped) if child_stripped else indent + 999
                        if child_stripped and child_indent <= indent:
                            break
                        children_lines.append(child_line)
                        i += 1
                    children = parse_items(children_lines, indent + 2)
                    result.append({key: children})
                    continue
            i += 1
        return result

    return parse_items(nav_lines, 2)


def flatten_nav(nav, depth=0):
    pages = []
    for item in nav:
        if isinstance(item, dict):
            for title, value in item.items():
                if isinstance(value, str):
                    pages.append((title, value, depth))
                elif isinstance(value, list):
                    pages.append((title, None, depth))
                    pages.extend(flatten_nav(value, depth + 1))
    return pages


def _dedent_block(block_lines):
    non_empty = [l for l in block_lines if l.strip()]
    if not non_empty:
        return block_lines
    min_indent = min(len(l) - len(l.lstrip()) for l in non_empty)
    return [l[min_indent:] if l.strip() else "" for l in block_lines]


def strip_mkdocs_syntax(content):
    lines = content.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        admonition_match = re.match(r'^(\?{3}|!{3})\s+(\w+)\s*"?([^"]*)"?\s*$', line)
        if admonition_match:
            kind = admonition_match.group(2).upper()
            title = admonition_match.group(3).strip()
            if title:
                result.append(f"**{kind}: {title}**")
            else:
                result.append(f"**{kind}**")
            result.append("")
            i += 1
            block = []
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].strip() == ""):
                block.append(lines[i])
                i += 1
            result.extend(_dedent_block(block))
            continue
        result.append(line)
        i += 1
    return "\n".join(result)


def extract_ai_summary(content):
    match = re.search(
        r'(?:\?{3}|!{3})\s+info\s+"AI Summary"\s*\n((?:\s{4,}.*\n?)+)',
        content,
    )
    if not match:
        return ""
    block = match.group(1)
    lines = [line[4:].rstrip() if len(line) > 4 else "" for line in block.split("\n")]
    text = " ".join(line.strip() for line in lines if line.strip())
    return text


def extract_first_paragraph(content):
    lines = content.split("\n")
    paragraph = []
    in_content = False
    for line in lines:
        stripped = line.strip()
        if not in_content:
            if stripped.startswith("#"):
                in_content = True
                continue
            if stripped.startswith("---"):
                in_content = True
                continue
            continue
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith("#") or stripped.startswith("```") or stripped.startswith("|"):
            if paragraph:
                break
            continue
        if stripped.startswith("**INFO") or stripped.startswith("**WARNING"):
            continue
        paragraph.append(stripped)
    return " ".join(paragraph) if paragraph else ""


def generate_llms_txt(nav_pages):
    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {SITE_DESCRIPTION}",
        "",
        f"Docs: {SITE_URL}",
        f"GitHub: https://github.com/DeepBlueCoding/python-manta",
        f"PyPI: https://pypi.org/project/python-manta/",
        "",
    ]

    current_section = None
    for title, filepath, depth in nav_pages:
        if filepath is None:
            current_section = title
            lines.append(f"## {title}")
            lines.append("")
            continue

        doc_path = DOCS_DIR / filepath
        if not doc_path.exists():
            continue

        content = doc_path.read_text()
        description = extract_ai_summary(content)
        if not description:
            description = extract_first_paragraph(strip_mkdocs_syntax(content))

        page_url = SITE_URL + filepath.replace(".md", "/")
        if description:
            lines.append(f"- [{title}]({page_url}): {description}")
        else:
            lines.append(f"- [{title}]({page_url})")

    lines.append("")
    return "\n".join(lines)


def generate_llms_full_txt(nav_pages):
    lines = [
        f"# {SITE_NAME} — Complete Documentation",
        "",
        f"> {SITE_DESCRIPTION}",
        "",
    ]

    for title, filepath, depth in nav_pages:
        if filepath is None:
            continue

        doc_path = DOCS_DIR / filepath
        if not doc_path.exists():
            continue

        content = doc_path.read_text()
        cleaned = strip_mkdocs_syntax(content)
        lines.append(cleaned.strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    nav = load_nav()
    nav_pages = flatten_nav(nav)

    llms_txt = generate_llms_txt(nav_pages)
    llms_full_txt = generate_llms_full_txt(nav_pages)

    output_llms = DOCS_DIR / "llms.txt"
    output_full = DOCS_DIR / "llms-full.txt"

    output_llms.write_text(llms_txt)
    output_full.write_text(llms_full_txt)

    print(f"Generated {output_llms} ({len(llms_txt)} bytes)")
    print(f"Generated {output_full} ({len(llms_full_txt)} bytes)")


if __name__ == "__main__":
    main()
