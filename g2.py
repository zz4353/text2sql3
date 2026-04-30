"""Generate samples 11–20 for test3.json, based on test2.json samples 11–20.
Same table/column structure, ~20 records each, different values.
Run after g1.py — appends to test3.json (or create standalone by changing OUTPUT).
"""
import json

def sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"

def build_or_ignore(table, alias_to_col, records):
    aliases = list(alias_to_col.keys())
    db_cols = list(alias_to_col.values())
    col_str = ", ".join(f'"{c}"' for c in db_cols)
    rows = ["       (" + ", ".join(sql_val(r[a]) for a in aliases) + ")" for r in records]
    return f'INSERT OR IGNORE INTO {table} ({col_str})\nVALUES\n' + ',\n'.join(rows) + ';'

def build_on_conflict(table, alias_to_col, records, conflict_col):
    aliases = list(alias_to_col.keys())
    db_cols = list(alias_to_col.values())
    col_str = ", ".join(f'"{c}"' for c in db_cols)
    rows = ["       (" + ", ".join(sql_val(r[a]) for a in aliases) + ")" for r in records]
    return f'INSERT INTO {table} ({col_str})\nVALUES\n' + ',\n'.join(rows) + f'\nON CONFLICT ({conflict_col}) DO NOTHING;'

def build_insert(table, alias_to_col, records):
    aliases = list(alias_to_col.keys())
    db_cols = list(alias_to_col.values())
    col_str = ", ".join(f'"{c}"' for c in db_cols)
    rows = ["       (" + ", ".join(sql_val(r[a]) for a in aliases) + ")" for r in records]
    return f'INSERT INTO "{table}" ({col_str})\nVALUES\n' + ',\n'.join(rows) + ';'

def build_or_ignore_ids(table, col, ids):
    return f'INSERT OR IGNORE INTO {table} ({col}) VALUES ' + ', '.join(f'({i})' for i in ids) + ';'

samples = []
sid = 11

# ═══════════════════════════════════════════════════════════════════════════
# 11. debit_card_specializing.customers  (20 records) — based on test2 id=89
#     Columns: Currency, CustomerID
#     Format: INSERT INTO customers ... ON CONFLICT (CustomerID) DO NOTHING
#     CustomerID: 16001–16020
# ═══════════════════════════════════════════════════════════════════════════
currencies = ["USD","EUR","GBP","AUD","CAD","CHF","JPY","CNY","SEK","NOK",
              "USD","EUR","GBP","AUD","CAD","CHF","JPY","CNY","SEK","NOK"]
