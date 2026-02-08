import os
import sqlite3
import pandas as pd

DB_NAME = "score.db"
DATA_DIR = "File"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

def table_exists(table_name):
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

for filename in os.listdir(DATA_DIR):
    if not filename.endswith(".xlsx"):
        continue

    grade = filename.replace(".xlsx", "")
    table_name = f"grade_{grade}"
    file_path = os.path.join(DATA_DIR, filename)

    # ⭐ 核心优化：表已存在 → 整个年级跳过
    if table_exists(table_name):
        print(f"{table_name} 已存在，跳过该年级")
        continue

    print(f"发现新年级：{grade}，开始导入")

    # 1️⃣ 创建年级表
    cursor.execute(f"""
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            class TEXT,
            student_id TEXT,
            remark TEXT
        )
    """)

    # 2️⃣ 读取 Excel
    df = pd.read_excel(file_path)

    # 3️⃣ 写入数据
    for _, row in df.iterrows():
        cursor.execute(
            f"""
            INSERT INTO {table_name} (name, class, student_id, remark)
            VALUES (?, ?, ?, ?)
            """,
            (
                row.get("姓名"),
                row.get("班级"),
                row.get("学号"),
                row.get("备注")
            )
        )

    print(f"{table_name} 导入完成")

conn.commit()
conn.close()

print("初始化完成（仅导入新年级）")
