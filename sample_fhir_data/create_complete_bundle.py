"""Create complete bundle with 6 cases from FHIR Server plus patient-1007"""
import json
from datetime import datetime, timedelta

# Patient data for 6 cases from FHIR Server
patients_data = [
    {
        "id": "patient-1001",
        "name": "劉大偉",
        "gender": "male",
        "birthDate": "1965-03-20",
        "identifier": "B123456789",
        "address": {"city": "台北市", "district": "中正區", "postalCode": "100"},
        "exam": {
            "id": "exam-001",
            "code": "PET_FDG_WB",
            "display": "全身 FDG PET/CT",
            "snomed": "78800008",  # PET scan
            "reason": "肺癌追蹤",
            "reasonCode": "C78.00"
        },
        "conditions": ["C78.00", "I10"],  # 肺癌轉移, 高血壓
        "medications": ["197361"],  # Amlodipine
        "allergies": []
    },
    {
        "id": "patient-1002",
        "name": "張小雨",
        "gender": "female",
        "birthDate": "1978-07-15",
        "identifier": "C234567890",
        "address": {"city": "新北市", "district": "板橋區", "postalCode": "220"},
        "exam": {
            "id": "exam-002",
            "code": "BONE_3PHASE",
            "display": "三相骨骼掃描",
            "snomed": "77477000",  # Bone scan
            "reason": "骨轉移評估",
            "reasonCode": "C79.5"
        },
        "conditions": ["C79.5", "M81.0"],  # 骨轉移, 骨質疏鬆
        "medications": ["315980"],  # Vitamin D3
        "allergies": ["7980"]  # Penicillin
    },
    {
        "id": "patient-1003",
        "name": "吳小明",
        "gender": "male",
        "birthDate": "1985-11-30",
        "identifier": "D345678901",
        "address": {"city": "台中市", "district": "西屯區", "postalCode": "407"},
        "exam": {
            "id": "exam-005",
            "code": "THYROID_UPTAKE",
            "display": "甲狀腺攝取率",
            "snomed": "39937001",  # Thyroid uptake
            "reason": "甲狀腺功能亢進",
            "reasonCode": "E05.0"
        },
        "conditions": ["E05.0", "E04.1"],  # 甲狀腺功能亢進, 甲狀腺結節
        "medications": ["1596450"],  # Methimazole
        "allergies": []
    },
    {
        "id": "patient-1004",
        "name": "黃小芳",
        "gender": "female",
        "birthDate": "1990-02-14",
        "identifier": "E456789012",
        "address": {"city": "高雄市", "district": "前金區", "postalCode": "801"},
        "exam": {
            "id": "exam-006",
            "code": "RENAL_MAG3",
            "display": "腎功能掃描 (MAG3)",
            "snomed": "241620005",  # Renal scan MAG3
            "reason": "腎功能評估",
            "reasonCode": "N18.9"
        },
        "conditions": ["N18.9", "I10"],  # 慢性腎臟病, 高血壓
        "medications": ["197361", "311700"],  # Amlodipine, Omeprazole
        "allergies": []
    },
    {
        "id": "patient-1005",
        "name": "陳志強",
        "gender": "male",
        "birthDate": "1972-09-25",
        "identifier": "F567890123",
        "address": {"city": "桃園市", "district": "中壢區", "postalCode": "320"},
        "exam": {
            "id": "exam-004",
            "code": "MIBG_SCAN",
            "display": "MIBG 心臟交感神經顯像",
            "snomed": "432100008",  # MIBG scan
            "reason": "心臟交感神經評估",
            "reasonCode": "I25.9"
        },
        "conditions": ["I25.9", "I10"],  # 缺血性心臟病, 高血壓
        "medications": ["197361"],  # Amlodipine
        "allergies": ["312498006"]  # Iodinated contrast
    },
    {
        "id": "patient-1006",
        "name": "王小明",
        "gender": "male",
        "birthDate": "1988-04-10",
        "identifier": "G678901234",
        "address": {"city": "台南市", "district": "東區", "postalCode": "701"},
        "exam": {
            "id": "exam-003",
            "code": "RENAL_DMSA",
            "display": "腎皮質掃描 (DMSA)",
            "snomed": "241520004",  # DMSA scan
            "reason": "腎皮質功能評估",
            "reasonCode": "N18.9"
        },
        "conditions": ["N18.9", "N13.8"],  # 慢性腎臟病, 其他腎功能障礙
        "medications": ["197361"],  # Amlodipine
        "allergies": []
    }
]

