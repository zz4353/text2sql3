"""Generate test3.json — 10 variations of the first 10 samples in test2.json.
Same table/column structure, ~20 records each, different values.
"""
import json

def sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"

def build_insert(table, alias_to_col, records):
    """INSERT INTO "table" ("col") VALUES\n       (...);"""
    aliases = list(alias_to_col.keys())
    db_cols = list(alias_to_col.values())
    col_str = ", ".join(f'"{c}"' for c in db_cols)
    rows = ["       (" + ", ".join(sql_val(r[a]) for a in aliases) + ")" for r in records]
    return f'INSERT INTO "{table}" ({col_str})\nVALUES\n' + ',\n'.join(rows) + ';'

def build_or_ignore(table, alias_to_col, records):
    """INSERT OR IGNORE INTO table ("col") VALUES\n       (...);"""
    aliases = list(alias_to_col.keys())
    db_cols = list(alias_to_col.values())
    col_str = ", ".join(f'"{c}"' for c in db_cols)
    rows = ["       (" + ", ".join(sql_val(r[a]) for a in aliases) + ")" for r in records]
    return f'INSERT OR IGNORE INTO {table} ({col_str})\nVALUES\n' + ',\n'.join(rows) + ';'

def build_on_conflict(table, alias_to_col, records, conflict_col):
    """INSERT INTO table ("col") VALUES\n       (...)\nON CONFLICT (col) DO NOTHING;"""
    aliases = list(alias_to_col.keys())
    db_cols = list(alias_to_col.values())
    col_str = ", ".join(f'"{c}"' for c in db_cols)
    rows = ["       (" + ", ".join(sql_val(r[a]) for a in aliases) + ")" for r in records]
    return f'INSERT INTO {table} ({col_str})\nVALUES\n' + ',\n'.join(rows) + f'\nON CONFLICT ({conflict_col}) DO NOTHING;'

def build_or_ignore_ids(table, col, ids):
    """INSERT OR IGNORE INTO table (col) VALUES (id1), (id2), ...;"""
    return f'INSERT OR IGNORE INTO {table} ({col}) VALUES ' + ', '.join(f'({i})' for i in ids) + ';'

samples = []
sid = 1

# ═══════════════════════════════════════════════════════════════════════════
# 1. debit_card_specializing.customers  (20 records) — based on test2 id=3
#    Columns: Segment, CustomerID
#    Format: INSERT INTO customers ... ON CONFLICT (CustomerID) DO NOTHING
#    CustomerID range: 14001–14020
# ═══════════════════════════════════════════════════════════════════════════
segs = ["SME", "LAM", "KAM", "SME", "LAM", "SME", "KAM", "LAM", "SME", "LAM",
        "KAM", "SME", "LAM", "SME", "KAM", "LAM", "SME", "LAM", "KAM", "SME"]
