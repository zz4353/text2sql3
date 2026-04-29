from db_client import get_table_info, DB_ID, clone_db_to_memory
from collections import defaultdict, Counter

def sort_columns_and_values(columns, values):
    sorted_pairs = sorted(enumerate(columns), key=lambda x: x[1])

    new_columns = [col for _, col in sorted_pairs]

    order = [idx for idx, _ in sorted_pairs]
    new_values = []
    for row in values:
        new_row = [row[i] for i in order]
        new_values.append(new_row)

    return new_columns, new_values

def snapshot_database(conn):
    cursor = conn.cursor()
    state = {}
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%';
    """)

    table_names = [row[0] for row in cursor.fetchall()]

    for table in table_names:
        state[table] = {}
        cursor.execute(f'SELECT * FROM "{table}"')
        columns = [desc[0] for desc in cursor.description]
        values = cursor.fetchall()
        state[table]['columns'], state[table]['values'] = sort_columns_and_values(columns, values)

    return state


def run_sqls_and_dump_state(sqls, db_id):
    mem_conn = clone_db_to_memory(db_id)
    cursor = mem_conn.cursor()

    for sql in sqls:
        try:
            cursor.execute(sql)
            mem_conn.commit()
        except Exception as e:
            mem_conn.close()
            return None, e

    state = snapshot_database(mem_conn)
    mem_conn.close()
    return state, None


def compare_sqls(gold_sqls, pred_sqls, db_id):
    gold_state, gold_err = run_sqls_and_dump_state(gold_sqls, db_id)
    pred_state, pred_err = run_sqls_and_dump_state(pred_sqls, db_id)

    if pred_err is not None:
        return False, f"pred_sqls lỗi: {pred_err}"

    if gold_err is not None:
        return False, f"gold_sqls lỗi: {gold_err}"

    if set(gold_state.keys()) != set(pred_state.keys()):
        return False, f"Khác tập bảng: {set(gold_state.keys())} != {set(pred_state.keys())}"

    for table in gold_state:
        gold_cols = gold_state[table]['columns']
        pred_cols = pred_state[table]['columns']

        if gold_cols != pred_cols:
            return False, f"Bảng '{table}': khác cột {gold_cols} != {pred_cols}"

        gold_values = gold_state[table]['values']
        pred_values = pred_state[table]['values']

        if Counter(map(tuple, gold_values)) != Counter(map(tuple, pred_values)):
            return False, f"Bảng '{table}': khác values"

    return True, None



































# snapshot trước và sau khi hoàn thành insert. (dữ liệu có cả rowid)
# sau đó lấy ra các rowid bị ảnh hưởng -> ok (khác với bản lúc trước).
# row giữ nguyên, bị xóa, bị thay đổi, thêm mới.

# chỉ xét các rowid bị ảnh hưởng, không xét các rowid khác.
# xử lý để mapping dữ liệu...
# xử lý phần bị ảnh hưởng bởi trigger riêng...

# Lấy tập rowid bị ảnh hưởng bởi câu lệnh.
# Lấy dữ liệu từ các rowid này -> tập dữ liệu từ pred sql và tập từ gold sql
# So sánh 2 tập dữ liệu này:
# Duyệt vòng for từng rowid:
#     - Nếu dữ liệu của rowid trùng nhau -> bỏ qua. 
#     - Nếu dữ liệu của rowid khác nhau -> Lưu lại vào tập khác nhau.

# Loại bỏ các cột timestamp, auto generate,...
# bỏ qua phần rowid ở tập còn lại, bắt đầu so sánh dữ liệu...