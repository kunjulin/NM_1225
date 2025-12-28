"""清除所有 snapshot 進 APP DB 的 FHIR data"""
import asyncio
import sys
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import OrderCase, ReviewEvent, Outbox

# 設定輸出編碼為 UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def clear_all_snapshots():
    """清除所有 snapshot 資料（包括 OrderCase, ReviewEvent, Outbox）"""
    async with async_session_maker() as db:
        # 1. 先統計現有資料
        cases_result = await db.execute(select(OrderCase))
        cases = cases_result.scalars().all()
        case_count = len(cases)
        
        if case_count == 0:
            print("資料庫中沒有任何 snapshot 資料需要清除")
            return
        
        case_ids = [case.id for case in cases]
        
        # 統計相關記錄
        review_events_result = await db.execute(
            select(ReviewEvent).where(ReviewEvent.case_id.in_(case_ids))
        )
        review_events = review_events_result.scalars().all()
        review_event_count = len(review_events)
        
        outbox_result = await db.execute(
            select(Outbox).where(Outbox.case_id.in_(case_ids))
        )
        outbox_items = outbox_result.scalars().all()
        outbox_count = len(outbox_items)
        
        # 2. 顯示統計資訊
        print("=" * 60)
        print("準備清除所有 snapshot 資料")
        print("=" * 60)
        print(f"案件數 (OrderCase): {case_count}")
        print(f"審查事件數 (ReviewEvent): {review_event_count}")
        print(f"Outbox 項目數 (Outbox): {outbox_count}")
        print("=" * 60)
        
        # 3. 刪除相關的 ReviewEvent
        if review_event_count > 0:
            print(f"\n正在刪除 {review_event_count} 個審查事件...")
            await db.execute(delete(ReviewEvent))
        
        # 4. 刪除相關的 Outbox
        if outbox_count > 0:
            print(f"正在刪除 {outbox_count} 個 Outbox 項目...")
            await db.execute(delete(Outbox))
        
        # 5. 刪除所有 OrderCase（包含 snapshot_json）
        print(f"正在刪除 {case_count} 個案件（包含 snapshot 資料）...")
        await db.execute(delete(OrderCase))
        
        # 6. 提交變更
        await db.commit()
        
        print("\n" + "=" * 60)
        print("✓ 成功清除所有 snapshot 資料")
        print("=" * 60)
        print(f"已刪除:")
        print(f"  - {case_count} 個案件 (OrderCase)")
        print(f"  - {review_event_count} 個審查事件 (ReviewEvent)")
        print(f"  - {outbox_count} 個 Outbox 項目 (Outbox)")
        print("=" * 60)


if __name__ == "__main__":
    print("開始清除所有 snapshot 資料...\n")
    asyncio.run(clear_all_snapshots())
    print("\n完成！")

