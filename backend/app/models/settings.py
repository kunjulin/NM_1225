"""
AppSettings 資料模型
系統設定儲存（包含 LLM 設定）
"""
from typing import Optional

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSettings(Base):
    """AppSettings 資料表
    
    儲存系統設定，使用 key-value 格式
    主要用於 LLM 設定，但可擴展用於其他系統設定
    """
    __tablename__ = "app_settings"
    
    # 主鍵：設定鍵名
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    # 設定值（JSON 格式字串）
    value: Mapped[str] = mapped_column(Text, default='')
    
    # 設定描述
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 是否為敏感資料（如 API Key）
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 時間戳記
    created_at: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[str] = mapped_column(String(50))


# LLM 設定的預設鍵名常數
class LLMSettingsKeys:
    """LLM 設定鍵名常數"""
    ENDPOINT_URL = "llm.endpoint_url"           # LLM API endpoint URL
    MODEL_NAME = "llm.model_name"               # 模型名稱
    API_KEY = "llm.api_key"                     # API Key（加密儲存）
    SYSTEM_PROMPT = "llm.system_prompt"         # System Prompt
    USER_PROMPT_TEMPLATE = "llm.user_prompt_template"  # User Prompt Template
    AUTO_ANALYZE = "llm.auto_analyze"           # 是否自動分析
    TIMEOUT_SECONDS = "llm.timeout_seconds"     # 請求超時秒數
    MAX_TOKENS = "llm.max_tokens"               # 最大 tokens
    TEMPERATURE = "llm.temperature"             # Temperature 參數
    DISABLE_THINKING_MODE = "llm.disable_thinking_mode"  # 是否禁用 thinking mode


# 預設的 System Prompt
DEFAULT_SYSTEM_PROMPT = """You are a clinical decision support assistant for Nuclear Medicine. 
You MUST base your reasoning ONLY on the provided FHIR snapshot and CDS flags. 
Do NOT use external knowledge or assumptions beyond what is explicitly present in the input.
If information is missing or unclear, you MUST say "INSUFFICIENT_DATA" and list exactly what is missing.

Safety and hallucination control:
- Do not invent diagnoses, lab values, allergies, or indications.
- Do not infer contraindications unless explicitly supported by the snapshot.
- Every clinical claim MUST cite one or more evidence references from the input (resourceType/id/path).
- If no evidence exists, state that evidence is not available.

Output format:
- Return ONLY valid JSON that conforms to the provided JSON schema.
- Do not include markdown, explanations, or free text outside JSON.

Task:
Given a nuclear medicine imaging order (e.g., bone scan), summarize the case, assess appropriateness based on the provided indication and clinical context, 
and integrate CDS flags to explain what additional data is required to finalize the medication/protocol decision."""


# 預設的 User Prompt Template
DEFAULT_USER_PROMPT_TEMPLATE = """You will receive:
1) A patient FHIR snapshot (already filtered and de-identified if needed)
2) The imaging order summary (ServiceRequest)
3) CDS evaluation output (RuleEval + flags)

Your job:
- Produce a concise case summary (nuclear medicine relevant)
- Evaluate whether the exam is appropriate GIVEN ONLY the provided indication/context
- Integrate CDS flags to produce an actionable "what to complete next" checklist
- If data is insufficient, return INSUFFICIENT_DATA and specify missing items

Return JSON only, matching this schema:

{
  "examDecision": {
    "status": "APPROPRIATE" | "POTENTIALLY_APPROPRIATE" | "NOT_APPROPRIATE" | "INSUFFICIENT_DATA",
    "rationale": [
      {
        "statement": "string",
        "evidence": [
          {"ref": "ResourceType/id", "path": "string", "snippet": "string"}
        ]
      }
    ],
    "missingData": [
      {
        "dataItem": "WEIGHT_KG" | "RENAL_FUNCTION" | "ALLERGY" | "INDICATION_DETAILS" | "PREGNANCY_STATUS" | "OTHER",
        "whyNeeded": "string",
        "howToObtain": "string"
      }
    ],
    "contraindicationSignals": [
      {
        "signal": "string",
        "severity": "INFO" | "WARN" | "HIGH",
        "evidence": [{"ref":"ResourceType/id","path":"string","snippet":"string"}]
      }
    ]
  },
  "caseSummary": {
    "oneLiner": "string",
    "indication": "string",
    "keyHistory": ["string"],
    "keyLabs": ["string"],
    "allergies": ["string"],
    "recentImaging": ["string"]
  },
  "cdssIntegration": {
    "overallSeverity": "PASS" | "WARN" | "FAIL",
    "isBatchEligible": true | false,
    "flagsExplained": [
      {
        "code": "string",
        "severity": "INFO" | "WARN" | "FAIL",
        "title": "string",
        "explain": "string",
        "recommendation": "string"
      }
    ],
    "nextActions": [
      {
        "action": "COLLECT_DATA" | "ADJUST_PROTOCOL" | "PHARM_REVIEW" | "CONTACT_ORDERING_MD" | "DEFER_EXAM",
        "details": "string"
      }
    ]
  },
  "quality": {
    "limitations": ["string"],
    "confidence": "HIGH" | "MEDIUM" | "LOW"
  }
}

Input payload:
{INPUT_PAYLOAD}"""

