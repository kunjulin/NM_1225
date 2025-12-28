"""檢查 THAS FHIR Server 上的 ServiceRequest"""
import asyncio
import json
from app.fhir.client import FHIRClient

async def check_service_requests():
    """檢查 ServiceRequest"""
    client = FHIRClient()
    
    print("=" * 60)
    print("檢查 THAS FHIR Server 上的 ServiceRequest")
    print("=" * 60)
    
    # 1. 查詢所有 active 的 ServiceRequest（不使用 category 過濾）
    print("\n1. 查詢所有 status=active 的 ServiceRequest（無 category 過濾）:")
    result1 = await client._request("GET", "ServiceRequest", params={"status": "active"})
    if result1 and "entry" in result1:
        print(f"   找到 {len(result1['entry'])} 個 ServiceRequest")
        for entry in result1["entry"]:
            sr = entry.get("resource", {})
            sr_id = sr.get("id", "N/A")
            subject = sr.get("subject", {}).get("reference", "N/A")
            categories = sr.get("category", [])
            category_display = categories[0].get("coding", [{}])[0].get("display", "N/A") if categories else "N/A"
            print(f"   - ID: {sr_id}, Patient: {subject}, Category: {category_display}")
    else:
        print("   未找到任何 ServiceRequest")
    
    # 2. 查詢使用 category=nuclear-medicine 過濾
    print("\n2. 查詢 status=active 且 category=nuclear-medicine 的 ServiceRequest:")
    result2 = await client._request("GET", "ServiceRequest", params={"status": "active", "category": "nuclear-medicine"})
    if result2 and "entry" in result2:
        print(f"   找到 {len(result2['entry'])} 個 ServiceRequest")
        for entry in result2["entry"]:
            sr = entry.get("resource", {})
            sr_id = sr.get("id", "N/A")
            subject = sr.get("subject", {}).get("reference", "N/A")
            print(f"   - ID: {sr_id}, Patient: {subject}")
    else:
        print("   未找到任何 ServiceRequest（可能 category 過濾條件不匹配）")
    
    # 3. 檢查 patient-1007 相關的 ServiceRequest
    print("\n3. 查詢 Patient/patient-1007 相關的 ServiceRequest:")
    result3 = await client._request("GET", "ServiceRequest", params={"status": "active", "subject": "Patient/patient-1007"})
    if result3 and "entry" in result3:
        print(f"   找到 {len(result3['entry'])} 個 ServiceRequest")
        for entry in result3["entry"]:
            sr = entry.get("resource", {})
            sr_id = sr.get("id", "N/A")
            categories = sr.get("category", [])
            category_display = categories[0].get("coding", [{}])[0].get("display", "N/A") if categories else "N/A"
            print(f"   - ID: {sr_id}, Category: {category_display}")
            print(f"     完整資料: {json.dumps(sr, indent=2, ensure_ascii=False)}")
    else:
        print("   未找到任何 ServiceRequest")
    
    print("\n" + "=" * 60)
    print("檢查完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_service_requests())

