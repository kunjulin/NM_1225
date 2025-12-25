"""
規則引擎
依據 spec/04_rules_engine.md 實作 CDS 規則評估
"""
import json
from typing import Optional

from app.schemas.rule_eval import RuleEval, RuleFlag, Severity
from app.models import OrderCase
from app.rules.config import RulesConfig


class RuleEngine:
    """規則引擎
    
    評估案件並產生 RuleEval 結果
    包含 overallSeverity、isBatchEligible、flags[]
    """
    
    def __init__(self):
        self.config = RulesConfig()
    
    def evaluate(self, case: OrderCase) -> RuleEval:
        """評估案件
        
        Args:
            case: OrderCase 物件
            
        Returns:
            RuleEval 評估結果
        """
        flags: list[RuleFlag] = []
        
        # 解析資料
        local_facts = json.loads(case.local_facts_json or "{}")
        draft = json.loads(case.draft_json or "{}")
        snapshot = json.loads(case.snapshot_json or "{}")
        
        # === 檢查必要資料 ===
        
        # 體重檢查
        weight = local_facts.get("weightKg", {}).get("value")
        if not weight and not snapshot.get("weightKg"):
            flags.append(RuleFlag(
                code="MISSING_WEIGHT",
                severity=Severity.FAIL,
                title="缺乏體重資料",
                explain="無法計算適當劑量，請補齊體重資料",
                recommendation="請從病人快照接受自動填入或手動輸入體重",
                tags=["dose", "required"]
            ))
        
        # 腎功能檢查（特定檢查需要）
        exam_code = draft.get("examCode") or snapshot.get("examCode")
        if exam_code in ["MAG3", "DTPA"]:
            egfr = local_facts.get("eGFR", {}).get("value")
            if not egfr:
                flags.append(RuleFlag(
                    code="MISSING_RENAL_FUNCTION",
                    severity=Severity.WARN,
                    title="缺乏腎功能資料",
                    explain="腎功能掃描建議提供 eGFR 資料",
                    recommendation="請補齊腎功能資料",
                    tags=["renal", "recommended"]
                ))
        
        # === 劑量檢查 ===
        
        suggested_dose = draft.get("suggestedDose", {})
        dose_value = suggested_dose.get("value")
        
        if dose_value and exam_code:
            # 取得劑量範圍
            dose_range = self.config.get_dose_range(exam_code)
            if dose_range:
                min_dose, max_dose = dose_range
                if dose_value < min_dose or dose_value > max_dose:
                    flags.append(RuleFlag(
                        code="DOSE_OUT_OF_RANGE",
                        severity=Severity.WARN,
                        title="劑量超出建議範圍",
                        explain=f"建議劑量範圍為 {min_dose}-{max_dose} MBq，目前為 {dose_value} MBq",
                        recommendation="請確認劑量或提供 Override 理由",
                        tags=["dose"]
                    ))
        
        # === Override 檢查 ===
        
        override = draft.get("override", {})
        if override.get("isOverride"):
            if override.get("reason"):
                flags.append(RuleFlag(
                    code="OVERRIDE_WITH_REASON",
                    severity=Severity.INFO,
                    title="醫師已提供 Override 理由",
                    explain=f"Override 理由: {override.get('reason')}",
                    tags=["override"]
                ))
            else:
                flags.append(RuleFlag(
                    code="OVERRIDE_REQUIRES_REVIEW",
                    severity=Severity.WARN,
                    title="Override 需要審查",
                    explain="醫師偏離建議劑量但未提供理由",
                    recommendation="請補充 Override 理由",
                    tags=["override"]
                ))
        
        # === 檢查藥物匹配 ===
        
        radiopharm_code = draft.get("radiopharmaceuticalCode")
        if exam_code and radiopharm_code:
            expected_radiopharm = self.config.get_radiopharmaceutical(exam_code)
            if expected_radiopharm and radiopharm_code != expected_radiopharm:
                flags.append(RuleFlag(
                    code="EXAM_DRUG_MISMATCH",
                    severity=Severity.FAIL,
                    title="檢查與藥物不匹配",
                    explain=f"檢查 {exam_code} 應使用 {expected_radiopharm}，目前為 {radiopharm_code}",
                    recommendation="請修正放射藥物選擇",
                    tags=["mismatch"]
                ))
        
        # === 本地資料使用標記 ===
        
        for key, fact in local_facts.items():
            if fact.get("source") in ["MANUAL", "AUTOFILL"]:
                flags.append(RuleFlag(
                    code="LOCAL_DATA_USED",
                    severity=Severity.INFO,
                    title=f"使用本地資料: {key}",
                    explain=f"資料來源: {fact.get('source')}",
                    tags=["local_data"]
                ))
        
        # === 計算整體結果 ===
        
        # 找出最高嚴重度
        severity_order = {Severity.FAIL: 3, Severity.WARN: 2, Severity.INFO: 1, Severity.PASS: 0}
        max_severity = Severity.PASS
        for flag in flags:
            if severity_order.get(flag.severity, 0) > severity_order.get(max_severity, 0):
                max_severity = flag.severity
        
        # 批次核准資格
        has_fail = any(f.severity == Severity.FAIL for f in flags)
        is_batch_eligible = not has_fail and max_severity != Severity.FAIL
        
        return RuleEval(
            overallSeverity=max_severity,
            isBatchEligible=is_batch_eligible,
            flags=flags
        )

