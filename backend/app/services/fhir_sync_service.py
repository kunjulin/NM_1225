"""
FHIR 同步服務
從 FHIR Server 同步 ServiceRequest 到本地工作清單
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.order_case import OrderCase
from app.schemas.case import CaseStatus
from app.fhir.client import FHIRClient
from app.rules.engine import RuleEngine
from app.schemas.rule_eval import Severity

logger = logging.getLogger(__name__)


class FHIRSyncService:
    """FHIR 同步服務
    
    從 FHIR Server 查詢核醫相關的 ServiceRequest，
    並建立對應的 OrderCase 到本地資料庫
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.fhir_client = FHIRClient()
        self.rule_engine = RuleEngine()
    
    async def sync_service_requests(
        self,
        last_updated: Optional[str] = None,
        category: Optional[str] = None,
    ) -> dict:
        """同步 ServiceRequest
        
        Args:
            last_updated: 只同步此時間之後更新的 ServiceRequest
            category: 過濾類別（核醫相關）
            
        Returns:
            同步結果統計
        """
        stats = {
            "fetched": 0,
            "created": 0,
            "skipped": 0,
            "errors": 0,
            "error_details": [],
        }
        
        try:
            # 從 FHIR Server 查詢 ServiceRequest
            service_requests = await self._fetch_service_requests(
                status="active",
                last_updated=last_updated,
                category=category or self.settings.fhir_service_request_category,
            )
            
            stats["fetched"] = len(service_requests)
            
            for sr in service_requests:
                try:
                    result = await self._process_service_request(sr)
                    if result == "created":
                        stats["created"] += 1
                    else:
                        stats["skipped"] += 1
                except Exception as e:
                    logger.error(f"Error processing ServiceRequest: {e}")
                    stats["errors"] += 1
                    stats["error_details"].append(str(e))
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error syncing ServiceRequests: {e}")
            stats["errors"] += 1
            stats["error_details"].append(str(e))
        
        return stats
    
    async def _fetch_service_requests(
        self,
        status: Optional[str] = None,
        last_updated: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        """從 FHIR Server 取得 ServiceRequest
        
        Args:
            status: 狀態過濾
            last_updated: 最後更新時間過濾
            category: 類別過濾（用於識別核醫相關的 ServiceRequest）
            
        Returns:
            ServiceRequest 資源列表
        """
        params = {}
        
        if status:
            params["status"] = status
        
        if last_updated:
            params["_lastUpdated"] = f"gt{last_updated}"
        
        # 嘗試根據類別過濾（如果 FHIR Server 支援）
        if category:
            params["category"] = category
        
        try:
            result = await self.fhir_client._request("GET", "ServiceRequest", params=params)
            
            if result and "entry" in result:
                return [e.get("resource", {}) for e in result["entry"]]
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching ServiceRequests: {e}")
            return []
    
    async def _process_service_request(self, service_request: dict) -> str:
        """處理單一 ServiceRequest
        
        Args:
            service_request: ServiceRequest FHIR 資源
            
        Returns:
            處理結果 ("created" 或 "skipped")
        """
        sr_id = service_request.get("id")
        if not sr_id:
            raise ValueError("ServiceRequest missing id")
        
        service_request_ref = f"ServiceRequest/{sr_id}"
        
        # 檢查是否已存在
        existing = await self.db.execute(
            select(OrderCase).where(OrderCase.service_request_ref == service_request_ref)
        )
        if existing.scalar_one_or_none():
            logger.debug(f"ServiceRequest {sr_id} already exists, skipping")
            return "skipped"
        
        # 取得 Patient 參考
        subject = service_request.get("subject", {})
        patient_ref = subject.get("reference", "")
        
        if not patient_ref:
            raise ValueError(f"ServiceRequest {sr_id} missing subject reference")
        
        # 取得 Patient 資訊
        patient = await self.fhir_client.get_patient(patient_ref)
        patient_name = self._extract_patient_name(patient) if patient else ""
        patient_id = self._extract_patient_id(patient) if patient else ""
        
        # 取得檢查資訊
        code = service_request.get("code", {})
        coding = code.get("coding", [{}])[0] if code.get("coding") else {}
        exam_code = coding.get("code", "")
        exam_display = coding.get("display", "") or code.get("text", "")
        
        # 嘗試取得體重
        weight_kg = None
        try:
            weight_obs = await self.fhir_client.get_latest_weight(patient_ref)
            if weight_obs:
                value_quantity = weight_obs.get("valueQuantity", {})
                weight_kg = value_quantity.get("value")
        except Exception as e:
            logger.warning(f"Failed to get weight for {patient_ref}: {e}")
        
        # 建立 snapshot
        snapshot = {
            "patientName": patient_name,
            "patientId": patient_id,
            "examCode": exam_code,
            "examDisplay": exam_display,
            "weightKg": weight_kg,
            "hasAllergy": None,  # 可以之後補充
        }
        
        # 建立 OrderCase
        now = datetime.now(timezone.utc).isoformat()
        case_id = str(uuid.uuid4())
        
        order_case = OrderCase(
            id=case_id,
            patient_ref=patient_ref,
            service_request_ref=service_request_ref,
            status=CaseStatus.NM_PENDING.value,
            owner_subject=None,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False),
            local_facts_json="{}",
            draft_json=None,
            final_fhir_medication_request_ref=None,
            created_at=now,
            updated_at=now,
        )
        
        self.db.add(order_case)
        # 先 flush 以便後續查詢
        await self.db.flush()
        
        # 執行 CDS 規則評估
        rule_eval = self.rule_engine.evaluate(order_case)
        
        # 如果 CDS 評估為 PASS，自動建立草案
        if rule_eval.overallSeverity == Severity.PASS:
            # 取得 NA-2024 劑量計算
            dose_calc = self.rule_engine.calculate_na2024_dose(exam_code, weight_kg)
            
            if dose_calc:
                # 建立草案
                draft_data = {
                    "examCode": exam_code,
                    "radiopharmaceuticalCode": exam_code,  # 使用檢查代碼作為放射性藥物代碼
                    "suggestedDose": {
                        "value": dose_calc.suggested_dose,
                        "unit": "MBq"
                    },
                    "override": {
                        "isOverride": False
                    }
                }
                
                order_case.draft_json = json.dumps(draft_data, ensure_ascii=False)
                order_case.status = CaseStatus.NM_DRAFTED.value
                order_case.updated_at = now
                
                logger.info(f"Auto-created draft for OrderCase {case_id} (CDS PASS)")
            else:
                logger.warning(f"Could not calculate dose for OrderCase {case_id}, keeping as NM_PENDING")
        
        logger.info(f"Created OrderCase {case_id} from ServiceRequest {sr_id} (status: {order_case.status})")
        
        return "created"
    
    def _extract_patient_name(self, patient: dict) -> str:
        """從 Patient 資源提取名稱"""
        names = patient.get("name", [])
        if not names:
            return ""
        
        name = names[0]
        
        # 優先使用 text
        if name.get("text"):
            return name["text"]
        
        # 組合 family + given
        family = name.get("family", "")
        given = name.get("given", [])
        given_str = " ".join(given) if given else ""
        
        if family and given_str:
            return f"{family} {given_str}"
        
        return family or given_str
    
    def _extract_patient_id(self, patient: dict) -> str:
        """從 Patient 資源提取識別碼"""
        identifiers = patient.get("identifier", [])
        
        # 優先找 MRN 或 official
        for ident in identifiers:
            if ident.get("use") == "official" or "MRN" in ident.get("type", {}).get("text", ""):
                return ident.get("value", "")
        
        # 返回第一個識別碼
        if identifiers:
            return identifiers[0].get("value", "")
        
        # 使用 Patient ID
        return patient.get("id", "")
    
    async def get_last_sync_time(self) -> Optional[str]:
        """取得最後同步時間
        
        Returns:
            最後建立的 OrderCase 時間，或 None
        """
        result = await self.db.execute(
            select(OrderCase.created_at)
            .order_by(OrderCase.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row if row else None