# Condition mappings
condition_map = {
    "C78.00": {"display": "Secondary malignant neoplasm of lung", "text": "肺癌轉移"},
    "C79.5": {"display": "Secondary malignant neoplasm of bone", "text": "骨轉移"},
    "E05.0": {"display": "Thyrotoxicosis with diffuse goiter", "text": "甲狀腺功能亢進"},
    "E04.1": {"display": "Nontoxic single thyroid nodule", "text": "甲狀腺結節"},
    "I10": {"display": "Essential (primary) hypertension", "text": "原發性高血壓"},
    "I25.9": {"display": "Chronic ischemic heart disease", "text": "缺血性心臟病"},
    "M81.0": {"display": "Age-related osteoporosis", "text": "骨質疏鬆症"},
    "N18.9": {"display": "Chronic kidney disease", "text": "慢性腎臟病"},
    "N13.8": {"display": "Other obstructive and reflux uropathy", "text": "其他腎功能障礙"}
}

# Medication mappings
medication_map = {
    "197361": {"display": "Amlodipine 5 MG Oral Tablet", "text": "脈優 5mg"},
    "311700": {"display": "Omeprazole 20 MG Delayed Release Oral Capsule", "text": "耐適恩 20mg"},
    "315980": {"display": "Cholecalciferol 1000 UNT Oral Tablet", "text": "維生素D3 1000IU"},
    "1596450": {"display": "Methimazole 5 MG Oral Tablet", "text": "甲狀腺抑制劑 5mg"}
}

# Allergy mappings
allergy_map = {
    "7980": {"display": "Penicillin", "text": "Penicillin (盤尼西林)"},
    "312498006": {"display": "Iodinated contrast media", "text": "碘顯影劑"}
}

def create_patient(p_data):
    """Create Patient resource"""
    family, given = p_data["name"][0], p_data["name"][1:]
    return {
        "fullUrl": f"urn:uuid:{p_data['id']}",
        "resource": {
            "resourceType": "Patient",
            "id": p_data["id"],
            "meta": {
                "profile": ["https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/Patient-twcore"]
            },
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "NI"
                            }
                        ]
                    },
                    "system": "http://www.moi.gov.tw/",
                    "value": p_data["identifier"]
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "text": p_data["name"],
                    "family": family,
                    "given": [given] if given else []
                }
            ],
            "gender": p_data["gender"],
            "birthDate": p_data["birthDate"],
            "address": [
                {
                    "use": "home",
                    "type": "physical",
                    "city": p_data["address"]["city"],
                    "district": p_data["address"]["district"],
                    "postalCode": p_data["address"]["postalCode"]
                }
            ]
        },
        "request": {
            "method": "PUT",
            "url": f"Patient/{p_data['id']}"
        }
    }

def create_service_request(p_data):
    """Create ServiceRequest resource"""
    exam = p_data["exam"]
    cond_info = condition_map.get(exam["reasonCode"], {"display": exam["reason"], "text": exam["reason"]})
    return {
        "fullUrl": f"urn:uuid:{exam['id']}",
        "resource": {
            "resourceType": "ServiceRequest",
            "id": exam["id"],
            "status": "active",
            "intent": "order",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "394649004",
                            "display": "Nuclear medicine"
                        }
                    ],
                    "text": "核子醫學科"
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": exam["snomed"],
                        "display": exam["display"]
                    }
                ],
                "text": exam["display"]
            },
            "subject": {
                "reference": f"Patient/{p_data['id']}",
                "display": p_data["name"]
            },
            "authoredOn": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "requester": {
                "reference": "Practitioner/clinical-doc-001",
                "display": "臨床醫師"
            },
            "reasonCode": [
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/sid/icd-10-cm",
                            "code": exam["reasonCode"],
                            "display": cond_info["display"]
                        }
                    ],
                    "text": cond_info["text"]
                }
            ]
        },
        "request": {
            "method": "PUT",
            "url": f"ServiceRequest/{exam['id']}"
        }
    }

