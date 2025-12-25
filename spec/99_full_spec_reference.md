# SMART on FHIR Medication Stewardship App -- Engineering Specification

## Overview

This document specifies the complete engineering requirements for a
SMART on FHIR Medication Stewardship App. It integrates Nuclear Medicine
(NM) ordering, Clinical Decision Support (CDS), and single-pharmacist
verification with batch approval, based on FHIR R4 and FastAPI backend
services.

## User Roles and Login Routing

Single SMART App with role-based UI switching using configuration
mapping (demo mode).\
\
Roles:\
- NM Physician: create MedicationRequest and submit for pharmacy
verification\
- Pharmacist: review, claim, verify, batch-approve eligible orders

## Core Workflow

1\. ServiceRequest created by clinical physician\
2. NM physician reviews order\
3. CDS calculates dose using NA-2024 rules\
4. NM physician confirms → MedicationRequest\
5. Task(status=ready) created\
6. Pharmacist claims Task\
7. Rule engine evaluates eligibility\
8. Batch or individual approval\
9. Approved orders exported

## FHIR Resources

ServiceRequest, MedicationRequest, Task, Patient, Observation,
Provenance (optional)

## Verification Rules

Exam-drug match, valid weight, NA-2024 dose range, override handling

## Rule Engine Output

overallSeverity, isBatchEligible, flags\[\], policy metadata

## Pharmacy Grouping

Exceptions (manual), Pass Queue (batch), My Claimed

## Batch Approval

Bulk claim then bulk approve using PATCH or FHIR batch

## Backend APIs

GET /pharmacy/worklist\
POST /pharmacy/bulk-approve

## Security

Role-based SMART scopes, Task owner enforcement

## Export

Only completed Tasks included, CSV output

## Implementation Notes

Backend authoritative for rules, frontend uses isBatchEligible

# Appendix B. Workflow Diagrams (Images)

## B1. End-to-End Workflow

![](media/image1.png){width="6.0in" height="15.720429790026246in"}

## B2. Role-Based Login Routing

![](media/image2.png){width="6.0in" height="4.455621172353456in"}

## B3. Pharmacy Batch Approval

![](media/image3.png){width="6.0in" height="8.32799978127734in"}

# Appendix C. Optimized Workflow (Subscription-driven)

This optimized workflow clarifies event sources and worklist
responsibilities. NM physicians subscribe to ServiceRequest events,
while pharmacists subscribe to Task (pharmacy-verify) events.
MedicationRequest creation is not directly subscribed by pharmacists.

## C1. Optimized End-to-End Workflow with Subscriptions

![](media/image4.png){width="6.0in" height="19.53638779527559in"}

# Appendix D. TW Core Compatibility and Validation

## D1. TW Core Conformance Matrix

The following table defines conformance of each FHIR resource used in
this project against Taiwan Core Implementation Guide (TW Core IG), FHIR
R4 base, or project-specific extensions.

  ----------------------------------------------------------------------------------
  FHIR Resource       TW Core Profile            Usage in This     Notes /
                                                 Project           Extensions
  ------------------- -------------------------- ----------------- -----------------
  Patient             TWCore-Patient             TW Core compliant No extension
                                                                   required

  ServiceRequest      TWCore-ServiceRequest      TW Core compliant Use reasonCode
                                                                   for indication

  MedicationRequest   TWCore-MedicationRequest   TW Core +         Radiopharm code,
                                                 Extension         MBq dose

  Observation         TWCore-Observation         TW Core compliant LOINC 29463-7
  (Weight)                                                         

  Task                N/A                        FHIR R4 base +    pharmacy-verify
                                                 Project Profile   workflow

  Subscription        N/A                        FHIR R4 base      Event-driven
                                                                   worklists

  Provenance          Optional                   FHIR R4 base      Audit trail
                                                 (optional)        
  ----------------------------------------------------------------------------------

## D2. Radiopharmaceutical Coding Strategy

Radiopharmaceuticals are coded using local institutional codes in the
demo phase, with a clear mapping strategy to international or national
standard terminologies.

Recommended approach:\
1. Use institution-defined CodeSystem (e.g., urn:oid:1.2.3.4.5.6.7.8.9)\
2. Populate medicationCodeableConcept.coding with local code + display\
3. Maintain a mapping table for future alignment (e.g., SNOMED CT,
RxNorm, or national registry)\
4. Dose unit must use UCUM \'MBq\'

