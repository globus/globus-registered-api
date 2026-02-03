import typing as t

import json
from difflib import Differ


def diff_schema(orig_schema: dict[str, t.Any], new_schema: dict[str, t.Any]) -> str:
    """
    Produce a minimized diff between two OpenAPI schemas.

    :returns: A serialized minimal string diff between two schemas.
    """

    left = json.dumps(orig_schema, indent=2).splitlines(keepends=True)
    right = json.dumps(new_schema, indent=2).splitlines(keepends=True)

    diff_lines = list(Differ().compare(left, right))
    return "".join(_minimize_diff_lines(diff_lines))


def _minimize_diff_lines(lines: list[str]) -> t.Iterator[str]:
    """
    Minimize diff lines, yielding a generator of lines that should be shown.

    Lines will be printed if they:
        1. Have a "+ " or "- " prefix (indicating addition or removal)
       2. Are contextually useful as parents of added/removed lines.
    """

    ranges = _compute_diff_index_ranges(lines)

    for range_idx, (start, end) in enumerate(ranges):
        prev = ranges[range_idx - 1] if range_idx > 0 else (0, 0)

        context_lines: list[str] = []
        if start > 0:
            # Add lines of parent elements, identified by indentation changes.
            indent_level = _compute_indent_level(lines[start])
            for idx in reversed(range(prev[1] + 1, start)):
                new_level = _compute_indent_level(lines[idx])
                if new_level < indent_level:
                    context_lines.append(lines[idx])
                    indent_level = new_level

        for line in reversed(context_lines):
            yield line
        for idx in range(start, end + 1):
            yield lines[idx]


def _compute_diff_index_ranges(lines: t.Iterable[str]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    current_range: None | tuple[int, int] = None

    for idx, line in enumerate(lines):
        if not line.startswith("  "):
            # Line is "important" (addition, removal)
            if current_range is None:
                # Create a new range
                current_range = idx, idx
            else:
                # Extend the current range
                current_range = (current_range[0], idx)

        else:
            # Line is not "important"
            if current_range is not None:
                ranges.append(current_range)
                current_range = None

    if current_range is not None:
        ranges.append(current_range)
    return ranges

def _compute_indent_level(line: str) -> int:
    return len(line[1:]) - len(line[1:].lstrip())
