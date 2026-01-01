import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Typography,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Chip,
} from '@mui/material'
import {
  Close as CloseIcon,
  Science as NMIcon,
  LocalPharmacy as PharmacyIcon,
  Assessment as AnalyticsIcon,
  People as UsersIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'

interface HelpPageProps {
  open: boolean
  onClose: () => void
}

export function HelpPage({ open, onClose }: HelpPageProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: '90vh',
        },
      }}
    >
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h5" fontWeight={600}>
            操作說明書
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ pb: 2 }}>
          {/* 核醫工作清單 */}
          <Paper elevation={0} sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
            <Stack direction="row" alignItems="center" spacing={1} mb={2}>
              <NMIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                核醫工作清單
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary" paragraph>
              核醫醫師使用此頁面查看待處理的核醫檢查案件，並進行劑量草案建立與送審。
            </Typography>
            
            <Typography variant="subtitle2" fontWeight={600} mt={2} mb={1}>
              主要功能：
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="1. 同步 FHIR 資料"
                  secondary="點擊「同步 FHIR」按鈕，從 FHIR Server 同步最新的 ServiceRequest 資料。系統會自動建立新的案件。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="2. 日期篩選"
                  secondary="使用「期望執行日期」篩選器，可以篩選特定日期的案件，方便安排工作。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="3. 查看工作清單"
                  secondary={
                    <>
                      工作清單分為多個標籤頁：
                      <br />• 待處理：新同步的案件，尚未建立草案
                      <br />• 已建立草案：已建立劑量草案，等待送審
                      <br />• 藥師退回：被藥師退回的案件，需要重新處理
                      <br />• 已送審：已送審給藥師的案件
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="4. 批次送審"
                  secondary="在「已建立草案」標籤頁中，可以勾選多個案件（CDS 評估為 PASS/INFO/WARN 的案件），點擊「批次送審」按鈕一次送審多個案件。注意：CDS 評估為 FAIL 的案件需要個別處理，無法批次送審。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="5. 查看案件詳情"
                  secondary="點擊任一案件列，即可進入案件詳情頁面，查看完整的病人資料、CDS 評估結果，並建立或修改劑量草案。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="6. 狀態說明"
                  secondary={
                    <>
                      <Chip label="待處理" size="small" sx={{ mr: 0.5, mb: 0.5 }} /> 新案件，尚未處理
                      <br />
                      <Chip label="已建立草案" size="small" sx={{ mr: 0.5, mb: 0.5 }} /> 已建立劑量草案，可送審
                      <br />
                      <Chip label="藥師退回" size="small" sx={{ mr: 0.5, mb: 0.5 }} /> 被藥師退回，需重新處理
                      <br />
                      <Chip label="已送審" size="small" sx={{ mr: 0.5, mb: 0.5 }} /> 已送審給藥師審查
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="7. CDS 評估標示"
                  secondary={
                    <>
                      <Chip label="PASS" size="small" color="success" sx={{ mr: 0.5, mb: 0.5 }} /> 通過檢查
                      <br />
                      <Chip label="INFO" size="small" color="info" sx={{ mr: 0.5, mb: 0.5 }} /> 資訊提示
                      <br />
                      <Chip label="WARN" size="small" color="warning" sx={{ mr: 0.5, mb: 0.5 }} /> 警告
                      <br />
                      <Chip label="FAIL" size="small" color="error" sx={{ mr: 0.5, mb: 0.5 }} /> 失敗，需個別處理
                    </>
                  }
                />
              </ListItem>
            </List>
          </Paper>

          {/* 藥師工作清單 */}
          <Paper elevation={0} sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
            <Stack direction="row" alignItems="center" spacing={1} mb={2}>
              <PharmacyIcon color="secondary" />
              <Typography variant="h6" fontWeight={600}>
                藥師工作清單
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary" paragraph>
              藥師使用此頁面審查核醫醫師送審的案件，進行核准或退回作業。
            </Typography>
            
            <Typography variant="subtitle2" fontWeight={600} mt={2} mb={1}>
              主要功能：
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="1. 查看工作清單"
                  secondary={
                    <>
                      工作清單分為四個標籤頁：
                      <br />• 醫師回覆：核醫醫師回應退回的案件
                      <br />• 可批次核准：CDS 評估通過且符合批次核准條件的案件
                      <br />• 需逐筆審查：不符合批次核准條件的案件，需要逐筆審查
                      <br />• 批准待上傳：已核准但尚未上傳到 FHIR Server 的案件
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="2. 批次核准"
                  secondary="在「可批次核准」標籤頁中，可以勾選多個案件，點擊「批次核准」按鈕一次核准多個案件。系統會自動建立 MedicationRequest 並上傳到 FHIR Server。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="3. 逐筆審查"
                  secondary="在「需逐筆審查」標籤頁中，點擊案件進入詳情頁面，查看完整的病人資料、CDS 評估結果、核醫醫師的草案與說明，然後決定核准或退回。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="4. 退回案件"
                  secondary={
                    <>
                      如果發現問題（如劑量不當、缺少必要資料等），可以退回案件給核醫醫師，並選擇退回原因：
                      <br />• 劑量超出範圍
                      <br />• 缺少資料
                      <br />• 資料不符
                      <br />• 過敏疑慮
                      <br />• 其他
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="5. 查看案件詳情"
                  secondary="點擊任一案件列，即可進入案件詳情頁面，查看完整的病人資料、CDS 評估結果、核醫醫師的草案與說明，以及審查歷程。"
                />
              </ListItem>
            </List>
          </Paper>

          {/* 分析儀表板 */}
          <Paper elevation={0} sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
            <Stack direction="row" alignItems="center" spacing={1} mb={2}>
              <AnalyticsIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                分析儀表板
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary" paragraph>
              提供系統使用統計與分析資料，幫助了解系統運作狀況與改善方向。
            </Typography>
            
            <Typography variant="subtitle2" fontWeight={600} mt={2} mb={1}>
              主要功能：
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="1. 日期範圍篩選"
                  secondary="使用「起始日期」和「結束日期」選擇要分析的資料範圍，預設為最近 30 天。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="2. KPI 指標卡片"
                  secondary={
                    <>
                      顯示四個關鍵指標：
                      <br />• 總案件數：期間內處理的案件總數
                      <br />• 藥師介入率：藥師退回或要求修改的案件比例
                      <br />• 批次核准率：批次核准的案件比例
                      <br />• Auto-fill 接受率：自動填入功能的接受率
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="3. 退回原因分佈圖"
                  secondary="以圓餅圖顯示各種退回原因的分佈情況，幫助了解常見的退回原因。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="4. 醫師回應動作分佈圖"
                  secondary="以長條圖顯示核醫醫師回應退回案件時採取的動作分佈。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="5. Auto-fill 統計"
                  secondary={
                    <>
                      顯示自動填入功能的統計資料：
                      <br />• 產生候選值：系統自動產生的候選值數量
                      <br />• 已接受：使用者接受的候選值數量
                      <br />• 已拒絕：使用者拒絕的候選值數量
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="6. 匯出 CSV"
                  secondary="點擊「匯出 CSV」按鈕，可以將分析資料匯出為 CSV 檔案，方便進一步分析。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="7. 上傳記錄"
                  secondary="點擊「上傳記錄」按鈕，可以查看 MedicationRequest 上傳到 FHIR Server 的記錄，包括成功與失敗的記錄。"
                />
              </ListItem>
            </List>
          </Paper>

          {/* 使用者管理 */}
          <Paper elevation={0} sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
            <Stack direction="row" alignItems="center" spacing={1} mb={2}>
              <UsersIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                使用者管理
              </Typography>
              <Chip label="管理員專用" size="small" color="warning" />
            </Stack>
            <Typography variant="body2" color="text.secondary" paragraph>
              系統管理員使用此頁面管理使用者帳號，包括審核新使用者、指派角色、啟用/停用帳號等。
            </Typography>
            
            <Typography variant="subtitle2" fontWeight={600} mt={2} mb={1}>
              主要功能：
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="1. 查看使用者清單"
                  secondary={
                    <>
                      頁面分為兩個標籤頁：
                      <br />• 待審核：等待審核的新使用者（首次登入的使用者）
                      <br />• 所有使用者：系統中的所有使用者
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="2. 審核新使用者"
                  secondary="在「待審核」標籤頁中，點擊使用者旁的「審核通過」圖示，選擇要指派給使用者的角色（核醫醫師、藥師、系統管理員），然後點擊「審核通過」按鈕。審核通過後，使用者即可使用系統。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="3. 編輯使用者角色"
                  secondary="在「所有使用者」標籤頁中，點擊已啟用使用者旁的「編輯」圖示，可以修改使用者的角色指派。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="4. 啟用/停用帳號"
                  secondary="點擊「停用」圖示可以停用使用者帳號，點擊「啟用」圖示可以重新啟用已停用的帳號。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="5. 新增使用者"
                  secondary={
                    <>
                      點擊「新增使用者」按鈕，可以手動建立新的使用者帳號，需要填寫：
                      <br />• 使用者識別碼（subject）
                      <br />• 顯示名稱
                      <br />• 電子郵件（選填）
                      <br />• 指派角色
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="6. 使用者狀態"
                  secondary={
                    <>
                      <Chip label="待審核" size="small" color="warning" sx={{ mr: 0.5, mb: 0.5 }} /> 等待管理員審核
                      <br />
                      <Chip label="已啟用" size="small" color="success" sx={{ mr: 0.5, mb: 0.5 }} /> 正常使用中
                      <br />
                      <Chip label="已停用" size="small" color="error" sx={{ mr: 0.5, mb: 0.5 }} /> 已停用，無法登入
                    </>
                  }
                />
              </ListItem>
            </List>
          </Paper>

          {/* 系統設定 */}
          <Paper elevation={0} sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
            <Stack direction="row" alignItems="center" spacing={1} mb={2}>
              <SettingsIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                系統設定
              </Typography>
              <Chip label="管理員專用" size="small" color="warning" />
            </Stack>
            <Typography variant="body2" color="text.secondary" paragraph>
              系統管理員使用此頁面設定 LLM（大型語言模型）API 連線與提示詞，用於 AI 輔助分析功能。
            </Typography>
            
            <Typography variant="subtitle2" fontWeight={600} mt={2} mb={1}>
              主要功能：
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="1. LLM API 設定"
                  secondary={
                    <>
                      設定連接到 LLM API 的參數：
                      <br />• API Endpoint URL：LLM API 的基礎 URL（例如 Ollama: http://localhost:11434/v1）
                      <br />• 模型名稱：使用的模型名稱（例如 llama3.1, gpt-4, mistral 等）
                      <br />• API Key：如果需要 API Key，在此輸入（可選）
                      <br />• 請求超時：API 請求的超時時間（秒）
                      <br />• 最大 Tokens：回應的最大 token 數量
                      <br />• Temperature：控制回應的隨機性（0-1，建議 0.1）
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="2. 自動分析開關"
                  secondary="開啟「自動分析」後，當使用者進入案件詳情頁面時，系統會自動執行 LLM 分析。關閉後，需要手動點擊「執行分析」按鈕。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="3. 連線測試"
                  secondary="點擊「測試連線」按鈕，可以測試與 LLM API 的連線是否正常，並顯示延遲時間。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="4. 提示詞設定"
                  secondary={
                    <>
                      設定兩個提示詞：
                      <br />• System Prompt：定義 AI 助手的角色與行為規範
                      <br />• User Prompt Template：使用者提示詞模板，{'{INPUT_PAYLOAD}'} 會被替換為實際的 FHIR 資料
                      <br />點擊「重設為預設」按鈕可以恢復為系統預設的提示詞。
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="5. LLM 錯誤日誌"
                  secondary="展開「LLM 錯誤日誌」區塊，可以查看最近失敗的分析記錄，包括錯誤訊息、案件 ID、執行時間等資訊。點擊「前往案件詳情」可以查看相關案件。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="6. 儲存設定"
                  secondary="完成設定後，點擊「儲存設定」按鈕儲存所有設定。點擊「重設」按鈕可以恢復為目前的設定值。"
                />
              </ListItem>
            </List>
          </Paper>

          {/* 案件詳情頁面 */}
          <Paper elevation={0} sx={{ p: 3, bgcolor: 'background.default' }}>
            <Typography variant="h6" fontWeight={600} mb={2}>
              案件詳情頁面
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              點擊工作清單中的任一案件，即可進入案件詳情頁面，查看完整的病人資料與進行操作。
            </Typography>
            
            <Typography variant="subtitle2" fontWeight={600} mt={2} mb={1}>
              主要功能：
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="1. 查看病人資料"
                  secondary={
                    <>
                      頁面會顯示完整的病人臨床資料，包括：
                      <br />• 基本資訊：姓名、ID、體重等
                      <br />• 就醫紀錄：門診、急診、住院等
                      <br />• 診斷/病史：ICD-10 診斷碼與說明
                      <br />• 用藥紀錄：目前使用的藥物
                      <br />• 檢驗結果：腎功能、肝功能、甲狀腺功能等
                      <br />• 過敏史：過敏原與反應症狀
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="2. 查看 CDS 評估結果"
                  secondary={
                    <>
                      顯示 CDS（臨床決策支援）規則的評估結果，包括：
                      <br />• 整體嚴重程度（PASS/INFO/WARN/FAIL）
                      <br />• 各項檢查標記（Flags）與說明
                      <br />• 建議的下一步動作
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="3. 建立/修改劑量草案（核醫醫師）"
                  secondary={
                    <>
                      核醫醫師可以：
                      <br />• 查看系統建議的劑量（基於 NA-2024 標準）
                      <br />• 建立或修改劑量草案
                      <br />• 選擇是否覆蓋建議劑量，並填寫覆蓋原因
                      <br />• 填寫備註說明
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="4. 送審案件（核醫醫師）"
                  secondary="完成劑量草案後，點擊「送審」按鈕，將案件送給藥師審查。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="5. 核准/退回案件（藥師）"
                  secondary={
                    <>
                      藥師可以：
                      <br />• 查看核醫醫師建立的劑量草案與說明
                      <br />• 點擊「核准」按鈕核准案件（系統會自動建立 MedicationRequest）
                      <br />• 點擊「退回」按鈕退回案件，選擇退回原因並填寫說明
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="6. AI 輔助分析"
                  secondary={
                    <>
                      如果系統已設定 LLM API，可以：
                      <br />• 自動分析（如果開啟自動分析功能）
                      <br />• 手動點擊「執行分析」按鈕
                      <br />分析結果包括：
                      <br />• 檢查適當性評估
                      <br />• 案件摘要
                      <br />• CDS 標記解釋
                      <br />• 建議的下一步動作
                    </>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="7. 查看審查歷程"
                  secondary={
                    <>
                      顯示案件的完整審查歷程，包括：
                      <br />• 建立時間
                      <br />• 送審時間
                      <br />• 退回/回應記錄
                      <br />• 核准時間
                    </>
                  }
                />
              </ListItem>
            </List>
          </Paper>

          <Divider sx={{ my: 3 }} />

          {/* 一般操作說明 */}
          <Paper elevation={0} sx={{ p: 3, bgcolor: 'background.default' }}>
            <Typography variant="h6" fontWeight={600} mb={2}>
              一般操作說明
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="角色切換"
                  secondary="點擊右上角的角色標籤（核醫醫師/藥師），可以切換不同的角色視角，查看對應的工作清單。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="重新整理"
                  secondary="點擊各頁面的「重新整理」圖示，可以手動更新資料。部分頁面會自動定期更新（如工作清單每 30 秒更新一次）。"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="登出"
                  secondary="點擊右上角的使用者頭像，選擇「登出」即可登出系統。"
                />
              </ListItem>
            </List>
          </Paper>
        </Box>
      </DialogContent>
    </Dialog>
  )
}