## D3. Mandatory Field Validation Checklist

The following mandatory elements must be validated by backend services
before allowing progression in workflow.

-   \- ServiceRequest.subject, code, requester, authoredOn

-   \- ServiceRequest.reasonCode or reasonReference

-   \- MedicationRequest.subject, medicationCodeableConcept, authoredOn,
    requester

-   \-
    MedicationRequest.dosageInstruction.doseAndRate.doseQuantity.value
    and unit (MBq)

-   \- MedicationRequest.basedOn → ServiceRequest reference

-   \- Observation (Weight): LOINC 29463-7, effectiveDateTime within
    lookback window

-   \- Task.code = pharmacy-verify

-   \- Task.focus → MedicationRequest reference

-   \- Task.basedOn → ServiceRequest reference

-   \- Task.status transitions must follow defined state machine

-   \- Task.owner must be populated after claim

# Chapter 6. Standards Conformance and Architecture Rationale

本系統採用 FHIR R4 作為核心資料交換標準，並以台灣核心資料群（TW Core
Implementation Guide）\
作為臨床資料之相容基礎，結合 SMART on FHIR 應用程式架構與 FHIR Task
為基礎的工作流管理機制，\
建構一套適用於核子醫學放射藥物用藥治理之臨床決策與覆核系統。

在臨床資料層面，Patient、ServiceRequest、MedicationRequest 與
Observation（如體重、腎功能）等資源，\
皆依循 TW Core IG
所定義之結構與必填欄位進行實作，以確保與國內既有醫療資訊系統及跨機構資料交換之相容性。\
ServiceRequest 用於表達臨床醫師所開立之影像檢查需求與適應症，\
MedicationRequest
則由核醫醫師依檢查程序與臨床情境建立放射藥物用藥指示，\
並透過延伸欄位支援放射藥物代碼、劑量單位（UCUM MBq）及臨床決策規則版本。

在工作流程層面，本系統採用 FHIR Task
資源建立獨立之藥師覆核任務（pharmacy-verify），\
作為核醫醫師送交藥師審核之正式工作單位。\
Task 資源承載覆核狀態轉換、單人覆核（claim/owner）與審核結果註記，\
形成一條清楚可稽核之用藥治理流程。

系統並利用 FHIR Subscription 機制建立事件驅動之應用流程：\
核醫端訂閱 ServiceRequest 事件以形成檢查與用藥工作清單；\
藥師端僅訂閱 Task（pharmacy-verify）事件，\
確保藥師僅接收正式送審之用藥案件，\
避免直接監聽所有 MedicationRequest 所造成之噪音與責任不清。

此一設計使臨床資料交換（TW Core 相容）與用藥治理工作流（FHIR R4 base +
專案延伸）之責任邊界清楚分離，\
同時支援臨床決策支援、批次審核、審核退回與用藥訂購清單產生等實務需求，\
具備良好的可擴充性、可治理性與實務落地能力。

# Chapter 7. Study Objectives and Evaluation Metrics

## 7.1 Study Objectives

本研究旨在建構並評估一套基於 FHIR R4、TW Core 與 SMART on FHIR
架構之核子醫學放射藥物用藥治理與臨床決策支援系統，透過結構化醫囑、劑量規則引擎與藥師覆核工作流，提升放射藥物用藥之安全性、一致性與流程效率。

具體研究目的包括：

1\.
評估臨床決策支援系統（CDS）導入後，放射藥物不適當劑量比例之改善情形。

2\. 量化藥師介入對核醫用藥品質之影響。

3\. 分析 Task-based 覆核流程對整體作業效率（TAT）之影響。

4\. 建立可稽核、可比較之用藥治理指標體系。

## 7.2 Key Performance Indicators (KPIs)

主要與次要評估指標如下：

（一）主要評估指標（Primary Outcomes）

1\. 不適當劑量比例：未符合劑量規則且無合理說明之藥囑比例。

2\. 藥師介入率：藥師退回或拒絕之藥囑比例。

（二）次要評估指標（Secondary Outcomes）

3\. 醫令處理時間（TAT）：從 MedicationRequest 建立至 Task 完成之時間。

4\. 批次核准比例：符合規則並以批次方式核准之藥囑比例。

