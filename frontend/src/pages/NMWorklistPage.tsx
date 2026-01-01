import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Badge,
  IconButton,
  Tooltip,
  Button,
  Stack,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  TextField,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as PassIcon,
  Info as InfoIcon,
  Send as SendIcon,
  Sync as SyncIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { WorklistResponse, WorklistItem, Severity, BulkSubmitResponse, SyncWorklistResponse, SyncStatusResponse } from '../types'
import { severityColors, statusColors } from '../theme'

const severityIcons: Record<Severity, React.ReactNode> = {
  PASS: <PassIcon sx={{ fontSize: 18 }} />,
  INFO: <InfoIcon sx={{ fontSize: 18 }} />,
  WARN: <WarningIcon sx={{ fontSize: 18 }} />,
  FAIL: <ErrorIcon sx={{ fontSize: 18 }} />,
}

const statusLabels: Record<string, string> = {
  NM_PENDING: '待處理',
  NM_DRAFTED: '已建立草案',
  RETURNED: '藥師退回',
  PHARM_READY: '已送審',
}

export function NMWorklistPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { getAuthHeaders } = useAuth()
  const [tabValue, setTabValue] = useState(0)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' | 'warning' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  const [bulkSubmitDialogOpen, setBulkSubmitDialogOpen] = useState(false)
  const [bulkSubmitResult, setBulkSubmitResult] = useState<BulkSubmitResponse | null>(null)
  const [isSyncing, setIsSyncing] = useState(false)
  const [filterDate, setFilterDate] = useState<string>('') // 期望執行日期篩選

  // 處理日期篩選變更
  const handleFilterDateChange = (date: string) => {
    setFilterDate(date)
    // 清除選取，因為篩選後可能影響可選項目
    setSelectedIds(new Set())
  }

  const { data, isLoading, error, refetch } = useQuery<WorklistResponse>({
    queryKey: ['nm-worklist'],
    queryFn: async () => {
      try {
        apiClient.setAuthHeaders(getAuthHeaders())
        const result = await apiClient.get<WorklistResponse>('/nm/worklist')
        console.log('NM Worklist API response:', result)
        return result
      } catch (err) {
        console.error('NM Worklist API error:', err)
        throw err
      }
    },
    refetchInterval: 30000, // 30 秒自動刷新
    refetchOnMount: 'always', // 每次進入頁面都重新獲取
    staleTime: 0, // 資料立即過期，確保每次都刷新
  })

  // 同步狀態 Query
  const { data: syncStatus, refetch: refetchSyncStatus } = useQuery<SyncStatusResponse>({
    queryKey: ['sync-status'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<SyncStatusResponse>('/nm/sync-status')
    },
    refetchInterval: 10000, // 每 10 秒更新
  })

  // 手動同步 FHIR ServiceRequest
  const handleSyncFromFHIR = async () => {
    setIsSyncing(true)
    try {
      apiClient.setAuthHeaders(getAuthHeaders())
      const result = await apiClient.post<SyncWorklistResponse>('/nm/sync-worklist', {})
      // 建立同步結果訊息
      const parts: string[] = []
      if (result.fetched > 0) parts.push(`取得 ${result.fetched} 筆`)
      if (result.created > 0) parts.push(`新增 ${result.created} 筆`)
      if (result.updated > 0) parts.push(`更新 ${result.updated} 筆`)
      if (result.skipped > 0) parts.push(`略過 ${result.skipped} 筆`)
      
      const message = parts.length > 0 
        ? `同步完成：${parts.join('，')}`
        : '同步完成：無新資料'
      
      setSnackbar({
        open: true,
        message: message,
        severity: result.errors > 0 ? 'warning' : 'success',
      })
      refetch()
      refetchSyncStatus()
    } catch (err) {
      setSnackbar({
        open: true,
        message: `同步失敗：${(err as Error).message}`,
        severity: 'error',
      })
    } finally {
      setIsSyncing(false)
    }
  }

  // 批次送審 Mutation
  const bulkSubmitMutation = useMutation({
    mutationFn: async (caseIds: string[]) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post<BulkSubmitResponse>('/nm/bulk-submit', { caseIds })
    },
    onSuccess: (result) => {
      setBulkSubmitResult(result)
      setBulkSubmitDialogOpen(true)
      setSelectedIds(new Set()) // 送審後清除選取
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
    },
    onError: (error) => {
      setSnackbar({ open: true, message: `批次送審失敗: ${(error as Error).message}`, severity: 'error' })
    },
  })

  const handleRowClick = (caseId: string) => {
    navigate(`/case/${caseId}`)
  }

  const getSubmittableCaseIds = (items: WorklistItem[]): string[] => {
    // 僅送審 CDS 非 FAIL 的案件
    return items
      .filter(item => item.ruleEval.overallSeverity !== 'FAIL')
      .map(item => item.caseId)
  }

  const handleSelectAll = (items: WorklistItem[]) => {
    // 只選擇可送審的項目（非 FAIL）
    const submittableItems = items.filter(item => item.ruleEval.overallSeverity !== 'FAIL')
    if (selectedIds.size === submittableItems.length && submittableItems.length > 0) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(submittableItems.map(i => i.caseId)))
    }
  }

  const handleSelect = (caseId: string) => {
    const newSet = new Set(selectedIds)
    if (newSet.has(caseId)) {
      newSet.delete(caseId)
    } else {
      newSet.add(caseId)
    }
    setSelectedIds(newSet)
  }

  const handleBulkSubmit = () => {
    if (selectedIds.size === 0) {
      setSnackbar({ open: true, message: '請選擇要送審的案件', severity: 'info' })
      return
    }
    bulkSubmitMutation.mutate(Array.from(selectedIds))
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    setSelectedIds(new Set()) // 切換 tab 時清除選取
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-TW', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // 篩選函數：根據選擇的日期篩選項目
  const filterItemsByDate = (items: WorklistItem[]): WorklistItem[] => {
    if (!filterDate) {
      return items // 沒有選擇日期時顯示全部
    }
    
    const selectedDate = new Date(filterDate)
    selectedDate.setHours(0, 0, 0, 0) // 設定為當天的開始時間
    
    return items.filter((item) => {
      if (!item.snapshotSummary.occurrenceDateTime) {
        return false // 沒有執行日期的項目不顯示
      }
      
      const itemDate = new Date(item.snapshotSummary.occurrenceDateTime)
      itemDate.setHours(0, 0, 0, 0) // 設定為當天的開始時間
      
      return itemDate.getTime() === selectedDate.getTime()
    })
  }

  // 過濾後的群組資料
  const getFilteredGroups = () => {
    if (!data) return []
    
    return data.groups.map((group) => ({
      ...group,
      items: filterItemsByDate(group.items),
      count: filterDate ? filterItemsByDate(group.items).length : group.count,
    })).filter((group) => group.items.length > 0 || !filterDate) // 如果有篩選日期，只顯示有項目的群組
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
      <Alert severity="error">
        載入工作清單失敗：{(error as Error).message}
      </Alert>
    )
  }

  const groups = getFilteredGroups()

  // 如果沒有群組，顯示空狀態
  if (groups.length === 0) {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="h5" fontWeight={600}>
              核醫工作清單
            </Typography>
            {syncStatus && (
              <Typography variant="caption" color="text.secondary">
                上次同步: {syncStatus.lastSyncTime ? new Date(syncStatus.lastSyncTime).toLocaleString('zh-TW') : '尚未同步'}
                {syncStatus.nextSyncIn && ` | 下次同步: ${syncStatus.nextSyncIn}秒後`}
              </Typography>
            )}
          </Box>
          <Stack direction="row" spacing={1} alignItems="center">
            <TextField
              type="date"
              label="期望執行日期"
              size="small"
              value={filterDate}
              onChange={(e) => handleFilterDateChange(e.target.value)}
              InputLabelProps={{
                shrink: true,
              }}
              sx={{ width: 180 }}
            />
            <Tooltip title="從 FHIR Server 同步 ServiceRequest">
              <Button
                variant="outlined"
                size="small"
                startIcon={isSyncing ? <CircularProgress size={16} /> : <SyncIcon />}
                onClick={handleSyncFromFHIR}
                disabled={isSyncing}
              >
                {isSyncing ? '同步中...' : '同步 FHIR'}
              </Button>
            </Tooltip>
            <Tooltip title="重新整理">
              <IconButton onClick={() => refetch()}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>
        <Card>
          <CardContent>
            <Box p={4} textAlign="center">
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {filterDate 
                  ? `沒有 ${new Date(filterDate).toLocaleDateString('zh-TW')} 的待處理案件`
                  : '目前沒有待處理的案件'
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {filterDate 
                  ? '請選擇其他日期或清除篩選條件查看全部案件'
                  : '請點擊「同步 FHIR」從 FHIR Server 拉取 ServiceRequest，或使用測試資料功能建立示範資料'
                }
              </Typography>
            </Box>
          </CardContent>
        </Card>

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

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h5" fontWeight={600}>
            核醫工作清單
          </Typography>
          {syncStatus && (
            <Typography variant="caption" color="text.secondary">
              上次同步: {syncStatus.lastSyncTime ? new Date(syncStatus.lastSyncTime).toLocaleString('zh-TW') : '尚未同步'}
              {syncStatus.nextSyncIn && ` | 下次同步: ${syncStatus.nextSyncIn}秒後`}
            </Typography>
          )}
        </Box>
        <Stack direction="row" spacing={1} alignItems="center">
          <TextField
            type="date"
            label="期望執行日期"
            size="small"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
            InputLabelProps={{
              shrink: true,
            }}
            sx={{ width: 180 }}
          />
          <Tooltip title="從 FHIR Server 同步 ServiceRequest">
            <Button
              variant="outlined"
              size="small"
              startIcon={isSyncing ? <CircularProgress size={16} /> : <SyncIcon />}
              onClick={handleSyncFromFHIR}
              disabled={isSyncing}
            >
              {isSyncing ? '同步中...' : '同步 FHIR'}
            </Button>
          </Tooltip>
          <Tooltip title="重新整理">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      <Tabs
        value={tabValue}
        onChange={handleTabChange}
        sx={{ mb: 2 }}
      >
        {groups.map((group) => (
          <Tab
            key={group.groupKey}
            label={
              <Badge badgeContent={group.count} color="primary" sx={{ pr: 2 }}>
                <Typography sx={{ fontSize: '1rem' }}>{group.title}</Typography>
              </Badge>
            }
          />
        ))}
      </Tabs>

      {groups.map((group, index) => {
        const submittableIds = getSubmittableCaseIds(group.items)
        const submittableCount = submittableIds.length

        return (
          <Box
            key={group.groupKey}
            role="tabpanel"
            hidden={tabValue !== index}
          >
            {tabValue === index && (
              <Card>
                {/* 已建立草案 Tab 顯示批次送審按鈕 */}
                {group.groupKey === 'NM_DRAFTED' && (
                  <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" color="text.secondary">
                        可送審案件: {submittableCount} / {group.items.length}
                        {group.items.length - submittableCount > 0 && (
                          <Chip 
                            label={`${group.items.length - submittableCount} 件 CDS FAIL 需個別處理`}
                            size="small"
                            color="error"
                            variant="outlined"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Typography>
                      <Stack direction="row" spacing={2} alignItems="center">
                        {selectedIds.size > 0 && (
                          <Button
                            variant="contained"
                            color="primary"
                            startIcon={<SendIcon />}
                            onClick={handleBulkSubmit}
                            disabled={bulkSubmitMutation.isPending}
                          >
                            {bulkSubmitMutation.isPending ? '送審中...' : `批次送審 (${selectedIds.size})`}
                          </Button>
                        )}
                      </Stack>
                    </Stack>
                  </Box>
                )}
                <CardContent sx={{ p: 0 }}>
                  {group.items.length === 0 ? (
                    <Box p={4} textAlign="center">
                      <Typography color="text.secondary">
                        目前沒有 {group.title} 的案件
                      </Typography>
                    </Box>
                  ) : (
                    <TableContainer>
                      <Table>
                        <TableHead>
                          <TableRow>
                            {group.groupKey === 'NM_DRAFTED' && (
                              <TableCell padding="checkbox">
                                <Checkbox
                                  checked={
                                    selectedIds.size === submittableCount && 
                                    submittableCount > 0
                                  }
                                  indeterminate={
                                    selectedIds.size > 0 && 
                                    selectedIds.size < submittableCount
                                  }
                                  onChange={() => handleSelectAll(group.items)}
                                />
                              </TableCell>
                            )}
                          <TableCell>病人</TableCell>
                          <TableCell>檢查</TableCell>
                          <TableCell>期望執行時間</TableCell>
                          <TableCell>狀態</TableCell>
                          <TableCell>CDS</TableCell>
                          <TableCell>Flags</TableCell>
                          <TableCell>更新時間</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {group.items.map((item: WorklistItem) => {
                          const isSubmittable = item.ruleEval.overallSeverity !== 'FAIL'
                          const isSelected = selectedIds.has(item.caseId)
                          return (
                            <TableRow
                              key={item.caseId}
                              hover
                              onClick={() => handleRowClick(item.caseId)}
                              sx={{ cursor: 'pointer' }}
                            >
                              {group.groupKey === 'NM_DRAFTED' && (
                                <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                                  <Checkbox
                                    checked={isSelected}
                                    disabled={!isSubmittable}
                                    onChange={() => handleSelect(item.caseId)}
                                  />
                                </TableCell>
                              )}
                              <TableCell>
                                <Typography variant="body2" fontWeight={500}>
                                  {item.snapshotSummary.patientName || '未知'}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {item.snapshotSummary.patientId || item.patientRef}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                {item.snapshotSummary.examDisplay || item.snapshotSummary.examCode || '-'}
                              </TableCell>
                              <TableCell>
                                {item.snapshotSummary.occurrenceDateTime ? (
                                  <Typography variant="caption">
                                    {new Date(item.snapshotSummary.occurrenceDateTime).toLocaleString('zh-TW', {
                                      year: 'numeric',
                                      month: '2-digit',
                                      day: '2-digit',
                                      hour: '2-digit',
                                      minute: '2-digit'
                                    })}
                                  </Typography>
                                ) : (
                                  '-'
                                )}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={statusLabels[item.status] || item.status}
                                  size="small"
                                  sx={{
                                    bgcolor: statusColors[item.status as keyof typeof statusColors] || '#9E9E9E',
                                    color: '#FFF',
                                  }}
                                />
                              </TableCell>
                              <TableCell>
                                <Chip
                                  icon={severityIcons[item.ruleEval.overallSeverity] as React.ReactElement}
                                  label={item.ruleEval.overallSeverity}
                                  size="small"
                                  sx={{
                                    bgcolor: severityColors[item.ruleEval.overallSeverity],
                                    color: '#FFF',
                                    '& .MuiChip-icon': { color: '#FFF' },
                                  }}
                                />
                              </TableCell>
                              <TableCell>
                                {item.ruleEval.flags.length > 0 ? (
                                  <Chip
                                    label={item.ruleEval.flags.length}
                                    size="small"
                                    color={
                                      item.ruleEval.flags.some(f => f.severity === 'FAIL')
                                        ? 'error'
                                        : item.ruleEval.flags.some(f => f.severity === 'WARN')
                                        ? 'warning'
                                        : 'default'
                                    }
                                  />
                                ) : (
                                  '-'
                                )}
                              </TableCell>
                              <TableCell>
                                <Typography variant="caption">
                                  {formatDate(item.updatedAt)}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          )
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          )}
        </Box>
      )})}

      {/* 批次送審結果對話框 */}
      <Dialog 
        open={bulkSubmitDialogOpen} 
        onClose={() => setBulkSubmitDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>批次送審結果</DialogTitle>
        <DialogContent>
          {bulkSubmitResult && (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                成功送審 {bulkSubmitResult.ok.length} 件案件
              </Alert>
              {bulkSubmitResult.failed.length > 0 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {bulkSubmitResult.failed.length} 件案件送審失敗
                </Alert>
              )}
              {bulkSubmitResult.failed.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>失敗原因:</Typography>
                  {bulkSubmitResult.failed.map((item, i) => (
                    <Typography key={i} variant="body2" color="error">
                      • {item.caseId.slice(0, 8)}: {item.message}
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkSubmitDialogOpen(false)} variant="contained">
            確定
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

