"""
FHIR Client
與外部 FHIR Server 的通訊模組
支援 Local HAPI FHIR 與 THAS 競賽環境切換
"""
import json
from typing import Any, Optional

import httpx

from app.config import get_settings


class FHIRClient:
    """FHIR Client
    
    提供與 FHIR Server 的 CRUD 操作
    支援 timeout 與 graceful fallback
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.fhir_base_url
        self.timeout = self.settings.fhir_timeout_seconds
    
    async def _request(
        self, 
        method: str, 
        path: str, 
        data: Optional[dict] = None,
        params: Optional[dict] = None
    ) -> Optional[dict]:
        """發送 FHIR 請求"""
        url = f"{self.base_url}/{path}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=params)
                elif method == "POST":
                    response = await client.post(
                        url, 
                        json=data,
                        headers={"Content-Type": "application/fhir+json"}
                    )
                elif method == "PUT":
                    response = await client.put(
                        url, 
                        json=data,
                        headers={"Content-Type": "application/fhir+json"}
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    # 記錄錯誤但不拋出，graceful fallback
                    return None
                    
            except httpx.TimeoutException:
                # Timeout: 返回 None，讓呼叫端使用快取
                return None
            except httpx.RequestError:
                # 連線錯誤: 返回 None
                return None
    
    # === Patient ===
    
    async def get_patient(self, patient_ref: str) -> Optional[dict]:
        """取得 Patient 資源"""
        # patient_ref 格式: "Patient/123"
        return await self._request("GET", patient_ref)
    
    # === ServiceRequest ===
    
    async def get_service_request(self, ref: str) -> Optional[dict]:
        """取得 ServiceRequest 資源"""
        return await self._request("GET", ref)
    
    async def search_service_requests(
        self, 
        status: Optional[str] = None,
        last_updated: Optional[str] = None
    ) -> list[dict]:
        """搜尋 ServiceRequest"""
        params = {}
        if status:
            params["status"] = status
        if last_updated:
            params["_lastUpdated"] = last_updated
        
        result = await self._request("GET", "ServiceRequest", params=params)
        if result and "entry" in result:
            return [e.get("resource", {}) for e in result["entry"]]
        return []
    
    # === Observation ===
    
    async def get_latest_weight(self, patient_ref: str) -> Optional[dict]:
        """取得最近的體重 Observation
        
        LOINC 29463-7 = Body weight
        """
        # 提取 Patient ID
        patient_id = patient_ref.replace("Patient/", "")
        
        result = await self._request(
            "GET", 
            "Observation",
            params={
                "patient": patient_id,
                "code": "29463-7",
                "_sort": "-date",
                "_count": "1"
            }
        )
        
        if result and "entry" in result and len(result["entry"]) > 0:
            return result["entry"][0].get("resource")
        return None
    
    async def get_renal_function(self, patient_ref: str) -> Optional[dict]:
        """取得腎功能 Observation (eGFR 或 Creatinine)"""
        patient_id = patient_ref.replace("Patient/", "")
        
        # 先嘗試 eGFR (LOINC 33914-3)
        result = await self._request(
            "GET",
            "Observation",
            params={
                "patient": patient_id,
                "code": "33914-3",
                "_sort": "-date",
                "_count": "1"
            }
        )
        
        if result and "entry" in result and len(result["entry"]) > 0:
            return result["entry"][0].get("resource")
        
        # 若無 eGFR，嘗試 Creatinine (LOINC 2160-0)
        result = await self._request(
            "GET",
            "Observation",
            params={
                "patient": patient_id,
                "code": "2160-0",
                "_sort": "-date",
                "_count": "1"
            }
        )
        
        if result and "entry" in result and len(result["entry"]) > 0:
            return result["entry"][0].get("resource")
        
        return None
    
    # === AllergyIntolerance ===
    
    async def get_allergies(self, patient_ref: str) -> list[dict]:
        """取得過敏資料"""
        patient_id = patient_ref.replace("Patient/", "")
        
        result = await self._request(
            "GET",
            "AllergyIntolerance",
            params={"patient": patient_id}
        )
        
        if result and "entry" in result:
            return [e.get("resource", {}) for e in result["entry"]]
        return []
    
    # === MedicationRequest ===
    
    async def create_medication_request(self, data: dict) -> Optional[dict]:
        """建立 MedicationRequest（最終核准時）"""
        return await self._request("POST", "MedicationRequest", data=data)
    
    def build_medication_request(
        self,
        patient_ref: str,
        service_request_ref: str,
        draft: dict,
        requester_ref: str
    ) -> dict:
        """建構 MedicationRequest FHIR 資源"""
        return {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "urn:oid:1.2.3.4.5.6.7.8.9",  # 本地代碼系統
                        "code": draft.get("radiopharmaceuticalCode", ""),
                        "display": draft.get("radiopharmaceuticalDisplay", "")
                    }
                ]
            },
            "subject": {
                "reference": patient_ref
            },
            "requester": {
                "reference": requester_ref
            },
            "basedOn": [
                {"reference": service_request_ref}
            ],
            "dosageInstruction": [
                {
                    "doseAndRate": [
                        {
                            "doseQuantity": {
                                "value": draft.get("suggestedDose", {}).get("value"),
                                "unit": draft.get("suggestedDose", {}).get("unit", "MBq"),
                                "system": "http://unitsofmeasure.org",
                                "code": "MBq"
                            }
                        }
                    ]
                }
            ],
            "note": [
                {
                    "text": draft.get("notes", "")
                }
            ] if draft.get("notes") else []
        }