（三）探索性指標（Exploratory Outcomes）

5\. 退回原因分布：藥師退回藥囑之原因分類。

6\. Override 比例：醫師偏離建議劑量並填寫理由之比例。

# Chapter 8. Identity, Role, and Access Management (Low-Coupling Design)

為避免藥物管理系統在效能與可用性上受限於院內 HIS FHIR 系統之反應速度，\
本系統於身份識別（Authentication）與角色權限（Authorization）設計上，\
採取「低耦合、分層治理」之策略。

本章節說明人員角色與權限資料之來源劃分原則，以及與 HIS
系統之最小必要整合範圍。

8.1 Authentication（身份識別）

本系統建議沿用院內既有之身份驗證機制（如 HIS 帳號、AD/LDAP、SSO 或 SMART
on FHIR OIDC），\
僅取得登入者之唯一識別碼（subject / employee
ID）與基本顯示資訊（如姓名）。\
身份驗證成功後，系統即不再依賴 HIS 進行即時人員查詢，以避免效能瓶頸。

8.2 Authorization（角色與權限控管）

本系統之角色（如核醫醫師、藥師、系統管理者）與其對應之工作流權限，\
皆由藥物管理系統本地定義與維護，並不直接依賴 HIS FHIR 中之
PractitionerRole 或 RBAC 設定。\
此設計可確保用藥治理流程之彈性與即時性。

角色權限範例包括：\
- 核醫醫師：檢查案件檢視、用藥草案建立、送審藥師\
- 藥師：全部待審案件檢視、單人 Claim、批次核准、退回修正\
- 管理者：規則設定、角色管理、系統監控

8.3 Optional Practitioner Lookup（選配）

若需於介面或稽核報表中顯示完整人員資訊（如科別或職類），\
系統可於非同步背景流程中，透過 HIS FHIR 查詢 Practitioner 或
PractitionerRole 資源，\
並將結果快取於本地資料庫，以避免於使用者操作流程中即時呼叫 HIS。

8.4 Audit Logging（稽核紀錄）

所有關鍵操作（Claim、核准、退回、批次處理）皆於本地系統中建立稽核紀錄，\
並標註執行者之身份識別碼與角色。\
此設計可確保在不高度依賴 HIS 的情況下，仍能滿足醫療品質與資安稽核需求。

透過上述設計，本系統在保留與院內 HIS 身份體系整合之同時，\
可將角色與流程治理完全掌握於本地，達成高效、可擴充且低耦合之藥物管理閉環架構。

# Chapter 9. Low-Coupling HIS Integration and Deferred Synchronization Architecture

本系統在設計上明確避免與院內 HIS FHIR 系統形成緊密耦合（tight
coupling），\
以防止 HIS 效能瓶頸對藥物管理作業與臨床工作流造成連鎖影響。\
因此，本章節重新定義本系統與 HIS
之整合邏輯，採用「必要資料讀取、流程本地化、結果延遲同步」之設計原則。

9.1 Design Principle

本系統遵循以下三項核心原則：\
1. HIS 僅作為臨床事實（clinical facts）來源，而非工作流引擎。\
2. 所有用藥審查、角色分工、狀態管理與稽核流程皆於藥物管理系統本地完成。\
3. 與 HIS 的寫入操作僅於流程關鍵節點進行，並採用非同步同步機制。

9.2 Minimal HIS FHIR Resource Usage

為降低依賴與提升效能，本系統僅於必要時存取下列 HIS FHIR 資源：\
- ServiceRequest：取得臨床醫師所開立之影像檢查醫令。\
- Patient：取得病人基本識別資料。\
- Observation（限定）：體重與腎功能等用於劑量決策之關鍵檢查值。\
（選配）AllergyIntolerance /
Condition：僅於規則引擎需判斷禁忌或適應症時使用。

上述資料皆於案件建立時擷取並儲存為本地快照（snapshot），\
後續工作清單顯示與流程操作皆以本地資料為準，避免於使用者互動過程中即時呼叫
HIS。

9.3 Local Workflow Ownership

藥物管理系統於本地建立 OrderCase 與 ReviewTask 等內部資料模型，\
完整承載以下資訊：\
- 案件狀態（核醫處理中、送藥師審查、核准、退回等）\
- Claim / owner 機制（單人覆核）\
- 規則引擎輸出（flags、severity、建議）\
- 稽核軌跡與操作紀錄