def create_encounter(p_data, encounter_num):
    """Create Encounter resource"""
    base_date = datetime.now() - timedelta(days=(encounter_num + 1) * 30)
    return {
        "fullUrl": f"urn:uuid:encounter-{p_data['id']}-{encounter_num}",
        "resource": {
            "resourceType": "Encounter",
            "id": f"encounter-{p_data['id']}-{encounter_num}",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            },
            "subject": {
                "reference": f"Patient/{p_data['id']}",
                "display": p_data["name"]
            },
            "period": {
                "start": base_date.strftime("%Y-%m-%dT09:00:00+08:00"),
                "end": (base_date + timedelta(hours=1)).strftime("%Y-%m-%dT10:00:00+08:00")
            }
        },
        "request": {
            "method": "PUT",
            "url": f"Encounter/encounter-{p_data['id']}-{encounter_num}"
        }
    }

def create_condition(p_data, condition_code):
    """Create Condition resource"""
    cond_info = condition_map[condition_code]
    return {
        "fullUrl": f"urn:uuid:condition-{p_data['id']}-{condition_code}",
        "resource": {
            "resourceType": "Condition",
            "id": f"condition-{p_data['id']}-{condition_code}",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "problem-list-item",
                            "display": "Problem List Item"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10-cm",
                        "code": condition_code,
                        "display": cond_info["display"]
                    }
                ],
                "text": cond_info["text"]
            },
            "subject": {
                "reference": f"Patient/{p_data['id']}",
                "display": p_data["name"]
            },
            "onsetDateTime": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            "recordedDate": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        },
        "request": {
            "method": "PUT",
            "url": f"Condition/condition-{p_data['id']}-{condition_code}"
        }
    }

def create_observation(p_data, obs_type, obs_num):
    """Create Observation resource"""
    obs_map = {
        "weight": {"code": "29463-7", "display": "Body weight", "text": "體重", "value": 70, "unit": "kg", "category": "vital-signs"},
        "creatinine": {"code": "2160-0", "display": "Creatinine", "text": "肌酸酐", "value": 1.0, "unit": "mg/dL", "category": "laboratory"},
        "egfr": {"code": "33914-3", "display": "eGFR", "text": "腎絲球過濾率", "value": 78, "unit": "mL/min/1.73m2", "category": "laboratory"},
        "tsh": {"code": "3016-3", "display": "TSH", "text": "促甲狀腺激素", "value": 2.5, "unit": "mIU/L", "category": "laboratory"},
        "hgb": {"code": "718-7", "display": "Hemoglobin", "text": "血紅素", "value": 14.5, "unit": "g/dL", "category": "laboratory"}
    }
    obs = obs_map[obs_type]
    return {
        "fullUrl": f"urn:uuid:obs-{p_data['id']}-{obs_type}-{obs_num}",
        "resource": {
            "resourceType": "Observation",
            "id": f"obs-{p_data['id']}-{obs_type}-{obs_num}",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": obs["category"],
                            "display": "Vital Signs" if obs["category"] == "vital-signs" else "Laboratory"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": obs["code"],
                        "display": obs["display"]
                    }
                ],
                "text": obs["text"]
            },
            "subject": {
                "reference": f"Patient/{p_data['id']}",
                "display": p_data["name"]
            },
            "effectiveDateTime": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT08:00:00+08:00"),
            "valueQuantity": {
                "value": obs["value"],
                "unit": obs["unit"],
                "system": "http://unitsofmeasure.org",
                "code": obs["unit"]
            }
        },
        "request": {
            "method": "PUT",
            "url": f"Observation/obs-{p_data['id']}-{obs_type}-{obs_num}"
        }
    }

def create_medication_statement(p_data, med_code):
    """Create MedicationStatement resource"""
    med_info = medication_map[med_code]
    return {
        "fullUrl": f"urn:uuid:medstmt-{p_data['id']}-{med_code}",
        "resource": {
            "resourceType": "MedicationStatement",
            "id": f"medstmt-{p_data['id']}-{med_code}",
            "status": "active",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": med_code,
                        "display": med_info["display"]
                    }
                ],
                "text": med_info["text"]
            },
            "subject": {
                "reference": f"Patient/{p_data['id']}",
                "display": p_data["name"]
            },
            "effectivePeriod": {
                "start": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            }
        },
        "request": {
            "method": "PUT",
            "url": f"MedicationStatement/medstmt-{p_data['id']}-{med_code}"
        }
    }

