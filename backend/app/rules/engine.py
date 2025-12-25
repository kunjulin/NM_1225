"""
規則引擎
依據 spec/04_rules_engine.md 實作 CDS 規則評估
包含 NA-2024 劑量計算
"""
import json
from typing import Optional
from dataclasses import dataclass

from app.schemas.rule_eval import RuleEval, RuleFlag, Severity
from app.models import OrderCase
from app.rules.config import RulesConfig


@dataclass
class DoseCalculationResult:
    """NA-2024 劑量計算結果"""
    suggested_dose: float       # 建議劑量 (MBq)
    min_dose: float            # 最小劑量 (MBq)
    max_dose: float            # 最大劑量 (MBq)
    formula: str               # 計算公式說明
    reference: str             # 參考標準
    weight_used: Optional[float]  # 使用的體重 (kg)
    is_pediatric: bool         # 是否為兒童劑量計算


class RuleEngine:
    """規則引擎
    
    評估案件並產生 RuleEval 結果
    包含 overallSeverity、isBatchEligible、flags[]
    """
    
    # 兒童體重閾值 (kg)，低於此值使用 NA-2024 兒童劑量計算
    PEDIATRIC_WEIGHT_THRESHOLD = 70.0
    
    def __init__(self):
        self.config = RulesConfig()
    
    def calculate_na2024_dose(
        self, 
        exam_code: str, 
        weight_kg: Optional[float]
    ) -> Optional[DoseCalculationResult]:
        """根據 NA-2024 指引計算劑量
        
        Args:
            exam_code: 檢查代碼
            weight_kg: 病人體重 (kg)
            
        Returns:
            DoseCalculationResult 或 None (如果無法計算)
        """
        na2024 = self.config.get_na2024_config(exam_code)
        if not na2024:
            return None
        
        activity_per_kg = na2024.get("activity_per_kg")
        min_activity = na2024.get("min_activity")
        max_activity = na2024.get("max_activity")
        adult_standard = na2024.get("adult_standard", max_activity)
        
        if not all([activity_per_kg, min_activity, max_activity]):
            return None
        
        # 取得高端係數（如果沒有，使用低端係數）
        activity_per_kg_high = na2024.get("activity_per_kg_high", activity_per_kg)
        
        # 如果沒有體重，只返回範圍資訊
        if not weight_kg:
            return DoseCalculationResult(
                suggested_dose=min_activity,  # 無體重時使用最小劑量
                min_dose=min_activity,
                max_dose=max_activity,
                formula=f"需提供體重以計算個人化劑量 (範圍: {min_activity}-{max_activity} MBq)",
                reference="NA-2024",
                weight_used=None,
                is_pediatric=False
            )
        
        # 判斷是否為兒童（依體重）
        is_pediatric = weight_kg < self.PEDIATRIC_WEIGHT_THRESHOLD
        
        if is_pediatric:
            # 兒童劑量計算: 體重 × activity_per_kg_high (使用高端係數)，但不超過最高劑量
            calculated_high = weight_kg * activity_per_kg_high
            calculated_dose = min(calculated_high, max_activity)
            
            # 確保不小於最小劑量
            if calculated_dose < min_activity:
                calculated_dose = min_activity
            
            formula = f"{weight_kg:.1f} kg × {activity_per_kg_high} MBq/kg = {calculated_high:.1f} MBq"
            if calculated_dose == min_activity:
                formula += f" (使用最小劑量 {min_activity} MBq)"
            elif calculated_dose == max_activity:
                formula += f" (上限 {max_activity} MBq)"
            
            return DoseCalculationResult(
                suggested_dose=round(calculated_dose, 1),
                min_dose=min_activity,
                max_dose=max_activity,
                formula=formula,
                reference="NA-2024",
                weight_used=weight_kg,
                is_pediatric=True
            )
        else:
            # 成人劑量計算 (依據 NA-2024)
            # 建議劑量: 體重 × 高端係數，但不超過最高劑量
            calculated_high = weight_kg * activity_per_kg_high
            suggested = min(calculated_high, max_activity)
            
            # 最大劑量: min(體重 × 高端係數, max_activity)
            calculated_max = weight_kg * activity_per_kg_high
            final_max = min(calculated_max, max_activity)
            
            formula = f"體重 {weight_kg:.1f} kg × {activity_per_kg_high} MBq/kg = {calculated_high:.1f} MBq"
            if suggested == max_activity:
                formula += f" (上限 {max_activity} MBq)"
            formula += f" (範圍: {min_activity}-{final_max:.1f} MBq)"
            
            return DoseCalculationResult(
                suggested_dose=round(suggested, 1),
                min_dose=min_activity,
                max_dose=round(final_max, 1),
                formula=formula,
                reference="NA-2024",
                weight_used=weight_kg,
                is_pediatric=False
            )
    
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
        
        # === 取得體重 ===
        weight = local_facts.get("weightKg", {}).get("value")
        if not weight:
            weight = snapshot.get("weightKg")
        
        # === 取得檢查代碼 ===
        exam_code = draft.get("examCode") or snapshot.get("examCode")
        
        # === 檢查必要資料 ===
        
        # 體重檢查
        if not weight:
            flags.append(RuleFlag(
                code="MISSING_WEIGHT",
                severity=Severity.FAIL,
                title="缺乏體重資料",
                explain="無法計算適當劑量，請補齊體重資料",
                recommendation="請從病人快照接受自動填入或手動輸入體重",
                tags=["dose", "required"]
            ))
        
        # 腎功能檢查（特定檢查需要）
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
        
        # === 劑量檢查 (使用 NA-2024) ===
        
        suggested_dose = draft.get("suggestedDose", {})
        dose_value = suggested_dose.get("value")
        
        if dose_value and exam_code:
            # 使用 NA-2024 計算劑量範圍
            dose_calc = self.calculate_na2024_dose(exam_code, weight)
            
            if dose_calc:
                # 檢查劑量是否在 NA-2024 範圍內
                if dose_value < dose_calc.min_dose:
                    flags.append(RuleFlag(
                        code="DOSE_BELOW_MIN",
                        severity=Severity.FAIL,
                        title="劑量低於最小建議值",
                        explain=f"NA-2024 最小劑量為 {dose_calc.min_dose} MBq，目前為 {dose_value} MBq",
                        recommendation="請調整劑量或提供 Override 理由",
                        tags=["dose", "na2024"]
                    ))
                elif dose_value > dose_calc.max_dose:
                    flags.append(RuleFlag(
                        code="DOSE_ABOVE_MAX",
                        severity=Severity.FAIL,
                        title="劑量超過最大建議值",
                        explain=f"NA-2024 建議最大劑量為 {dose_calc.max_dose} MBq，目前為 {dose_value} MBq",
                        recommendation="請調整劑量或提供 Override 理由",
                        tags=["dose", "na2024"]
                    ))
                
                # 如果劑量與建議值相差超過 20%，發出警告
                if dose_calc.suggested_dose > 0:
                    deviation = abs(dose_value - dose_calc.suggested_dose) / dose_calc.suggested_dose
                    if deviation > 0.2 and dose_value >= dose_calc.min_dose and dose_value <= dose_calc.max_dose:
                        flags.append(RuleFlag(
                            code="DOSE_DEVIATION",
                            severity=Severity.INFO,
                            title="劑量與建議值有差異",
                            explain=f"NA-2024 建議劑量為 {dose_calc.suggested_dose} MBq，目前為 {dose_value} MBq (差異 {deviation*100:.0f}%)",
                            tags=["dose", "na2024"]
                        ))
            else:
                # Fallback 到舊的劑量範圍檢查
                dose_range = self.config.get_dose_range(exam_code)
                if dose_range:
                    min_dose, max_dose = dose_range
                    if dose_value < min_dose or dose_value > max_dose:
                        flags.append(RuleFlag(
                            code="DOSE_OUT_OF_RANGE",
                            severity=Severity.FAIL,
                            title="劑量超出建議範圍",
                            explain=f"建議劑量範圍為 {min_dose}-{max_dose} MBq，目前為 {dose_value} MBq",
                            recommendation="請調整劑量或提供 Override 理由",
                            tags=["dose"]
                        ))
        
        # === Override 檢查 ===
        # 注意：Override 理由不作為 CDS flag，只存在於 draft_json 中
        # 前端會在 "醫師回應 / Override" 區塊顯示 override 理由
        # 這裡只檢查是否有 override 但沒有理由的情況（用於提醒）
        
        override = draft.get("override") or {}
        if override.get("isOverride") and not override.get("reason"):
            # 如果有 override 但沒有理由，提醒需要補充
            flags.append(RuleFlag(
                code="OVERRIDE_REQUIRES_REVIEW",
                severity=Severity.WARN,
                title="Override 需要審查",
                explain="醫師偏離建議劑量但未提供理由",
                recommendation="請補充 Override 理由",
                tags=["override"]
            ))
        
        # === 本地資料使用標記 ===
        
        for key, fact in local_facts.items():
            if isinstance(fact, dict) and fact.get("source") in ["MANUAL", "AUTOFILL"]:
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
        
        # === Override 降階機制 ===
        # 如果有 FAIL 項目，但醫師已提供 Override 理由，則降階為 WARN
        has_fail = any(f.severity == Severity.FAIL for f in flags)
        has_override_reason = override.get("isOverride") and override.get("reason")
        
        if has_fail and has_override_reason:
            # 降階為 WARN，允許送審（但需藥師審查）
            max_severity = Severity.WARN
            # 新增一個說明 flag
            flags.append(RuleFlag(
                code="FAIL_OVERRIDDEN",
                severity=Severity.WARN,
                title="FAIL 已由醫師 Override",
                explain=f"原有 FAIL 項目已由醫師提供理由覆寫，降階為 WARN",
                tags=["override", "downgrade"]
            ))
        
        # 批次核准資格：有 FAIL 且沒有 Override 時不可批次核准
        is_batch_eligible = not (has_fail and not has_override_reason) and max_severity != Severity.FAIL
        
        return RuleEval(
            overallSeverity=max_severity,
            isBatchEligible=is_batch_eligible,
            flags=flags
        )
    
    def get_dose_calculation_for_case(self, case: OrderCase) -> Optional[DoseCalculationResult]:
        """取得案件的 NA-2024 劑量計算結果
        
        Args:
            case: OrderCase 物件
            
        Returns:
            DoseCalculationResult 或 None
        """
        local_facts = json.loads(case.local_facts_json or "{}")
        draft = json.loads(case.draft_json or "{}")
        snapshot = json.loads(case.snapshot_json or "{}")
        
        # 取得體重
        weight = local_facts.get("weightKg", {}).get("value")
        if not weight:
            weight = snapshot.get("weightKg")
        
        # 取得檢查代碼
        exam_code = draft.get("examCode") or snapshot.get("examCode")
        
        if exam_code:
            return self.calculate_na2024_dose(exam_code, weight)
        
        return None