此設計確保即使 HIS FHIR 反應緩慢或暫時不可用，\
藥物管理作業仍可持續進行。

9.4 Deferred Write-back to HIS

本系統僅於藥物管理流程完成後，\
將最終確認之 MedicationRequest 回傳至 HIS FHIR 系統。\
中間流程中產生之草案、修正、退回與審查狀態，皆不即時同步至 HIS。

為避免 HIS 寫入延遲影響使用者體驗，\
所有寫回操作皆透過本地 Outbox / Queue 機制非同步執行，\
並具備重試與錯誤追蹤能力。

9.5 Benefits of the Low-Coupling Architecture

此低耦合整合架構具備以下優點：\
- 顯著提升用藥管理系統回應速度與穩定性。\
- 避免 HIS 效能問題影響臨床與藥師作業。\
- 降低 HIS 端需配合之客製與維運成本。\
- 保留與 TW Core / FHIR R4 標準之相容性。\
- 支援後續跨院、跨系統擴充與研究分析。

本章節所述架構為本系統正式建議之 HIS 整合模式，\
並取代任何即時雙向耦合或以 HIS 作為工作流核心之設計假設。

# Chapter 10. Competition Demo Mode and THAS Deployment Profile

為因應衛福部 FHIR 50 競賽（THAS 測試環境）僅提供單一 partition 之限制，\
本系統設計一套「Demo Mode（展示模式）」以確保在不影響正式架構原則下，\
仍可完整展示核子醫學放射藥物管理之閉環流程。

10.1 Dual-Mode Execution Strategy

本系統支援兩種執行模式：\
- Production Mode：用於院內正式部署，角色與流程依據實際人員權限運作。\
- Demo Mode：用於競賽與展示環境，允許在單一 partition 下模擬多角色操作。

系統透過設定參數（如 APP_MODE=demo）啟用 Demo Mode，\
並於介面明確標示「DEMO MODE」，避免與正式系統混淆。

10.2 Role View Switch in Demo Mode

在 Demo Mode 中，系統允許登入者於應用程式內切換操作視角（Role View
Switch），\
包括：\
- Nuclear Medicine Physician View\
- Pharmacist View

此角色切換僅影響介面呈現與操作權限判斷，\
實際登入身份（login subject）仍完整保留於系統稽核紀錄中，\
確保操作行為可追溯。

10.3 Demo Scenario Seeding

為確保展示流程之穩定性與完整性，\
Demo Mode 提供「一鍵 Demo Scenario」功能，\
可快速建立多筆代表性案例，例如：\
- 成人標準劑量案例\
- 兒童體重調整案例\
- 腎功能不全案例\
- 劑量超出建議範圍案例\
- 缺乏必要 Observation 案例

系統將於本地建立對應之 OrderCase 與 Workflow 狀態，\
並可選擇性同步最小必要之 FHIR 資源（ServiceRequest、Observation）至 THAS
測試伺服器。

10.4 Minimal THAS FHIR Interaction Contract

在競賽環境中，本系統對 THAS FHIR Server 僅執行最小必要之互動：\
- Read：ServiceRequest、Patient、Observation（必要時）\
- Write：最終核准之 MedicationRequest

所有中間流程狀態（審查、退回、Claim、批次核准）皆僅存在於本地系統，\
避免因外部 FHIR 伺服器效能限制影響展示體驗。

10.5 Audit and Transparency in Demo Mode

即使於 Demo Mode 下，系統仍完整記錄以下稽核資訊：\
- 真實登入者身份（login subject）\
- 當下操作視角（acting role）\
- 操作時間與行為類型

此設計可向評審清楚說明系統於正式環境下之角色與權限控管能力，\
同時兼顧競賽展示之實用性。

本章節所述 Demo Mode 僅為競賽與展示用途，\
不影響本系統於 Production Mode 下之安全性、治理與標準相容性設計。

# Chapter 11. Local Clinical Data Completion and Return-Response Analytics

本章節針對實際臨床作業中常見之「臨床資料缺失」與「藥師退回後醫師回應」兩項情境，\
定義本系統之正式處理機制、資料模型與研究分析支援方式，\
以確保臨床決策支援（CDS）之完整性與用藥治理之可稽核性。

11.1 Local Clinical Data Completion (Clinical Facts Override)

