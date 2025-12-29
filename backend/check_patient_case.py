"""檢查指定病人的案件狀態與審查歷程"""
import asyncio
import json
from sqlalchemy import select
from app.database import async_session_maker
from app.models import OrderCase, ReviewEvent

async def check_patient_case(patient_ref: str):
    """檢查指定病人的案件狀態與審查歷程"""
    async with async_session_maker() as db:
        # 查詢該病人的所有案件
        result = await db.execute(
            select(OrderCase).where(OrderCase.patient_ref == patient_ref)
        )
        cases = result.scalars().all()
        
        if not cases:
            print(f"未找到與 {patient_ref} 相關的案件")
            return
        
        print(f"找到 {len(cases)} 個與 {patient_ref} 相關的案件:\n")
        
        for case in cases:
            print(f"=" * 80)
            print(f"案件 ID: {case.id}")
            print(f"狀態: {case.status}")
            print(f"ServiceRequest: {case.service_request_ref}")
            print(f"擁有者: {case.owner_subject or '(無)'}")
            print(f"建立時間: {case.created_at}")
            print(f"更新時間: {case.updated_at}")
            
            # 解析 snapshot
            if case.snapshot_json:
                snapshot = json.loads(case.snapshot_json)
                print(f"病人名稱: {snapshot.get('patientName', 'N/A')}")
                print(f"檢查項目: {snapshot.get('examDisplay', snapshot.get('examCode', 'N/A'))}")
            
            # 檢查是否應該出現在核醫工作清單
            nm_statuses = ['NM_PENDING', 'NM_DRAFTED', 'RETURNED', 'PHARM_READY']
            in_nm_worklist = case.status in nm_statuses
            print(f"\n是否應出現在核醫工作清單: {'是' if in_nm_worklist else '否'}")
            if not in_nm_worklist:
                print(f"  原因: 狀態 {case.status} 不在核醫工作清單的狀態範圍內")
                print(f"  核醫工作清單包含的狀態: {', '.join(nm_statuses)}")
            
            # 檢查是否應該出現在藥師工作清單
            pharm_statuses = ['PHARM_READY', 'PHARM_IN_PROGRESS', 'APPROVED']
            in_pharm_worklist = case.status in pharm_statuses
            print(f"是否應出現在藥師工作清單: {'是' if in_pharm_worklist else '否'}")
            if not in_pharm_worklist:
                print(f"  原因: 狀態 {case.status} 不在藥師工作清單的狀態範圍內")
                print(f"  藥師工作清單包含的狀態: {', '.join(pharm_statuses)}")
            
            # 查詢審查歷程
            review_result = await db.execute(
                select(ReviewEvent)
                .where(ReviewEvent.case_id == case.id)
                .order_by(ReviewEvent.created_at.asc())
            )
            review_events = review_result.scalars().all()
            
            print(f"\n審查歷程 (共 {len(review_events)} 筆):")
            if review_events:
                for event in review_events:
                    payload = None
                    if event.payload_json:
                        try:
                            payload = json.loads(event.payload_json)
                        except:
                            pass
                    
                    print(f"  - [{event.created_at}] {event.event_type}")
                    print(f"    執行者: {event.actor_subject} ({event.acting_role})")
                    if payload:
                        print(f"    內容: {json.dumps(payload, ensure_ascii=False)}")
            else:
                print("  (無審查歷程)")
            
            print()

if __name__ == "__main__":
    import sys
    patient_ref = sys.argv[1] if len(sys.argv) > 1 else "Patient/patient-1007"
    asyncio.run(check_patient_case(patient_ref))