records = [{"currency": currencies[i], "customer id": 16001 + i} for i in range(20)]
alias_to_col = {"currency": "Currency", "customer id": "CustomerID"}
gold = build_on_conflict("customers", alias_to_col, records, "CustomerID")

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following records into the database: " +
        " ".join(f"{i+1}. Currency: {r['currency']}, CustomerID: {r['customer id']}" for i, r in enumerate(records))
    ),
    "metadata": {"record_count": len(records), "column_count": 2, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 12. debit_card_specializing.gasstations  (20 records) — based on test2 id=90
#     Columns: ChainID, GasStationID, Segment
#     Format: INSERT INTO gasstations ... ON CONFLICT (GasStationID) DO NOTHING
#     GasStationID: 2001–2020
# ═══════════════════════════════════════════════════════════════════════════
segs = ["Value for money","Premium","Other","Value for money","Premium",
        "Other","Value for money","Premium","Other","Value for money",
        "Premium","Other","Value for money","Premium","Other",
        "Value for money","Premium","Other","Value for money","Premium"]
chains = [3,7,12,5,18,22,9,14,1,6,11,20,8,15,4,17,2,10,13,19]
records = [{"chain id": chains[i], "gas station id": 2001 + i, "segment": segs[i]} for i in range(20)]
alias_to_col = {"chain id": "ChainID", "gas station id": "GasStationID", "segment": "Segment"}
gold = build_on_conflict("gasstations", alias_to_col, records, "GasStationID")

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please insert the following records into the database:\n\n" +
        str([{"ChainID": r["chain id"], "GasStationID": r["gas station id"], "Segment": r["segment"]} for r in records])
    ),
    "metadata": {"record_count": len(records), "column_count": 3, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 13. debit_card_specializing.gasstations  (20 records) — based on test2 id=99
#     Columns: ChainID, GasStationID, Segment
#     Format: INSERT INTO gasstations ... ON CONFLICT (GasStationID) DO NOTHING
#     GasStationID: 3001–3020
# ═══════════════════════════════════════════════════════════════════════════
segs2  = ["Premium","Value for money","Other","Premium","Value for money",
          "Other","Premium","Other","Value for money","Premium",
          "Value for money","Other","Premium","Value for money","Other",
          "Premium","Value for money","Other","Premium","Value for money"]
chains2= [8,3,15,21,6,11,17,2,9,14,4,20,7,12,1,18,5,13,22,10]
records = [{"chain id": chains2[i], "gas station id": 3001 + i, "segment": segs2[i]} for i in range(20)]
alias_to_col = {"chain id": "ChainID", "gas station id": "GasStationID", "segment": "Segment"}
gold = build_on_conflict("gasstations", alias_to_col, records, "GasStationID")

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following gas station records to the database:\n\n" +
        " ".join(
            f"{i+1}. Gas Station ID {r['gas station id']}, Chain ID {r['chain id']}, Segment \"{r['segment']}\""
            for i, r in enumerate(records)
        )
    ),
    "metadata": {"record_count": len(records), "column_count": 3, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 14. european_football_2 — 2 tables — based on test2 id=108
#     Table 1: Player (player_api_id) — INSERT OR IGNORE, inline
#     Table 2: Player_Attributes (overall_rating, player_api_id, potential)
#     20 players
# ═══════════════════════════════════════════════════════════════════════════
player_ids = [300001,300002,300003,300004,300005,300006,300007,300008,300009,300010,
              300011,300012,300013,300014,300015,300016,300017,300018,300019,300020]
ratings    = [82,76,88,71,84,79,90,73,85,77,83,68,87,75,81,70,86,74,89,72]
potentials = [88,82,93,78,89,85,95,80,91,83,88,75,92,81,87,77,91,80,94,79]

gold_player = build_or_ignore_ids("Player", "player_api_id", player_ids)

pa_records = [{"rating": ratings[i], "pid": player_ids[i], "potential": potentials[i]} for i in range(20)]
alias_pa = {"rating": "overall_rating", "pid": "player_api_id", "potential": "potential"}
gold_pa = build_insert("Player_Attributes", alias_pa, pa_records)

samples.append({
    "db_id": "european_football_2",
    "user_request": (
        "Please add the following records into the database: " +
        " ".join(
            f"{i+1}. player api id: {player_ids[i]}, potential: {potentials[i]}, overall rating: {ratings[i]}"
            for i in range(20)
        )
    ),
    "metadata": {"record_count": len(player_ids), "column_count": 3, "table_count": 2, "output_format": "list"},
    "gold_sql": [gold_player, gold_pa],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 15. financial.district  (5 records) — based on test2 id=120
#     All columns, format: INSERT OR IGNORE INTO district
#     district_id: 91–95
# ═══════════════════════════════════════════════════════════════════════════
dist_records = [
    {"A5":"35","A4":"88600","district_id":91,"A2":"Bruntál","A3":"north Moravia",
     "A6":"22","A7":"7","A8":1,"A9":3,"A10":47.2,"A11":8800,"A13":10.1,"A14":71,"A16":1540},
    {"A5":"28","A4":"72400","district_id":92,"A2":"Jeseník","A3":"north Moravia",
     "A6":"15","A7":"4","A8":1,"A9":2,"A10":41.8,"A11":8500,"A13":11.3,"A14":65,"A16":1210},
    {"A5":"19","A4":"156700","district_id":93,"A2":"Pardubice","A3":"east Bohemia",
     "A6":"32","A7":"11","A8":2,"A9":4,"A10":66.4,"A11":10300,"A13":4.2,"A14":108,"A16":2890},
    {"A5":"23","A4":"134200","district_id":94,"A2":"Havlíčkův Brod","A3":"east Bohemia",
     "A6":"29","A7":"8","A8":1,"A9":3,"A10":55.7,"A11":9700,"A13":5.6,"A14":96,"A16":2240},
    {"A5":"31","A4":"118500","district_id":95,"A2":"Cheb","A3":"west Bohemia",
     "A6":"18","A7":"6","A8":1,"A9":2,"A10":69.3,"A11":9500,"A13":6.9,"A14":89,"A16":2010},
]
alias_to_col = {
    "A5":"A5","A4":"A4","district_id":"district_id","A2":"A2","A3":"A3",
    "A6":"A6","A7":"A7","A8":"A8","A9":"A9","A10":"A10",
    "A11":"A11","A13":"A13","A14":"A14","A16":"A16",
}
gold = build_or_ignore("district", alias_to_col, dist_records)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Please add the following records to the database:\n\n"
        f"```json\n{json.dumps(dist_records, ensure_ascii=False, indent=2)}\n```"
    ),
    "metadata": {"record_count": len(dist_records), "column_count": 14, "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 16. debit_card_specializing.transactions_1k  (20 records) — based on test2 id=122
#     Columns: Price, TransactionID, Amount
#     Format: INSERT OR IGNORE INTO transactions_1k
#     TransactionID: 301–320
# ═══════════════════════════════════════════════════════════════════════════
records = [
    {"price": 199.99, "txn id": 301, "amount": 2},
    {"price": 49.50,  "txn id": 302, "amount": 5},
    {"price": 875.00, "txn id": 303, "amount": 1},
    {"price": 32.25,  "txn id": 304, "amount": 8},
    {"price": 420.00, "txn id": 305, "amount": 3},
    {"price": 67.75,  "txn id": 306, "amount": 4},
    {"price": 1200.00,"txn id": 307, "amount": 1},
    {"price": 15.99,  "txn id": 308, "amount": 10},
    {"price": 540.50, "txn id": 309, "amount": 2},
    {"price": 88.00,  "txn id": 310, "amount": 3},
    {"price": 260.00, "txn id": 311, "amount": 2},
    {"price": 73.25,  "txn id": 312, "amount": 6},
    {"price": 950.00, "txn id": 313, "amount": 1},
    {"price": 41.00,  "txn id": 314, "amount": 7},
    {"price": 315.75, "txn id": 315, "amount": 2},
    {"price": 128.50, "txn id": 316, "amount": 4},
    {"price": 690.00, "txn id": 317, "amount": 1},
    {"price": 25.99,  "txn id": 318, "amount": 9},
    {"price": 480.00, "txn id": 319, "amount": 2},
    {"price": 105.00, "txn id": 320, "amount": 3},
]
alias_to_col = {"price": "Price", "txn id": "TransactionID", "amount": "Amount"}
gold = build_or_ignore("transactions_1k", alias_to_col, records)

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following records to the database:\n\n"
        f"```json\n{json.dumps([{'Price':r['price'],'Amount':r['amount'],'TransactionID':r['txn id']} for r in records], indent=2)}\n```"
    ),
    "metadata": {"record_count": len(records), "column_count": 3, "table_count": 1, "output_format": "json"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 17. formula_1.status  (20 records) — based on test2 id=131
#     Columns: statusId, status
#     Format: INSERT OR IGNORE INTO status
#     statusId: 20–39
# ═══════════════════════════════════════════════════════════════════════════
status_names = [
    "Queued","Processing","Dispatched","Delivered","Returned",
    "Cancelled","Refunded","Partially Delivered","Backordered","On Route",
    "Held","Released","Escalated","Investigating","Resolved",
    "Archived","Transferred","Merged","Split","Voided",
]
records = [{"status id": 20 + i, "status name": status_names[i]} for i in range(20)]
alias_to_col = {"status id": "statusId", "status name": "status"}
gold = build_or_ignore("status", alias_to_col, records)

samples.append({
    "db_id": "formula_1",
    "user_request": (
        "Please proceed with the batch import of the following status records into the database:\n\n" +
        " ".join(f"status ID {r['status id']}, status {r['status name']};" for r in records)
    ),
    "metadata": {"record_count": len(records), "column_count": 2, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 18. debit_card_specializing — 2 tables — based on test2 id=132
#     Table 1: customers (CustomerID) — INSERT OR IGNORE, inline
#     Table 2: yearmonth (Date, CustomerID)
#     20 records
# ═══════════════════════════════════════════════════════════════════════════
cids_18 = [22001,22002,22003,22004,22005,22006,22007,22008,22009,22010,
           22011,22012,22013,22014,22015,22016,22017,22018,22019,22020]
months  = [f"2015{m:02d}" for m in range(1, 13)] + [f"2016{m:02d}" for m in range(1, 9)]

gold_cust = build_or_ignore_ids("customers", "CustomerID", cids_18)

ym_records = [{"date": months[i], "customer id": cids_18[i]} for i in range(20)]
alias_ym = {"date": "Date", "customer id": "CustomerID"}
gold_ym = build_insert("yearmonth", alias_ym, ym_records)

samples.append({
    "db_id": "debit_card_specializing",
    "user_request": (
        "Please add the following records to the database:\n\n"
        f"```json\n{json.dumps([{'CustomerID':cids_18[i],'Date':months[i]} for i in range(20)], indent=2)}\n```"
    ),
    "metadata": {"record_count": len(cids_18), "column_count": 2, "table_count": 2, "output_format": "json"},
    "gold_sql": [gold_cust, gold_ym],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 19. formula_1.status  (20 records) — based on test2 id=139
#     Columns: statusId, status
#     Format: INSERT OR IGNORE INTO status
#     statusId: 40–59
# ═══════════════════════════════════════════════════════════════════════════
status_names2 = [
    "In Review","Submitted","Acknowledged","Forwarded","Reassigned",
    "Suspended","Reactivated","Closed","Reopened","Flagged",
    "Verified","Rejected","Appealed","Under Audit","Cleared",
    "Blocked","Unblocked","Deferred","Expedited","Finalized",
]
records = [{"status id": 40 + i, "status name": status_names2[i]} for i in range(20)]
alias_to_col = {"status id": "statusId", "status name": "status"}
gold = build_or_ignore("status", alias_to_col, records)

samples.append({
    "db_id": "formula_1",
    "user_request": (
        "Please proceed to insert the following records into the database: " +
        " ".join(f"status ID {r['status id']}, status {r['status name']};" for r in records)
    ),
    "metadata": {"record_count": len(records), "column_count": 2, "table_count": 1, "output_format": "list"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ═══════════════════════════════════════════════════════════════════════════
# 20. financial.district  (5 records) — based on test2 id=148
#     All columns, format: INSERT OR IGNORE INTO district
#     Column order: A3,A2,A11,district_id,A4,A5,A6,A7,A8,A9,A10,A13,A14,A16
#     district_id: 96–100
# ═══════════════════════════════════════════════════════════════════════════
dist_records2 = [
    {"A3":"Prague","A2":"Prague 5","A11":14500,"district_id":96,"A4":"1350000",
     "A5":"8","A6":"28","A7":"18","A8":4,"A9":8,"A10":82.3,"A13":1.1,"A14":165,"A16":12500},
    {"A3":"central Bohemia","A2":"Mladá Boleslav","A11":11200,"district_id":97,"A4":"124000",
     "A5":"18","A6":"22","A7":"9","A8":2,"A9":4,"A10":58.9,"A13":3.8,"A14":119,"A16":2650},
    {"A3":"south Bohemia","A2":"Písek","A11":9800,"district_id":98,"A4":"70400",
     "A5":"30","A6":"16","A7":"5","A8":1,"A9":2,"A10":49.1,"A13":5.2,"A14":87,"A16":1380},
    {"A3":"west Bohemia","A2":"Sokolov","A11":9100,"district_id":99,"A4":"96200",
     "A5":"22","A6":"14","A7":"6","A8":1,"A9":3,"A10":62.5,"A13":8.7,"A14":76,"A16":1920},
    {"A3":"north Bohemia","A2":"Děčín","A11":9600,"district_id":100,"A4":"133700",
     "A5":"27","A6":"19","A7":"8","A8":2,"A9":3,"A10":67.4,"A13":7.3,"A14":83,"A16":2480},
]
alias_to_col = {
    "A3":"A3","A2":"A2","A11":"A11","district_id":"district_id","A4":"A4",
    "A5":"A5","A6":"A6","A7":"A7","A8":"A8","A9":"A9",
    "A10":"A10","A13":"A13","A14":"A14","A16":"A16",
}
gold = build_or_ignore("district", alias_to_col, dist_records2)

samples.append({
    "db_id": "financial",
    "user_request": (
        "Please add the following records to the database:\n\n"
        " | " + " | ".join(["A5","A11","A3","A10","A2","A14","A4","A6","A7","A8","A9","A13","district_id","A16"]) + " |\n" +
        " | " + " | ".join(["---"]*14) + " |\n" +
        "\n".join(
            f" | {r['A5']} | {r['A11']} | {r['A3']} | {r['A10']} | {r['A2']} | {r['A14']} | {r['A4']} | {r['A6']} | {r['A7']} | {r['A8']} | {r['A9']} | {r['A13']} | {r['district_id']} | {r['A16']} |"
            for r in dist_records2
        )
    ),
    "metadata": {"record_count": len(dist_records2), "column_count": 14, "table_count": 1, "output_format": "table"},
    "gold_sql": [gold],
    "id": sid,
})
sid += 1

# ─── Write output ──────────────────────────────────────────────────────────
with open("test3.json", "r", encoding="utf-8") as f:
    existing = json.load(f)

existing.extend(samples)

with open("test3.json", "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"Done — appended {len(samples)} samples to test3.json (total: {len(existing)})")
for s in samples:
    print(f"  id={s['id']} db={s['db_id']} records={s['metadata']['record_count']} tables={s['metadata']['table_count']} sqls={len(s['gold_sql'])}")
