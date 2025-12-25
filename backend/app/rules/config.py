"""
規則設定
從 YAML 檔案載入劑量規則與檢查配置
"""
import os
from typing import Optional, Tuple

import yaml


# 預設規則配置（當 YAML 檔案不存在時使用）
DEFAULT_RULES = {
    "exams": {
        "BONE_SCAN": {
            "name": "骨骼掃描",
            "radiopharmaceutical": "local-tc99m-mdp",
            "dose_range": [555, 925],  # MBq
            "required_facts": ["weight"],
            "pediatric_factor": 0.0267,  # MBq/kg (NA-2024)
        },
        "MAG3": {
            "name": "腎功能掃描",
            "radiopharmaceutical": "local-tc99m-mag3",
            "dose_range": [185, 370],
            "required_facts": ["weight", "renal"],
        },
        "DMSA": {
            "name": "腎臟皮質掃描",
            "radiopharmaceutical": "local-tc99m-dmsa",
            "dose_range": [37, 185],
            "required_facts": ["weight"],
            "pediatric_factor": 0.0178,
        },
        "MIBG": {
            "name": "MIBG 掃描",
            "radiopharmaceutical": "local-i123-mibg",
            "dose_range": [111, 370],
            "required_facts": ["weight"],
        },
        "FDG_PET": {
            "name": "正子造影",
            "radiopharmaceutical": "local-f18-fdg",
            "dose_range": [185, 444],
            "required_facts": ["weight"],
            "pediatric_factor": 0.0296,
        },
        "DTPA": {
            "name": "腎絲球過濾率掃描",
            "radiopharmaceutical": "local-tc99m-dtpa",
            "dose_range": [185, 370],
            "required_facts": ["weight", "renal"],
        },
    },
    "batch_policy": {
        "allow_warn_flags": True,
        "max_warn_count": 2,
        "require_weight": True,
    }
}


class RulesConfig:
    """規則配置管理"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        """載入配置"""
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        
        # 嘗試從預設路徑載入
        default_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", 
            "rules_config.yaml"
        )
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        
        return DEFAULT_RULES
    
    def get_exam_config(self, exam_code: str) -> Optional[dict]:
        """取得檢查配置"""
        return self.config.get("exams", {}).get(exam_code)
    
    def get_dose_range(self, exam_code: str) -> Optional[Tuple[float, float]]:
        """取得劑量範圍"""
        exam = self.get_exam_config(exam_code)
        if exam and "dose_range" in exam:
            return tuple(exam["dose_range"])
        return None
    
    def get_radiopharmaceutical(self, exam_code: str) -> Optional[str]:
        """取得對應的放射藥物代碼"""
        exam = self.get_exam_config(exam_code)
        if exam:
            return exam.get("radiopharmaceutical")
        return None
    
    def get_required_facts(self, exam_code: str) -> list[str]:
        """取得必要的臨床事實"""
        exam = self.get_exam_config(exam_code)
        if exam:
            return exam.get("required_facts", [])
        return []
    
    def get_pediatric_factor(self, exam_code: str) -> Optional[float]:
        """取得兒童劑量係數"""
        exam = self.get_exam_config(exam_code)
        if exam:
            return exam.get("pediatric_factor")
        return None
    
    def get_na2024_config(self, exam_code: str) -> Optional[dict]:
        """取得 NA-2024 劑量配置
        
        Returns:
            NA-2024 配置字典，包含:
            - activity_per_kg: MBq/kg
            - min_activity: 最小劑量 MBq
            - max_activity: 最大劑量 MBq
            - adult_standard: 成人標準劑量 MBq
        """
        exam = self.get_exam_config(exam_code)
        if exam:
            return exam.get("na2024")
        return None
    
    def get_batch_policy(self) -> dict:
        """取得批次核准政策"""
        return self.config.get("batch_policy", {})

