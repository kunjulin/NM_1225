"""
LLM 服務
負責呼叫 OpenAI 相容 API 進行臨床分析
"""
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Any

import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AppSettings, 
    LLMSettingsKeys, 
    LLMAnalysis, 
    AnalysisStatus, 
    TriggerType,
    OrderCase,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT_TEMPLATE,
)
from app.schemas.snapshot import PatientSnapshotResponse
from app.services.snapshot_service import SnapshotService


logger = logging.getLogger(__name__)


class LLMSettings:
    """LLM 設定資料類別"""
    def __init__(
        self,
        endpoint_url: str = "",
        model_name: str = "gpt-4",
        api_key: str = "",
        system_prompt: str = "",
        user_prompt_template: str = "",
        auto_analyze: bool = False,
        timeout_seconds: float = 60.0,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        disable_thinking_mode: bool = False,
    ):
        self.endpoint_url = endpoint_url
        self.model_name = model_name
        self.api_key = api_key
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.user_prompt_template = user_prompt_template or DEFAULT_USER_PROMPT_TEMPLATE
        self.auto_analyze = auto_analyze
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.disable_thinking_mode = disable_thinking_mode
    
    def is_configured(self) -> bool:
        """檢查是否已設定 LLM"""
        return bool(self.endpoint_url)
    
    def get_api_payload_extra_params(self) -> dict:
        """取得 API 請求的額外參數
        
        根據設定返回需要添加的額外參數
        """
        extra_params = {}
        
        if self.disable_thinking_mode:
            # 禁用 thinking mode
            extra_params["thinking_mode"] = False
            logger.debug(f"為模型 {self.model_name} 禁用 thinking mode（手動設定）")
        
        return extra_params
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """轉換為字典"""
        result = {
            "endpoint_url": self.endpoint_url,
            "model_name": self.model_name,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "auto_analyze": self.auto_analyze,
            "timeout_seconds": self.timeout_seconds,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "disable_thinking_mode": self.disable_thinking_mode,
        }
        if include_sensitive:
            result["api_key"] = self.api_key
        else:
            # 只顯示是否有設定 API Key
            result["has_api_key"] = bool(self.api_key)
        return result


class LLMAnalysisResult:
    """LLM 分析結果"""
    def __init__(
        self,
        id: str,
        case_id: str,
        status: str,
        result: Optional[dict] = None,
        error_message: Optional[str] = None,
        latency_ms: Optional[int] = None,
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.case_id = case_id
        self.status = status
        self.result = result
        self.error_message = error_message
        self.latency_ms = latency_ms
        self.created_at = created_at
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": self.id,
            "caseId": self.case_id,
            "status": self.status,
            "result": self.result,
            "errorMessage": self.error_message,
            "latencyMs": self.latency_ms,
            "createdAt": self.created_at,
        }


