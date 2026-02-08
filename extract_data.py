# extract_data.py
# extract_data.py
"""Extract vocabulary rows from chinese_code.py.

chinese_code.py contains the vocabulary as Python literals (lists of tuples), but the
tuples are formatted across multiple lines. A line-by-line parser will miss them and
return 0 items.

This extractor uses Python's AST + literal_eval to reliably pull the *_rows lists.
"""

from __future__ import annotations

from pathlib import Path
import ast
from typing import Any, Dict, List


def _get_source_path() -> Path:
    base_dir = Path(__file__).resolve().parent
    return base_dir / "chinese_code.py"


def extract_all_rows() -> List[Dict[str, str]]:
    """Return all vocab rows found in chinese_code.py.

    Output dict keys:
      section, hanzi, pinyin, english, french,
      sent_hanzi, sent_pinyin, sent_english, sent_french
    """
    file_path = _get_source_path()
    if not file_path.exists():
        raise FileNotFoundError(f"chinese_code.py not found at: {file_path}")

    code = file_path.read_text(encoding="utf-8")
    tree = ast.parse(code, filename=str(file_path))

    # Map list variable name (e.g., pronoun_rows) -> section title (e.g., "Pronouns & Basics")
    sections: Dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = getattr(node.func, "id", None)
        if func_name != "draw_table_page":
            continue
        if len(node.args) < 2:
            continue

        title_node, list_node = node.args[0], node.args[1]
        if (
            isinstance(title_node, ast.Constant)
            and isinstance(title_node.value, str)
            and isinstance(list_node, ast.Name)
        ):
            sections[list_node.id] = title_node.value

    all_rows: List[Dict[str, str]] = []

    # Walk top-level assignments to capture *_rows lists in file order
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue

        var_name = node.targets[0].id
        if not var_name.endswith("_rows"):
            continue

        # Only handle literal lists/tuples; skip anything computed
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue

        try:
            value: Any = ast.literal_eval(node.value)
        except Exception:
            continue

        if not isinstance(value, list):
            continue

        section_title = sections.get(var_name, "Unknown")

        for item in value:
            if not (isinstance(item, tuple) and len(item) == 8):
                continue
            if not all(isinstance(x, str) for x in item):
                continue

            hanzi, pinyin, english, french, sent_hanzi, sent_pinyin, sent_english, sent_french = item

            all_rows.append({
                "section": section_title,
                "hanzi": hanzi,
                "pinyin": pinyin,
                "english": english,
                "french": french,
                "sent_hanzi": sent_hanzi,
                "sent_pinyin": sent_pinyin,
                "sent_english": sent_english,
                "sent_french": sent_french,
            })

    print(f"[extract_data.py] Successfully extracted {len(all_rows)} vocabulary items.")
    return all_rows