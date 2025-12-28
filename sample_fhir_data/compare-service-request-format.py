"""比較 ServiceRequest 格式，找出 1007 和其他成功資料的差異"""
import json
import sys

# 讀取用戶上傳的 ServiceRequest 格式
with open('patient_complete_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

# 找出 ServiceRequest
service_request = None
for entry in bundle['entry']:
    if entry.get('resource', {}).get('resourceType') == 'ServiceRequest':
        service_request = entry['resource']
        break

if not service_request:
    print("Error: ServiceRequest not found in bundle")
    sys.exit(1)

print("=" * 80)
print("用戶上傳的 ServiceRequest (exam-007) 格式:")
print("=" * 80)
print(f"ID: {service_request.get('id')}")
print(f"Status: {service_request.get('status')}")
print(f"Subject: {service_request.get('subject', {}).get('reference')}")

# 檢查 category
category = service_request.get('category', [])
print(f"\nCategory 欄位:")
print(json.dumps(category, indent=2, ensure_ascii=False))

if category:
    cat_item = category[0]
    print(f"\nCategory 詳細分析:")
    print(f"  - text: {cat_item.get('text')}")
    coding = cat_item.get('coding', [])
    if coding:
        print(f"  - coding:")
        for code in coding:
            print(f"    - system: {code.get('system')}")
            print(f"    - code: {code.get('code')}")
            print(f"    - display: {code.get('display')}")

print("\n" + "=" * 80)
print("可能的問題:")
print("=" * 80)

# 檢查 category text
cat_text = category[0].get('text') if category else None
if cat_text != 'nuclear-medicine':
    print(f"⚠ Category text 是 '{cat_text}'，應該是 'nuclear-medicine'")

# 檢查 coding display
coding_display = None
if category and category[0].get('coding'):
    coding_display = category[0]['coding'][0].get('display')
if coding_display != 'nuclear-medicine':
    print(f"⚠ Category coding.display 是 '{coding_display}'，應該是 'nuclear-medicine'")

# 檢查 coding code
coding_code = None
if category and category[0].get('coding'):
    coding_code = category[0]['coding'][0].get('code')
print(f"ℹ Category coding.code 是 '{coding_code}' (SNOMED code)")

print("\n" + "=" * 80)
print("系統查詢參數:")
print("=" * 80)
print("系統使用: category=nuclear-medicine")
print("這會匹配:")
print("  - Category[].text = 'nuclear-medicine'")
print("  - Category[].coding[].display = 'nuclear-medicine'")
print("  - Category[].coding[].code = 'nuclear-medicine' (如果有的話)")

print("\n" + "=" * 80)
print("建議:")
print("=" * 80)
print("根據 FHIR 規範，category 查詢參數應該能匹配 text 和 display")
print("如果仍無法匹配，可能需要:")
print("1. 確認資料是否成功上傳到 FHIR Server")
print("2. 檢查 FHIR Server 的查詢實現是否支援 text/display 匹配")
print("3. 嘗試使用 coding.code 來查詢（但這不是標準做法）")

