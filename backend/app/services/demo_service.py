"""
Demo 服務
示範資料建立與管理
"""
import json
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderCase, ReviewEvent, Outbox
from app.schemas import CaseStatus
from app.schemas.demo import SeedRequest, SeedResponse, SeedScenario
from app.services.auth_service import CurrentUser


# 示範案例模板
DEMO_SCENARIOS = {
    "adult_standard": {
        "name": "成人標準劑量案例",
        "description": "成人骨掃描標準劑量",
        "cases": [
            {
                "examCode": "BONE_SCAN",
                "examDisplay": "骨骼掃描 (Tc-99m MDP)",
                "patientName": "王大明",
                "patientId": "A123456789",
                "weightKg": 70.0,
                "suggestedDose": {"value": 740, "unit": "MBq"},
            }
        ]
    },
    "pediatric": {
        "name": "兒童體重調整案例",
        "description": "兒童需依體重調整劑量",
        "cases": [
            {
                "examCode": "DMSA",
                "examDisplay": "腎臟皮質掃描 (Tc-99m DMSA)",
                "patientName": "李小華",
                "patientId": "B234567890",
                "weightKg": 25.0,
                "suggestedDose": {"value": 74, "unit": "MBq"},
            }
        ]
    },
    "renal_impairment": {
        "name": "腎功能不全案例",
        "description": "需考慮腎功能的案例",
        "cases": [
            {
                "examCode": "MAG3",
                "examDisplay": "腎功能掃描 (Tc-99m MAG3)",
                "patientName": "張美麗",
                "patientId": "C345678901",
                "weightKg": 55.0,
                "eGFR": 35.0,
                "suggestedDose": {"value": 185, "unit": "MBq"},
            }
        ]
    },
    "missing_weight": {
        "name": "缺乏體重資料案例",
        "description": "體重資料缺失，需要自動填入或手動補齊",
        "cases": [
            {
                "examCode": "BONE_SCAN",
                "examDisplay": "骨骼掃描 (Tc-99m MDP)",
                "patientName": "陳志明",
                "patientId": "D456789012",
                "weightKg": None,  # 缺乏體重
                "suggestedDose": None,
            }
        ]
    },
    "dose_out_of_range": {
        "name": "劑量超出範圍案例",
        "description": "劑量超出建議範圍，需要審查",
        "cases": [
            {
                "examCode": "FDG_PET",
                "examDisplay": "正子造影 (F-18 FDG)",
                "patientName": "林秀英",
                "patientId": "E567890123",
                "weightKg": 80.0,
                "suggestedDose": {"value": 600, "unit": "MBq"},  # 超出標準範圍
                "override": {"isOverride": True, "reason": "肥胖病人需要較高劑量"},
            }
        ]
    },
}


class DemoService:
    """Demo 服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def seed_demo_data(
        self, 
        request: SeedRequest,
        current_user: CurrentUser
    ) -> SeedResponse:
        """建立示範資料"""
        if request.clearExisting:
            await self.reset_all()
        
        # 決定要建立的情境
        scenario_keys = request.scenarios or list(DEMO_SCENARIOS.keys())
        
        created_count = 0
        created_scenarios = []
        
        for key in scenario_keys:
            if key not in DEMO_SCENARIOS:
                continue
            
            scenario = DEMO_SCENARIOS[key]
            cases_created = 0
            
            for case_data in scenario["cases"]:
                await self._create_demo_case(case_data, current_user)
                cases_created += 1
                created_count += 1
            
            created_scenarios.append(SeedScenario(
                name=scenario["name"],
                description=scenario["description"],
                cases=cases_created
            ))
        
        await self.db.commit()
        
        return SeedResponse(
            created=created_count,
            scenarios=created_scenarios
        )
    
    async def reset_all(self):
        """重置所有示範資料"""
        await self.db.execute(delete(ReviewEvent))
        await self.db.execute(delete(Outbox))
        await self.db.execute(delete(OrderCase))
        await self.db.commit()
    
    async def _create_demo_case(
        self, 
        case_data: dict,
        current_user: CurrentUser
    ):
        """建立單一示範案件"""
        case_id = str(uuid.uuid4())
        patient_ref = f"Patient/{case_data['patientId']}"
        service_request_ref = f"ServiceRequest/{uuid.uuid4()}"
        
        now = datetime.now(timezone.utc)
        
        # 建立 snapshot
        snapshot = {
            "patientName": case_data.get("patientName"),
            "patientId": case_data.get("patientId"),
            "examCode": case_data.get("examCode"),
            "examDisplay": case_data.get("examDisplay"),
            "weightKg": case_data.get("weightKg"),
            "hasAllergy": False,
            "observations": [],
            "allergies": [],
            "conditions": [],
        }
        
        # 建立 local_facts
        local_facts = {}
        if case_data.get("weightKg"):
            local_facts["weightKg"] = {
                "value": case_data["weightKg"],
                "asOf": now.isoformat(),
                "source": "HIS",
            }
        if case_data.get("eGFR"):
            local_facts["eGFR"] = {
                "value": case_data["eGFR"],
                "unit": "mL/min/1.73m2",
                "asOf": now.isoformat(),
                "source": "HIS",
            }
        
        # 建立 draft
        draft = None
        status = CaseStatus.NM_PENDING.value
        if case_data.get("suggestedDose"):
            draft = {
                "examCode": case_data["examCode"],
                "radiopharmaceuticalCode": f"local-{case_data['examCode'].lower()}",
                "suggestedDose": case_data["suggestedDose"],
                "override": case_data.get("override"),
            }
            status = CaseStatus.NM_DRAFTED.value
        
        # 建立 OrderCase
        order_case = OrderCase(
            id=case_id,
            patient_ref=patient_ref,
            service_request_ref=service_request_ref,
            status=status,
            owner_subject=None,
            snapshot_json=json.dumps(snapshot),
            local_facts_json=json.dumps(local_facts),
            draft_json=json.dumps(draft) if draft else None,
            final_fhir_medication_request_ref=None,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
        
        self.db.add(order_case)

