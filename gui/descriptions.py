from pathlib import Path
import json
from ftesc.resources import get_resource_path

_DESC_CACHE = None


def load_param_descriptions() -> dict:
    global _DESC_CACHE
    if _DESC_CACHE is not None:
        return _DESC_CACHE
    path = Path(get_resource_path("docs", "param_descriptions.json"))
    if not path.exists():
        _DESC_CACHE = {}
        return _DESC_CACHE
    try:
        _DESC_CACHE = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        _DESC_CACHE = {}
    return _DESC_CACHE


def get_description(section_key: str, field_key: str) -> str | None:
    descs = load_param_descriptions()
    return descs.get(section_key, {}).get(field_key)