records = [{"segment": segs[i], "customer id": 14001 + i} for i in range(20)]
alias_to_col = {"segment": "Segment", "customer id": "CustomerID"}
gold = build_on_conflict("customers", alias_to_col, records, "CustomerID")

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following customer records to the database:\n\n"
        "Segment,CustomerID\n" +
        "\n".join(f"{r['segment']},{r['customer id']}" for r in records)
    ),
    "metadata": {"record_count": len(records), "column_count": 2, "table_count": 1, "output_format": "csv"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 2. student_club.zip_code  (20 records) — based on test2 id=11
#    Columns: city, zip_code, state, county
#    Format: INSERT OR IGNORE INTO zip_code
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"city": "Albuquerque", "zip": 87101, "state": "New Mexico",     "county": "Bernalillo County"},
    {"city": "Spokane",      "zip": 99201, "state": "Washington",     "county": "Spokane County"},
    {"city": "Tacoma",       "zip": 98401, "state": "Washington",     "county": "Pierce County"},
    {"city": "Aurora",       "zip": 80010, "state": "Colorado",       "county": "Arapahoe County"},
    {"city": "Anaheim",      "zip": 92801, "state": "California",     "county": "Orange County"},
    {"city": "Santa Ana",    "zip": 92701, "state": "California",     "county": "Orange County"},
    {"city": "Corpus Christi","zip":78401, "state": "Texas",          "county": "Nueces County"},
    {"city": "Riverside",    "zip": 92501, "state": "California",     "county": "Riverside County"},
    {"city": "Lexington",    "zip": 40501, "state": "Kentucky",       "county": "Fayette County"},
    {"city": "St. Louis",    "zip": 63101, "state": "Missouri",       "county": "St. Louis City"},
    {"city": "Pittsburgh",   "zip": 15201, "state": "Pennsylvania",   "county": "Allegheny County"},
    {"city": "Stockton",     "zip": 95201, "state": "California",     "county": "San Joaquin County"},
    {"city": "St. Paul",     "zip": 55101, "state": "Minnesota",      "county": "Ramsey County"},
    {"city": "Greensboro",   "zip": 27401, "state": "North Carolina", "county": "Guilford County"},
    {"city": "Lincoln",      "zip": 68501, "state": "Nebraska",       "county": "Lancaster County"},
    {"city": "Plano",        "zip": 75023, "state": "Texas",          "county": "Collin County"},
    {"city": "Henderson",    "zip": 89002, "state": "Nevada",         "county": "Clark County"},
    {"city": "Buffalo",      "zip": 14201, "state": "New York",       "county": "Erie County"},
    {"city": "Fort Wayne",   "zip": 46801, "state": "Indiana",        "county": "Allen County"},
    {"city": "Jersey City",  "zip": 7302,  "state": "New Jersey",     "county": "Hudson County"},
]
alias_to_col = {"city": "city", "zip": "zip_code", "state": "state", "county": "county"}
gold = build_or_ignore("zip_code", alias_to_col, records)

