import React, { useState } from 'react'
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
  AutoAwesome as AutofillIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import {
  PatientSnapshot,
  WorklistItem,
  CandidateFact,
  ReturnReasonCode,
  ResponseAction,
} from '../types'
import { severityColors, statusColors } from '../theme'

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { getAuthHeaders, actingRole, subject } = useAuth()
  
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

  // 取得案件快照
  const { data: snapshot, isLoading, error, refetch } = useQuery<PatientSnapshot>({
    queryKey: ['case-snapshot', caseId],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<PatientSnapshot>(`/cases/${caseId}/snapshot`)
    },
    enabled: !!caseId,
  })

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
      setSnackbar({ open: true, message: '回應成功', severity: 'success' })
      queryClient.invalidateQueries({ queryKey: ['case-snapshot', caseId] })
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `回應失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })

  // Accept Autofill
  const acceptAutofillMutation = useMutation({
    mutationFn: async (facts: CandidateFact[]) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/cases/${caseId}/autofill/accept`, {
        caseId,
        facts: facts.map(f => ({
          factType: f.factType,
          value: f.value,
          unit: f.unit,
          asOf: f.asOf,
          sourceType: f.sourceType,
          sourceRef: f.sourceRef,
          confidence: f.confidence,
          extractionMethod: f.extractionMethod,
        })),
      })
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: '自動填入已接受', severity: 'success' })
      queryClient.invalidateQueries({ queryKey: ['case-snapshot', caseId] })
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `自動填入失敗: ${(error as Error).message}`, severity: 'error' })
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
        <Button startIcon={<BackIcon />} onClick={() => navigate(-1)} sx={{ mb: 2 }}>
          返回
        </Button>
        <Alert severity="error">
          載入案件失敗：{(error as Error)?.message || '案件不存在'}
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
          <Tooltip title="重新整理">
            <IconButton onClick={() => refetch()}>
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
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">病人參考</Typography>
                  <Typography>{snapshot.patientRef}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">ServiceRequest</Typography>
                  <Typography>{snapshot.serviceRequestRef}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Candidate Facts (Autofill) */}
          {snapshot.candidateFacts.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <AutofillIcon color="secondary" />
                    <Typography variant="h6">自動填入候選值</Typography>
                  </Stack>
                  <Button
                    variant="contained"
                    color="secondary"
                    size="small"
                    onClick={() => acceptAutofillMutation.mutate(snapshot.candidateFacts)}
                    disabled={acceptAutofillMutation.isPending}
                  >
                    全部接受
                  </Button>
                </Box>
                <List dense>
                  {snapshot.candidateFacts.map((fact, i) => (
                    <ListItem key={i}>
                      <ListItemIcon>
                        <Chip
                          label={fact.confidence}
                          size="small"
                          color={
                            fact.confidence === 'HIGH'
                              ? 'success'
                              : fact.confidence === 'MEDIUM'
                              ? 'warning'
                              : 'default'
                          }
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={`${fact.factType}: ${fact.value} ${fact.unit || ''}`}
                        secondary={`來源: ${fact.sourceType} | ${new Date(fact.asOf).toLocaleDateString()}`}
                      />
                    </ListItem>
                  ))}
                </List>
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
                  <Button
                    variant="contained"
                    startIcon={<SubmitIcon />}
                    onClick={() => submitMutation.mutate()}
                    disabled={submitMutation.isPending}
                    fullWidth
                  >
                    送交藥師審查
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<EditIcon />}
                    onClick={() => setRespondDialogOpen(true)}
                    fullWidth
                  >
                    回應退回
                  </Button>
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

