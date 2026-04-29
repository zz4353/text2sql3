import re
import csv
from jinja2 import Template
from difflib import get_close_matches
from functools import lru_cache

_IDENT = r'''(?:"[^"]+"|`[^`]+`|\[[^\]]+\]|'[^']+'|\w+)'''
_INSERT_PATTERN = re.compile(
    rf'INSERT\s+(?:OR\s+\w+\s+)?INTO\s+({_IDENT})\s*\(([^)]+)\)',
    re.IGNORECASE,
)


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and (
        (s[0] == '"' and s[-1] == '"') or
        (s[0] == '`' and s[-1] == '`') or
        (s[0] == "'" and s[-1] == "'") or
        (s[0] == '[' and s[-1] == ']')
    ):
        return s[1:-1]
    return s


def extract_columns_from_insert(sql_list: list[str]) -> list[str]:
    cols = []
    for sql in sql_list:
        m = _INSERT_PATTERN.search(sql)
        if not m:
            continue
        table = _unquote(m.group(1))
        for col in m.group(2).split(","):
            col = _unquote(col)
            if col:
                cols.append(f"{table}.{col}")
    return cols

def sqlite_affinity_type(declared_type: str) -> str:
    declared_type = declared_type.upper()
    if "INT" in declared_type:
        return "INTEGER"
    elif "CHAR" in declared_type or "CLOB" in declared_type or "TEXT" in declared_type:
        return "TEXT"
    elif "BLOB" in declared_type:
        return "BLOB"
    elif "REAL" in declared_type or "FLOA" in declared_type or "DOUB" in declared_type:
        return "REAL"
    else:
        return "NUMERIC"
    
def normalize_value_by_column(value, declared_type: str):
    if value is None:
        return None

    affinity = sqlite_affinity_type(declared_type)
    
    # Chuẩn hóa giá trị value theo kiểu dữ liệu affinity
    try:
        if affinity == "INTEGER":
            if isinstance(value, bool): 
                return int(value)
            elif isinstance(value, int): 
                return value
            elif isinstance(value, float):
                if value.is_integer():
                    return int(value)
                else: 
                    return value
            elif isinstance(value, str):
                s = value.strip()
                if s.isdigit():
                    return int(s)
                try:
                    f = float(s)
                    if f.is_integer():
                        return int(f)
                    else:
                        return f
                except Exception:
                    return s
            else:
                return value
        elif affinity == "TEXT":
            return str(value)
        elif affinity == "BLOB":
            return value
        elif affinity == "REAL":
            return float(value)
        elif affinity == "NUMERIC":
            if isinstance(value, bool):
                return int(value)   
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                if value.is_integer():
                    return int(value)
                else:
                    return value
            if isinstance(value, str):
                s = value.strip()
                if s.isdigit():
                    return int(s)
                try:
                    f = float(s)
                    if f.is_integer():
                        return int(f)
                    return float(s)
                except Exception:
                    return s
            return value
        else:
            return value
    except Exception:
        return value

def render_sql_for_log1(sql, params):
    parts = sql.split("?")
    if len(parts) - 1 != len(params):
        raise ValueError("Number of placeholders does not match params")

    rendered_sql = [] 
    
    def to_sql_literal(val):
        if val is None:
            return "NULL"
        if isinstance(val, bool):
            return "1" if val else "0"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            return "'" + val.replace("'", "''") + "'"
        raise TypeError(f"Unsupported param type: {type(val)}")

    for part, param in zip(parts, params + [None]):
        rendered_sql.append(part)
        if param is not None:
            rendered_sql.append(to_sql_literal(param))

    return "".join(rendered_sql)

def render_sql_for_log(sql, params):
    parts = sql.split("?")
    if len(parts) - 1 != len(params):
        raise ValueError("Number of placeholders does not match params")

    rendered_sql = []

    def to_sql_literal(val):
        if val is None:
            return "NULL"
        if isinstance(val, bool):
            return "1" if val else "0"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            return "'" + val.replace("'", "''") + "'"
        raise TypeError(f"Unsupported param type: {type(val)}")

    _sentinel = object()
    for part, param in zip(parts, params + [_sentinel]):
        rendered_sql.append(part)
        if param is not _sentinel:
            rendered_sql.append(to_sql_literal(param))

    return "".join(rendered_sql)

def render_prompt(template_path, **kwargs):
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    template = Template(template_str)
    return template.render(**kwargs)

def remove_alignment_schema(schema: str) -> str:
    lines = []
    for line in schema.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        # gộp nhiều space liên tiếp thành 1 space
        line = re.sub(r'\s{2,}', ' ', line)
        lines.append(line)
    return "\n".join(lines)

def read_csv_with_fallback(path) -> list[dict]:
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin1")

    for enc in encodings:
        try:
            with open(path, encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        "csv",
        b"",
        0,
        1,
        f"Cannot decode CSV file with encodings: {encodings}"
    )

@lru_cache(maxsize=100)
def fuzzy_match(query: str, candidates: tuple[str], cutoff: float = 0.7):
    best_matches = get_close_matches(
        query,
        candidates,
        n=1,
        cutoff=cutoff,
    )

    if not best_matches:
        return None
    
    return best_matches[0]