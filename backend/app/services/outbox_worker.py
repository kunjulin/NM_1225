"""
Outbox Worker
處理延遲 write-back 到 FHIR Server
同時處理 ServiceRequest 同步輪詢
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import OrderCase, Outbox, ReviewEvent, User
from app.schemas import CaseStatus
from app.fhir.client import FHIRClient
from app.config import get_settings
from app.services.fhir_sync_service import FHIRSyncService
from app.services.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)


class OutboxWorker:
    """Outbox Worker
    
    定期檢查 outbox 表並處理待同步的項目
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.fhir_client = FHIRClient()
        self.running = False
        self._last_sync_time: str | None = None
    
    async def start(self):
        """啟動 Worker"""
        self.running = True
        print(f"[OutboxWorker] Started (polling every {self.settings.outbox_poll_interval_seconds}s)")
        print(f"[OutboxWorker] FHIR Server: {self.settings.fhir_base_url}")
        logger.info(f"Outbox Worker started (polling every {self.settings.outbox_poll_interval_seconds}s)")
        logger.info(f"FHIR Server: {self.settings.fhir_base_url}")
        
        while self.running:
            try:
                await self.process_pending()
            except Exception as e:
                logger.error(f"Outbox Worker error: {e}", exc_info=True)
            
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
                result = await self._create_medication_request(case, item, db)
                
                if result:
                    # 成功
                    item.status = "DONE"
                    item.last_error = None  # 清除之前的錯誤
                    case.status = CaseStatus.SYNCED.value
                    case.final_fhir_medication_request_ref = f"MedicationRequest/{result.get('id')}"
                    case.updated_at = datetime.now(timezone.utc).isoformat()
                    logger.info(f"Successfully synced case: {case.id}")
                else:
                    # 如果 last_error 已經被設置（在 _create_medication_request 中），使用它
                    error_msg = item.last_error or "Failed to create MedicationRequest"
                    raise Exception(error_msg)
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
        item: Outbox,
        db: AsyncSession
    ) -> dict | None:
        """建立 MedicationRequest 到 FHIR Server"""
        draft = json.loads(case.draft_json or "{}")
        
        # 驗證必要欄位
        if not draft.get("radiopharmaceuticalCode"):
            error_msg = "Missing radiopharmaceuticalCode in draft"
            logger.error(f"Invalid draft for case {case.id}: {error_msg}")
            raise ValueError(error_msg)
        
        if not draft.get("suggestedDose", {}).get("value"):
            error_msg = "Missing suggestedDose.value in draft"
            logger.error(f"Invalid draft for case {case.id}: {error_msg}")
            raise ValueError(error_msg)
        
        # 取得 requester_ref：從 ReviewEvent 查詢批准者，再從 User 取得 practitioner_ref
        requester_ref = await self._get_requester_ref(db, case.id)
        
        # 建構 FHIR 資源
        medication_request = self.fhir_client.build_medication_request(
            patient_ref=case.patient_ref,
            service_request_ref=case.service_request_ref,
            draft=draft,
            requester_ref=requester_ref
        )
        
        logger.info(f"Creating MedicationRequest for case {case.id} to {self.settings.fhir_base_url}")
        # 記錄完整的 payload（INFO 級別，方便調試）
        logger.info(f"MedicationRequest payload for case {case.id}: {json.dumps(medication_request, indent=2, ensure_ascii=False)}")
        
        # 發送到 FHIR Server（使用新的方法獲取詳細錯誤）
        result, error_message = await self.fhir_client.create_medication_request_with_error(medication_request)
        
        if result:
            logger.info(f"Successfully created MedicationRequest: {result.get('id')}")
        else:
            error_msg = error_message or "Unknown error"
            logger.warning(f"Failed to create MedicationRequest for case {case.id}: {error_msg}")
            # 將詳細錯誤訊息保存到 item，這樣在異常處理時可以獲取
            item.last_error = error_msg
        
        return result
    
    async def _get_requester_ref(self, db: AsyncSession, case_id: str) -> str:
        """取得 MedicationRequest 的 requester_ref
        
        優先順序：
        1. 從 ReviewEvent 查詢最新的 APPROVE 事件，取得 actor_subject
        2. 從 User 表查詢該 actor_subject 的 practitioner_ref
        3. 如果找不到 practitioner_ref，嘗試從 ServiceRequest 取得 requester（作為 fallback）
        4. 如果都找不到，在 Demo Mode 下使用 "Practitioner/demo-nm-physician"
        5. 在 Production Mode 下，如果找不到則使用 actor_subject 作為 Practitioner ID
        
        Returns:
            requester_ref: 如 "Practitioner/123" 或 "Practitioner/demo-nm-physician"
        """
        # 1. 查詢最新的 APPROVE 事件
        approve_event_result = await db.execute(
            select(ReviewEvent)
            .where(
                and_(
                    ReviewEvent.case_id == case_id,
                    ReviewEvent.event_type == "APPROVE"
                )
            )
            .order_by(ReviewEvent.created_at.desc())
            .limit(1)
        )
        approve_event = approve_event_result.scalar_one_or_none()
        
        if approve_event and approve_event.actor_subject:
            # 2. 從 User 表查詢 practitioner_ref
            user_result = await db.execute(
                select(User).where(User.subject == approve_event.actor_subject)
            )
            user = user_result.scalar_one_or_none()
            
            if user and user.practitioner_ref:
                logger.info(f"Using practitioner_ref from User: {user.practitioner_ref} for case {case_id}")
                return user.practitioner_ref
            else:
                logger.warning(f"User {approve_event.actor_subject} not found or has no practitioner_ref for case {case_id}")
        
        # 3. 嘗試從 ServiceRequest 取得 requester（需要從 FHIR Server 查詢）
        # 這裡我們先跳過，因為需要額外的 FHIR 查詢，而且通常 ServiceRequest 的 requester 是臨床醫師，不是核醫醫師
        
        # 4. Fallback: 根據模式決定
        if self.settings.is_demo_mode:
            logger.info(f"Using demo practitioner_ref for case {case_id}")
            return "Practitioner/demo-nm-physician"
        else:
            # Production Mode: 如果找不到 practitioner_ref，使用 actor_subject
            if approve_event and approve_event.actor_subject:
                # 嘗試使用 actor_subject 作為 Practitioner ID（假設它是 Practitioner/{id} 格式）
                if approve_event.actor_subject.startswith("Practitioner/"):
                    logger.warning(f"Using actor_subject as practitioner_ref for case {case_id}: {approve_event.actor_subject}")
                    return approve_event.actor_subject
                else:
                    # 如果不是 Practitioner/ 格式，嘗試加上前綴
                    logger.warning(f"Using actor_subject with Practitioner/ prefix for case {case_id}: Practitioner/{approve_event.actor_subject}")
                    return f"Practitioner/{approve_event.actor_subject}"
            else:
                # 如果連 APPROVE 事件都找不到，使用預設值
                logger.error(f"No APPROVE event found for case {case_id}, using fallback")
                return "Practitioner/demo-nm-physician"
    
    async def retry_outbox_item(self, db: AsyncSession, outbox_id: str) -> bool:
        """手動重試 Outbox 項目
        
        Args:
            db: 資料庫會話
            outbox_id: Outbox 項目 ID
            
        Returns:
            是否成功處理
        """
        # 查詢 Outbox 項目
        result = await db.execute(
            select(Outbox).where(Outbox.id == outbox_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise ValueError(f"Outbox item {outbox_id} not found")
        
        # 只有 FAILED 狀態的項目可以手動重試
        if item.status not in ["FAILED", "PENDING"]:
            raise ValueError(f"Cannot retry outbox item in status: {item.status}")
        
        # 重置狀態為 PENDING，清除 next_retry_at，讓 Worker 立即處理
        item.status = "PENDING"
        item.next_retry_at = None
        item.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 立即處理（不等待 Worker 輪詢）
        await self._process_item(db, item)
        
        return item.status == "DONE"


# 全域 Worker 實例
_worker: OutboxWorker | None = None
_sync_worker: 'FHIRSyncWorker | None' = None
_clinical_data_worker: 'ClinicalDataSyncWorker | None' = None


async def start_outbox_worker():
    """啟動 Outbox Worker（背景任務）"""
    global _worker
    if _worker is None:
        _worker = OutboxWorker()
    # start() 會進入無限循環，在背景運行
    await _worker.start()


async def stop_outbox_worker():
    """停止 Outbox Worker"""
    global _worker
    if _worker:
        await _worker.stop()


class FHIRSyncWorker:
    """FHIR 同步 Worker
    
    定期從 FHIR Server 同步 ServiceRequest 到本地工作清單
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self._last_sync_time: str | None = None
        self._last_sync_completed_at: str | None = None
        self._next_sync_at: datetime | None = None
    
    async def start(self):
        """啟動 Worker"""
        self.running = True
        print(f"[FHIRSyncWorker] Started (polling every {self.settings.fhir_sync_poll_interval_seconds}s)")
        logger.info("FHIR Sync Worker started")
        
        while self.running:
            try:
                await self.sync_service_requests()
            except Exception as e:
                logger.error(f"FHIR Sync Worker error: {e}")
            
            await asyncio.sleep(self.settings.fhir_sync_poll_interval_seconds)
    
    async def stop(self):
        """停止 Worker"""
        self.running = False
        logger.info("FHIR Sync Worker stopped")
    
    async def sync_service_requests(self):
        """同步 ServiceRequest"""
        async with async_session_maker() as db:
            sync_service = FHIRSyncService(db)
            
            # 取得上次同步時間
            if not self._last_sync_time:
                self._last_sync_time = await sync_service.get_last_sync_time()
            
            # 執行同步
            result = await sync_service.sync_service_requests(
                last_updated=self._last_sync_time
            )
            
            if result["created"] > 0:
                logger.info(
                    f"FHIR Sync: fetched={result['fetched']}, "
                    f"created={result['created']}, skipped={result['skipped']}"
                )
            
            # 更新最後同步時間
            now = datetime.now(timezone.utc)
            self._last_sync_time = now.isoformat()
            self._last_sync_completed_at = now.isoformat()
            self._next_sync_at = now + timedelta(seconds=self.settings.fhir_sync_poll_interval_seconds)
    
    def get_status(self) -> dict:
        """取得同步狀態"""
        now = datetime.now(timezone.utc)
        next_sync_in = None
        
        if self._next_sync_at:
            delta = (self._next_sync_at - now).total_seconds()
            next_sync_in = max(0, int(delta))
        
        return {
            "is_running": self.running,
            "last_sync_time": self._last_sync_completed_at,
            "next_sync_in": next_sync_in,
            "sync_interval_seconds": self.settings.fhir_sync_poll_interval_seconds,
        }


async def start_fhir_sync_worker():
    """啟動 FHIR 同步 Worker（背景任務）"""
    global _sync_worker
    _sync_worker = FHIRSyncWorker()
    await _sync_worker.start()


async def stop_fhir_sync_worker():
    """停止 FHIR 同步 Worker"""
    global _sync_worker
    if _sync_worker:
        await _sync_worker.stop()


def get_sync_status() -> dict:
    """取得 FHIR 同步狀態"""
    global _sync_worker
    if _sync_worker:
        return _sync_worker.get_status()
    
    # Worker 未啟動時的預設狀態
    settings = get_settings()
    return {
        "is_running": False,
        "last_sync_time": None,
        "next_sync_in": None,
        "sync_interval_seconds": settings.fhir_sync_poll_interval_seconds,
    }


class ClinicalDataSyncWorker:
    """臨床資料同步 Worker
    
    非同步拉取案件的完整臨床資料（Encounters, Conditions, Medications, Procedures, Lab Results, Allergies）
    這個 Worker 會處理只有基本快照的案件，在背景補充完整的臨床資料
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self._processed_count = 0
        self._last_processed_at: str | None = None
    
    async def start(self):
        """啟動 Worker"""
        self.running = True
        poll_interval = 30.0  # 每 30 秒檢查一次
        print(f"[ClinicalDataSyncWorker] Started (polling every {poll_interval}s)")
        logger.info("Clinical Data Sync Worker started")
        
        while self.running:
            try:
                await self.sync_clinical_data()
            except Exception as e:
                logger.error(f"Clinical Data Sync Worker error: {e}", exc_info=True)
            
            await asyncio.sleep(poll_interval)
    
    async def stop(self):
        """停止 Worker"""
        self.running = False
        logger.info("Clinical Data Sync Worker stopped")
    
    async def sync_clinical_data(self):
        """同步臨床資料
        
        查詢缺少臨床資料的案件，並在背景拉取完整的臨床資料
        """
        async with async_session_maker() as db:
            # 查詢缺少臨床資料的案件（只處理最近建立的案件，避免處理太舊的案件）
            # 只處理最近 24 小時內建立的案件
            cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            
            result = await db.execute(
                select(OrderCase)
                .where(OrderCase.created_at >= cutoff_time)
                .limit(10)  # 每次處理 10 筆
            )
            cases = result.scalars().all()
            
            processed = 0
            for case in cases:
                # 檢查是否缺少臨床資料
                snapshot_data = json.loads(case.snapshot_json or "{}")
                has_clinical_data = (
                    snapshot_data.get("encounters") or
                    snapshot_data.get("conditionList") or
                    snapshot_data.get("medications") or
                    snapshot_data.get("procedures") or
                    snapshot_data.get("labResults") or
                    snapshot_data.get("allergyList")
                )
                
                if not has_clinical_data:
                    try:
                        logger.info(f"Fetching clinical data for case {case.id}")
                        snapshot_service = SnapshotService(db)
                        await snapshot_service._refresh_snapshot(case)
                        await db.flush()
                        processed += 1
                        logger.info(f"Successfully fetched clinical data for case {case.id}")
                    except Exception as e:
                        logger.error(f"Failed to fetch clinical data for case {case.id}: {e}", exc_info=True)
                        # 繼續處理下一個案件
            
            if processed > 0:
                await db.commit()
                self._processed_count += processed
                self._last_processed_at = datetime.now(timezone.utc).isoformat()
                logger.info(f"Processed {processed} cases with clinical data sync")


async def start_clinical_data_sync_worker():
    """啟動臨床資料同步 Worker（背景任務）"""
    global _clinical_data_worker
    _clinical_data_worker = ClinicalDataSyncWorker()
    await _clinical_data_worker.start()


async def stop_clinical_data_sync_worker():
    """停止臨床資料同步 Worker"""
    global _clinical_data_worker
    if _clinical_data_worker:
        await _clinical_data_worker.stop()


