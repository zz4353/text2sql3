"""Generate 10 INSERT test samples into test24.json.
All samples from financial database.
"""
import json

def sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"

def build_insert(table, alias_to_col, records):
    aliases = list(alias_to_col.keys())
    db_cols  = list(alias_to_col.values())
    col_str  = ", ".join(f'"{c}"' for c in db_cols)
    rows = []
    for r in records:
        vals = ", ".join(sql_val(r[a]) for a in aliases)
        rows.append(f"       ({vals})")
    return f'INSERT INTO "{table}" ({col_str})\nVALUES\n' + ',\n'.join(rows) + ';'

samples = []
sid = 1

# ═══════════════════════════════════════════════════════════════════════════
# 1. financial.trans  (4 records)
#    Semantic: interest credited transactions
#    NOT NULL: trans_id, account_id, date, type, amount, balance
#    Optional: k_symbol (UROK for interest)
#    max trans_id=3682987 → use 3710000+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"transaction number": 3710000, "account": 1, "transaction date": "1998-12-31", "direction": "PRIJEM", "amount": 125, "new balance": 10125, "purpose": "UROK"},
    {"transaction number": 3710001, "account": 2, "transaction date": "1998-12-31", "direction": "PRIJEM", "amount": 250, "new balance": 25250, "purpose": "UROK"},
    {"transaction number": 3710002, "account": 3, "transaction date": "1998-12-31", "direction": "PRIJEM", "amount": 180, "new balance": 18180, "purpose": "UROK"},
    {"transaction number": 3710003, "account": 5, "transaction date": "1998-12-31", "direction": "PRIJEM", "amount": 95, "new balance": 9595, "purpose": "UROK"},
]
alias_to_col = {
    "transaction number": "trans_id",
    "account": "account_id",
    "transaction date": "date",
    "direction": "type",
    "amount": "amount",
    "new balance": "balance",
    "purpose": "k_symbol",
}
gold = build_insert("trans", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Record the following year-end interest credit transactions:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 2. financial.trans  (3 records)
#    Semantic: pension income transactions
#    NOT NULL: trans_id, account_id, date, type, amount, balance
#    Optional: operation, k_symbol (DUCHOD for pension)
#    max trans_id=3682987 → use 3710010+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"transaction number": 3710010, "account": 10, "transaction date": "1998-08-01", "direction": "PRIJEM", "method": "PREVOD Z UCTU", "amount": 8500, "new balance": 15200, "purpose": "DUCHOD"},
    {"transaction number": 3710011, "account": 15, "transaction date": "1998-08-01", "direction": "PRIJEM", "method": "PREVOD Z UCTU", "amount": 9200, "new balance": 22400, "purpose": "DUCHOD"},
    {"transaction number": 3710012, "account": 20, "transaction date": "1998-08-01", "direction": "PRIJEM", "method": "PREVOD Z UCTU", "amount": 7800, "new balance": 18900, "purpose": "DUCHOD"},
]
alias_to_col = {
    "transaction number": "trans_id",
    "account": "account_id",
    "transaction date": "date",
    "direction": "type",
    "method": "operation",
    "amount": "amount",
    "new balance": "balance",
    "purpose": "k_symbol",
}
gold = build_insert("trans", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Record the following monthly pension deposits:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 3. financial.trans  (4 records)
#    Semantic: statement fee charges
#    NOT NULL: trans_id, account_id, date, type, amount, balance
#    Optional: k_symbol (SLUZBY for statement fees)
#    max trans_id=3682987 → use 3710020+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"transaction number": 3710020, "account": 1, "transaction date": "1998-09-30", "direction": "VYDAJ", "amount": 15, "new balance": 10110, "purpose": "SLUZBY"},
    {"transaction number": 3710021, "account": 2, "transaction date": "1998-09-30", "direction": "VYDAJ", "amount": 15, "new balance": 25235, "purpose": "SLUZBY"},
    {"transaction number": 3710022, "account": 3, "transaction date": "1998-09-30", "direction": "VYDAJ", "amount": 15, "new balance": 18165, "purpose": "SLUZBY"},
    {"transaction number": 3710023, "account": 5, "transaction date": "1998-09-30", "direction": "VYDAJ", "amount": 15, "new balance": 9580, "purpose": "SLUZBY"},
]
alias_to_col = {
    "transaction number": "trans_id",
    "account": "account_id",
    "transaction date": "date",
    "direction": "type",
    "amount": "amount",
    "new balance": "balance",
    "purpose": "k_symbol",
}
gold = build_insert("trans", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Charge the following monthly statement fees:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 4. financial.loan  (4 records)
#    Semantic: problematic loans with debt status
#    NOT NULL: loan_id, account_id, date, amount, duration, payments, status
#    Focus on status D (running contract, client in debt)
#    max loan_id=7308 → use 7600+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"loan number": 7600, "borrower account": 25, "approval date": "1997-03-15", "loan amount": 150000, "term months": 48, "monthly payment": 3125.0, "repayment status": "D"},
    {"loan number": 7601, "borrower account": 30, "approval date": "1997-06-20", "loan amount": 200000, "term months": 60, "monthly payment": 3333.33, "repayment status": "D"},
    {"loan number": 7602, "borrower account": 35, "approval date": "1997-09-10", "loan amount": 95000, "term months": 36, "monthly payment": 2638.89, "repayment status": "D"},
    {"loan number": 7603, "borrower account": 40, "approval date": "1997-11-25", "loan amount": 180000, "term months": 48, "monthly payment": 3750.0, "repayment status": "B"},
]
alias_to_col = {
    "loan number": "loan_id",
    "borrower account": "account_id",
    "approval date": "date",
    "loan amount": "amount",
    "term months": "duration",
    "monthly payment": "payments",
    "repayment status": "status",
}
gold = build_insert("loan", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Record the following loans with payment issues:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 5. financial.district  (3 records)
#    Semantic: district urban structure (municipalities distribution focus)
#    NOT NULL: district_id, A2-A11, A13, A14, A16
#    Focus on urban/rural composition
#    max district_id=77 → use 83+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {
        "district number": 83,
        "district name": "Karlovy Vary",
        "region": "west Bohemia",
        "population": "124500",
        "municipalities with under 500": "38",
        "municipalities 500-1999": "25",
        "municipalities 2000-9999": "10",
        "cities over 10000": 2,
        "not used": 3,
        "urban ratio": 68.5,
        "average salary": 9800,
        "unemployment 1996": 6.2,
        "entrepreneurs per 1000": 88,
        "crimes 1996": 2450,
    },
    {
        "district number": 84,
        "district name": "Jihlava",
        "region": "south Moravia",
        "population": "108200",
        "municipalities with under 500": "45",
        "municipalities 500-1999": "28",
        "municipalities 2000-9999": "7",
        "cities over 10000": 1,
        "not used": 2,
        "urban ratio": 55.3,
        "average salary": 10100,
        "unemployment 1996": 4.9,
        "entrepreneurs per 1000": 102,
        "crimes 1996": 1890,
    },
    {
        "district number": 85,
        "district name": "Prostějov",
        "region": "north Moravia",
        "population": "95600",
        "municipalities with under 500": "32",
        "municipalities 500-1999": "22",
        "municipalities 2000-9999": "8",
        "cities over 10000": 1,
        "not used": 2,
        "urban ratio": 61.2,
        "average salary": 9400,
        "unemployment 1996": 7.1,
        "entrepreneurs per 1000": 85,
        "crimes 1996": 1620,
    },
]
alias_to_col = {
    "district number": "district_id",
    "district name": "A2",
    "region": "A3",
    "population": "A4",
    "municipalities with under 500": "A5",
    "municipalities 500-1999": "A6",
    "municipalities 2000-9999": "A7",
    "cities over 10000": "A8",
    "not used": "A9",
    "urban ratio": "A10",
    "average salary": "A11",
    "unemployment 1996": "A13",
    "entrepreneurs per 1000": "A14",
    "crimes 1996": "A16",
}
gold = build_insert("district", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Add the following district urban structure data:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 6. financial.client  (5 records)
#    Semantic: senior clients (born 1940s-1950s)
#    NOT NULL: client_id, gender, birth_date, district_id
#    max client_id=13998 → use 14600+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"client number": 14600, "sex": "M", "date of birth": "1945-03-12", "home district": 1},
    {"client number": 14601, "sex": "F", "date of birth": "1948-07-25", "home district": 18},
    {"client number": 14602, "sex": "M", "date of birth": "1952-11-08", "home district": 35},
    {"client number": 14603, "sex": "F", "date of birth": "1950-05-19", "home district": 50},
    {"client number": 14604, "sex": "M", "date of birth": "1947-09-30", "home district": 25},
]
alias_to_col = {
    "client number": "client_id",
    "sex": "gender",
    "date of birth": "birth_date",
    "home district": "district_id",
}
gold = build_insert("client", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Register the following senior clients:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 7. financial.account  (3 records)
#    Semantic: weekly statement accounts
#    NOT NULL: account_id, district_id, frequency, date
#    Focus on POPLATEK TYDNE frequency
#    max account_id=11382 → use 12100+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"account number": 12100, "branch location": 10, "statement frequency": "POPLATEK TYDNE", "opening date": "1998-08-15"},
    {"account number": 12101, "branch location": 25, "statement frequency": "POPLATEK TYDNE", "opening date": "1998-09-20"},
    {"account number": 12102, "branch location": 40, "statement frequency": "POPLATEK TYDNE", "opening date": "1998-10-10"},
]
alias_to_col = {
    "account number": "account_id",
    "branch location": "district_id",
    "statement frequency": "frequency",
    "opening date": "date",
}
gold = build_insert("account", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Open the following accounts with weekly statement frequency:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 8. financial.card  (4 records)
#    Semantic: junior cards for young clients
#    NOT NULL: card_id, disp_id, type, issued
#    Focus on junior card type
#    max card_id=1247 → use 1600+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"card number": 1600, "account holder": 50, "card class": "junior", "issue date": "1998-06-15"},
    {"card number": 1601, "account holder": 55, "card class": "junior", "issue date": "1998-07-20"},
    {"card number": 1602, "account holder": 60, "card class": "junior", "issue date": "1998-08-25"},
    {"card number": 1603, "account holder": 65, "card class": "junior", "issue date": "1998-09-30"},
]
alias_to_col = {
    "card number": "card_id",
    "account holder": "disp_id",
    "card class": "type",
    "issue date": "issued",
}
gold = build_insert("card", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Issue the following junior credit cards:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 9. financial.order  (5 records)
#    Semantic: household utility payment orders
#    NOT NULL: order_id, account_id, bank_to, account_to, amount, k_symbol
#    Focus on SIPO (household) payments
#    max order_id=46338 → use 47100+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"standing order id": 47100, "payer account": 5, "payee bank": "AB", "payee account": 66778899, "monthly amount": 950.0, "payment type": "SIPO"},
    {"standing order id": 47101, "payer account": 10, "payee bank": "CD", "payee account": 77889900, "monthly amount": 1100.0, "payment type": "SIPO"},
    {"standing order id": 47102, "payer account": 15, "payee bank": "EF", "payee account": 88990011, "monthly amount": 850.0, "payment type": "SIPO"},
    {"standing order id": 47103, "payer account": 20, "payee bank": "GH", "payee account": 99001122, "monthly amount": 1250.0, "payment type": "SIPO"},
    {"standing order id": 47104, "payer account": 25, "payee bank": "IJ", "payee account": 10112233, "monthly amount": 1050.0, "payment type": "SIPO"},
]
alias_to_col = {
    "standing order id": "order_id",
    "payer account": "account_id",
    "payee bank": "bank_to",
    "payee account": "account_to",
    "monthly amount": "amount",
    "payment type": "k_symbol",
}
gold = build_insert("order", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Set up the following household utility payment orders:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 10. financial.disp  (5 records)
#     Semantic: authorized users (DISPONENT) for shared accounts
#     NOT NULL: disp_id, client_id, account_id, type
#     Focus on DISPONENT type
#     max disp_id=13690 → use 14300+
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"authorization id": 14300, "client": 5, "account": 1, "relationship": "DISPONENT"},
    {"authorization id": 14301, "client": 10, "account": 2, "relationship": "DISPONENT"},
    {"authorization id": 14302, "client": 15, "account": 3, "relationship": "DISPONENT"},
    {"authorization id": 14303, "client": 20, "account": 5, "relationship": "DISPONENT"},
    {"authorization id": 14304, "client": 25, "account": 10, "relationship": "DISPONENT"},
]
alias_to_col = {
    "authorization id": "disp_id",
    "client": "client_id",
    "account": "account_id",
    "relationship": "type",
}
gold = build_insert("disp", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Add the following authorized users to accounts:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": len(alias_to_col), "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ─── Write output ─────────────────────────────────────────────────────────
with open("test24.json", "w", encoding="utf-8") as f:
    json.dump(samples, f, ensure_ascii=False, indent=4)

print(f"Done — {len(samples)} samples written to test24.json")
for s in samples:
    print(f"  id={s['id']} db={s['db_id']} records={s['metadata']['record_count']} tables={s['metadata']['table_count']} sqls={len(s['gold_sql'])}")
