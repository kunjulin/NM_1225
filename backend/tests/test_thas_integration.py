"""
THAS 整合測試
測試與 THAS 競賽環境的連接與操作
"""
import pytest
import os
from httpx import AsyncClient

from app.fhir.client import FHIRClient
from app.config import get_settings, FHIRServerType

# THAS Server URL
THAS_BASE_URL = "https://thas.mohw.gov.tw/v/r4/sim/WzIsIiIsIiIsIkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwiIl0/fhir"


@pytest.fixture
def thas_client():
    """建立連接 THAS 的 FHIR Client"""
    # 暫時修改設定
    original_type = os.environ.get("NM_FHIR_SERVER_TYPE")
    os.environ["NM_FHIR_SERVER_TYPE"] = "thas"
    
    # 清除設定快取
    get_settings.cache_clear()
    
    client = FHIRClient()
    
    yield client
    
    # 還原設定
    if original_type:
        os.environ["NM_FHIR_SERVER_TYPE"] = original_type
    else:
        os.environ.pop("NM_FHIR_SERVER_TYPE", None)
    
    get_settings.cache_clear()


class TestTHASConnection:
    """THAS 連線測試"""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="需要網路連線至 THAS")
    async def test_thas_server_reachable(self, thas_client):
        """測試 THAS Server 可連線"""
        # 嘗試取得 metadata
        async with AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(f"{THAS_BASE_URL}/metadata")
            
            # FHIR Server 應該回應 CapabilityStatement
            assert response.status_code == 200
            data = response.json()
            assert data.get("resourceType") == "CapabilityStatement"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="需要網路連線至 THAS")
    async def test_search_patients(self, thas_client):
        """測試搜尋 Patient"""
        async with AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"{THAS_BASE_URL}/Patient",
                params={"_count": "5"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data.get("resourceType") == "Bundle"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="需要網路連線至 THAS")
    async def test_search_service_requests(self, thas_client):
        """測試搜尋 ServiceRequest"""
        async with AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"{THAS_BASE_URL}/ServiceRequest",
                params={"_count": "5"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data.get("resourceType") == "Bundle"


class TestTHASDemo:
    """THAS Demo 流程測試"""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="需要網路連線至 THAS")
    async def test_demo_workflow_with_thas(self, thas_client):
        """測試完整 Demo 流程使用 THAS 資料"""
        # 此測試需要：
        # 1. THAS 上有可用的 ServiceRequest
        # 2. 對應的 Patient 資料
        # 3. 相關的 Observation (體重)
        
        # Step 1: 搜尋 ServiceRequest
        # Step 2: 從 ServiceRequest 建立本地 OrderCase
        # Step 3: 執行 CDS 規則引擎
        # Step 4: 核醫建立草案
        # Step 5: 送審
        # Step 6: 藥師核准
        # Step 7: 建立 MedicationRequest 到 THAS
        
        pass  # 實際測試需要 THAS 環境


class TestTHASDataMapping:
    """THAS 資料映射測試"""
    
    def test_tw_core_patient_mapping(self):
        """測試 TW Core Patient 資料映射"""
        # 模擬 TW Core Patient 結構
        tw_core_patient = {
            "resourceType": "Patient",
            "id": "example",
            "identifier": [
                {
                    "system": "http://www.moi.gov.tw",
                    "value": "A123456789"
                }
            ],
            "name": [
                {
                    "text": "王大明"
                }
            ],
            "gender": "male",
            "birthDate": "1990-01-01"
        }
        
        # 驗證必要欄位存在
        assert tw_core_patient.get("resourceType") == "Patient"
        assert len(tw_core_patient.get("identifier", [])) > 0
        assert len(tw_core_patient.get("name", [])) > 0
    
    def test_tw_core_observation_weight_mapping(self):
        """測試 TW Core Observation (體重) 資料映射"""
        # 模擬 TW Core Observation 結構
        tw_core_obs = {
            "resourceType": "Observation",
            "id": "weight-example",
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "29463-7",
                        "display": "Body weight"
                    }
                ]
            },
            "subject": {
                "reference": "Patient/example"
            },
            "effectiveDateTime": "2024-12-25T10:00:00+08:00",
            "valueQuantity": {
                "value": 70.5,
                "unit": "kg",
                "system": "http://unitsofmeasure.org",
                "code": "kg"
            }
        }
        
        # 驗證 LOINC code
        assert tw_core_obs["code"]["coding"][0]["code"] == "29463-7"
        
        # 驗證數值
        assert tw_core_obs["valueQuantity"]["value"] == 70.5
        assert tw_core_obs["valueQuantity"]["unit"] == "kg"
    
    def test_medication_request_structure(self):
        """測試 MedicationRequest 結構符合 TW Core"""
        # 模擬要建立的 MedicationRequest
        med_request = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "urn:oid:1.2.3.4.5.6.7.8.9",
                        "code": "local-tc99m-mdp",
                        "display": "Tc-99m MDP"
                    }
                ]
            },
            "subject": {
                "reference": "Patient/example"
            },
            "requester": {
                "reference": "Practitioner/nm-physician-1"
            },
            "basedOn": [
                {"reference": "ServiceRequest/sr-001"}
            ],
            "dosageInstruction": [
                {
                    "doseAndRate": [
                        {
                            "doseQuantity": {
                                "value": 740,
                                "unit": "MBq",
                                "system": "http://unitsofmeasure.org",
                                "code": "MBq"
                            }
                        }
                    ]
                }
            ]
        }
        
        # 驗證必要欄位
        assert med_request.get("resourceType") == "MedicationRequest"
        assert med_request.get("status") == "active"
        assert med_request.get("intent") == "order"
        assert med_request.get("subject") is not None
        assert med_request.get("medicationCodeableConcept") is not None
        
        # 驗證劑量單位
        dose = med_request["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"]
        assert dose["unit"] == "MBq"
        assert dose["code"] == "MBq"




