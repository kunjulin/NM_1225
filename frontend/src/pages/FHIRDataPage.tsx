import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Divider,
  Link,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import {
  HealthAndSafety as FHIRIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material'

export function FHIRDataPage() {
  return (
    <Box>
      {/* Header */}
      <Stack direction="row" alignItems="center" spacing={2} mb={3}>
        <FHIRIcon color="primary" sx={{ fontSize: 32 }} />
        <Typography variant="h5" fontWeight={600}>
          FHIR 資料
        </Typography>
      </Stack>

      {/* TW Core 相容性說明 Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} mb={3}>
            <FHIRIcon color="primary" />
            <Typography variant="h6">台灣核心資料群（TW Core）相容性與支援度</Typography>
          </Stack>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              本系統遵循 HL7 FHIR R4 標準，並與「台灣核心實作指引（TW Core IG）」保持相容。
              以下說明本系統對 TW Core 的支援情況。
            </Typography>
          </Alert>

          {/* TW Core 官方連結 */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              相關資源
            </Typography>
            <Stack spacing={1}>
              <Link
                href="https://twcore.mohw.gov.tw/ig/twcore/0.3.0/index.html"
                target="_blank"
                rel="noopener noreferrer"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  textDecoration: 'none',
                }}
              >
                <OpenInNewIcon fontSize="small" />
                <Typography variant="body2">
                  台灣核心實作指引（TW Core IG）官方網站
                </Typography>
              </Link>
            </Stack>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* 支援的 FHIR 資源類型 */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              支援的 FHIR 資源類型
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              本系統支援以下 FHIR R4 資源類型，並符合 TW Core 的實作指引：
            </Typography>
            
            <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>資源類型</strong></TableCell>
                    <TableCell><strong>TW Core 支援</strong></TableCell>
                    <TableCell><strong>說明</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Patient</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>病人基本資料，支援 TW Core Patient Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>ServiceRequest</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>檢查服務請求，支援 TW Core ServiceRequest Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>MedicationRequest</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>用藥請求，支援 TW Core MedicationRequest Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Observation</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>檢驗觀察值，支援 TW Core Observation Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Condition</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>診斷條件，支援 TW Core Condition Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>AllergyIntolerance</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>過敏反應，支援 TW Core AllergyIntolerance Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Medication</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>藥物資訊，支援 TW Core Medication Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Encounter</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>就醫記錄，支援 TW Core Encounter Profile</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Procedure</TableCell>
                    <TableCell>
                      <Chip 
                        icon={<CheckIcon />} 
                        label="完全支援" 
                        color="success" 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>處置記錄，支援 TW Core Procedure Profile</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* 相容性說明 */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              相容性說明
            </Typography>
            <Stack spacing={2}>
              <Box>
                <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                  <CheckIcon color="success" />
                  <Typography variant="body2" fontWeight={600}>
                    FHIR R4 標準相容
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ pl: 4 }}>
                  本系統完全遵循 HL7 FHIR R4 標準，確保與其他 FHIR 相容系統的互通性。
                </Typography>
              </Box>

              <Box>
                <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                  <CheckIcon color="success" />
                  <Typography variant="body2" fontWeight={600}>
                    TW Core Profile 支援
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ pl: 4 }}>
                  系統支援 TW Core 定義的各種 Profile，包括 Patient、ServiceRequest、MedicationRequest 等核心資源的台灣在地化擴充。
                </Typography>
              </Box>

              <Box>
                <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                  <CheckIcon color="success" />
                  <Typography variant="body2" fontWeight={600}>
                    資料交換格式
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ pl: 4 }}>
                  支援 JSON 格式的 FHIR 資源交換，符合 TW Core 的資料格式規範。
                </Typography>
              </Box>

              <Box>
                <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                  <InfoIcon color="info" />
                  <Typography variant="body2" fontWeight={600}>
                    持續更新
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ pl: 4 }}>
                  系統會持續追蹤 TW Core 的更新，確保與最新版本的相容性。
                </Typography>
              </Box>
            </Stack>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* 實作細節 */}
          <Box>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              實作細節
            </Typography>
            <Stack spacing={2}>
              <Box>
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  資料同步機制
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  系統透過 FHIR RESTful API 與外部 FHIR 伺服器進行資料同步，支援 ServiceRequest 的查詢與 MedicationRequest 的建立。
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  臨床資料快照
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  系統會建立包含 Patient、Observation、Condition、AllergyIntolerance 等資源的臨床資料快照，用於臨床決策支援。
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  驗證與錯誤處理
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  系統會驗證接收到的 FHIR 資源是否符合 TW Core Profile 的規範，並提供適當的錯誤處理機制。
                </Typography>
              </Box>
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* 技術規格 Card */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            技術規格
          </Typography>
          <Stack spacing={2}>
            <Box>
              <Typography variant="body2" fontWeight={600} gutterBottom>
                FHIR 版本
              </Typography>
              <Typography variant="body2" color="text.secondary">
                HL7 FHIR R4 (4.0.1)
              </Typography>
            </Box>

            <Box>
              <Typography variant="body2" fontWeight={600} gutterBottom>
                TW Core 版本
              </Typography>
              <Typography variant="body2" color="text.secondary">
                參考 TW Core IG 0.3.0 版本
              </Typography>
            </Box>

            <Box>
              <Typography variant="body2" fontWeight={600} gutterBottom>
                資料格式
              </Typography>
              <Typography variant="body2" color="text.secondary">
                JSON (application/fhir+json)
              </Typography>
            </Box>

            <Box>
              <Typography variant="body2" fontWeight={600} gutterBottom>
                API 端點
              </Typography>
              <Typography variant="body2" color="text.secondary" component="pre" sx={{ 
                fontFamily: 'monospace', 
                bgcolor: 'background.default', 
                p: 1, 
                borderRadius: 1,
                fontSize: '0.875rem',
              }}>
                GET /fhir/ServiceRequest{'\n'}
                POST /fhir/MedicationRequest{'\n'}
                GET /fhir/Patient/{id}
              </Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  )
}