當來自 HIS 之 ServiceRequest 或 Observation 資料不足以支持用藥決策時，\
本系統允許核醫醫師於藥物管理系統內補登必要之臨床資料，\
作為 CDS 判斷與劑量建議之依據。

可補登之臨床資料包含但不限於：\
- 體重（Weight, kg）\
- 腎功能（eGFR 或 Serum Creatinine）\
- 過敏史摘要（Allergy summary）

所有補登資料皆儲存於本地 OrderCase 中，並標註：\
- 資料來源（HIS / Local Override）\
- 補登者身份\
- 補登時間\
- 補登原因

補登後，系統將即時重新執行 CDS 規則引擎，\
並更新劑量建議、風險旗標（flags）與嚴重度（severity）。

11.2 Rule Engine Behavior for Missing or Overridden Data

規則引擎需明確標示因資料缺失或補登所產生之判斷結果，例如：\
- MISSING_WEIGHT：缺乏體重資料（severity: FAIL 或 WARN）\
- MISSING_RENAL_FUNCTION：缺乏腎功能資料\
- ALLERGY_REVIEW_REQUIRED：需人工確認過敏史\
- LOCAL_DATA_USED：本次判斷使用本地補登資料

相關旗標將顯示於 NM 與 Pharmacy Worklist，\
並作為批次核准或逐筆審查之分群依據。

11.3 Pharmacist Return and Structured Return Reasons

當藥師對用藥草案存有疑慮時，可將案件退回核醫醫師，\
並需選擇一或多個結構化退回原因（Return Reason Codes），例如：\
- 劑量超出建議範圍\
- 臨床資料不足\
- 檢查與藥物不匹配\
- 過敏或禁忌症疑慮

退回事件將完整記錄於系統中，\
包含退回原因、補充說明、退回者與時間戳記。

11.4 Physician Response to Return

核醫醫師處理退回案件時，\
需標示其回應方式（Response Action），例如：\
- UPDATED_DOSE：修正劑量\
- ADDED_MISSING_DATA：補齊臨床資料\
- PROVIDED_OVERRIDE_JUSTIFICATION：維持原劑量並提供理由\
- CANCELLED_ORDER：取消藥囑

每次回應皆形成一個新的藥囑草案版本（draft revision），\
以保留完整之版本演進與稽核紀錄。

11.5 Analytics and Research Metrics

本系統支援以下與補登與退回互動相關之統計與研究指標：\
- 臨床資料缺失率（Missing data rate）\
- 補登資料使用比例\
- 藥師退回率與退回原因分布\
- 醫師回應類型分布\
- 退回後重新核准之比例\
- 各類情境之處理時間（TAT）

上述指標可作為臨床品質改善與研究分析之重要依據，\
並可與系統導入前後進行比較。

# Addendum A. Patient Snapshot Review and Auto-Completion of Missing Facts

本附錄針對臨床實務中「病人病程紀錄（patient
snapshot）已包含關鍵資訊」之情境，\
定義系統如何在核醫藥管理作業中利用病程摘要，自動擷取並預填（auto-fill）體重、過敏與檢驗數值等關鍵事實，\
以降低醫師手動輸入負擔並提升 CDS 執行效率。

A.1 Patient Snapshot Scope and Data Sources

藥物管理系統建立 OrderCase 時，除擷取 ServiceRequest 與必要 Observation
外，\
可同步取得病人之「病程紀錄摘要（patient
snapshot）」，作為核醫醫師在開立用藥草案時之臨床參考。\
patient snapshot 可由下列來源組成（依醫院可得性與權限決定）：\
- FHIR
資源彙整：Condition、AllergyIntolerance、Observation（vitals/labs）、MedicationStatement（選配）等\
- 文件型摘要（選配）：DocumentReference/Composition（若院內提供）\
- 系統內既有摘要欄位（例如 ServiceRequest.note 或 Encounter
summary，若有）

A.2 Auto-Completion (Auto-fill) Logic

系統在載入 patient snapshot 時，將執行自動擷取流程，嘗試補足 CDS
所需之關鍵資料：\
1. 體重（Weight）：優先從 Observation（LOINC
29463-7）取得；若缺，嘗試從病程摘要或文件摘要中抽取最近一次數值。\
2. 過敏史（Allergy）：優先從 AllergyIntolerance
取得；若缺，嘗試從病程摘要之問題清單或備註欄位抽取關鍵字。\
3. 腎功能（Renal function）：優先從
Observation（Scr/eGFR）取得；若缺，嘗試從檢驗摘要或文件摘要抽取最近一次數值。