samples.append({
    "db_id": "student_club",
    "user_request": (
        "Please proceed to import the following records into the database:\n\n"
        "county,zip code,city,state\n" +
        "\n".join(f"{r['county']},{r['zip']},{r['city']},{r['state']}" for r in records)
    ),
    "metadata": {"record_count": len(records), "column_count": 4, "table_count": 1, "output_format": "csv"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 3. debit_card_specializing.customers  (20 records) — based on test2 id=12
#    Columns: Currency, Segment, CustomerID
#    Format: INSERT INTO customers ... ON CONFLICT (CustomerID) DO NOTHING
#    CustomerID range: 15001–15020
# ═══════════════════════════════════════════════════════════════════════════
currencies = ["CZK","EUR","EUR","CZK","CZK","EUR","CZK","EUR","CZK","EUR",
              "CZK","EUR","CZK","EUR","EUR","CZK","EUR","CZK","EUR","CZK"]
segs2      = ["SME","LAM","SME","LAM","KAM","SME","LAM","KAM","SME","LAM",
              "KAM","SME","LAM","SME","LAM","KAM","SME","LAM","SME","KAM"]
records = [{"currency": currencies[i], "segment": segs2[i], "customer id": 15001 + i} for i in range(20)]
alias_to_col = {"currency": "Currency", "segment": "Segment", "customer id": "CustomerID"}
gold = build_on_conflict("customers", alias_to_col, records, "CustomerID")

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following records to the database:\n\n" +
        "\n".join(
            f"- Currency: {r['currency']}, CustomerID: {r['customer id']}, Segment: {r['segment']};"
            for r in records
        )
    ),
    "metadata": {"record_count": len(records), "column_count": 3, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 4. financial.account  (20 records) — based on test2 id=21
#    Columns: district_id, account_id, frequency, date
#    Format: INSERT OR IGNORE INTO account
#    account_id: 200–219
# ═══════════════════════════════════════════════════════════════════════════
freqs = ["POPLATEK MESICNE","POPLATEK TYDNE","POPLATEK PO OBRATU","POPLATEK MESICNE",
         "POPLATEK TYDNE","POPLATEK MESICNE","POPLATEK PO OBRATU","POPLATEK MESICNE",
         "POPLATEK TYDNE","POPLATEK MESICNE","POPLATEK MESICNE","POPLATEK TYDNE",
         "POPLATEK PO OBRATU","POPLATEK MESICNE","POPLATEK TYDNE","POPLATEK MESICNE",
         "POPLATEK PO OBRATU","POPLATEK MESICNE","POPLATEK TYDNE","POPLATEK MESICNE"]
dists = [5,12,20,7,33,1,45,18,9,27,3,14,22,40,6,29,11,35,8,16]
dates = ["1993-03-10","1994-06-22","1995-08-05","1996-01-30","1996-11-15",
         "1997-02-28","1997-07-14","1997-10-01","1998-03-25","1998-05-19",
         "1998-06-08","1998-07-31","1998-09-04","1998-10-17","1998-11-22",
         "1999-01-09","1999-04-03","1999-07-20","1999-09-11","2000-02-14"]
records = [
    {"district id": dists[i], "account id": 200 + i, "frequency": freqs[i], "date": dates[i]}
    for i in range(20)
]
alias_to_col = {"district id": "district_id", "account id": "account_id", "frequency": "frequency", "date": "date"}
gold = build_or_ignore("account", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Please add the following records to the database:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": 4, "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 5. financial.district  (5 records) — based on test2 id=23
#    All columns: district_id, A2–A16
#    Format: INSERT INTO "district" (standard build_insert)
#    district_id: 86–90
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"district number": 86, "district name": "Liberec",   "region": "north Bohemia",
     "population": "103400", "municipalities with under 500": "41",
     "municipalities 500-1999": "20", "municipalities 2000-9999": "8",
     "cities over 10000": 2, "not used": 3, "urban ratio": 72.1,
     "average salary": 10200, "unemployment 1996": 5.8, "entrepreneurs per 1000": 94, "crimes 1996": 2310},
    {"district number": 87, "district name": "Opava",     "region": "north Moravia",
     "population": "177200", "municipalities with under 500": "52",
     "municipalities 500-1999": "30", "municipalities 2000-9999": "12",
     "cities over 10000": 3, "not used": 4, "urban ratio": 58.4,
     "average salary": 9600, "unemployment 1996": 8.3, "entrepreneurs per 1000": 79, "crimes 1996": 3150},
    {"district number": 88, "district name": "Znojmo",    "region": "south Moravia",
     "population": "113600", "municipalities with under 500": "67",
     "municipalities 500-1999": "35", "municipalities 2000-9999": "6",
     "cities over 10000": 1, "not used": 2, "urban ratio": 44.7,
     "average salary": 8900, "unemployment 1996": 9.1, "entrepreneurs per 1000": 73, "crimes 1996": 1740},
    {"district number": 89, "district name": "Nový Jičín","region": "north Moravia",
     "population": "152300", "municipalities with under 500": "44",
     "municipalities 500-1999": "27", "municipalities 2000-9999": "10",
     "cities over 10000": 2, "not used": 3, "urban ratio": 63.9,
     "average salary": 10500, "unemployment 1996": 6.7, "entrepreneurs per 1000": 88, "crimes 1996": 2640},
    {"district number": 90, "district name": "Vsetín",    "region": "north Moravia",
     "population": "145800", "municipalities with under 500": "38",
     "municipalities 500-1999": "24", "municipalities 2000-9999": "9",
     "cities over 10000": 2, "not used": 2, "urban ratio": 60.2,
     "average salary": 9300, "unemployment 1996": 7.5, "entrepreneurs per 1000": 81, "crimes 1996": 2080},
]
alias_to_col = {
    "district number": "district_id", "district name": "A2", "region": "A3",
    "population": "A4", "municipalities with under 500": "A5",
    "municipalities 500-1999": "A6", "municipalities 2000-9999": "A7",
    "cities over 10000": "A8", "not used": "A9", "urban ratio": "A10",
    "average salary": "A11", "unemployment 1996": "A13",
    "entrepreneurs per 1000": "A14", "crimes 1996": "A16",
}
gold = build_insert("district", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Add the following district urban structure data:\n\n"
        f"```json\n{json.dumps(records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": 14, "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 6. financial.disp  (20 records) — based on test2 id=43
#    Columns: type, disp_id, account_id, client_id
#    Format: INSERT OR IGNORE INTO disp
#    disp_id: 15001–15020
# ═══════════════════════════════════════════════════════════════════════════
types  = ["OWNER","DISPONENT","OWNER","OWNER","DISPONENT","OWNER","DISPONENT","OWNER","OWNER","DISPONENT",
          "OWNER","DISPONENT","OWNER","OWNER","DISPONENT","OWNER","DISPONENT","OWNER","OWNER","DISPONENT"]
accs   = [200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219]
clis   = [15000,15001,15002,15003,15004,15005,15006,15007,15008,15009,
          15010,15011,15012,15013,15014,15015,15016,15017,15018,15019]
records = [
    {"relationship": types[i], "disp id": 15001 + i, "account id": accs[i], "client id": clis[i]}
    for i in range(20)
]
alias_to_col = {"relationship": "type", "disp id": "disp_id", "account id": "account_id", "client id": "client_id"}
gold = build_or_ignore("disp", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Please insert the following records into the database: " +
        " ".join(
            f"{i+1}. type: {r['relationship']}, account id: {r['account id']}, "
            f"client id: {r['client id']}, disp id: {r['disp id']}"
            for i, r in enumerate(records)
        )
    ),
    "metadata": {"record_count": len(records), "column_count": 4, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 7. financial.client  (20 records) — based on test2 id=46
#    Columns: birth_date, gender, district_id, client_id
#    Format: INSERT OR IGNORE INTO client
#    client_id: 15000–15019
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"birth date": "1988-02-14", "client id": 15000, "district id": 5,  "sex": "F"},
    {"birth date": "1975-08-30", "client id": 15001, "district id": 12, "sex": "M"},
    {"birth date": "1992-11-05", "client id": 15002, "district id": 20, "sex": "F"},
    {"birth date": "1983-04-22", "client id": 15003, "district id": 7,  "sex": "M"},
    {"birth date": "1969-07-18", "client id": 15004, "district id": 33, "sex": "F"},
    {"birth date": "1995-01-09", "client id": 15005, "district id": 1,  "sex": "M"},
    {"birth date": "1980-06-27", "client id": 15006, "district id": 45, "sex": "F"},
    {"birth date": "1971-03-14", "client id": 15007, "district id": 18, "sex": "M"},
    {"birth date": "1987-09-03", "client id": 15008, "district id": 9,  "sex": "F"},
    {"birth date": "1963-12-25", "client id": 15009, "district id": 27, "sex": "M"},
    {"birth date": "1991-05-11", "client id": 15010, "district id": 3,  "sex": "F"},
    {"birth date": "1978-10-08", "client id": 15011, "district id": 14, "sex": "M"},
    {"birth date": "1985-07-29", "client id": 15012, "district id": 22, "sex": "F"},
    {"birth date": "1967-02-16", "client id": 15013, "district id": 40, "sex": "M"},
    {"birth date": "1993-08-20", "client id": 15014, "district id": 6,  "sex": "F"},
    {"birth date": "1976-04-04", "client id": 15015, "district id": 29, "sex": "M"},
    {"birth date": "1989-11-17", "client id": 15016, "district id": 11, "sex": "F"},
    {"birth date": "1972-06-12", "client id": 15017, "district id": 35, "sex": "M"},
    {"birth date": "1984-01-28", "client id": 15018, "district id": 8,  "sex": "F"},
    {"birth date": "1960-09-06", "client id": 15019, "district id": 16, "sex": "M"},
]
alias_to_col = {"birth date": "birth_date", "sex": "gender", "district id": "district_id", "client id": "client_id"}
gold = build_or_ignore("client", alias_to_col, records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Please insert the following records into the database: \n\n" +
        str([{k: v for k, v in r.items()} for r in records])
    ),
    "metadata": {"record_count": len(records), "column_count": 4, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 8. debit_card_specializing.customers  (20 records) — based on test2 id=48
#    Column: CustomerID only
#    Format: INSERT OR IGNORE INTO customers (CustomerID) VALUES (id1), ...
#    Table format user_request
# ═══════════════════════════════════════════════════════════════════════════
cids_8 = [20001,20002,20003,20004,20005,20006,20007,20008,20009,20010,
          20011,20012,20013,20014,20015,20016,20017,20018,20019,20020]
gold = build_or_ignore_ids("customers", "CustomerID", cids_8)

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following records to the database:\n\n"
        "| CustomerID |\n"
        "| ---------- |\n" +
        "\n".join(f"| {c}      |" for c in cids_8)
    ),
    "metadata": {"record_count": len(cids_8), "column_count": 1, "table_count": 1, "output_format": "table"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 9. debit_card_specializing.customers  (20 records) — based on test2 id=55
#    Column: CustomerID only (via Consumption/Date dict, only CustomerID extracted)
#    Format: INSERT OR IGNORE INTO customers (CustomerID) VALUES (id1), ...
# ═══════════════════════════════════════════════════════════════════════════
cids_9 = [21001,21002,21003,21004,21005,21006,21007,21008,21009,21010,
          21011,21012,21013,21014,21015,21016,21017,21018,21019,21020]
gold = build_or_ignore_ids("customers", "CustomerID", cids_9)

raw_records = [
    {"Consumption": round(500 + i * 37.5, 2), "CustomerID": cids_9[i], "Date": f"2014{(i%12+1):02d}"}
    for i in range(20)
]
samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please insert the following records into the database: \n\n" +
        str(raw_records)
    ),
    "metadata": {"record_count": len(cids_9), "column_count": 1, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 10. debit_card_specializing.transactions_1k  (20 records) — based on test2 id=88
#     Columns: Price, TransactionID, Amount
#     Format: INSERT OR IGNORE INTO transactions_1k
#     TransactionID: 201–220
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"transaction id": 201, "amount": 3, "price": 89.99},
    {"transaction id": 202, "amount": 1, "price": 450.00},
    {"transaction id": 203, "amount": 5, "price": 22.50},
    {"transaction id": 204, "amount": 2, "price": 175.75},
    {"transaction id": 205, "amount": 4, "price": 60.00},
    {"transaction id": 206, "amount": 1, "price": 999.99},
    {"transaction id": 207, "amount": 6, "price": 35.25},
    {"transaction id": 208, "amount": 2, "price": 210.00},
    {"transaction id": 209, "amount": 3, "price": 125.50},
    {"transaction id": 210, "amount": 1, "price": 680.00},
    {"transaction id": 211, "amount": 7, "price": 18.99},
    {"transaction id": 212, "amount": 2, "price": 340.00},
    {"transaction id": 213, "amount": 4, "price": 75.00},
    {"transaction id": 214, "amount": 1, "price": 550.50},
    {"transaction id": 215, "amount": 3, "price": 99.00},
    {"transaction id": 216, "amount": 5, "price": 44.75},
    {"transaction id": 217, "amount": 2, "price": 280.00},
    {"transaction id": 218, "amount": 1, "price": 720.25},
    {"transaction id": 219, "amount": 4, "price": 55.00},
    {"transaction id": 220, "amount": 2, "price": 160.00},
]
alias_to_col = {"price": "Price", "transaction id": "TransactionID", "amount": "Amount"}
gold = build_or_ignore("transactions_1k", alias_to_col, records)

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following transactions to the database: \n\n" +
        " ".join(
            f"{i+1}. Transaction ID {r['transaction id']} with an amount of {r['amount']} and a price of {r['price']}"
            for i, r in enumerate(records)
        )
    ),
    "metadata": {"record_count": len(records), "column_count": 3, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ─── Write output ──────────────────────────────────────────────────────────
with open("test3.json", "w", encoding="utf-8") as f:
    json.dump(samples, f, ensure_ascii=False, indent=2)

print(f"Done — {len(samples)} samples written to test3.json")
for s in samples:
    print(f"  id={s['id']} db={s['db_id']} records={s['metadata']['record_count']} cols={s['metadata']['column_count']} sqls={len(s['gold_sql'])}")
