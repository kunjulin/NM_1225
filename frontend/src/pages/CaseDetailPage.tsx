import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Paper,
  Snackbar,
  Tooltip,
  IconButton,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  CheckCircle as ApproveIcon,
  Cancel as ReturnIcon,
  Send as SubmitIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircleOutline as PassIcon,
  Science as DoseIcon,
  Save as SaveIcon,
  Forum as ForumIcon,
  Person as PersonIcon,
  Reply as ReplyIcon,
  LocalPharmacy as PharmacyIcon,
  ExpandMore as ExpandMoreIcon,
  LocalHospital as HospitalIcon,
  Biotech as LabIcon,
  Medication as MedicationIcon,
  MedicalServices as ProcedureIcon,
  HealthAndSafety as AllergyIcon,
  Assignment as DiagnosisIcon,
  SmartToy as AIIcon,
  Psychology as AnalysisIcon,
  Checklist as ChecklistIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material'
import Accordion from '@mui/material/Accordion'
import AccordionSummary from '@mui/material/AccordionSummary'
import AccordionDetails from '@mui/material/AccordionDetails'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import {
  PatientSnapshot,
  ReturnReasonCode,
  ResponseAction,
  Severity,
  DraftData,
  EncounterInfo,
  ConditionInfo,
  MedicationInfo,
  ProcedureInfo,
  LabResultInfo,
  AllergyInfo,
  LLMAnalysisResponse,
  LLMSettingsStatus,
} from '../types'
import { severityColors, statusColors } from '../theme'

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { getAuthHeaders, actingRole } = useAuth()
  
  const [returnDialogOpen, setReturnDialogOpen] = useState(false)
  const [returnReasons, setReturnReasons] = useState<ReturnReasonCode[]>([])
  const [returnComment, setReturnComment] = useState('')
  
  const [respondDialogOpen, setRespondDialogOpen] = useState(false)
  const [responseAction, setResponseAction] = useState<ResponseAction>('UPDATED_DOSE')
  const [responseComment, setResponseComment] = useState('')
  
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  
  // 劑量編輯狀態
  const [editDose, setEditDose] = useState<number | null>(null)
  const [isEditingDose, setIsEditingDose] = useState(false)
  
  // 體重輸入狀態
  const [manualWeight, setManualWeight] = useState<string>('')
  
  // Override 狀態
  const [overrideReason, setOverrideReason] = useState('')

  // 取得案件快照
  const [forceRefresh, setForceRefresh] = useState(false)
  const { data: snapshot, isLoading, error, refetch } = useQuery<PatientSnapshot>({
    queryKey: ['case-snapshot', caseId, forceRefresh],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      const refreshParam = forceRefresh ? '?refresh=true' : ''
      return apiClient.get<PatientSnapshot>(`/cases/${caseId}/snapshot${refreshParam}`)
    },
    enabled: !!caseId,
    refetchOnMount: 'always', // 每次進入頁面都重新獲取
    staleTime: 0, // 資料立即過期，確保每次都刷新
  })
  
  // 處理手動刷新（從 FHIR Server 重新取得資料）
  const handleRefresh = () => {
    setForceRefresh(prev => !prev) // 切換狀態以觸發重新查詢
    setTimeout(() => {
      refetch() // 立即觸發查詢
    }, 100)
  }

  // 初始化 Override 理由（從 draft 中載入）
  useEffect(() => {
    if (snapshot?.draft?.override?.isOverride && snapshot.draft.override.reason) {
      setOverrideReason(snapshot.draft.override.reason)
    }
  }, [snapshot])

  // Claim
  const claimMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/pharmacy/cases/${caseId}/claim`)
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Claim 成功', severity: 'success' })
      queryClient.invalidateQueries({ queryKey: ['case-snapshot', caseId] })
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `Claim 失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })

  // Approve
  const approveMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/pharmacy/cases/${caseId}/approve`)
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: '核准成功', severity: 'success' })
      navigate('/pharmacy/worklist')
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `核准失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })

  // Return
  const returnMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/pharmacy/cases/${caseId}/return`, {
        returnReasonCodes: returnReasons,
        comment: returnComment,
      })
    },
    onSuccess: () => {
      setReturnDialogOpen(false)
      setSnackbar({ open: true, message: '退回成功', severity: 'success' })
      // 確保兩邊工作清單都會更新
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
      navigate('/pharmacy/worklist')
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `退回失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })

  // Submit
  const submitMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/nm/cases/${caseId}/submit`)
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: '送審成功', severity: 'success' })
      // 刷新兩邊的工作清單
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
      navigate('/nm/worklist')
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `送審失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })

  // Respond
  const respondMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/nm/cases/${caseId}/respond`, {
        responseAction,
        comment: responseComment,
      })
    },
    onSuccess: () => {
      setRespondDialogOpen(false)
      setSnackbar({ open: true, message: '回應成功，已重新送交藥師審查', severity: 'success' })
      // 刷新所有相關資料
      queryClient.invalidateQueries({ queryKey: ['case-snapshot', caseId] })
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
      // 回應後導航到工作清單
      navigate('/nm/worklist')
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `回應失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })


  // Save Draft (劑量更新)
  const saveDraftMutation = useMutation({
    mutationFn: async (params: { doseValue: number; overrideReason?: string }) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      const draftData: DraftData = {
        examCode: snapshot?.draft?.examCode || 'BONE_SCAN',
        radiopharmaceuticalCode: snapshot?.draft?.radiopharmaceuticalCode || 'local-tc99m-mdp',
        suggestedDose: { value: params.doseValue, unit: 'MBq' },
        override: params.overrideReason 
          ? { isOverride: true, reason: params.overrideReason }
          : snapshot?.draft?.override,
        notes: snapshot?.draft?.notes,
      }
      return apiClient.post(`/nm/cases/${caseId}/draft`, { draft: draftData })
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: '草案已儲存', severity: 'success' })
      setIsEditingDose(false)
      queryClient.invalidateQueries({ queryKey: ['case-snapshot', caseId] })
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `儲存失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })
  
  // 儲存手動輸入的體重
  const saveManualWeightMutation = useMutation({
    mutationFn: async (weight: number) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/cases/${caseId}/manual-fact`, {
        factType: 'WEIGHT_KG',
        value: weight,
        unit: 'kg',
      })
    },
    onSuccess: async () => {
      setSnackbar({ open: true, message: '體重已儲存，CDS 已重新評估', severity: 'success' })
      setManualWeight('')
      // 同時更新 snapshot 和工作清單，並強制重新載入
      await queryClient.invalidateQueries({ queryKey: ['case-snapshot', caseId] })
      await queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
      // 強制重新載入 snapshot 以取得最新的 CDS 評估結果
      refetch()
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `儲存失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })
  
  // 儲存 Override 並送審
  const saveOverrideAndSubmitMutation = useMutation({
    mutationFn: async (params: { doseValue?: number; overrideReason: string }) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      // 先儲存草案（含 Override）
      const draftData: DraftData = {
        examCode: snapshot?.draft?.examCode || 'BONE_SCAN',
        radiopharmaceuticalCode: snapshot?.draft?.radiopharmaceuticalCode || 'local-tc99m-mdp',
        suggestedDose: { 
          value: params.doseValue || snapshot?.draftDose?.value || 0, 
          unit: 'MBq' 
        },
        override: { isOverride: true, reason: params.overrideReason },
        notes: snapshot?.draft?.notes,
      }
      await apiClient.post(`/nm/cases/${caseId}/draft`, { draft: draftData })
      // 再送審
      return apiClient.post(`/nm/cases/${caseId}/submit`)
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: '已儲存 Override 並送審', severity: 'success' })
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
      navigate('/nm/worklist')
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `送審失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    )
  }

  if (error || !snapshot) {
    return (
      <Box>
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <Button startIcon={<BackIcon />} onClick={() => navigate(-1)}>
            返回
          </Button>
          <Button variant="contained" onClick={() => navigate('/nm/worklist')}>
            前往工作清單
          </Button>
        </Stack>
        <Alert severity="error">
          載入案件失敗：{(error as Error)?.message || '案件不存在'}
          <br />
          案件可能已被刪除或資料庫已重設，請回到工作清單重新選擇。
        </Alert>
      </Box>
    )
  }

  const isNM = actingRole === 'NM_PHYSICIAN'
  const isPharmacist = actingRole === 'PHARMACIST'

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Stack direction="row" alignItems="center" spacing={2}>
          <IconButton onClick={() => navigate(-1)}>
            <BackIcon />
          </IconButton>
          <Typography variant="h5" fontWeight={600}>
            案件詳情
          </Typography>
          <Chip label={caseId?.slice(0, 8)} size="small" />
        </Stack>
        <Stack direction="row" spacing={1}>
          <Tooltip title="重新整理（從 FHIR Server 重新取得臨床資料）">
            <IconButton onClick={handleRefresh} disabled={isLoading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      <Grid container spacing={3}>
        {/* 左側：病人資訊與快照 */}
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                病人資訊
              </Typography>
              <Grid container spacing={2}>
                {/* 病人資訊區塊 */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    病人資訊
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">病人參考</Typography>
                      <Typography>{snapshot.patientRef}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">體重</Typography>
                      <Typography>
                        {snapshot.doseCalculation?.weightUsed 
                          ? `${snapshot.doseCalculation.weightUsed} kg`
                          : snapshot.snapshot.weightKg 
                          ? `${snapshot.snapshot.weightKg} kg`
                          : '未提供'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Grid>
                
                {/* 臨床醫囑資訊區塊 */}
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    臨床醫囑資訊
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">ServiceRequest</Typography>
                      <Typography>{snapshot.serviceRequestRef}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">檢查項目</Typography>
                      <Typography>
                        {snapshot.snapshot.examDisplay 
                          || snapshot.snapshot.examCode 
                          || snapshot.draft?.examCode 
                          || '未指定'}
                      </Typography>
                    </Grid>
                    {/* 期望執行時間 */}
                    {snapshot.snapshot.occurrenceDateTime && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">期望執行時間</Typography>
                        <Typography>
                          {new Date(snapshot.snapshot.occurrenceDateTime).toLocaleString('zh-TW', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </Typography>
                      </Grid>
                    )}
                    {/* 開單醫師 */}
                    {snapshot.snapshot.requesterDisplay && (
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">開單醫師</Typography>
                        <Typography>{snapshot.snapshot.requesterDisplay}</Typography>
                      </Grid>
                    )}
                    {/* 適應症說明 */}
                    {snapshot.snapshot.reasonCodeDisplay && (
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary">適應症說明</Typography>
                        <Typography>{snapshot.snapshot.reasonCodeDisplay}</Typography>
                      </Grid>
                    )}
                  </Grid>
                </Grid>
                
                {/* 案件狀態 */}
                {snapshot.status && (
                  <Grid item xs={12}>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2" color="text.secondary">案件狀態</Typography>
                    <Chip 
                      label={snapshot.status} 
                      size="small" 
                      sx={{ 
                        bgcolor: statusColors[snapshot.status as keyof typeof statusColors] || '#9E9E9E',
                        color: '#FFF' 
                      }} 
                    />
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>

          {/* 臨床資料展示區塊 */}
          <ClinicalDataPanel snapshot={snapshot} />

          {/* AI 輔助分析面板 */}
          <AIAnalysisPanel caseId={caseId!} />

          {/* 藥師意見與審查歷程 - 只在有退回相關事件時顯示 */}
          {snapshot.reviewEvents && snapshot.reviewEvents.length > 0 && (
            <Card sx={{ mb: 3, border: '2px solid', borderColor: 'warning.main' }}>
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                  <ForumIcon color="warning" />
                  <Typography variant="h6">藥師意見與審查歷程</Typography>
                  <Chip label={snapshot.reviewEvents.length} size="small" color="warning" />
                </Stack>
                
                {/* 審查歷程時間軸 */}
                <Box sx={{ 
                  position: 'relative',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    left: '16px',
                    top: 0,
                    bottom: 0,
                    width: '2px',
                    bgcolor: 'grey.300',
                  }
                }}>
                  {snapshot.reviewEvents.map((event) => {
                    const isReturn = event.eventType === 'RETURN'
                    const isResponse = event.eventType === 'RESPONSE'
                    const isSubmit = event.eventType === 'SUBMIT'
                    const isPharmacist = event.actingRole === 'PHARMACIST'
                    
                    // 格式化時間
                    const eventTime = new Date(event.createdAt).toLocaleString('zh-TW', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                    
                    // 退回原因對照
                    const returnReasonLabels: Record<string, string> = {
                      DOSE_OUT_OF_RANGE: '劑量超出範圍',
                      MISSING_DATA: '資料不完整',
                      MISMATCH: '資料不符',
                      ALLERGY_CONCERN: '過敏疑慮',
                      OTHER: '其他原因',
                    }
                    
                    // 回應動作對照
                    const responseActionLabels: Record<string, string> = {
                      UPDATED_DOSE: '已調整劑量',
                      ADDED_MISSING_DATA: '已補齊資料',
                      PROVIDED_OVERRIDE_JUSTIFICATION: '提供 Override 理由',
                      CANCELLED_ORDER: '取消醫囑',
                    }
                    
                    // 事件類型標籤
                    const eventTypeLabels: Record<string, string> = {
                      RETURN: '退回',
                      RESPONSE: '回應',
                      SUBMIT: '送審',
                      APPROVE: '核准',
                      CLAIM: '認領',
                    }
                    
                    // 時間軸節點顏色
                    const dotColor = isReturn ? 'error.main' : isResponse ? 'success.main' : isSubmit ? 'primary.main' : 'grey.500'
                    
                    return (
                      <Box 
                        key={event.id} 
                        sx={{ 
                          display: 'flex',
                          mb: 3,
                          position: 'relative',
                        }}
                      >
                        {/* 時間軸節點 */}
                        <Box sx={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          bgcolor: dotColor,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          zIndex: 1,
                          flexShrink: 0,
                        }}>
                          {isPharmacist ? (
                            <PharmacyIcon sx={{ fontSize: 16, color: 'white' }} />
                          ) : (
                            <PersonIcon sx={{ fontSize: 16, color: 'white' }} />
                          )}
                        </Box>
                        
                        {/* 事件內容 */}
                        <Box sx={{ ml: 2, flex: 1 }}>
                          {/* 標題列：角色 + 時間 + 事件類型 */}
                          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" mb={1}>
                            <Chip 
                              label={isPharmacist ? '藥師' : '核醫醫師'}
                              size="small" 
                              sx={{
                                bgcolor: isPharmacist ? 'secondary.main' : 'primary.main',
                                color: 'white',
                                fontWeight: 600,
                              }}
                            />
                            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                              {eventTime}
                            </Typography>
                            <Chip 
                              label={eventTypeLabels[event.eventType] || event.eventType}
                              size="small"
                              variant="outlined"
                              color={isReturn ? 'error' : isResponse ? 'success' : 'primary'}
                            />
                          </Stack>
                          
                          {/* 退回原因 Chips */}
                          {isReturn && event.payload?.returnReasonCodes && event.payload.returnReasonCodes.length > 0 && (
                            <Box sx={{ mb: 1 }}>
                              <Typography variant="caption" color="error.dark" fontWeight={600} sx={{ mr: 1 }}>
                                退回原因:
                              </Typography>
                              {event.payload.returnReasonCodes.map((code) => (
                                <Chip 
                                  key={code} 
                                  label={returnReasonLabels[code] || code} 
                                  size="small"
                                  color="error"
                                  sx={{ mr: 0.5, mb: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}
                          
                          {/* 意見內容 - 不同顏色區分 */}
                          {event.payload?.comment && (
                            <Paper 
                              elevation={0}
                              sx={{ 
                                p: 1.5, 
                                bgcolor: isPharmacist ? '#FCE4EC' : '#E3F2FD',
                                borderLeft: '4px solid',
                                borderColor: isPharmacist ? 'secondary.main' : 'primary.main',
                              }}
                            >
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                {event.payload.comment}
                              </Typography>
                            </Paper>
                          )}
                          
                          {/* 回應動作標籤 */}
                          {isResponse && event.payload?.action && (
                            <Box sx={{ mt: 1 }}>
                              <Chip 
                                icon={<ReplyIcon />}
                                label={responseActionLabels[event.payload.action] || event.payload.action}
                                size="small"
                                color="success"
                                variant="outlined"
                              />
                            </Box>
                          )}
                        </Box>
                      </Box>
                    )
                  })}
                </Box>
              </CardContent>
            </Card>
          )}
          
          {/* 醫師回應區塊 - 只在 RETURNED 狀態時顯示 */}
          {snapshot.status === 'RETURNED' && isNM && (
            <Card sx={{ mb: 3, border: '2px solid', borderColor: 'primary.main' }}>
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                  <ReplyIcon color="primary" />
                  <Typography variant="h6">醫師回應</Typography>
                </Stack>
                
                {/* 歷史回應記錄 */}
                {snapshot.reviewEvents && snapshot.reviewEvents.filter(e => e.eventType === 'RESPONSE').length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      歷史回應記錄
                    </Typography>
                    {snapshot.reviewEvents.filter(e => e.eventType === 'RESPONSE').map((event) => {
                      const eventTime = new Date(event.createdAt).toLocaleString('zh-TW')
                      const responseActionLabels: Record<string, string> = {
                        UPDATED_DOSE: '已調整劑量',
                        ADDED_MISSING_DATA: '已補齊資料',
                        PROVIDED_OVERRIDE_JUSTIFICATION: '提供 Override 理由',
                        CANCELLED_ORDER: '取消醫囑',
                      }
                      return (
                        <Paper key={event.id} variant="outlined" sx={{ p: 1.5, mb: 1, bgcolor: 'grey.50' }}>
                          <Stack direction="row" spacing={1} alignItems="center" mb={0.5}>
                            <Typography variant="caption" color="text.secondary">{eventTime}</Typography>
                            {event.payload?.action && (
                              <Chip 
                                label={responseActionLabels[event.payload.action] || event.payload.action}
                                size="small"
                                color="success"
                                variant="outlined"
                              />
                            )}
                          </Stack>
                          {event.payload?.comment && (
                            <Typography variant="body2">{event.payload.comment}</Typography>
                          )}
                        </Paper>
                      )
                    })}
                  </Box>
                )}
                
                {/* 新回應輸入區 */}
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  新增回應
                </Typography>
                <Stack spacing={2}>
                  <FormControl fullWidth size="small">
                    <InputLabel>回應動作</InputLabel>
                    <Select
                      value={responseAction}
                      onChange={(e) => setResponseAction(e.target.value as ResponseAction)}
                      label="回應動作"
                    >
                      <MenuItem value="UPDATED_DOSE">已調整劑量</MenuItem>
                      <MenuItem value="ADDED_MISSING_DATA">已補齊資料</MenuItem>
                      <MenuItem value="PROVIDED_OVERRIDE_JUSTIFICATION">提供 Override 理由</MenuItem>
                      <MenuItem value="CANCELLED_ORDER">取消醫囑</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField
                    fullWidth
                    size="small"
                    label="回應說明 *"
                    multiline
                    rows={3}
                    value={responseComment}
                    onChange={(e) => setResponseComment(e.target.value)}
                    placeholder="請說明您的處理方式..."
                    helperText="填寫回應說明後，即可送交藥師審查"
                    error={!responseComment.trim()}
                  />
                  
                  {/* 有填寫回應才顯示送審按鈕 */}
                  {responseComment.trim() && (
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<SubmitIcon />}
                      onClick={() => respondMutation.mutate()}
                      disabled={respondMutation.isPending}
                      fullWidth
                    >
                      送交藥師審查
                    </Button>
                  )}
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* CDS 評估結果面板 */}
          {snapshot.ruleEval && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    {snapshot.ruleEval.overallSeverity === 'FAIL' && <ErrorIcon color="error" />}
                    {snapshot.ruleEval.overallSeverity === 'WARN' && <WarningIcon color="warning" />}
                    {snapshot.ruleEval.overallSeverity === 'INFO' && <InfoIcon color="info" />}
                    {snapshot.ruleEval.overallSeverity === 'PASS' && <PassIcon color="success" />}
                    <Typography variant="h6">CDS 評估結果</Typography>
                  </Stack>
                  <Chip
                    label={snapshot.ruleEval.overallSeverity}
                    size="small"
                    sx={{
                      bgcolor: severityColors[snapshot.ruleEval.overallSeverity as Severity],
                      color: '#FFF',
                    }}
                  />
                </Box>
                
                {/* FAIL 級別警示 */}
                {snapshot.ruleEval.overallSeverity === 'FAIL' && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    <strong>CDS 評估失敗</strong> - 請處理以下問題或提供 Override 理由才能送審
                  </Alert>
                )}
                
                {/* 批次核准資格 */}
                <Box mb={2}>
                  <Chip
                    label={snapshot.ruleEval.isBatchEligible ? '可批次核准' : '需逐筆審查'}
                    size="small"
                    color={snapshot.ruleEval.isBatchEligible ? 'success' : 'warning'}
                    variant="outlined"
                  />
                </Box>
                
                {/* Flags 列表 */}
                {snapshot.ruleEval.flags.length > 0 ? (
                  <List dense>
                    {snapshot.ruleEval.flags.map((flag, i) => (
                      <ListItem 
                        key={i}
                        sx={{
                          bgcolor: flag.severity === 'FAIL' ? 'error.light' : 
                                   flag.severity === 'WARN' ? 'warning.light' : 'transparent',
                          borderRadius: 1,
                          mb: 0.5,
                        }}
                      >
                        <ListItemIcon>
                          {flag.severity === 'FAIL' && <ErrorIcon color="error" />}
                          {flag.severity === 'WARN' && <WarningIcon color="warning" />}
                          {flag.severity === 'INFO' && <InfoIcon color="info" />}
                          {flag.severity === 'PASS' && <PassIcon color="success" />}
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography variant="body2" fontWeight={600}>{flag.title}</Typography>
                              <Chip label={flag.code} size="small" variant="outlined" />
                            </Stack>
                          }
                          secondary={
                            <>
                              <Typography variant="body2" color="text.secondary">{flag.explain}</Typography>
                              {flag.recommendation && (
                                <Typography variant="body2" color="primary" sx={{ mt: 0.5 }}>
                                  建議: {flag.recommendation}
                                </Typography>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="text.secondary">無警告或錯誤</Typography>
                )}
              </CardContent>
            </Card>
          )}

          {/* 醫師回應 / Override 區塊 */}
          {isNM && (
            <Card sx={{ mb: 3, borderColor: snapshot.ruleEval?.overallSeverity === 'FAIL' ? 'error.main' : 'primary.main', borderWidth: 2, borderStyle: 'solid' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom color={snapshot.ruleEval?.overallSeverity === 'FAIL' ? 'error.main' : 'primary.main'}>
                  醫師回應 / Override
                </Typography>
                
                {/* 顯示已存在的 Override 資訊 */}
                {snapshot.draft?.override?.isOverride && snapshot.draft?.override?.reason && (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <strong>已設定 Override：</strong> {snapshot.draft.override.reason}
                  </Alert>
                )}
                
                {/* 當有 FAIL 或 WARN 時顯示提示 */}
                {snapshot.ruleEval && ['FAIL', 'WARN'].includes(snapshot.ruleEval.overallSeverity) && (
                  <Alert severity={snapshot.ruleEval.overallSeverity === 'FAIL' ? 'error' : 'warning'} sx={{ mb: 2 }}>
                    {snapshot.ruleEval.overallSeverity === 'FAIL' 
                      ? 'CDS 評估失敗，請補充資料或填寫 Override 理由後才能送審'
                      : '建議填寫備註說明偏離 CDS 建議的原因'
                    }
                  </Alert>
                )}
                
                <Grid container spacing={2}>
                  {/* 體重輸入（缺少體重時顯示，或核醫醫師可以修改體重） */}
                  {(() => {
                    const hasMissingWeight = snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT')
                    const currentWeight = snapshot.doseCalculation?.weightUsed || snapshot.snapshot.weightKg
                    // 如果缺少體重，或狀態為 NM_PENDING（待核醫處理），都顯示輸入欄位
                    // 這樣即使沒有體重資料，核醫醫師也可以手動輸入
                    const shouldShowWeightInput = hasMissingWeight || snapshot.status === 'NM_PENDING' || currentWeight
                    
                    if (!shouldShowWeightInput) return null
                    
                    return (
                      <Grid item xs={12}>
                        <Paper 
                          variant="outlined" 
                          sx={{ 
                            p: 2, 
                            bgcolor: hasMissingWeight ? 'error.light' : 'primary.light',
                            borderColor: hasMissingWeight ? 'error.main' : 'primary.main',
                          }}
                        >
                          <Typography 
                            variant="body2" 
                            fontWeight={600} 
                            color={hasMissingWeight ? 'error.dark' : 'primary.dark'} 
                            gutterBottom
                          >
                            {hasMissingWeight ? '缺少體重資料' : '體重資料（可修改）'}
                          </Typography>
                          {currentWeight && !hasMissingWeight && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                              目前體重: {currentWeight} kg
                            </Typography>
                          )}
                          <Stack direction="row" spacing={1} alignItems="center">
                            <TextField
                              label="輸入體重 (kg)"
                              type="number"
                              size="small"
                              value={manualWeight}
                              onChange={(e) => setManualWeight(e.target.value)}
                              sx={{ width: 150 }}
                              placeholder={currentWeight ? currentWeight.toString() : ''}
                            />
                            <Button
                              variant="contained"
                              color={hasMissingWeight ? 'error' : 'primary'}
                              size="small"
                              onClick={() => {
                                const w = parseFloat(manualWeight)
                                if (w > 0) saveManualWeightMutation.mutate(w)
                              }}
                              disabled={!manualWeight || saveManualWeightMutation.isPending}
                            >
                              {hasMissingWeight ? '儲存體重' : '更新體重'}
                            </Button>
                          </Stack>
                        </Paper>
                      </Grid>
                    )
                  })()}
                  
                  {/* Override 備註 */}
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Override 理由 / 備註"
                      multiline
                      rows={2}
                      value={overrideReason}
                      onChange={(e) => setOverrideReason(e.target.value)}
                      placeholder="請說明偏離 CDS 建議的原因，例如：特殊臨床狀況、病人需求等"
                      helperText={snapshot.ruleEval?.overallSeverity === 'FAIL' 
                        ? '填寫理由後可在右側核醫操作區送審' 
                        : '選填：可記錄特殊情況說明'
                      }
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* 劑量編輯與 NA-2024 計算參考 */}
          {isNM && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <DoseIcon color="primary" />
                    <Typography variant="h6">劑量設定</Typography>
                  </Stack>
                </Box>
                
                <Grid container spacing={2}>
                  {/* 目前草案劑量 */}
                  <Grid item xs={12}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        目前草案劑量
                      </Typography>
                      {isEditingDose ? (
                        <Stack direction="row" spacing={1} alignItems="center">
                          <TextField
                            type="number"
                            size="small"
                            value={editDose ?? (snapshot.draftDose?.value || '')}
                            onChange={(e) => setEditDose(parseFloat(e.target.value))}
                            InputProps={{
                              endAdornment: <Typography sx={{ ml: 1 }}>MBq</Typography>,
                            }}
                            sx={{ width: 150 }}
                          />
                          <Button
                            variant="contained"
                            size="small"
                            startIcon={<SaveIcon />}
                            onClick={() => editDose && saveDraftMutation.mutate({ doseValue: editDose })}
                            disabled={!editDose || saveDraftMutation.isPending}
                          >
                            儲存
                          </Button>
                          <Button
                            size="small"
                            onClick={() => {
                              setIsEditingDose(false)
                              setEditDose(null)
                            }}
                          >
                            取消
                          </Button>
                        </Stack>
                      ) : (
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography variant="h5">
                            {snapshot.draftDose?.value 
                              ? `${snapshot.draftDose.value} ${snapshot.draftDose.unit || 'MBq'}`
                              : '尚未設定'
                            }
                          </Typography>
                          <Button
                            size="small"
                            startIcon={<EditIcon />}
                            onClick={() => {
                              setEditDose(snapshot.draftDose?.value || null)
                              setIsEditingDose(true)
                            }}
                          >
                            編輯
                          </Button>
                        </Stack>
                      )}
                    </Paper>
                  </Grid>
                  
                  {/* NA-2024 劑量計算參考 */}
                  {/* 每個病人都應該顯示這個 panel */}
                  {snapshot.doseCalculation && (
                    <Grid item xs={12}>
                      <Paper 
                        variant="outlined" 
                        sx={{ 
                          p: 2, 
                          bgcolor: snapshot.doseCalculation.suggestedDose === 0 
                            ? 'info.light' 
                            : (snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT') 
                                ? 'warning.light' 
                                : 'primary.light'),
                          borderColor: snapshot.doseCalculation.suggestedDose === 0 
                            ? 'info.main' 
                            : (snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT') 
                                ? 'warning.main' 
                                : 'primary.main'),
                        }}
                      >
                        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                          <Box>
                            <Typography 
                              variant="body2" 
                              color={
                                snapshot.doseCalculation.suggestedDose === 0 
                                  ? 'info.dark' 
                                  : (snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT') 
                                      ? 'warning.dark' 
                                      : 'primary.dark')
                              } 
                              fontWeight={600} 
                              gutterBottom
                            >
                              NA-2024 劑量計算參考
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {snapshot.doseCalculation.formula}
                            </Typography>
                            {snapshot.doseCalculation.suggestedDose === 0 && (
                              <Alert severity="info" sx={{ mt: 1, mb: 1 }}>
                                請先指定檢查項目，系統將根據 NA-2024 指引計算建議劑量。
                              </Alert>
                            )}
                            {snapshot.doseCalculation.suggestedDose !== 0 && snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT') && (
                              <Alert severity="warning" sx={{ mt: 1, mb: 1 }}>
                                目前沒有體重資料，顯示的是劑量範圍。請輸入體重後，系統會自動計算個人化劑量。
                              </Alert>
                            )}
                            <Box mt={1}>
                              {snapshot.doseCalculation.isPediatric && (
                                <Chip 
                                  label="兒童劑量" 
                                  size="small" 
                                  color="secondary"
                                  sx={{ mr: 1 }}
                                />
                              )}
                              {snapshot.doseCalculation.weightUsed ? (
                                <Chip 
                                  label={`體重: ${snapshot.doseCalculation.weightUsed} kg`} 
                                  size="small" 
                                  variant="outlined"
                                />
                              ) : (
                                <Chip 
                                  label="未提供體重" 
                                  size="small" 
                                  color="warning"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </Box>
                          {snapshot.doseCalculation.suggestedDose > 0 && (
                            <Box textAlign="right">
                              <Typography 
                                variant="h5" 
                                color={
                                  snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT') 
                                    ? 'warning.dark' 
                                    : 'primary.dark'
                                }
                              >
                                {snapshot.doseCalculation.suggestedDose} MBq
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                範圍: {snapshot.doseCalculation.minDose} - {snapshot.doseCalculation.maxDose} MBq
                              </Typography>
                            </Box>
                          )}
                        </Stack>
                        {snapshot.doseCalculation.suggestedDose > 0 && (
                          <>
                            <Divider sx={{ my: 1.5 }} />
                            <Button
                              variant="contained"
                              size="small"
                              color={snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT') ? 'warning' : 'primary'}
                              onClick={() => {
                                saveDraftMutation.mutate({ doseValue: snapshot.doseCalculation!.suggestedDose })
                              }}
                              disabled={saveDraftMutation.isPending}
                            >
                              {snapshot.ruleEval?.flags.some(f => f.code === 'MISSING_WEIGHT') 
                                ? '採用範圍最小劑量' 
                                : '採用建議劑量'}
                            </Button>
                          </>
                        )}
                      </Paper>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          )}


          {/* 快照資料 */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                臨床資料快照
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Observations</Typography>
                    <Typography variant="h4">{snapshot.snapshot.observations.length}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">過敏</Typography>
                    <Typography variant="h4">{snapshot.snapshot.allergies.length}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">條件</Typography>
                    <Typography variant="h4">{snapshot.snapshot.conditions.length}</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 右側：操作面板 */}
        <Grid item xs={12} md={4}>
          {/* NM 操作 */}
          {isNM && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  核醫操作
                </Typography>
                <Stack spacing={2}>
                  {/* RETURNED 狀態：提示使用醫師回應區塊 */}
                  {snapshot.status === 'RETURNED' ? (
                    <Alert severity="info">
                      請在左側「醫師回應」區塊填寫回應後送審
                    </Alert>
                  ) : (
                    <>
                      {/* CDS FAIL 時：需 Override 才能送審 */}
                      {snapshot.ruleEval?.overallSeverity === 'FAIL' ? (
                        <>
                          {overrideReason.trim() ? (
                            <Button
                              variant="contained"
                              color="warning"
                              startIcon={<SubmitIcon />}
                              onClick={() => {
                                saveOverrideAndSubmitMutation.mutate({
                                  doseValue: snapshot.draftDose?.value,
                                  overrideReason: overrideReason,
                                })
                              }}
                              disabled={saveOverrideAndSubmitMutation.isPending}
                              fullWidth
                            >
                              Override 並送審
                            </Button>
                          ) : (
                            <Alert severity="error">
                              CDS 評估失敗，請在左側填寫 Override 理由
                            </Alert>
                          )}
                        </>
                      ) : (
                        <Button
                          variant="contained"
                          startIcon={<SubmitIcon />}
                          onClick={() => {
                            if (overrideReason.trim()) {
                              saveOverrideAndSubmitMutation.mutate({
                                doseValue: snapshot.draftDose?.value,
                                overrideReason: overrideReason,
                              })
                            } else {
                              submitMutation.mutate()
                            }
                          }}
                          disabled={submitMutation.isPending || saveOverrideAndSubmitMutation.isPending}
                          fullWidth
                        >
                          送交藥師審查
                        </Button>
                      )}
                    </>
                  )}
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* Pharmacist 操作 */}
          {isPharmacist && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  藥師操作
                </Typography>
                <Stack spacing={2}>
                  <Button
                    variant="outlined"
                    onClick={() => claimMutation.mutate()}
                    disabled={claimMutation.isPending}
                    fullWidth
                  >
                    Claim 案件
                  </Button>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<ApproveIcon />}
                    onClick={() => approveMutation.mutate()}
                    disabled={approveMutation.isPending}
                    fullWidth
                  >
                    核准
                  </Button>
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<ReturnIcon />}
                    onClick={() => setReturnDialogOpen(true)}
                    fullWidth
                  >
                    退回
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Return Dialog */}
      <Dialog open={returnDialogOpen} onClose={() => setReturnDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>退回案件</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            請選擇退回原因
          </Typography>
          <Stack spacing={1} mb={2}>
            {(['DOSE_OUT_OF_RANGE', 'MISSING_DATA', 'MISMATCH', 'ALLERGY_CONCERN', 'OTHER'] as ReturnReasonCode[]).map((code) => (
              <FormControlLabel
                key={code}
                control={
                  <Checkbox
                    checked={returnReasons.includes(code)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setReturnReasons([...returnReasons, code])
                      } else {
                        setReturnReasons(returnReasons.filter(r => r !== code))
                      }
                    }}
                  />
                }
                label={code}
              />
            ))}
          </Stack>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="補充說明"
            value={returnComment}
            onChange={(e) => setReturnComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReturnDialogOpen(false)}>取消</Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => returnMutation.mutate()}
            disabled={returnReasons.length === 0 || returnMutation.isPending}
          >
            確認退回
          </Button>
        </DialogActions>
      </Dialog>

      {/* Respond Dialog */}
      <Dialog open={respondDialogOpen} onClose={() => setRespondDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>回應藥師退回</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
            <InputLabel>回應動作</InputLabel>
            <Select
              value={responseAction}
              label="回應動作"
              onChange={(e) => setResponseAction(e.target.value as ResponseAction)}
            >
              <MenuItem value="UPDATED_DOSE">修正劑量</MenuItem>
              <MenuItem value="ADDED_MISSING_DATA">補齊臨床資料</MenuItem>
              <MenuItem value="PROVIDED_OVERRIDE_JUSTIFICATION">提供 Override 理由</MenuItem>
              <MenuItem value="CANCELLED_ORDER">取消藥囑</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="說明"
            value={responseComment}
            onChange={(e) => setResponseComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRespondDialogOpen(false)}>取消</Button>
          <Button
            variant="contained"
            onClick={() => respondMutation.mutate()}
            disabled={respondMutation.isPending}
          >
            確認回應
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

// === AI 輔助分析元件 ===

interface AIAnalysisPanelProps {
  caseId: string
}

/** AI 輔助分析面板 */
function AIAnalysisPanel({ caseId }: AIAnalysisPanelProps) {
  const queryClient = useQueryClient()
  const { getAuthHeaders } = useAuth()
  const [expanded, setExpanded] = useState(false)
  
  // 取得 LLM 設定狀態
  const { data: llmStatus } = useQuery<LLMSettingsStatus>({
    queryKey: ['llm-settings-status', caseId],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<LLMSettingsStatus>(`/cases/${caseId}/llm-settings`)
    },
  })
  
  // 取得最近的分析結果
  const { data: analysis, isLoading: isLoadingAnalysis } = useQuery<LLMAnalysisResponse | null>({
    queryKey: ['llm-analysis', caseId],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<LLMAnalysisResponse | null>(`/cases/${caseId}/llm-analysis`)
    },
    enabled: !!llmStatus?.isConfigured,
  })
  
  // 觸發分析 mutation
  const analyzeMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post<LLMAnalysisResponse>(`/cases/${caseId}/llm-analysis`, {
        trigger_type: 'MANUAL',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-analysis', caseId] })
    },
  })
  
  // 自動分析
  useEffect(() => {
    if (llmStatus?.isConfigured && llmStatus?.autoAnalyze && !analysis && !isLoadingAnalysis) {
      analyzeMutation.mutate()
    }
  }, [llmStatus, analysis, isLoadingAnalysis])
  
  // 如果 LLM 未設定，顯示提示
  if (!llmStatus?.isConfigured) {
    return (
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <AIIcon color="disabled" />
            <Typography variant="h6" color="text.secondary">AI 輔助分析</Typography>
            <Chip label="未設定" size="small" color="default" />
          </Stack>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info">
            LLM 尚未設定。請至「系統設定」頁面配置 LLM API 以啟用 AI 輔助分析功能。
          </Alert>
        </AccordionDetails>
      </Accordion>
    )
  }
  
  const isAnalyzing = analyzeMutation.isPending || analysis?.status === 'PROCESSING'
  const hasResult = analysis?.status === 'COMPLETED' && analysis.result
  const hasFailed = analysis?.status === 'FAILED'
  
  return (
    <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)} sx={{ mb: 2 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ width: '100%' }}>
          <AIIcon color={hasResult ? 'primary' : 'action'} />
          <Typography variant="h6">AI 輔助分析</Typography>
          {isAnalyzing && <CircularProgress size={16} />}
          {hasResult && (
            <>
              <Chip 
                label={analysis.result?.examDecision?.status || 'COMPLETED'} 
                size="small" 
                color={
                  analysis.result?.examDecision?.status === 'APPROPRIATE' ? 'success' :
                  analysis.result?.examDecision?.status === 'NOT_APPROPRIATE' ? 'error' :
                  analysis.result?.examDecision?.status === 'INSUFFICIENT_DATA' ? 'warning' :
                  'info'
                }
              />
              {analysis.latencyMs && (
                <Chip 
                  icon={<SpeedIcon />}
                  label={`${(analysis.latencyMs / 1000).toFixed(1)}s`} 
                  size="small" 
                  variant="outlined"
                />
              )}
            </>
          )}
          {hasFailed && <Chip label="分析失敗" size="small" color="error" />}
          <Box sx={{ flexGrow: 1 }} />
          <Button
            size="small"
            variant={hasResult ? 'outlined' : 'contained'}
            startIcon={isAnalyzing ? <CircularProgress size={14} /> : <AnalysisIcon />}
            onClick={(e) => {
              e.stopPropagation()
              analyzeMutation.mutate()
            }}
            disabled={isAnalyzing}
          >
            {hasResult ? '重新分析' : '執行分析'}
          </Button>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        {isAnalyzing && !hasResult && (
          <Box display="flex" justifyContent="center" alignItems="center" py={4}>
            <Stack alignItems="center" spacing={2}>
              <CircularProgress />
              <Typography color="text.secondary">正在執行 AI 分析...</Typography>
            </Stack>
          </Box>
        )}
        
        {hasFailed && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight={600} gutterBottom>
              分析失敗：{analysis?.errorMessage || '未知錯誤'}
            </Typography>
            {analysis?.errorMessage?.includes('連線超時') && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" component="div" sx={{ mb: 1 }}>
                  <strong>解決方法：</strong>
                </Typography>
                <Typography variant="caption" component="div" sx={{ mb: 0.5 }}>
                  1. 前往「系統設定」頁面，增加「請求超時（秒）」設定值（建議 120-180 秒）
                </Typography>
                <Typography variant="caption" component="div" sx={{ mb: 0.5 }}>
                  2. 檢查 LLM API 服務是否正常運作
                </Typography>
                <Typography variant="caption" component="div" sx={{ mb: 0.5 }}>
                  3. 檢查網路連線是否穩定
                </Typography>
                <Typography variant="caption" component="div" sx={{ mt: 1, fontStyle: 'italic' }}>
                  詳細資訊請查看後端日誌或使用除錯腳本：<code>python debug_llm_analysis.py &lt;case_id&gt;</code>
                </Typography>
              </Box>
            )}
            {analysis?.errorMessage && !analysis?.errorMessage?.includes('連線超時') && (
              <Typography variant="caption" component="div" sx={{ mt: 1, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                詳細資訊請查看後端日誌或資料庫中的 llm_analyses 表
              </Typography>
            )}
          </Alert>
        )}
        
        {hasResult && analysis.result && (
          <Stack spacing={3}>
            {/* 病例摘要 */}
            {analysis.result.caseSummary && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                  <DiagnosisIcon color="primary" />
                  <Typography variant="subtitle1" fontWeight={600}>病例摘要</Typography>
                </Stack>
                
                {analysis.result.caseSummary.oneLiner && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2" fontWeight={600}>
                      {analysis.result.caseSummary.oneLiner}
                    </Typography>
                  </Alert>
                )}
                
                <Grid container spacing={2}>
                  {analysis.result.caseSummary.indication && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">適應症</Typography>
                      <Typography>{analysis.result.caseSummary.indication}</Typography>
                    </Grid>
                  )}
                  {analysis.result.caseSummary.keyHistory?.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">重要病史</Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                        {analysis.result.caseSummary.keyHistory.map((h, i) => (
                          <Chip key={i} label={h} size="small" variant="outlined" />
                        ))}
                      </Stack>
                    </Grid>
                  )}
                  {analysis.result.caseSummary.keyLabs?.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">關鍵檢驗</Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                        {analysis.result.caseSummary.keyLabs.map((l, i) => (
                          <Chip key={i} label={l} size="small" color="info" variant="outlined" />
                        ))}
                      </Stack>
                    </Grid>
                  )}
                  {analysis.result.caseSummary.allergies?.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">過敏</Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                        {analysis.result.caseSummary.allergies.map((a, i) => (
                          <Chip key={i} label={a} size="small" color="error" variant="outlined" />
                        ))}
                      </Stack>
                    </Grid>
                  )}
                </Grid>
              </Paper>
            )}
            
            {/* 適應症評估 */}
            {analysis.result.examDecision && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                  <ChecklistIcon color={
                    analysis.result.examDecision.status === 'APPROPRIATE' ? 'success' :
                    analysis.result.examDecision.status === 'NOT_APPROPRIATE' ? 'error' : 'warning'
                  } />
                  <Typography variant="subtitle1" fontWeight={600}>適應症評估</Typography>
                  <Chip 
                    label={
                      analysis.result.examDecision.status === 'APPROPRIATE' ? '適當' :
                      analysis.result.examDecision.status === 'POTENTIALLY_APPROPRIATE' ? '可能適當' :
                      analysis.result.examDecision.status === 'NOT_APPROPRIATE' ? '不適當' :
                      '資料不足'
                    }
                    color={
                      analysis.result.examDecision.status === 'APPROPRIATE' ? 'success' :
                      analysis.result.examDecision.status === 'NOT_APPROPRIATE' ? 'error' : 'warning'
                    }
                  />
                </Stack>
                
                {/* 理由 */}
                {analysis.result.examDecision.rationale?.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>評估理由</Typography>
                    <List dense>
                      {analysis.result.examDecision.rationale.map((r, i) => (
                        <ListItem key={i}>
                          <ListItemIcon><PassIcon color="success" fontSize="small" /></ListItemIcon>
                          <ListItemText 
                            primary={r.statement}
                            secondary={r.evidence?.map(e => e.ref).join(', ')}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
                
                {/* 缺少資料 */}
                {analysis.result.examDecision.missingData?.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>缺少資料</Typography>
                    <List dense>
                      {analysis.result.examDecision.missingData.map((m, i) => (
                        <ListItem key={i}>
                          <ListItemIcon><WarningIcon color="warning" fontSize="small" /></ListItemIcon>
                          <ListItemText 
                            primary={m.dataItem}
                            secondary={
                              <>
                                <Typography variant="caption" display="block">原因: {m.whyNeeded}</Typography>
                                <Typography variant="caption" display="block">取得方式: {m.howToObtain}</Typography>
                              </>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
                
                {/* 禁忌症訊號 */}
                {analysis.result.examDecision.contraindicationSignals?.length > 0 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>禁忌症訊號</Typography>
                    <List dense>
                      {analysis.result.examDecision.contraindicationSignals.map((c, i) => (
                        <ListItem key={i}>
                          <ListItemIcon>
                            {c.severity === 'HIGH' ? <ErrorIcon color="error" fontSize="small" /> :
                             c.severity === 'WARN' ? <WarningIcon color="warning" fontSize="small" /> :
                             <InfoIcon color="info" fontSize="small" />}
                          </ListItemIcon>
                          <ListItemText primary={c.signal} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </Paper>
            )}
            
            {/* CDSS 整合建議 */}
            {analysis.result.cdssIntegration && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                  <DoseIcon color="primary" />
                  <Typography variant="subtitle1" fontWeight={600}>CDSS 整合建議</Typography>
                  <Chip 
                    label={analysis.result.cdssIntegration.overallSeverity}
                    size="small"
                    color={
                      analysis.result.cdssIntegration.overallSeverity === 'PASS' ? 'success' :
                      analysis.result.cdssIntegration.overallSeverity === 'FAIL' ? 'error' : 'warning'
                    }
                  />
                  {analysis.result.cdssIntegration.isBatchEligible && (
                    <Chip label="可批次核准" size="small" color="success" variant="outlined" />
                  )}
                </Stack>
                
                {/* 下一步行動 */}
                {analysis.result.cdssIntegration.nextActions?.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>建議行動</Typography>
                    <List dense>
                      {analysis.result.cdssIntegration.nextActions.map((a, i) => (
                        <ListItem key={i}>
                          <ListItemIcon>
                            <Chip 
                              label={
                                a.action === 'COLLECT_DATA' ? '收集資料' :
                                a.action === 'ADJUST_PROTOCOL' ? '調整方案' :
                                a.action === 'PHARM_REVIEW' ? '藥師審查' :
                                a.action === 'CONTACT_ORDERING_MD' ? '聯繫開單醫師' :
                                '延後檢查'
                              }
                              size="small"
                              color={
                                a.action === 'DEFER_EXAM' ? 'error' :
                                a.action === 'COLLECT_DATA' ? 'warning' : 'info'
                              }
                            />
                          </ListItemIcon>
                          <ListItemText primary={a.details} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
                
                {/* Flags 說明 */}
                {analysis.result.cdssIntegration.flagsExplained?.length > 0 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>Flag 說明</Typography>
                    <List dense>
                      {analysis.result.cdssIntegration.flagsExplained.map((f, i) => (
                        <ListItem key={i}>
                          <ListItemIcon>
                            {f.severity === 'FAIL' ? <ErrorIcon color="error" fontSize="small" /> :
                             f.severity === 'WARN' ? <WarningIcon color="warning" fontSize="small" /> :
                             <InfoIcon color="info" fontSize="small" />}
                          </ListItemIcon>
                          <ListItemText 
                            primary={f.title}
                            secondary={
                              <>
                                <Typography variant="caption" display="block">{f.explain}</Typography>
                                {f.recommendation && (
                                  <Typography variant="caption" display="block" color="primary">
                                    建議: {f.recommendation}
                                  </Typography>
                                )}
                              </>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </Paper>
            )}
            
            {/* 分析品質 */}
            {analysis.result.quality && (
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Typography variant="body2" color="text.secondary">分析信心度:</Typography>
                  <Chip 
                    label={
                      analysis.result.quality.confidence === 'HIGH' ? '高' :
                      analysis.result.quality.confidence === 'MEDIUM' ? '中' : '低'
                    }
                    size="small"
                    color={
                      analysis.result.quality.confidence === 'HIGH' ? 'success' :
                      analysis.result.quality.confidence === 'MEDIUM' ? 'warning' : 'error'
                    }
                    variant="outlined"
                  />
                  {analysis.result.quality.limitations?.length > 0 && (
                    <Tooltip title={analysis.result.quality.limitations.join('; ')}>
                      <Chip 
                        label={`${analysis.result.quality.limitations.length} 項限制`}
                        size="small"
                        variant="outlined"
                      />
                    </Tooltip>
                  )}
                </Stack>
              </Paper>
            )}
            
            {/* 原始回應（如果解析失敗） */}
            {analysis.result.raw_content && analysis.result.parse_error && (
              <Alert severity="warning">
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  LLM 回應無法解析為預期格式
                </Typography>
                <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {analysis.result.raw_content.slice(0, 500)}...
                </Typography>
              </Alert>
            )}
          </Stack>
        )}
        
        {!isAnalyzing && !hasResult && !hasFailed && (
          <Box display="flex" justifyContent="center" py={4}>
            <Stack alignItems="center" spacing={2}>
              <AIIcon sx={{ fontSize: 48, color: 'action.disabled' }} />
              <Typography color="text.secondary">點擊「執行分析」開始 AI 輔助分析</Typography>
            </Stack>
          </Box>
        )}
      </AccordionDetails>
    </Accordion>
  )
}


// === 臨床資料展示元件 ===

interface ClinicalDataPanelProps {
  snapshot: PatientSnapshot
}

/** 臨床資料展示面板 */
function ClinicalDataPanel({ snapshot }: ClinicalDataPanelProps) {
  const [clinicalTab, setClinicalTab] = useState(0)
  
  const { encounters = [], conditionList = [], medications = [], procedures = [], labResults, allergyList = [] } = snapshot.snapshot
  
  // 檢查是否有任何臨床資料
  const hasEncounters = encounters.length > 0
  const hasConditions = conditionList.length > 0
  const hasMedications = medications.length > 0
  const hasProcedures = procedures.length > 0
  const hasLabResults = labResults && (
    labResults.renal.length > 0 ||
    labResults.hepatic.length > 0 ||
    labResults.thyroid.length > 0 ||
    labResults.hematology.length > 0
  )
  const hasAllergies = allergyList.length > 0
  
  const hasClinicalData = hasEncounters || hasConditions || hasMedications || hasProcedures || hasLabResults || hasAllergies
  
  // Debug: 顯示資料狀態（開發時可用）
  console.log('ClinicalDataPanel Debug:', {
    hasEncounters, hasConditions, hasMedications, hasProcedures, hasLabResults, hasAllergies,
    encounters: encounters.length, conditionList: conditionList.length,
    medications: medications.length, procedures: procedures.length,
    labResults: labResults ? {
      renal: labResults.renal.length,
      hepatic: labResults.hepatic.length,
      thyroid: labResults.thyroid.length,
      hematology: labResults.hematology.length,
      other: labResults.other.length
    } : 'null',
    allergyList: allergyList.length,
    snapshot: snapshot.snapshot
  })
  
  if (!hasClinicalData) {
    // 即使沒有資料，也顯示一個提示訊息，方便調試
    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Alert severity="info">
            目前沒有可用的臨床資料。請確認已上傳 FHIR 測試資料，且案件的 Patient ID 與上傳的資料一致。
          </Alert>
        </CardContent>
      </Card>
    )
  }
  
  // 計算檢驗結果總數
  const labResultsCount = labResults ? (
    labResults.renal.length +
    labResults.hepatic.length +
    labResults.thyroid.length +
    labResults.hematology.length
  ) : 0
  
  // 計算總項目數 (含過敏和檢驗)
  const totalClinicalCount = encounters.length + conditionList.length + medications.length + procedures.length + allergyList.length + labResultsCount
  
  return (
    <>
      {/* 臨床紀錄 (就醫、診斷、用藥、處置、過敏、檢驗) */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <HospitalIcon color="primary" />
            <Typography variant="h6">臨床紀錄</Typography>
            <Chip 
              label={totalClinicalCount} 
              size="small" 
              color="primary" 
              variant="outlined"
            />
          </Stack>
        </AccordionSummary>
        <AccordionDetails>
          <Tabs 
            value={clinicalTab} 
            onChange={(_, newValue) => setClinicalTab(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab 
              icon={<HospitalIcon fontSize="small" />} 
              iconPosition="start" 
              label={`就醫 (${encounters.length})`} 
              disabled={!hasEncounters}
            />
            <Tab 
              icon={<DiagnosisIcon fontSize="small" />} 
              iconPosition="start" 
              label={`診斷 (${conditionList.length})`}
              disabled={!hasConditions}
            />
            <Tab 
              icon={<MedicationIcon fontSize="small" />} 
              iconPosition="start" 
              label={`用藥 (${medications.length})`}
              disabled={!hasMedications}
            />
            <Tab 
              icon={<ProcedureIcon fontSize="small" />} 
              iconPosition="start" 
              label={`處置 (${procedures.length})`}
              disabled={!hasProcedures}
            />
            <Tab 
              icon={<AllergyIcon fontSize="small" />} 
              iconPosition="start" 
              label={`過敏 (${allergyList.length})`}
              disabled={!hasAllergies}
            />
            <Tab 
              icon={<LabIcon fontSize="small" />} 
              iconPosition="start" 
              label={`檢驗 (${labResultsCount})`}
              disabled={!hasLabResults}
            />
          </Tabs>
          
          {/* 就醫紀錄 */}
          {clinicalTab === 0 && (
            <EncounterList encounters={encounters} />
          )}
          
          {/* 診斷/病史 */}
          {clinicalTab === 1 && (
            <ConditionList conditions={conditionList} />
          )}
          
          {/* 用藥紀錄 */}
          {clinicalTab === 2 && (
            <MedicationList medications={medications} />
          )}
          
          {/* 處置紀錄 */}
          {clinicalTab === 3 && (
            <ProcedureList procedures={procedures} />
          )}
          
          {/* 過敏 */}
          {clinicalTab === 4 && (
            <AllergyList allergies={allergyList} />
          )}
          
          {/* 檢驗 */}
          {clinicalTab === 5 && labResults && (
            <LabResultsPanel labResults={labResults} />
          )}
        </AccordionDetails>
      </Accordion>
      
    </>
  )
}

/** 就醫紀錄列表 */
function EncounterList({ encounters }: { encounters: EncounterInfo[] }) {
  if (encounters.length === 0) {
    return <Typography color="text.secondary">無就醫紀錄</Typography>
  }
  
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>類別</TableCell>
            <TableCell>日期</TableCell>
            <TableCell>就醫原因</TableCell>
            <TableCell>地點</TableCell>
            <TableCell>狀態</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {encounters.map((enc) => (
            <TableRow key={enc.id}>
              <TableCell>
                <Chip 
                  label={enc.classDisplay || enc.classCode || '-'} 
                  size="small"
                  color={enc.classCode === 'EMER' ? 'error' : enc.classCode === 'IMP' ? 'warning' : 'default'}
                />
              </TableCell>
              <TableCell>
                {enc.periodStart ? new Date(enc.periodStart).toLocaleDateString('zh-TW') : '-'}
              </TableCell>
              <TableCell>{enc.reasonDisplay || enc.typeDisplay || '-'}</TableCell>
              <TableCell>{enc.location || '-'}</TableCell>
              <TableCell>
                <Chip label={enc.status || '-'} size="small" variant="outlined" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

/** 診斷/病史列表 */
function ConditionList({ conditions }: { conditions: ConditionInfo[] }) {
  if (conditions.length === 0) {
    return <Typography color="text.secondary">無診斷記錄</Typography>
  }
  
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>診斷碼</TableCell>
            <TableCell>診斷名稱</TableCell>
            <TableCell>狀態</TableCell>
            <TableCell>發病日期</TableCell>
            <TableCell>嚴重程度</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {conditions.map((cond) => (
            <TableRow key={cond.id}>
              <TableCell>
                <Typography variant="body2" fontFamily="monospace">
                  {cond.code || '-'}
                </Typography>
              </TableCell>
              <TableCell>{cond.display || '-'}</TableCell>
              <TableCell>
                <Chip 
                  label={cond.clinicalStatus || '-'} 
                  size="small"
                  color={cond.clinicalStatus === 'active' ? 'warning' : 'default'}
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                {cond.onsetDateTime ? new Date(cond.onsetDateTime).toLocaleDateString('zh-TW') : '-'}
              </TableCell>
              <TableCell>{cond.severity || '-'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

/** 用藥紀錄列表 */
function MedicationList({ medications }: { medications: MedicationInfo[] }) {
  if (medications.length === 0) {
    return <Typography color="text.secondary">無用藥紀錄</Typography>
  }
  
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>藥物名稱</TableCell>
            <TableCell>劑量</TableCell>
            <TableCell>給藥途徑</TableCell>
            <TableCell>狀態</TableCell>
            <TableCell>用藥原因</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {medications.map((med) => (
            <TableRow key={med.id}>
              <TableCell>
                <Typography variant="body2" fontWeight={500}>
                  {med.medicationDisplay || med.medicationCode || '-'}
                </Typography>
              </TableCell>
              <TableCell>{med.dosageText || '-'}</TableCell>
              <TableCell>{med.route || '-'}</TableCell>
              <TableCell>
                <Chip 
                  label={med.status || '-'} 
                  size="small"
                  color={med.status === 'active' ? 'success' : 'default'}
                  variant="outlined"
                />
              </TableCell>
              <TableCell>{med.reasonDisplay || '-'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

/** 處置紀錄列表 */
function ProcedureList({ procedures }: { procedures: ProcedureInfo[] }) {
  if (procedures.length === 0) {
    return <Typography color="text.secondary">無處置紀錄</Typography>
  }
  
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>處置代碼</TableCell>
            <TableCell>處置名稱</TableCell>
            <TableCell>執行日期</TableCell>
            <TableCell>部位</TableCell>
            <TableCell>結果</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {procedures.map((proc) => (
            <TableRow key={proc.id}>
              <TableCell>
                <Typography variant="body2" fontFamily="monospace">
                  {proc.code || '-'}
                </Typography>
              </TableCell>
              <TableCell>{proc.display || '-'}</TableCell>
              <TableCell>
                {proc.performedDateTime 
                  ? new Date(proc.performedDateTime).toLocaleDateString('zh-TW')
                  : proc.performedPeriodStart 
                    ? new Date(proc.performedPeriodStart).toLocaleDateString('zh-TW')
                    : '-'
                }
              </TableCell>
              <TableCell>{proc.bodySite || '-'}</TableCell>
              <TableCell>{proc.outcome || '-'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

/** 檢驗結果展示面板 */
function LabResultsPanel({ labResults }: { labResults: NonNullable<PatientSnapshot['snapshot']['labResults']> }) {
  const categories = [
    { key: 'renal', label: '腎功能', data: labResults.renal, color: '#1976d2' },
    { key: 'hepatic', label: '肝功能', data: labResults.hepatic, color: '#ed6c02' },
    { key: 'thyroid', label: '甲狀腺功能', data: labResults.thyroid, color: '#9c27b0' },
    { key: 'hematology', label: '血液檢驗', data: labResults.hematology, color: '#d32f2f' },
  ].filter(cat => cat.data.length > 0)
  
  if (categories.length === 0) {
    return <Typography color="text.secondary">無檢驗資料</Typography>
  }
  
  return (
    <Grid container spacing={2}>
      {categories.map((category) => (
        <Grid item xs={12} md={6} key={category.key}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography 
              variant="subtitle1" 
              fontWeight={600} 
              gutterBottom
              sx={{ color: category.color }}
            >
              {category.label}
            </Typography>
            <Stack spacing={1}>
              {category.data.map((lab: LabResultInfo) => (
                <LabResultRow key={lab.id} lab={lab} />
              ))}
            </Stack>
          </Paper>
        </Grid>
      ))}
    </Grid>
  )
}

/** 單一檢驗結果行 */
function LabResultRow({ lab }: { lab: LabResultInfo }) {
  const hasReferenceRange = lab.referenceRangeLow !== undefined || lab.referenceRangeHigh !== undefined
  const referenceText = hasReferenceRange
    ? `${lab.referenceRangeLow ?? '-'} - ${lab.referenceRangeHigh ?? '-'}`
    : lab.referenceRangeText || ''
  
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        p: 1,
        borderRadius: 1,
        bgcolor: lab.isAbnormal ? 'error.light' : 'grey.50',
      }}
    >
      <Box>
        <Typography variant="body2" fontWeight={500}>
          {lab.codeDisplay || lab.code}
        </Typography>
        {referenceText && (
          <Typography variant="caption" color="text.secondary">
            參考範圍: {referenceText}
          </Typography>
        )}
      </Box>
      <Box textAlign="right">
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Typography 
            variant="body1" 
            fontWeight={600}
            color={lab.isAbnormal ? 'error.main' : 'text.primary'}
          >
            {lab.value ?? lab.valueString ?? '-'}
          </Typography>
          {lab.unit && (
            <Typography variant="body2" color="text.secondary">
              {lab.unit}
            </Typography>
          )}
          {lab.interpretation && lab.interpretation !== 'N' && (
            <Chip 
              label={lab.interpretation} 
              size="small" 
              color={lab.isAbnormal ? 'error' : 'default'}
            />
          )}
        </Stack>
        {lab.effectiveDateTime && (
          <Typography variant="caption" color="text.secondary">
            {new Date(lab.effectiveDateTime).toLocaleDateString('zh-TW')}
          </Typography>
        )}
      </Box>
    </Box>
  )
}

/** 過敏史列表 */
function AllergyList({ allergies }: { allergies: AllergyInfo[] }) {
  if (allergies.length === 0) {
    return <Typography color="text.secondary">無過敏記錄 (NKDA)</Typography>
  }
  
  const getCriticalityColor = (criticality?: string) => {
    switch (criticality) {
      case 'high': return 'error'
      case 'low': return 'warning'
      default: return 'default'
    }
  }
  
  const getCriticalityLabel = (criticality?: string) => {
    switch (criticality) {
      case 'high': return '高危'
      case 'low': return '低危'
      case 'unable-to-assess': return '無法評估'
      default: return ''
    }
  }
  
  return (
    <Stack spacing={2}>
      {allergies.map((allergy) => (
        <Paper 
          key={allergy.id}
          variant="outlined"
          sx={{ 
            p: 2,
            borderColor: allergy.criticality === 'high' ? 'error.main' : 'divider',
            borderWidth: allergy.criticality === 'high' ? 2 : 1,
          }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
            <Box>
              <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                <AllergyIcon 
                  fontSize="small" 
                  color={allergy.criticality === 'high' ? 'error' : 'warning'} 
                />
                <Typography variant="subtitle1" fontWeight={600}>
                  {allergy.display || allergy.code || '未知過敏原'}
                </Typography>
                {allergy.criticality && (
                  <Chip 
                    label={getCriticalityLabel(allergy.criticality)}
                    size="small"
                    color={getCriticalityColor(allergy.criticality) as 'error' | 'warning' | 'default'}
                  />
                )}
                {allergy.category && (
                  <Chip 
                    label={allergy.category === 'medication' ? '藥物' : 
                           allergy.category === 'food' ? '食物' :
                           allergy.category === 'environment' ? '環境' : allergy.category}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Stack>
              
              {/* 反應症狀 */}
              {allergy.reactions.length > 0 && (
                <Box mt={1}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    反應症狀:
                  </Typography>
                  <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                    {allergy.reactions.map((reaction, idx) => (
                      <Box key={idx}>
                        {reaction.manifestations.map((m, mIdx) => (
                          <Chip 
                            key={mIdx}
                            label={m.display || m.code}
                            size="small"
                            color={reaction.severity === 'severe' ? 'error' : 'default'}
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    ))}
                  </Stack>
                </Box>
              )}
            </Box>
            
            <Box textAlign="right">
              <Chip 
                label={allergy.clinicalStatus || 'active'}
                size="small"
                color={allergy.clinicalStatus === 'active' ? 'error' : 'default'}
                variant="outlined"
              />
              {allergy.recordedDate && (
                <Typography variant="caption" display="block" color="text.secondary" mt={0.5}>
                  記錄於 {new Date(allergy.recordedDate).toLocaleDateString('zh-TW')}
                </Typography>
              )}
            </Box>
          </Stack>
        </Paper>
      ))}
    </Stack>
  )
}

