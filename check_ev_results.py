"""Compare extracted_values.json against gold INSERT SQL."""
import json
import re


_IDENT = r'''(?:"[^"]+"|`[^`]+`|\[[^\]]+\]|'[^']+'|\w+)'''
_INSERT_COLS = re.compile(
    rf'INSERT\s+(?:OR\s+\w+\s+)?INTO\s+({_IDENT})\s*\(([^)]+)\)',
    re.IGNORECASE,
)
_VALUES_BLOCK = re.compile(r'\bVALUES\s*(.+)', re.IGNORECASE | re.DOTALL)


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] in ('"', '`', "'") and s[-1] == s[0]:
        return s[1:-1]
    if len(s) >= 2 and s[0] == '[' and s[-1] == ']':
        return s[1:-1]
    return s


def _split_values_row(row: str) -> list[str]:
    """Split 'val1, val2, ...' respecting quoted strings."""
    tokens, cur, in_q, q_char = [], [], False, None
    for ch in row:
        if in_q:
            cur.append(ch)
            if ch == q_char:
                in_q = False
        elif ch in ("'", '"'):
            in_q, q_char = True, ch
            cur.append(ch)
        elif ch == ',':
            tokens.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        tokens.append(''.join(cur).strip())
    return tokens


def _parse_value_rows(values_text: str) -> list[list[str]]:
    """Extract list of value rows from VALUES (...), (...), ..."""
    rows, i, n = [], 0, len(values_text)
    while i < n:
        if values_text[i] == '(':
            depth, start, i = 1, i + 1, i + 1
            in_q, q_char = False, None
            while i < n and depth > 0:
                ch = values_text[i]
                if in_q:
                    if ch == q_char:
                        in_q = False
                elif ch in ("'", '"'):
                    in_q, q_char = True, ch
                elif ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                i += 1
            rows.append(_split_values_row(values_text[start:i - 1]))
        else:
            i += 1
    return rows


def parse_insert_records(sql_list: list[str]) -> dict[str, list[dict]]:
    """Parse INSERT SQL list into {table: [record_dict, ...]}."""
    result = {}
    for sql in sql_list:
        m_cols = _INSERT_COLS.search(sql)
        if not m_cols:
            continue
        table = _unquote(m_cols.group(1))
        cols = [_unquote(c.strip()) for c in m_cols.group(2).split(',')]

        m_vals = _VALUES_BLOCK.search(sql, m_cols.end())
        if not m_vals:
            continue
        rows = _parse_value_rows(m_vals.group(1))
        records = result.setdefault(table, [])
        for row in rows:
            if len(row) == len(cols):
                records.append({c: _unquote(v) for c, v in zip(cols, row)})
    return result


def _normalize(v) -> str:
    if v is None:
        return 'null'
    return str(v).strip().lower()


def _record_key(rec: dict) -> frozenset:
    return frozenset((_normalize(k), _normalize(v)) for k, v in rec.items() if v is not None and str(v).strip().lower() != 'null')


with open('test.json', 'r', encoding='utf-8') as f:
    test_by_id = {s['id']: s for s in json.load(f)}

with open('results/pipeline4/extracted_values.json', 'r', encoding='utf-8') as f:
    pred_data = json.load(f)

n_correct = n_partial = n_wrong = n_err = 0
total = len(pred_data)

for item in pred_data:
    item_id = item['id']
    if 'error' in item:
        print(f"[{item_id}] ERROR: {item['error'][:80]}")
        n_err += 1
        continue

    gold_sqls = test_by_id[item_id]['gold_sql']
    gold_tables = parse_insert_records(gold_sqls)

    pred_groups = {g['table']: g['records'] for g in item.get('extract_values', [])}

    # Compare per table
    all_exact = True
    any_correct = False
    details = []
    for table, gold_recs in gold_tables.items():
        pred_recs = pred_groups.get(table, [])
        gold_keys = {_record_key(r) for r in gold_recs}
        pred_keys = {_record_key(r) for r in pred_recs}
        exact = gold_keys == pred_keys
        overlap = len(gold_keys & pred_keys)
        if exact:
            any_correct = True
        elif overlap > 0:
            any_correct = True
            all_exact = False
        else:
            all_exact = False
        details.append(f"{table}: gold={len(gold_recs)} pred={len(pred_recs)} match={overlap} {'EXACT' if exact else 'PARTIAL' if overlap else 'WRONG'}")

    if all_exact:
        status = 'OK  '
        n_correct += 1
    elif any_correct:
        status = 'PART'
        n_partial += 1
    else:
        status = 'FAIL'
        n_wrong += 1

    print(f"[{item_id}] {status}  {' | '.join(details)}")

print(f"\nCorrect (exact): {n_correct}/{total - n_err} ({n_correct/(total-n_err)*100:.1f}%)")
print(f"Partial        : {n_partial}/{total - n_err}")
print(f"Wrong          : {n_wrong}/{total - n_err}")
print(f"Error          : {n_err}/{total}")
