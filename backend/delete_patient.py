"""刪除指定病人的所有相關記錄"""
import asyncio
import json
from sqlalchemy import select, delete
from app.database import async_session_maker
from app.models import OrderCase, ReviewEvent, Outbox

async def delete_patient_records(patient_ref: str):
    """刪除指定病人的所有相關記錄"""
    async with async_session_maker() as db:
        # 1. 先查詢相關的 OrderCase
        result = await db.execute(
            select(OrderCase).where(OrderCase.patient_ref == patient_ref)
        )
        cases = result.scalars().all()
        
        if not cases:
            print(f"未找到與 {patient_ref} 相關的案件")
            return
        
        print(f"找到 {len(cases)} 個與 {patient_ref} 相關的案件:")
        for case in cases:
            snapshot = json.loads(case.snapshot_json or "{}")
            print(f"  - 案件 ID: {case.id}")
            print(f"    狀態: {case.status}")
            print(f"    ServiceRequest: {case.service_request_ref}")
            print(f"    病人名稱: {snapshot.get('patientName', 'N/A')}")
        
        # 2. 確認刪除
        print(f"\n即將刪除 {len(cases)} 個案件及其相關記錄...")
        
        case_ids = [case.id for case in cases]
        
        # 3. 刪除相關的 ReviewEvent
        review_events_result = await db.execute(
            select(ReviewEvent).where(ReviewEvent.case_id.in_(case_ids))
        )
        review_events = review_events_result.scalars().all()
        if review_events:
            print(f"  刪除 {len(review_events)} 個審查事件...")
            await db.execute(
                delete(ReviewEvent).where(ReviewEvent.case_id.in_(case_ids))
            )
        
        # 4. 刪除相關的 Outbox
        outbox_result = await db.execute(
            select(Outbox).where(Outbox.case_id.in_(case_ids))
        )
        outbox_items = outbox_result.scalars().all()
        if outbox_items:
            print(f"  刪除 {len(outbox_items)} 個 Outbox 項目...")
            await db.execute(
                delete(Outbox).where(Outbox.case_id.in_(case_ids))
            )
        
        # 5. 刪除 OrderCase
        print(f"  刪除 {len(cases)} 個案件...")
        await db.execute(
            delete(OrderCase).where(OrderCase.patient_ref == patient_ref)
        )
        
        # 6. 提交變更
        await db.commit()
        
        print(f"\n✓ 成功刪除 {patient_ref} 的所有相關記錄")

if __name__ == "__main__":
    import sys
    
    # 預設刪除 patient-1007
    patient_ref = sys.argv[1] if len(sys.argv) > 1 else "Patient/patient-1007"
    
    print(f"準備刪除病人: {patient_ref}")
    print("=" * 50)
    
    asyncio.run(delete_patient_records(patient_ref))
    
    print("=" * 50)
    print("完成！")



