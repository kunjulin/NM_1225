"""快速檢查資料庫中的資料"""
import asyncio
import json
from sqlalchemy import select
from app.database import async_session_maker
from app.models import OrderCase

async def check_db():
    async with async_session_maker() as db:
        # 查詢所有案件
        result = await db.execute(select(OrderCase))
        cases = result.scalars().all()
        
        print(f"總共有 {len(cases)} 個案件")
        
        for case in cases:
            print(f"\n案件 ID: {case.id}")
            print(f"  狀態: {case.status}")
            print(f"  病人: {case.patient_ref}")
            print(f"  ServiceRequest: {case.service_request_ref}")
            
            # 解析 snapshot
            if case.snapshot_json:
                snapshot = json.loads(case.snapshot_json)
                print(f"  病人名稱: {snapshot.get('patientName', 'N/A')}")
                print(f"  檢查: {snapshot.get('examDisplay', snapshot.get('examCode', 'N/A'))}")

if __name__ == "__main__":
    asyncio.run(check_db())