class LLMService:
    """LLM 服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_settings(self) -> LLMSettings:
        """取得 LLM 設定"""
        settings = LLMSettings()
        
        # 查詢所有 LLM 相關設定
        keys = [
            LLMSettingsKeys.ENDPOINT_URL,
            LLMSettingsKeys.MODEL_NAME,
            LLMSettingsKeys.API_KEY,
            LLMSettingsKeys.SYSTEM_PROMPT,
            LLMSettingsKeys.USER_PROMPT_TEMPLATE,
            LLMSettingsKeys.AUTO_ANALYZE,
            LLMSettingsKeys.TIMEOUT_SECONDS,
            LLMSettingsKeys.MAX_TOKENS,
            LLMSettingsKeys.TEMPERATURE,
            LLMSettingsKeys.DISABLE_THINKING_MODE,
        ]
        
        result = await self.db.execute(
            select(AppSettings).where(AppSettings.key.in_(keys))
        )
        rows = result.scalars().all()
        
        # 解析設定值
        for row in rows:
            try:
                if row.key == LLMSettingsKeys.ENDPOINT_URL:
                    settings.endpoint_url = row.value
                elif row.key == LLMSettingsKeys.MODEL_NAME:
                    settings.model_name = row.value or "gpt-4"
                elif row.key == LLMSettingsKeys.API_KEY:
                    settings.api_key = row.value
                elif row.key == LLMSettingsKeys.SYSTEM_PROMPT:
                    settings.system_prompt = row.value or DEFAULT_SYSTEM_PROMPT
                elif row.key == LLMSettingsKeys.USER_PROMPT_TEMPLATE:
                    settings.user_prompt_template = row.value or DEFAULT_USER_PROMPT_TEMPLATE
                elif row.key == LLMSettingsKeys.AUTO_ANALYZE:
                    settings.auto_analyze = row.value.lower() == "true"
                elif row.key == LLMSettingsKeys.TIMEOUT_SECONDS:
                    settings.timeout_seconds = float(row.value) if row.value else 60.0
                elif row.key == LLMSettingsKeys.MAX_TOKENS:
                    settings.max_tokens = int(row.value) if row.value else 4096
                elif row.key == LLMSettingsKeys.TEMPERATURE:
                    settings.temperature = float(row.value) if row.value else 0.1
                elif row.key == LLMSettingsKeys.DISABLE_THINKING_MODE:
                    settings.disable_thinking_mode = row.value.lower() == "true" if row.value else False
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse setting {row.key}: {e}")
        
        return settings
    
    async def save_settings(self, settings: LLMSettings) -> None:
        """儲存 LLM 設定"""
        now = datetime.now(timezone.utc).isoformat()
        
        settings_map = [
            (LLMSettingsKeys.ENDPOINT_URL, settings.endpoint_url, "LLM API Endpoint URL", False),
            (LLMSettingsKeys.MODEL_NAME, settings.model_name, "LLM Model Name", False),
            (LLMSettingsKeys.API_KEY, settings.api_key, "LLM API Key", True),
            (LLMSettingsKeys.SYSTEM_PROMPT, settings.system_prompt, "System Prompt", False),
            (LLMSettingsKeys.USER_PROMPT_TEMPLATE, settings.user_prompt_template, "User Prompt Template", False),
            (LLMSettingsKeys.AUTO_ANALYZE, str(settings.auto_analyze).lower(), "Auto Analyze on Case View", False),
            (LLMSettingsKeys.TIMEOUT_SECONDS, str(settings.timeout_seconds), "Request Timeout (seconds)", False),
            (LLMSettingsKeys.MAX_TOKENS, str(settings.max_tokens), "Max Tokens", False),
            (LLMSettingsKeys.TEMPERATURE, str(settings.temperature), "Temperature", False),
            (LLMSettingsKeys.DISABLE_THINKING_MODE, str(settings.disable_thinking_mode).lower(), "Disable Thinking Mode", False),
        ]
        
        for key, value, description, is_sensitive in settings_map:
            # 嘗試更新現有記錄
            result = await self.db.execute(
                select(AppSettings).where(AppSettings.key == key)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.value = value
                existing.updated_at = now
            else:
                new_setting = AppSettings(
                    key=key,
                    value=value,
                    description=description,
                    is_sensitive=is_sensitive,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(new_setting)
        
        await self.db.commit()
    
    async def test_connection(self) -> dict:
        """測試 LLM 連線
        
        Returns:
            dict: 包含 success, message, latency_ms
        """
        settings = await self.get_settings()
        
        if not settings.is_configured():
            return {
                "success": False,
                "message": "LLM endpoint URL 未設定",
                "latency_ms": None,
            }
        
        try:
            start_time = time.time()
            
            # 組合請求
            headers = {"Content-Type": "application/json"}
            if settings.api_key:
                headers["Authorization"] = f"Bearer {settings.api_key}"
            
            payload = {
                "model": settings.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'OK' to confirm connection."},
                ],
                "max_tokens": 10,
                "temperature": 0,
            }
            
            # 添加額外參數（如禁用 thinking mode）
            payload.update(settings.get_api_payload_extra_params())
            
            async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
                response = await client.post(
                    f"{settings.endpoint_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "連線成功",
                    "latency_ms": latency_ms,
                }
            else:
                return {
                    "success": False,
                    "message": f"HTTP {response.status_code}: {response.text[:200]}",
                    "latency_ms": latency_ms,
                }
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": f"連線超時（{settings.timeout_seconds}秒）",
                "latency_ms": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"連線失敗: {str(e)}",
                "latency_ms": None,
            }
    
    async def analyze_case(
        self,
        case_id: str,
        triggered_by: str,
        trigger_type: str = TriggerType.MANUAL,
    ) -> LLMAnalysisResult:
        """對案件執行 LLM 分析
        
        Args:
            case_id: 案件 ID
            triggered_by: 觸發者
            trigger_type: 觸發類型 (MANUAL/AUTO)
            
        Returns:
            LLMAnalysisResult: 分析結果
        """
        now = datetime.now(timezone.utc).isoformat()
        analysis_id = str(uuid.uuid4())
        
        # 取得設定
        settings = await self.get_settings()
        
        if not settings.is_configured():
            return LLMAnalysisResult(
                id=analysis_id,
                case_id=case_id,
                status=AnalysisStatus.FAILED,
                error_message="LLM 尚未設定，請至設定頁面配置 LLM API",
                created_at=now,
            )
        
        # 建立分析記錄
        analysis = LLMAnalysis(
            id=analysis_id,
            case_id=case_id,
            status=AnalysisStatus.PROCESSING,
            model_name=settings.model_name,
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            created_at=now,
            updated_at=now,
        )
        self.db.add(analysis)
        await self.db.flush()
        
        try:
            # 取得案件快照
            snapshot_service = SnapshotService(self.db)
            snapshot = await snapshot_service.get_snapshot(case_id, refresh=False)
            
            # 組合 input payload
            input_payload = self._build_input_payload(snapshot)
            
            # 組合 prompt
            user_prompt = settings.user_prompt_template.replace(
                "{INPUT_PAYLOAD}", 
                json.dumps(input_payload, ensure_ascii=False, indent=2)
            )
            
            analysis.prompt_used = f"[SYSTEM]\n{settings.system_prompt}\n\n[USER]\n{user_prompt}"
            
            # 呼叫 LLM
            start_time = time.time()
            
            headers = {"Content-Type": "application/json"}
            if settings.api_key:
                headers["Authorization"] = f"Bearer {settings.api_key}"
            
            payload = {
                "model": settings.model_name,
                "messages": [
                    {"role": "system", "content": settings.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature,
            }
            
            # 添加額外參數（如禁用 thinking mode）
            payload.update(settings.get_api_payload_extra_params())
            
            async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
                response = await client.post(
                    f"{settings.endpoint_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            
            latency_ms = int((time.time() - start_time) * 1000)
            analysis.latency_ms = latency_ms
            
            if response.status_code != 200:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = f"HTTP {response.status_code}: {response.text[:500]}"
                analysis.updated_at = datetime.now(timezone.utc).isoformat()
                await self.db.commit()
                
                return LLMAnalysisResult(
                    id=analysis_id,
                    case_id=case_id,
                    status=AnalysisStatus.FAILED,
                    error_message=analysis.error_message,
                    latency_ms=latency_ms,
                    created_at=now,
                )
            
            # 解析回應
            response_data = response.json()
            analysis.raw_response = json.dumps(response_data, ensure_ascii=False)
            
            # 提取 token 使用量
            usage = response_data.get("usage", {})
            analysis.prompt_tokens = usage.get("prompt_tokens")
            analysis.completion_tokens = usage.get("completion_tokens")
            analysis.total_tokens = usage.get("total_tokens")
            
            # 提取 LLM 回應內容
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 嘗試解析 JSON
            try:
                # 清理可能的 markdown 標記
                cleaned_content = content.strip()
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.startswith("```"):
                    cleaned_content = cleaned_content[3:]
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
                
                result_json = json.loads(cleaned_content)
                analysis.result_json = json.dumps(result_json, ensure_ascii=False)
                analysis.status = AnalysisStatus.COMPLETED
                
            except json.JSONDecodeError as e:
                # JSON 解析失敗，但仍標記為完成，將原始內容存入
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                analysis.result_json = json.dumps({
                    "raw_content": content,
                    "parse_error": str(e),
                }, ensure_ascii=False)
                analysis.status = AnalysisStatus.COMPLETED
                result_json = {"raw_content": content}
            
            analysis.updated_at = datetime.now(timezone.utc).isoformat()
            await self.db.commit()
            
            return LLMAnalysisResult(
                id=analysis_id,
                case_id=case_id,
                status=analysis.status,
                result=result_json,
                latency_ms=latency_ms,
                created_at=now,
            )
            
        except httpx.TimeoutException as e:
            error_msg = f"連線超時（{settings.timeout_seconds}秒）"
            logger.error(f"LLM analysis timeout for case {case_id}: {error_msg}")
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = error_msg
            analysis.updated_at = datetime.now(timezone.utc).isoformat()
            await self.db.commit()
            
            return LLMAnalysisResult(
                id=analysis_id,
                case_id=case_id,
                status=AnalysisStatus.FAILED,
                error_message=error_msg,
                created_at=now,
            )
        except httpx.RequestError as e:
            error_msg = f"網路連線錯誤: {str(e)}"
            logger.error(f"LLM analysis network error for case {case_id}: {error_msg}", exc_info=True)
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = error_msg
            analysis.updated_at = datetime.now(timezone.utc).isoformat()
            await self.db.commit()
            
            return LLMAnalysisResult(
                id=analysis_id,
                case_id=case_id,
                status=AnalysisStatus.FAILED,
                error_message=error_msg,
                created_at=now,
            )
        except json.JSONDecodeError as e:
            error_msg = f"JSON 解析錯誤: {str(e)}"
            logger.error(f"LLM analysis JSON decode error for case {case_id}: {error_msg}", exc_info=True)
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = error_msg
            analysis.updated_at = datetime.now(timezone.utc).isoformat()
            await self.db.commit()
            
            return LLMAnalysisResult(
                id=analysis_id,
                case_id=case_id,
                status=AnalysisStatus.FAILED,
                error_message=error_msg,
                created_at=now,
            )
        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_traceback = traceback.format_exc()
            logger.error(
                f"LLM analysis failed for case {case_id}: {error_msg}\n{traceback.format_exc()}",
                exc_info=True
            )
            analysis.status = AnalysisStatus.FAILED
            # 儲存詳細錯誤訊息（包含 traceback，但限制長度）
            full_error = f"{error_msg}\n\n詳細資訊:\n{error_traceback[:1000]}"  # 限制長度避免資料庫欄位過長
            analysis.error_message = full_error
            analysis.updated_at = datetime.now(timezone.utc).isoformat()
            await self.db.commit()
            
            return LLMAnalysisResult(
                id=analysis_id,
                case_id=case_id,
                status=AnalysisStatus.FAILED,
                error_message=error_msg,  # 前端只顯示簡短訊息
                created_at=now,
            )
    
    async def get_latest_analysis(self, case_id: str) -> Optional[LLMAnalysisResult]:
        """取得案件最近的分析結果
        
        Args:
            case_id: 案件 ID
            
        Returns:
            LLMAnalysisResult or None
        """
        result = await self.db.execute(
            select(LLMAnalysis)
            .where(LLMAnalysis.case_id == case_id)
            .order_by(desc(LLMAnalysis.created_at))
            .limit(1)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return None
        
        result_json = None
        if analysis.result_json:
            try:
                result_json = json.loads(analysis.result_json)
            except json.JSONDecodeError:
                pass
        
        return LLMAnalysisResult(
            id=analysis.id,
            case_id=analysis.case_id,
            status=analysis.status,
            result=result_json,
            error_message=analysis.error_message,
            latency_ms=analysis.latency_ms,
            created_at=analysis.created_at,
        )
    
    async def get_analysis_history(self, case_id: str, limit: int = 10) -> list[LLMAnalysisResult]:
        """取得案件的分析歷史
        
        Args:
            case_id: 案件 ID
            limit: 最大筆數
            
        Returns:
            list[LLMAnalysisResult]
        """
        result = await self.db.execute(
            select(LLMAnalysis)
            .where(LLMAnalysis.case_id == case_id)
            .order_by(desc(LLMAnalysis.created_at))
            .limit(limit)
        )
        analyses = result.scalars().all()
        
        results = []
        for analysis in analyses:
            result_json = None
            if analysis.result_json:
                try:
                    result_json = json.loads(analysis.result_json)
                except json.JSONDecodeError:
                    pass
            
            results.append(LLMAnalysisResult(
                id=analysis.id,
                case_id=analysis.case_id,
                status=analysis.status,
                result=result_json,
                error_message=analysis.error_message,
                latency_ms=analysis.latency_ms,
                created_at=analysis.created_at,
            ))
        
        return results
    
    async def get_failed_analyses(
        self, 
        limit: int = 50,
        case_id: Optional[str] = None
    ) -> list[LLMAnalysisResult]:
        """取得失敗的分析記錄
        
        Args:
            limit: 最大筆數
            case_id: 可選的案件 ID 過濾
            
        Returns:
            list[LLMAnalysisResult]: 失敗的分析記錄列表
        """
        query = select(LLMAnalysis).where(
            LLMAnalysis.status == AnalysisStatus.FAILED
        )
        
        if case_id:
            query = query.where(LLMAnalysis.case_id == case_id)
        
        query = query.order_by(desc(LLMAnalysis.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        analyses = result.scalars().all()
        
        results = []
        for analysis in analyses:
            result_json = None
            if analysis.result_json:
                try:
                    result_json = json.loads(analysis.result_json)
                except json.JSONDecodeError:
                    pass
            
            results.append(LLMAnalysisResult(
                id=analysis.id,
                case_id=analysis.case_id,
                status=analysis.status,
                result=result_json,
                error_message=analysis.error_message,
                latency_ms=analysis.latency_ms,
                created_at=analysis.created_at,
            ))
        
        return results
    
    def _build_input_payload(self, snapshot: PatientSnapshotResponse) -> dict:
        """組合 LLM 輸入 payload
        
        將 snapshot 和 ruleEval 轉換為 LLM 可理解的格式
        """
        # 取得檢查類型
        exam_code = snapshot.snapshot.examCode if hasattr(snapshot.snapshot, 'examCode') else None
        if not exam_code and snapshot.draft:
            exam_code = snapshot.draft.examCode
        
        # 組合 ServiceRequest 資訊
        service_request = {
            "serviceRequestRef": snapshot.serviceRequestRef,
            "examCode": exam_code,
            "examDisplay": getattr(snapshot.snapshot, 'examDisplay', None),
            "occurrenceDateTime": snapshot.snapshot.occurrenceDateTime,
            "requesterDisplay": snapshot.snapshot.requesterDisplay,
            "reasonCodeDisplay": snapshot.snapshot.reasonCodeDisplay,
        }
        
        # 組合病人快照（移除敏感資訊）
        patient_snapshot = {
            "patientRef": snapshot.patientRef,
            "weightKg": snapshot.snapshot.weightKg,  # 體重資訊
            "encounters": [e.model_dump() for e in snapshot.snapshot.encounters] if snapshot.snapshot.encounters else [],
            "conditionList": [c.model_dump() for c in snapshot.snapshot.conditionList] if snapshot.snapshot.conditionList else [],
            "medications": [m.model_dump() for m in snapshot.snapshot.medications] if snapshot.snapshot.medications else [],
            "procedures": [p.model_dump() for p in snapshot.snapshot.procedures] if snapshot.snapshot.procedures else [],
            "allergyList": [a.model_dump() for a in snapshot.snapshot.allergyList] if snapshot.snapshot.allergyList else [],
            "labResults": snapshot.snapshot.labResults.model_dump() if snapshot.snapshot.labResults else None,
        }
        
        # 組合 RuleEval
        rule_eval = None
        if snapshot.ruleEval:
            rule_eval = {
                "overallSeverity": snapshot.ruleEval.overallSeverity,
                "isBatchEligible": snapshot.ruleEval.isBatchEligible,
                "flags": [
                    {
                        "code": f.code,
                        "severity": f.severity,
                        "title": f.title,
                        "explain": f.explain,
                        "recommendation": f.recommendation,
                    }
                    for f in snapshot.ruleEval.flags
                ],
            }
        
        return {
            "examType": exam_code,
            "serviceRequest": service_request,
            "patientSnapshot": patient_snapshot,
            "ruleEval": rule_eval,
        }