自動擷取結果將以「候選值（candidate facts）」呈現，並包含：\
- value（數值/文字）\
- effectiveDateTime / asOf（來源時間）\
- sourceType（FHIR resource / document text / note）\
- sourceRef（resource id 或 document reference）\
- confidence（High/Medium/Low）\
- extractionMethod（structured / pattern / NLP，若採用）

A.3 Clinician Review and Acceptance

為維持醫療品質與可稽核性，auto-fill 之候選值不得直接覆寫既有 HIS 事實。\
系統應提供核醫端介面：\
- 顯示候選值與來源（可點擊查看來源摘要/片段）\
- 一鍵「採用」或「忽略」候選值\
- 採用後寫入本地 Local Clinical Data Completion 欄位，標註來源為
Auto-fill

A.4 Audit and Research Metrics for Auto-fill

所有 auto-fill 相關事件需納入稽核與研究指標：\
- auto-fill 候選值產生數、採用率、忽略率\
- 依資料類型（體重/過敏/腎功能）分層統計\
- auto-fill 對 missing data rate 與 TAT 之影響\
- 自動擷取信心度與後續退回率關聯（探索性分析）

本附錄功能在 Demo Mode 可由內建案例資料（seed snapshot）模擬，\
在 Production Mode 則可依院內可提供之 patient snapshot 來源逐步擴充。

# Addendum B. Auto-fill Candidate Facts Schema and API Contract

## B.1 JSON Schema: Candidate Fact and Snapshot Response

// CandidateFact

{

\"type\": \"object\",

\"required\": \[\"factType\", \"value\", \"asOf\", \"sourceType\",
\"confidence\", \"extractionMethod\"\],

\"properties\": {

\"factType\": { \"type\": \"string\", \"enum\": \[\"WEIGHT_KG\",
\"EGFR\", \"SCR_MGDL\", \"ALLERGY_SUMMARY\"\] },

\"value\": { \"type\": \[\"number\", \"string\"\] },

\"unit\": { \"type\": \"string\", \"description\": \"UCUM where
applicable, e.g., \'kg\', \'mL/min/1.73m2\', \'mg/dL\'\" },

\"asOf\": { \"type\": \"string\", \"format\": \"date-time\",
\"description\": \"Effective time of the source fact\" },

\"sourceType\": { \"type\": \"string\", \"enum\": \[\"FHIR_RESOURCE\",
\"DOCUMENT_TEXT\", \"NOTE_TEXT\"\] },

\"sourceRef\": { \"type\": \"string\", \"description\": \"FHIR reference
(e.g., \'Observation/123\') or document id\" },

\"sourceSnippet\": { \"type\": \"string\", \"description\": \"Optional
short excerpt for UI display\" },

\"confidence\": { \"type\": \"string\", \"enum\": \[\"HIGH\",
\"MEDIUM\", \"LOW\"\] },

\"extractionMethod\": { \"type\": \"string\", \"enum\":
\[\"STRUCTURED\", \"PATTERN\", \"NLP\"\] },

\"derived\": {

\"type\": \"object\",

\"description\": \"Optional derived metadata\",

\"properties\": {

\"loinc\": { \"type\": \"string\" },

\"system\": { \"type\": \"string\" },

\"code\": { \"type\": \"string\" }

}

}

}

}

// PatientSnapshotResponse

{

\"type\": \"object\",

\"required\": \[\"caseId\", \"patientRef\", \"serviceRequestRef\",
\"snapshot\", \"candidateFacts\"\],

\"properties\": {

\"caseId\": { \"type\": \"string\" },

\"patientRef\": { \"type\": \"string\" },

\"serviceRequestRef\": { \"type\": \"string\" },

\"snapshot\": {

\"type\": \"object\",

\"properties\": {

\"conditions\": { \"type\": \"array\", \"items\": { \"type\": \"object\"
} },

\"allergies\": { \"type\": \"array\", \"items\": { \"type\": \"object\"
} },

\"observations\": { \"type\": \"array\", \"items\": { \"type\":
\"object\" } },

