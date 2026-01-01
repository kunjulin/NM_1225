"""檢查資料庫中的分析記錄"""
import sqlite3

conn = sqlite3.connect('nm_stewardship.db')
cursor = conn.cursor()

# 檢查總數
cursor.execute('SELECT COUNT(*) FROM llm_analyses')
total = cursor.fetchone()[0]
print(f'分析記錄總數: {total}')

if total > 0:
    # 檢查是否有目標記錄
    cursor.execute('SELECT id, case_id, status, created_at FROM llm_analyses WHERE id = ?', 
                   ('7f22e7de-7f3b-43f8-a277-41db070c5a53',))
    row = cursor.fetchone()
    if row:
        print(f'\n找到目標分析記錄:')
        print(f'  ID: {row[0]}')
        print(f'  Case ID: {row[1]}')
        print(f'  Status: {row[2]}')
        print(f'  Created: {row[3]}')
    else:
        print('\n未找到目標分析 ID: 7f22e7de-7f3b-43f8-a277-41db070c5a53')
    
    # 檢查目標案件 ID
    cursor.execute('SELECT id, case_id, status, created_at FROM llm_analyses WHERE case_id = ? ORDER BY created_at DESC', 
                   ('74c6764b-0b17-4d63-85bf-7454f71eca34',))
    rows = cursor.fetchall()
    if rows:
        print(f'\n找到 {len(rows)} 筆目標案件的記錄:')
        for r in rows:
            print(f'  ID: {r[0][:8]}..., Status: {r[2]}, Time: {r[3]}')
    else:
        print('\n未找到目標案件 ID 的記錄: 74c6764b-0b17-4d63-85bf-7454f71eca34')
    
    # 顯示最近幾筆記錄
    cursor.execute('SELECT id, case_id, status, created_at FROM llm_analyses ORDER BY created_at DESC LIMIT 5')
    rows = cursor.fetchall()
    print(f'\n最近 5 筆記錄:')
    for r in rows:
        print(f'  ID: {r[0][:8]}..., Case: {r[1][:8]}..., Status: {r[2]}, Time: {r[3]}')

conn.close()

