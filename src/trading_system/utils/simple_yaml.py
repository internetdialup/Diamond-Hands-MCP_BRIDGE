from __future__ import annotations

from pathlib import Path
from typing import Any


def _strip_comments(line: str) -> str:
    if "#" not in line:
        return line.rstrip("\n")
    prefix, _, suffix = line.partition("#")
    if prefix.strip():
        return prefix.rstrip()
    if not suffix:
        return ""
    return ""


def _clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = _strip_comments(raw_line).rstrip()
        if not line.strip():
            continue
        lines.append(line)
    return lines


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _parse_block(lines: list[str], start: int, indent: int) -> tuple[Any, int]:
    if start >= len(lines):
        return {}, start

    current = lines[start]
    current_indent = _indent_of(current)
    if current_indent < indent:
        return {}, start

    if current.lstrip().startswith("- "):
        items: list[Any] = []
        index = start
        while index < len(lines):
            line = lines[index]
            if _indent_of(line) != indent or not line.lstrip().startswith("- "):
                break
            content = line.lstrip()[2:].strip()
            index += 1
            if not content:
                nested, index = _parse_block(lines, index, indent + 2)
                items.append(nested)
                continue
            if ":" in content:
                key, _, value = content.partition(":")
                item: dict[str, Any] = {}
                key = key.strip()
                value = value.strip()
                if value:
                    item[key] = _parse_scalar(value)
                else:
                    nested, index = _parse_block(lines, index, indent + 2)
                    item[key] = nested
                if index < len(lines) and _indent_of(lines[index]) > indent:
                    nested, index = _parse_block(lines, index, indent + 2)
                    if isinstance(nested, dict):
                        item.update(nested)
                items.append(item)
                continue
            items.append(_parse_scalar(content))
        return items, index

    mapping: dict[str, Any] = {}
    index = start
    while index < len(lines):
        line = lines[index]
        current_indent = _indent_of(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"Unexpected indentation near line: {line}")

        stripped = line.strip()
        if ":" not in stripped:
            raise ValueError(f"Expected key/value entry, got: {line}")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        index += 1

        if value:
            mapping[key] = _parse_scalar(value)
            continue

        if index >= len(lines) or _indent_of(lines[index]) <= indent:
            mapping[key] = {}
            continue

        nested, index = _parse_block(lines, index, indent + 2)
        mapping[key] = nested
    return mapping, index


def load_yaml_like(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = _clean_lines(text)
    if not lines:
        return {}
    payload, _ = _parse_block(lines, 0, _indent_of(lines[0]))
    if not isinstance(payload, dict):
        raise ValueError("Top-level config must be a mapping")
    return payload