\"documents\": { \"type\": \"array\", \"items\": { \"type\": \"object\"
} }

}

},

\"candidateFacts\": {

\"type\": \"array\",

\"items\": { \"\$ref\": \"#/CandidateFact\" }

}

}

}

## B.2 JSON Schema: Accept/Reject Auto-fill

// AcceptAutoFillRequest

{

\"type\": \"object\",

\"required\": \[\"caseId\", \"facts\"\],

\"properties\": {

\"caseId\": { \"type\": \"string\" },

\"facts\": {

\"type\": \"array\",

\"items\": {

\"type\": \"object\",

\"required\": \[\"factType\", \"value\", \"asOf\", \"sourceType\",
\"confidence\", \"extractionMethod\"\],

\"properties\": {

\"factType\": { \"type\": \"string\" },

\"value\": { \"type\": \[\"number\", \"string\"\] },

\"unit\": { \"type\": \"string\" },

\"asOf\": { \"type\": \"string\", \"format\": \"date-time\" },

\"sourceType\": { \"type\": \"string\" },

\"sourceRef\": { \"type\": \"string\" },

\"confidence\": { \"type\": \"string\" },

\"extractionMethod\": { \"type\": \"string\" }

}

}

},

\"acceptedBy\": { \"type\": \"string\", \"description\": \"login
subject; server may override from token\" },

\"reason\": { \"type\": \"string\", \"description\": \"Optional
acceptance note\" }

}

}

// RejectAutoFillRequest

{

\"type\": \"object\",

\"required\": \[\"caseId\", \"rejections\"\],

\"properties\": {

\"caseId\": { \"type\": \"string\" },

\"rejections\": {

\"type\": \"array\",

\"items\": {

\"type\": \"object\",

\"required\": \[\"factType\", \"sourceRef\"\],

\"properties\": {

\"factType\": { \"type\": \"string\" },

\"sourceRef\": { \"type\": \"string\" },

\"reason\": { \"type\": \"string\" }

}

}

}

}

}

## B.3 FastAPI-style Endpoint Specifications

Base URL: /api

1\) GET /cases/{caseId}/snapshot

Purpose:

\- Retrieve patient snapshot (summarized clinical course) and auto-fill
candidate facts for the case.

Path Params:

\- caseId: string

Query Params (optional):

\- refresh=true\|false (default false): if true, re-fetch from HIS FHIR
and recompute candidates.

Response 200 (PatientSnapshotResponse):

\- returns snapshot + candidateFacts\[\]

2\) POST /cases/{caseId}/autofill/accept

Purpose:

\- Clinician accepts one or more candidate facts; persist into
localFacts (source=AutoFill) and rerun CDS.

Request Body (AcceptAutoFillRequest):

\- caseId, facts\[\]

Response 200:

{

\"caseId\": \"string\",

\"updatedLocalFacts\": { \"type\": \"object\" },

\"cds\": {

\"overallSeverity\": \"PASS\|WARN\|FAIL\",

\"isBatchEligible\": true,

\"flags\": \[ { \"code\": \"string\", \"severity\":
\"INFO\|WARN\|FAIL\", \"title\": \"string\", \"explain\": \"string\" }
\]

}

}

3\) POST /cases/{caseId}/autofill/reject

Purpose:

\- Clinician rejects candidate facts (for audit + to prevent repeated
prompting); no localFacts update.

Request Body (RejectAutoFillRequest)

Response 200:

{

\"caseId\": \"string\",

\"rejected\": true

}

4\) GET /analytics/autofill/summary?from=YYYY-MM-DD&to=YYYY-MM-DD

Purpose:

\- Provide research-ready metrics for auto-fill usage and impact.

Response 200:

{

\"window\": {\"from\":\"YYYY-MM-DD\",\"to\":\"YYYY-MM-DD\"},

\"candidatesGenerated\": 0,

\"candidatesAccepted\": 0,

\"candidatesRejected\": 0,

\"acceptRate\": 0.0,

\"byFactType\": \[

{\"factType\":\"WEIGHT_KG\",\"generated\":0,\"accepted\":0,\"rejected\":0,\"acceptRate\":0.0}

\],

\"impact\": {

\"missingDataRateBefore\": 0.0,

\"missingDataRateAfter\": 0.0,

\"medianTATBefore\": 0.0,

\"medianTATAfter\": 0.0

}

}