def create_allergy_intolerance(p_data, allergy_code):
    """Create AllergyIntolerance resource"""
    allergy_info = allergy_map[allergy_code]
    return {
        "fullUrl": f"urn:uuid:allergy-{p_data['id']}-{allergy_code}",
        "resource": {
            "resourceType": "AllergyIntolerance",
            "id": f"allergy-{p_data['id']}-{allergy_code}",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": "active",
                        "display": "Active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }
                ]
            },
            "type": "allergy",
            "category": ["medication"],
            "criticality": "high" if allergy_code == "7980" else "low",
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct" if allergy_code == "312498006" else "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": allergy_code,
                        "display": allergy_info["display"]
                    }
                ],
                "text": allergy_info["text"]
            },
            "patient": {
                "reference": f"Patient/{p_data['id']}",
                "display": p_data["name"]
            },
            "onsetDateTime": (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d"),
            "recordedDate": (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        },
        "request": {
            "method": "PUT",
            "url": f"AllergyIntolerance/allergy-{p_data['id']}-{allergy_code}"
        }
    }

# Read existing patient-1007 bundle
with open("patient_complete_bundle.json", "r", encoding="utf-8") as f:
    existing_bundle = json.load(f)

# Create new bundle starting with patient-1007 data
bundle = {
    "resourceType": "Bundle",
    "type": "transaction",
    "entry": existing_bundle["entry"].copy()  # Keep patient-1007 data
}

# Add Practitioner if not exists
practitioner_exists = any(
    e.get("resource", {}).get("id") == "clinical-doc-001" 
    for e in bundle["entry"]
)

if not practitioner_exists:
    bundle["entry"].append({
        "fullUrl": "urn:uuid:practitioner-clinical-doc-001",
        "resource": {
            "resourceType": "Practitioner",
            "id": "clinical-doc-001",
            "active": True,
            "name": [
                {
                    "use": "official",
                    "text": "臨床醫師",
                    "family": "臨床",
                    "given": ["醫師"]
                }
            ]
        },
        "request": {
            "method": "PUT",
            "url": "Practitioner/clinical-doc-001"
        }
    })

# Add data for each of the 6 patients
for p_data in patients_data:
    # Patient
    bundle["entry"].append(create_patient(p_data))
    
    # ServiceRequest
    bundle["entry"].append(create_service_request(p_data))
    
    # Encounters (2 per patient)
    for i in range(2):
        bundle["entry"].append(create_encounter(p_data, i))
    
    # Conditions
    for cond_code in p_data["conditions"]:
        bundle["entry"].append(create_condition(p_data, cond_code))
    
    # Observations (weight, creatinine, and exam-specific)
    bundle["entry"].append(create_observation(p_data, "weight", 0))
    bundle["entry"].append(create_observation(p_data, "creatinine", 0))
    
    # Add exam-specific observations
    if "RENAL" in p_data["exam"]["code"]:
        bundle["entry"].append(create_observation(p_data, "egfr", 0))
    if "THYROID" in p_data["exam"]["code"]:
        bundle["entry"].append(create_observation(p_data, "tsh", 0))
    else:
        bundle["entry"].append(create_observation(p_data, "hgb", 0))
    
    # Medications
    for med_code in p_data["medications"]:
        bundle["entry"].append(create_medication_statement(p_data, med_code))
    
    # Allergies
    for allergy_code in p_data["allergies"]:
        bundle["entry"].append(create_allergy_intolerance(p_data, allergy_code))

# Write to file
with open("patient_complete_bundle.json", "w", encoding="utf-8") as f:
    json.dump(bundle, f, ensure_ascii=False, indent=2)

# Count resources
counts = {}
for entry in bundle["entry"]:
    resource_type = entry.get("resource", {}).get("resourceType", "Unknown")
    counts[resource_type] = counts.get(resource_type, 0) + 1

print(f"Created complete bundle with {len(bundle['entry'])} entries")
print("\nResource counts:")
for resource_type, count in sorted(counts.items()):
    print(f"  - {resource_type}: {count}")
