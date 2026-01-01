"""
直接檢查資料庫檔案（包含 WAL）
"""
import sqlite3
import sys
import io

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

db_path = 'nm_stewardship.db'

try:
    # SQLite 會自動處理 WAL 檔案
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 檢查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_analyses'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("❌ llm_analyses 資料表不存在")
        conn.close()
        sys.exit(1)
    
    # 統計總數
    cursor.execute("SELECT COUNT(*) FROM llm_analyses")
    total = cursor.fetchone()[0]
    print(f"總記錄數: {total}")
    
    if total == 0:
        print("\n資料庫中沒有任何 LLM 分析記錄")
        conn.close()
        sys.exit(0)
    
    # 按狀態統計
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM llm_analyses 
        GROUP BY status
    """)
    status_counts = cursor.fetchall()
    print("\n按狀態統計:")
    for status, count in status_counts:
        print(f"  {status}: {count}")
    
    # 檢查特定 ID
    target_id = "7f22e7de-7f3b-43f8-a277-41db070c5a53"
    cursor.execute("SELECT id, case_id, status, created_at FROM llm_analyses WHERE id = ?", (target_id,))
    target_row = cursor.fetchone()
    
    if target_row:
        print(f"\n✅ 找到目標分析記錄:")
        print(f"  分析 ID: {target_row[0]}")
        print(f"  案件 ID: {target_row[1]}")
        print(f"  狀態: {target_row[2]}")
        print(f"  建立時間: {target_row[3]}")
    else:
        print(f"\n❌ 未找到分析 ID: {target_id}")
    
    # 檢查目標案件 ID
    case_id = "74c6764b-0b17-4d63-85bf-7454f71eca34"
    cursor.execute("""
        SELECT id, case_id, status, created_at, error_message 
        FROM llm_analyses 
        WHERE case_id = ? 
        ORDER BY created_at DESC
    """, (case_id,))
    case_rows = cursor.fetchall()
    
    if case_rows:
        print(f"\n✅ 找到 {len(case_rows)} 筆目標案件的記錄:")
        for i, row in enumerate(case_rows, 1):
            print(f"\n  記錄 #{i}:")
            print(f"    分析 ID: {row[0]}")
            print(f"    狀態: {row[2]}")
            print(f"    建立時間: {row[3]}")
            if row[4]:
                error_preview = row[4][:100].replace('\n', ' ')
                print(f"    錯誤訊息: {error_preview}...")
    else:
        print(f"\n❌ 未找到案件 ID 的記錄: {case_id}")
    
    # 最近 10 筆記錄
    cursor.execute("""
        SELECT id, case_id, status, model_name, created_at, error_message
        FROM llm_analyses 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    recent_rows = cursor.fetchall()
    
    if recent_rows:
        print(f"\n最近 {len(recent_rows)} 筆記錄:")
        print("-" * 80)
        for i, row in enumerate(recent_rows, 1):
            status_icon = "✅" if row[2] == "COMPLETED" else "❌" if row[2] == "FAILED" else "⏳"
            print(f"\n{i}. {status_icon} {row[2]}")
            print(f"   分析 ID: {row[0]}")
            print(f"   案件 ID: {row[1]}")
            print(f"   模型: {row[3] or 'N/A'}")
            print(f"   建立時間: {row[4]}")
            if row[5]:
                error_preview = row[5][:80].replace('\n', ' ')
                print(f"   錯誤: {error_preview}...")
    
    conn.close()
    
except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

