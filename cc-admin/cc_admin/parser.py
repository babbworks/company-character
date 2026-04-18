import re


def parse_sections(markdown: str, section_map: dict) -> dict:
    headers = list(re.finditer(r"^##\s+(.+?)$", markdown, re.MULTILINE))
    slots = {}
    for i, match in enumerate(headers):
        header = match.group(1).strip()
        if header in section_map:
            start = match.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(markdown)
            slots[section_map[header]] = markdown[start:end].strip()
    return slots


def babb_topics(topics: list[str]) -> list[str]:
    return [t for t in topics if t.startswith("babb-")]
