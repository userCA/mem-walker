"""
清理 DuckDB Graph Store 中的残留数据
"""

import duckdb

# DuckDB 默认使用内存数据库，但如果配置了文件路径需要调整
DB_PATH = "./data/duckdb_graph.db"

def cleanup_graph():
    print(f"🧹 清理 Graph Store 数据...")

    try:
        conn = duckdb.connect(database=DB_PATH, read_only=False)

        # 检查是否有表
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"   现有表: {[t[0] for t in tables]}")

        if tables:
            # 禁用外键约束检查（如果启用）
            try:
                conn.execute("PRAGMA foreign_keys=OFF")
            except:
                pass

            # 清空关系表（先清关系，再清实体）
            try:
                conn.execute("DELETE FROM relations")
                print("   ✅ 清空 relations 表")
            except Exception as e:
                print(f"   ⚠️ 清空 relations 失败: {e}")

            try:
                conn.execute("DELETE FROM entities")
                print("   ✅ 清空 entities 表")
            except Exception as e:
                print(f"   ⚠️ 清空 entities 失败: {e}")

            conn.commit()

        conn.close()
        print("✅ Graph Store 清理完成")

    except Exception as e:
        print(f"❌ 清理失败: {e}")

if __name__ == "__main__":
    cleanup_graph()
