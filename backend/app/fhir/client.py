"""
FHIR Client
與外部 FHIR Server 的通訊模組
支援 Local HAPI FHIR 與 THAS 競賽環境切換
"""
import json
import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


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
                # 確保使用 UTF-8 編碼處理回應
                headers = {"Accept": "application/fhir+json; charset=utf-8"}
                
                if method == "GET":
                    response = await client.get(url, params=params, headers=headers)
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
                    # 確保使用 UTF-8 編碼解析 JSON
                    # httpx 預設會處理 UTF-8，但明確指定更安全
                    response.encoding = "utf-8"
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    # 記錄詳細錯誤
                    error_text = response.text[:500] if response.text else "No error message"
                    logger.error(
                        f"FHIR request failed: {method} {url} - "
                        f"Status: {response.status_code}, Response: {error_text}"
                    )
                    return None
                    
            except httpx.TimeoutException as e:
                # Timeout: 記錄並返回 None
                logger.error(f"FHIR request timeout: {method} {url} - {str(e)}")
                return None
            except httpx.RequestError as e:
                # 連線錯誤: 記錄並返回 None
                logger.error(f"FHIR request error: {method} {url} - {str(e)}")
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
        
        # 嘗試多種排序方式，因為不同 FHIR Server 可能支援不同的排序欄位
        sort_options = ["-date", "-_lastUpdated", "-effective-date"]
        
        for sort_param in sort_options:
            result = await self._request(
                "GET", 
                "Observation",
                params={
                    "patient": patient_id,
                    "code": "29463-7",
                    "_sort": sort_param,
                    "_count": "1"
                }
            )
            
            if result and "entry" in result and len(result["entry"]) > 0:
                return result["entry"][0].get("resource")
        
        # 如果所有排序方式都失敗，嘗試不使用排序
        result = await self._request(
            "GET", 
            "Observation",
            params={
                "patient": patient_id,
                "code": "29463-7",
                "_count": "10"  # 取得多筆，然後在客戶端排序
            }
        )
        
        if result and "entry" in result:
            # 手動排序，使用 effectiveDateTime 或 _lastUpdated
            entries = result["entry"]
            entries.sort(key=lambda e: (
                e.get("resource", {}).get("effectiveDateTime", "") or 
                e.get("resource", {}).get("meta", {}).get("lastUpdated", "") or 
                ""
            ), reverse=True)
            
            if len(entries) > 0:
                return entries[0].get("resource")
        
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
    
    # === Encounter (就醫紀錄) ===
    
    async def get_encounters(self, patient_ref: str, count: int = 10) -> list[dict]:
        """取得病人就醫紀錄
        
        Args:
            patient_ref: 病人參考 (e.g., "Patient/123")
            count: 最多取回筆數
        
        Returns:
            就醫紀錄列表，依日期降序排列
        """
        patient_id = patient_ref.replace("Patient/", "")
        
        result = await self._request(
            "GET",
            "Encounter",
            params={
                "patient": patient_id,
                "_sort": "-date",
                "_count": str(count)
            }
        )
        
        if result and "entry" in result:
            return [e.get("resource", {}) for e in result["entry"]]
        return []
    
    # === Condition (診斷/病史) ===
    
    async def get_conditions(self, patient_ref: str) -> list[dict]:
        """取得病人診斷病史
        
        Args:
            patient_ref: 病人參考
        
        Returns:
            診斷/病史列表
        """
        patient_id = patient_ref.replace("Patient/", "")
        
        result = await self._request(
            "GET",
            "Condition",
            params={
                "patient": patient_id,
                "_sort": "-onset-date"
            }
        )
        
        if result and "entry" in result:
            return [e.get("resource", {}) for e in result["entry"]]
        return []
    
    # === MedicationStatement (用藥紀錄) ===
    
    async def get_medications(self, patient_ref: str) -> list[dict]:
        """取得病人目前用藥紀錄
        
        Args:
            patient_ref: 病人參考
        
        Returns:
            用藥紀錄列表
        """
        patient_id = patient_ref.replace("Patient/", "")
        
        result = await self._request(
            "GET",
            "MedicationStatement",
            params={
                "patient": patient_id,
                "status": "active"
            }
        )
        
        if result and "entry" in result:
            return [e.get("resource", {}) for e in result["entry"]]
        return []
    
    # === Procedure (處置紀錄) ===
    
    async def get_procedures(self, patient_ref: str, count: int = 10) -> list[dict]:
        """取得病人處置紀錄
        
        Args:
            patient_ref: 病人參考
            count: 最多取回筆數
        
        Returns:
            處置紀錄列表
        """
        patient_id = patient_ref.replace("Patient/", "")
        
        result = await self._request(
            "GET",
            "Procedure",
            params={
                "patient": patient_id,
                "_sort": "-date",
                "_count": str(count)
            }
        )
        
        if result and "entry" in result:
            return [e.get("resource", {}) for e in result["entry"]]
        return []
    
    # === Lab Observations (檢驗資料) ===
    
    async def get_lab_observations(
        self, 
        patient_ref: str,
        category: str = "laboratory",
        count: int = 50
    ) -> list[dict]:
        """取得病人檢驗資料
        
        Args:
            patient_ref: 病人參考
            category: 類別 (laboratory, vital-signs 等)
            count: 最多取回筆數
        
        Returns:
            檢驗資料列表
        """
        patient_id = patient_ref.replace("Patient/", "")
        
        result = await self._request(
            "GET",
            "Observation",
            params={
                "patient": patient_id,
                "category": category,
                "_sort": "-date",
                "_count": str(count)
            }
        )
        
        if result and "entry" in result:
            return [e.get("resource", {}) for e in result["entry"]]
        return []
    
    async def get_lab_by_codes(
        self, 
        patient_ref: str, 
        loinc_codes: list[str],
        count: int = 5
    ) -> dict[str, list[dict]]:
        """依 LOINC 代碼取得特定檢驗資料
        
        常用 LOINC 代碼:
        - 2160-0: Creatinine (血清肌酸酐)
        - 33914-3: eGFR (腎絲球過濾率)
        - 3094-0: BUN (血中尿素氮)
        - 1742-6: ALT (丙氨酸轉氨酶)
        - 1920-8: AST (天門冬氨酸轉氨酶)
        - 1975-2: Bilirubin Total (總膽紅素)
        - 3016-3: TSH (促甲狀腺激素)
        - 3026-2: T4 Free (游離甲狀腺素)
        - 718-7: Hemoglobin (血紅素)
        - 6690-2: WBC (白血球)
        - 777-3: Platelet (血小板)
        
        Args:
            patient_ref: 病人參考
            loinc_codes: LOINC 代碼列表
            count: 每個代碼最多取回筆數
        
        Returns:
            以 LOINC 代碼為 key 的檢驗資料字典
        """
        patient_id = patient_ref.replace("Patient/", "")
        results = {}
        
        for code in loinc_codes:
            result = await self._request(
                "GET",
                "Observation",
                params={
                    "patient": patient_id,
                    "code": code,
                    "_sort": "-date",
                    "_count": str(count)
                }
            )
            
            if result and "entry" in result:
                results[code] = [e.get("resource", {}) for e in result["entry"]]
            else:
                results[code] = []
        
        return results
    
    # === MedicationRequest ===
    
    async def create_medication_request(self, data: dict) -> Optional[dict]:
        """建立 MedicationRequest（最終核准時）"""
        return await self._request("POST", "MedicationRequest", data=data)
    
    async def create_medication_request_with_error(self, data: dict) -> tuple[Optional[dict], Optional[str]]:
        """建立 MedicationRequest 並返回結果和錯誤訊息
        
        Returns:
            (result, error_message) tuple
        """
        url = f"{self.base_url}/MedicationRequest"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                headers = {"Content-Type": "application/fhir+json"}
                response = await client.post(url, json=data, headers=headers)
                
                if response.status_code in [200, 201]:
                    response.encoding = "utf-8"
                    return response.json(), None
                else:
                    # 提取錯誤訊息
                    error_text = response.text[:2000] if response.text else "No error message"
                    try:
                        error_json = response.json()
                        # 處理 FHIR OperationOutcome
                        if error_json.get("resourceType") == "OperationOutcome":
                            issues = error_json.get("issue", [])
                            if issues:
                                error_details = []
                                for issue in issues[:5]:  # 最多顯示 5 個問題
                                    severity = issue.get("severity", "unknown")
                                    code = issue.get("code", "unknown")
                                    details = issue.get("details", {})
                                    text = details.get("text") or details.get("display") or issue.get("diagnostics", "")
                                    location = issue.get("location", [])
                                    location_str = ", ".join(location[:3]) if location else ""
                                    
                                    issue_msg = f"{severity}: {code}"
                                    if text:
                                        issue_msg += f" - {text}"
                                    if location_str:
                                        issue_msg += f" (at: {location_str})"
                                    error_details.append(issue_msg)
                                
                                error_text = "; ".join(error_details) if error_details else error_text
                        # 處理其他 JSON 錯誤格式
                        elif "issue" in error_json:
                            issues = error_json.get("issue", [])
                            error_details = "; ".join([
                                f"{issue.get('severity', '')}: {issue.get('code', '')} - {issue.get('details', {}).get('text', '')}"
                                for issue in issues[:5]
                            ])
                            error_text = error_details if error_details else error_text
                        # 如果有 message 欄位
                        elif "message" in error_json:
                            error_text = error_json.get("message", error_text)
                    except Exception as parse_error:
                        # 如果 JSON 解析失敗，使用原始文字
                        logger.warning(f"Failed to parse error response as JSON: {parse_error}")
                    
                    logger.error(
                        f"FHIR MedicationRequest creation failed: POST {url} - "
                        f"Status: {response.status_code}, Response: {error_text[:500]}"
                    )
                    # 保存完整錯誤訊息（最多 2000 字符）
                    return None, f"HTTP {response.status_code}: {error_text[:2000]}"
                    
            except httpx.TimeoutException as e:
                error_msg = f"Timeout: {str(e)}"
                logger.error(f"FHIR request timeout: POST {url} - {error_msg}")
                return None, error_msg
            except httpx.RequestError as e:
                error_msg = f"Request error: {str(e)}"
                logger.error(f"FHIR request error: POST {url} - {error_msg}")
                return None, error_msg
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"FHIR unexpected error: POST {url} - {error_msg}")
                return None, error_msg
    
    def build_medication_request(
        self,
        patient_ref: str,
        service_request_ref: str,
        draft: dict,
        requester_ref: str,
        occurrence_datetime: Optional[str] = None,
        route: Optional[dict] = None
    ) -> dict:
        """建構 MedicationRequest FHIR 資源
        
        符合 FHIR R4 規範和 TW Core MedicationRequest Profile 要求
        參考: https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition-MedicationRequest-twcore.html
        
        TW Core 必要欄位:
        - subject (必須)
        - medicationCodeableConcept (必須)
        - authoredOn (必須)
        - requester (必須)
        - dosageInstruction.doseAndRate.doseQuantity.value 和 unit (MBq) (必須)
        - basedOn → ServiceRequest reference (必須)
        
        新增欄位:
        - dosageInstruction.timing.event: 期望執行時間（來自 ServiceRequest.occurrenceDateTime）
        - dosageInstruction.route: 給藥途徑（來自 rules_config.yaml）
        """
        from datetime import datetime, timezone
        
        # 確保 medicationCodeableConcept 有 text（如果沒有 display）
        medication_code = draft.get("radiopharmaceuticalCode", "")
        medication_display = draft.get("radiopharmaceuticalDisplay", "") or medication_code
        
        # 取得劑量值
        dose_value = draft.get("suggestedDose", {}).get("value")
        dose_unit = draft.get("suggestedDose", {}).get("unit", "MBq")
        
        # 建構 dosageInstruction
        dosage_instruction = {
            "doseAndRate": [
                {
                    "doseQuantity": {
                        "value": dose_value,  # TW Core 必要欄位
                        "unit": dose_unit,  # 必須使用 UCUM 'MBq'（D2 規範）
                        "system": "http://unitsofmeasure.org",  # UCUM 系統
                        "code": "MBq"  # UCUM 代碼
                    }
                }
            ]
        }
        
        # 新增 timing.event（期望執行時間）
        if occurrence_datetime:
            dosage_instruction["timing"] = {
                "event": [occurrence_datetime]
            }
        
        # 新增 route（給藥途徑）
        if route:
            dosage_instruction["route"] = {
                "coding": [
                    {
                        "system": route.get("system", "http://snomed.info/sct"),
                        "code": route.get("code", "47625008"),
                        "display": route.get("display", "Intravenous route")
                    }
                ]
            }
        
        # 建構 MedicationRequest（符合 TW Core Profile）
        medication_request = {
            "resourceType": "MedicationRequest",
            "meta": {
                "profile": [
                    "https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/MedicationRequest-twcore"
                ]
            },
            "status": "active",
            "intent": "order",
            "authoredOn": datetime.now(timezone.utc).isoformat(),  # TW Core 必要欄位
            "medicationCodeableConcept": {
                # 符合 TW Core CodeableConcept 要求
                "coding": [
                    {
                        "system": "urn:oid:1.2.3.4.5.6.7.8.9",  # 本地代碼系統（符合 D2 規範）
                        "code": medication_code,
                        "display": medication_display
                    }
                ],
                "text": medication_display  # TW Core 建議提供 text
            },
            "subject": {
                "reference": patient_ref  # TW Core 必要欄位
            },
            "requester": {
                "reference": requester_ref  # TW Core 必要欄位
            },
            "basedOn": [
                {"reference": service_request_ref}  # TW Core 必要欄位（D3 規範）
            ],
            "dosageInstruction": [dosage_instruction]
        }
        
        # 只有在有 notes 時才添加（TW Core 可選欄位）
        if draft.get("notes"):
            medication_request["note"] = [
                {
                    "text": draft.get("notes", "")
                }
            ]
        
        return medication_request


