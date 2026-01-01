import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Stack,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  Divider,
  Paper,
  IconButton,
  Tooltip,
  CircularProgress,
  Chip,
  Slider,
  InputAdornment,
  Collapse,
} from '@mui/material'
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  PlayArrow as TestIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  RestartAlt as ResetIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  SmartToy as AIIcon,
  Error as ErrorIcon,
  Link as LinkIcon,
} from '@mui/icons-material'
import Accordion from '@mui/material/Accordion'
import AccordionSummary from '@mui/material/AccordionSummary'
import AccordionDetails from '@mui/material/AccordionDetails'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import type { LLMSettings, LLMSettingsUpdate, LLMTestConnectionResponse, LLMDefaultPrompts, LLMErrorLogsResponse } from '../types'

export function SettingsPage() {
  const queryClient = useQueryClient()
  const { getAuthHeaders } = useAuth()
  
  // Form state
  const [formData, setFormData] = useState<LLMSettingsUpdate>({
    endpoint_url: '',
    model_name: 'gpt-4',
    api_key: '',
    system_prompt: '',
    user_prompt_template: '',
    auto_analyze: false,
    timeout_seconds: 60,
    max_tokens: 4096,
    temperature: 0.1,
    disable_thinking_mode: false,
  })
  
  const [showApiKey, setShowApiKey] = useState(false)
  const [showSystemPrompt, setShowSystemPrompt] = useState(false)
  const [showUserPrompt, setShowUserPrompt] = useState(false)
  const [showErrorLogs, setShowErrorLogs] = useState(false)
  const [expandedErrorId, setExpandedErrorId] = useState<string | null>(null)
  const navigate = useNavigate()
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  
  // Fetch current settings
  const { data: settings, isLoading, error } = useQuery<LLMSettings>({
    queryKey: ['llm-settings'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<LLMSettings>('/settings/llm')
    },
  })
  
  // Fetch default prompts
  const { data: defaultPrompts } = useQuery<LLMDefaultPrompts>({
    queryKey: ['llm-default-prompts'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<LLMDefaultPrompts>('/settings/llm/defaults')
    },
  })
  
  // Fetch error logs
  const { data: errorLogs, isLoading: isLoadingErrorLogs, refetch: refetchErrorLogs } = useQuery<LLMErrorLogsResponse>({
    queryKey: ['llm-error-logs'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<LLMErrorLogsResponse>('/settings/llm/error-logs?limit=50')
    },
    enabled: showErrorLogs, // 只在展開時載入
  })

  // Clear error logs mutation
  const clearErrorLogsMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.delete<{ success: boolean; message: string; deleted_count: number }>('/settings/llm/error-logs')
    },
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: data.message,
        severity: 'success',
      })
      // 清除後重新載入錯誤日誌（應該會是空的）
      queryClient.invalidateQueries({ queryKey: ['llm-error-logs'] })
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.message || '清除失敗',
        severity: 'error',
      })
    },
  })
  
  // Initialize form with current settings
  useEffect(() => {
    if (settings) {
      setFormData({
        endpoint_url: settings.endpoint_url,
        model_name: settings.model_name,
        api_key: '', // 不從後端取得 API Key
        system_prompt: settings.system_prompt,
        user_prompt_template: settings.user_prompt_template,
        auto_analyze: settings.auto_analyze,
        timeout_seconds: settings.timeout_seconds,
        max_tokens: settings.max_tokens,
        temperature: settings.temperature,
        disable_thinking_mode: settings.disable_thinking_mode,
      })
    }
  }, [settings])
  
  // Save settings mutation
  const saveMutation = useMutation({
    mutationFn: async (data: LLMSettingsUpdate) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.put<LLMSettings>('/settings/llm', data)
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: '設定已儲存', severity: 'success' })
      queryClient.invalidateQueries({ queryKey: ['llm-settings'] })
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `儲存失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })
  
  // Test connection mutation
  const testMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post<LLMTestConnectionResponse>('/settings/llm/test')
    },
    onSuccess: (data) => {
      if (data.success) {
        setSnackbar({ 
          open: true, 
          message: `連線成功！延遲: ${data.latency_ms}ms`, 
          severity: 'success' 
        })
      } else {
        setSnackbar({ 
          open: true, 
          message: `連線失敗: ${data.message}`, 
          severity: 'error' 
        })
      }
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `測試失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })
  
  // Clear API key mutation
  const clearApiKeyMutation = useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.delete('/settings/llm/api-key')
    },
    onSuccess: () => {
      setSnackbar({ open: true, message: 'API Key 已清除', severity: 'info' })
      queryClient.invalidateQueries({ queryKey: ['llm-settings'] })
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `清除失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })
  
  const handleSave = () => {
    saveMutation.mutate(formData)
  }
  
  const handleReset = () => {
    if (settings) {
      setFormData({
        endpoint_url: settings.endpoint_url,
        model_name: settings.model_name,
        api_key: '',
        system_prompt: settings.system_prompt,
        user_prompt_template: settings.user_prompt_template,
        auto_analyze: settings.auto_analyze,
        timeout_seconds: settings.timeout_seconds,
        max_tokens: settings.max_tokens,
        temperature: settings.temperature,
        disable_thinking_mode: settings.disable_thinking_mode,
      })
    }
  }
  
  const handleResetToDefaults = () => {
    if (defaultPrompts) {
      setFormData({
        ...formData,
        system_prompt: defaultPrompts.system_prompt,
        user_prompt_template: defaultPrompts.user_prompt_template,
      })
      setSnackbar({ open: true, message: '已重設為預設提示詞', severity: 'info' })
    }
  }
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    )
  }
  
  if (error) {
    return (
      <Box>
        <Alert severity="error">
          載入設定失敗：{(error as Error)?.message || '未知錯誤'}
        </Alert>
      </Box>
    )
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Stack direction="row" alignItems="center" spacing={2}>
          <AIIcon color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h5" fontWeight={600}>
            系統設定
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<ResetIcon />}
            onClick={handleReset}
            disabled={saveMutation.isPending}
          >
            重設
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={saveMutation.isPending}
          >
            儲存設定
          </Button>
        </Stack>
      </Box>
      
      {/* LLM Settings Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} mb={3}>
            <AIIcon color="primary" />
            <Typography variant="h6">LLM API 設定</Typography>
            {settings?.is_configured ? (
              <Chip label="已設定" color="success" size="small" />
            ) : (
              <Chip label="未設定" color="warning" size="small" />
            )}
          </Stack>
          
          <Stack spacing={3}>
            {/* Endpoint URL */}
            <TextField
              fullWidth
              label="API Endpoint URL"
              value={formData.endpoint_url}
              onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
              placeholder="http://localhost:11434/v1"
              helperText="OpenAI 相容 API 的 base URL（例如 Ollama: http://localhost:11434/v1）"
            />
            
            {/* Model Name */}
            <TextField
              fullWidth
              label="模型名稱"
              value={formData.model_name}
              onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
              placeholder="gpt-4"
              helperText="使用的模型名稱（例如 llama3.1, gpt-4, mistral 等）"
            />
            
            {/* API Key */}
            <TextField
              fullWidth
              label="API Key（可選）"
              type={showApiKey ? 'text' : 'password'}
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              placeholder={settings?.has_api_key ? '••••••••（已設定，留空保留原值）' : '留空表示不使用 API Key'}
              helperText={settings?.has_api_key ? '已設定 API Key，輸入新值將會覆蓋' : '部分本地 LLM 不需要 API Key'}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowApiKey(!showApiKey)} edge="end">
                      {showApiKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                    {settings?.has_api_key && (
                      <Tooltip title="清除 API Key">
                        <IconButton 
                          onClick={() => clearApiKeyMutation.mutate()} 
                          edge="end"
                          color="error"
                        >
                          <CloseIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </InputAdornment>
                ),
              }}
            />
            
            <Divider />
            
            {/* Advanced Settings */}
            <Typography variant="subtitle1" fontWeight={600}>進階設定</Typography>
            
            <Stack direction="row" spacing={3}>
              {/* Timeout */}
              <TextField
                label="請求超時（秒）"
                type="number"
                value={formData.timeout_seconds}
                onChange={(e) => setFormData({ ...formData, timeout_seconds: parseFloat(e.target.value) || 60 })}
                sx={{ width: 150 }}
                inputProps={{ min: 10, max: 300 }}
              />
              
              {/* Max Tokens */}
              <TextField
                label="最大 Tokens"
                type="number"
                value={formData.max_tokens}
                onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) || 4096 })}
                sx={{ width: 150 }}
                inputProps={{ min: 256, max: 32768 }}
              />
              
              {/* Temperature */}
              <Box sx={{ width: 200 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Temperature: {formData.temperature}
                </Typography>
                <Slider
                  value={formData.temperature}
                  onChange={(_, value) => setFormData({ ...formData, temperature: value as number })}
                  min={0}
                  max={1}
                  step={0.1}
                  marks={[
                    { value: 0, label: '0' },
                    { value: 0.5, label: '0.5' },
                    { value: 1, label: '1' },
                  ]}
                />
              </Box>
            </Stack>
            
            {/* Auto Analyze */}
            <FormControlLabel
              control={
                <Switch
                  checked={formData.auto_analyze}
                  onChange={(e) => setFormData({ ...formData, auto_analyze: e.target.checked })}
                />
              }
              label="自動分析（進入案件詳情頁時自動執行 LLM 分析）"
            />
            
            {/* Disable Thinking Mode */}
            <FormControlLabel
              control={
                <Switch
                  checked={formData.disable_thinking_mode}
                  onChange={(e) => setFormData({ ...formData, disable_thinking_mode: e.target.checked })}
                />
              }
              label={
                <Box>
                  <Typography variant="body1">
                    停用 Thinking Mode
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    對於支援 thinking mode 的模型（如 Qwen 系列），啟用此選項將禁用 thinking mode 以獲得直接輸出和更好的性能
                  </Typography>
                </Box>
              }
            />
            
            <Divider />
            
            {/* Connection Test */}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="subtitle1" fontWeight={600}>連線測試</Typography>
                  <Typography variant="body2" color="text.secondary">
                    測試與 LLM API 的連線是否正常
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  startIcon={testMutation.isPending ? <CircularProgress size={16} /> : <TestIcon />}
                  onClick={() => testMutation.mutate()}
                  disabled={testMutation.isPending || !formData.endpoint_url}
                >
                  測試連線
                </Button>
              </Stack>
            </Paper>
          </Stack>
        </CardContent>
      </Card>
      
      {/* Prompts Card */}
      <Card>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6">提示詞設定</Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={handleResetToDefaults}
            >
              重設為預設
            </Button>
          </Stack>
          
          <Stack spacing={3}>
            {/* System Prompt */}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack 
                direction="row" 
                justifyContent="space-between" 
                alignItems="center" 
                sx={{ cursor: 'pointer' }}
                onClick={() => setShowSystemPrompt(!showSystemPrompt)}
              >
                <Typography variant="subtitle1" fontWeight={600}>
                  System Prompt
                </Typography>
                <IconButton size="small">
                  {showSystemPrompt ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Stack>
              <Typography variant="body2" color="text.secondary" mb={1}>
                定義 AI 助手的角色與行為規範
              </Typography>
              <Collapse in={showSystemPrompt}>
                <TextField
                  fullWidth
                  multiline
                  rows={12}
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  sx={{ mt: 2, fontFamily: 'monospace' }}
                />
              </Collapse>
            </Paper>
            
            {/* User Prompt Template */}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack 
                direction="row" 
                justifyContent="space-between" 
                alignItems="center" 
                sx={{ cursor: 'pointer' }}
                onClick={() => setShowUserPrompt(!showUserPrompt)}
              >
                <Typography variant="subtitle1" fontWeight={600}>
                  User Prompt Template
                </Typography>
                <IconButton size="small">
                  {showUserPrompt ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Stack>
              <Typography variant="body2" color="text.secondary" mb={1}>
                使用者提示詞模板，{'{INPUT_PAYLOAD}'} 會被替換為實際的 FHIR 資料
              </Typography>
              <Collapse in={showUserPrompt}>
                <TextField
                  fullWidth
                  multiline
                  rows={16}
                  value={formData.user_prompt_template}
                  onChange={(e) => setFormData({ ...formData, user_prompt_template: e.target.value })}
                  sx={{ mt: 2, fontFamily: 'monospace' }}
                />
              </Collapse>
            </Paper>
            
            {/* Variable Reference */}
            <Alert severity="info">
              <Typography variant="body2" fontWeight={600} gutterBottom>
                可用變數說明
              </Typography>
              <Typography variant="body2">
                <code>{'{INPUT_PAYLOAD}'}</code> - 會被替換為包含以下內容的 JSON：
              </Typography>
              <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                <li><code>examType</code> - 檢查類型代碼（如 BONE_SCAN）</li>
                <li><code>serviceRequest</code> - ServiceRequest 資訊</li>
                <li><code>patientSnapshot</code> - 病人臨床資料快照</li>
                <li><code>ruleEval</code> - CDS 規則評估結果</li>
              </ul>
            </Alert>
          </Stack>
        </CardContent>
      </Card>
      
      {/* Error Logs Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Accordion expanded={showErrorLogs} onChange={() => setShowErrorLogs(!showErrorLogs)}>
            <AccordionSummary expandIcon={showErrorLogs ? <ExpandLessIcon /> : <ExpandMoreIcon />}>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ width: '100%' }}>
                <ErrorIcon color="error" />
                <Typography variant="h6">LLM 錯誤日誌</Typography>
                {errorLogs && errorLogs.total > 0 && (
                  <Chip 
                    label={`${errorLogs.total} 筆錯誤`} 
                    color="error" 
                    size="small" 
                  />
                )}
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              {isLoadingErrorLogs ? (
                <Box display="flex" justifyContent="center" py={4}>
                  <CircularProgress />
                </Box>
              ) : errorLogs && errorLogs.errors.length > 0 ? (
                <Stack spacing={2}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" color="text.secondary">
                      顯示最近 {errorLogs.total} 筆失敗的分析記錄
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Button
                        size="small"
                        startIcon={<RefreshIcon />}
                        onClick={() => refetchErrorLogs()}
                      >
                        重新整理
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<ResetIcon />}
                        onClick={() => {
                          if (window.confirm('確定要清除所有 LLM 分析記錄嗎？此操作無法復原。')) {
                            clearErrorLogsMutation.mutate()
                          }
                        }}
                        disabled={clearErrorLogsMutation.isPending}
                      >
                        重置
                      </Button>
                    </Stack>
                  </Box>
                  
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>時間</TableCell>
                          <TableCell>案件 ID</TableCell>
                          <TableCell>模型</TableCell>
                          <TableCell>錯誤訊息</TableCell>
                          <TableCell>執行時間</TableCell>
                          <TableCell>操作</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {errorLogs.errors.map((error) => (
                          <TableRow key={error.id}>
                            <TableCell>
                              {error.createdAt ? new Date(error.createdAt).toLocaleString('zh-TW') : 'N/A'}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontFamily="monospace" fontSize="0.75rem">
                                {error.caseId?.slice(0, 8) || 'N/A'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontSize="0.75rem">
                                {(error.result as Record<string, unknown>)?.model_name as string || 'N/A'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  maxWidth: 400,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                                title={error.errorMessage || ''}
                              >
                                {error.errorMessage?.split('\n')[0] || '未知錯誤'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              {error.latencyMs ? `${error.latencyMs} ms` : 'N/A'}
                            </TableCell>
                            <TableCell>
                              <Stack direction="row" spacing={1}>
                                <Tooltip title="查看詳細資訊">
                                  <IconButton
                                    size="small"
                                    onClick={() => setExpandedErrorId(
                                      expandedErrorId === error.id ? null : error.id
                                    )}
                                  >
                                    {expandedErrorId === error.id ? 
                                      <ExpandLessIcon fontSize="small" /> : 
                                      <ExpandMoreIcon fontSize="small" />
                                    }
                                  </IconButton>
                                </Tooltip>
                                {error.caseId && (
                                  <Tooltip title="前往案件詳情">
                                    <IconButton
                                      size="small"
                                      onClick={() => navigate(`/cases/${error.caseId}`)}
                                    >
                                      <LinkIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                )}
                              </Stack>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  
                  {/* 展開的錯誤詳情 */}
                  {errorLogs.errors.map((error) => (
                    expandedErrorId === error.id && (
                      <Paper key={error.id} variant="outlined" sx={{ p: 2, bgcolor: 'error.light' }}>
                        <Stack spacing={2}>
                          <Box>
                            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                              錯誤訊息
                            </Typography>
                            <Typography 
                              variant="body2" 
                              component="pre" 
                              sx={{ 
                                whiteSpace: 'pre-wrap', 
                                wordBreak: 'break-word',
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                bgcolor: 'background.paper',
                                p: 1,
                                borderRadius: 1,
                                maxHeight: 300,
                                overflow: 'auto'
                              }}
                            >
                              {error.errorMessage || '無錯誤訊息'}
                            </Typography>
                          </Box>
                          
                          <Box>
                            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                              分析資訊
                            </Typography>
                            <Stack spacing={0.5}>
                              <Typography variant="body2">
                                <strong>分析 ID:</strong> {error.id}
                              </Typography>
                              <Typography variant="body2">
                                <strong>案件 ID:</strong> {error.caseId || 'N/A'}
                              </Typography>
                              <Typography variant="body2">
                                <strong>狀態:</strong> {error.status}
                              </Typography>
                              <Typography variant="body2">
                                <strong>建立時間:</strong> {error.createdAt ? new Date(error.createdAt).toLocaleString('zh-TW') : 'N/A'}
                              </Typography>
                              {error.latencyMs && (
                                <Typography variant="body2">
                                  <strong>執行時間:</strong> {error.latencyMs} ms
                                </Typography>
                              )}
                            </Stack>
                          </Box>
                          
                          {error.caseId && (
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<LinkIcon />}
                              onClick={() => navigate(`/cases/${error.caseId}`)}
                            >
                              前往案件詳情
                            </Button>
                          )}
                        </Stack>
                      </Paper>
                    )
                  ))}
                </Stack>
              ) : (
                <Alert severity="info">
                  目前沒有錯誤記錄
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>
      
      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert 
          severity={snackbar.severity} 
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          icon={snackbar.severity === 'success' ? <CheckIcon /> : undefined}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

