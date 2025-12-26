"""
Outbox Worker
處理延遲 write-back 到 FHIR Server
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import OrderCase, Outbox
from app.schemas import CaseStatus
from app.fhir.client import FHIRClient
from app.config import get_settings

logger = logging.getLogger(__name__)


class OutboxWorker:
    """Outbox Worker
    
    定期檢查 outbox 表並處理待同步的項目
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.fhir_client = FHIRClient()
        self.running = False
    
    async def start(self):
        """啟動 Worker"""
        self.running = True
        logger.info("Outbox Worker started")
        
        while self.running:
            try:
                await self.process_pending()
            except Exception as e:
                logger.error(f"Outbox Worker error: {e}")
            
            await asyncio.sleep(self.settings.outbox_poll_interval_seconds)
    
    async def stop(self):
        """停止 Worker"""
        self.running = False
        logger.info("Outbox Worker stopped")
    
    async def process_pending(self):
        """處理待處理的 Outbox 項目"""
        async with async_session_maker() as db:
            # 查詢待處理項目
            now = datetime.now(timezone.utc).isoformat()
            
            query = select(Outbox).where(
                and_(
                    Outbox.status.in_(["PENDING", "FAILED"]),
                    Outbox.retry_count < self.settings.outbox_max_retries,
                    # 檢查是否已過重試時間
                    (Outbox.next_retry_at.is_(None)) | (Outbox.next_retry_at <= now)
                )
            ).limit(10)  # 每次處理 10 筆
            
            result = await db.execute(query)
            items = result.scalars().all()
            
            for item in items:
                await self._process_item(db, item)
            
            await db.commit()
    
    async def _process_item(self, db: AsyncSession, item: Outbox):
        """處理單一 Outbox 項目"""
        logger.info(f"Processing outbox item: {item.id} for case: {item.case_id}")
        
        # 標記為處理中
        item.status = "IN_PROGRESS"
        item.updated_at = datetime.now(timezone.utc).isoformat()
        
        try:
            # 取得案件
            case_result = await db.execute(
                select(OrderCase).where(OrderCase.id == item.case_id)
            )
            case = case_result.scalar_one_or_none()
            
            if not case:
                item.status = "FAILED"
                item.last_error = "Case not found"
                return
            
            # 執行操作
            if item.operation == "CREATE_MEDICATION_REQUEST":
                result = await self._create_medication_request(case, item)
                
                if result:
                    # 成功
                    item.status = "DONE"
                    case.status = CaseStatus.SYNCED.value
                    case.final_fhir_medication_request_ref = f"MedicationRequest/{result.get('id')}"
                    case.updated_at = datetime.now(timezone.utc).isoformat()
                    logger.info(f"Successfully synced case: {case.id}")
                else:
                    raise Exception("Failed to create MedicationRequest")
            else:
                item.status = "FAILED"
                item.last_error = f"Unknown operation: {item.operation}"
        
        except Exception as e:
            logger.error(f"Error processing outbox item {item.id}: {e}")
            
            item.retry_count += 1
            item.last_error = str(e)
            
            if item.retry_count >= self.settings.outbox_max_retries:
                item.status = "FAILED"
                # 更新案件狀態
                case.status = CaseStatus.SYNC_FAILED.value
                case.updated_at = datetime.now(timezone.utc).isoformat()
            else:
                item.status = "FAILED"
                # 設定下次重試時間（指數退避）
                delay = 2 ** item.retry_count * 60  # 2, 4, 8, 16... 分鐘
                item.next_retry_at = (
                    datetime.now(timezone.utc) + timedelta(seconds=delay)
                ).isoformat()
        
        item.updated_at = datetime.now(timezone.utc).isoformat()
    
    async def _create_medication_request(
        self, 
        case: OrderCase, 
        item: Outbox
    ) -> dict | None:
        """建立 MedicationRequest 到 FHIR Server"""
        draft = json.loads(case.draft_json or "{}")
        
        # 建構 FHIR 資源
        medication_request = self.fhir_client.build_medication_request(
            patient_ref=case.patient_ref,
            service_request_ref=case.service_request_ref,
            draft=draft,
            requester_ref="Practitioner/demo-nm-physician"  # Demo 用
        )
        
        # 發送到 FHIR Server
        return await self.fhir_client.create_medication_request(medication_request)


# 全域 Worker 實例
_worker: OutboxWorker | None = None


async def start_outbox_worker():
    """啟動 Outbox Worker（背景任務）"""
    global _worker
    _worker = OutboxWorker()
    await _worker.start()


async def stop_outbox_worker():
    """停止 Outbox Worker"""
    global _worker
    if _worker:
        await _worker.stop()


