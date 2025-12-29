import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
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
  Button,
  Checkbox,
  IconButton,
  Tooltip,
  Snackbar,
  Stack,
  Badge,
  Tabs,
  Tab,
  Paper,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  CheckCircle as ApproveIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { WorklistResponse, WorklistItem, BulkApproveResponse } from '../types'
import { severityColors } from '../theme'

export function PharmacyWorklistPage() {
  const navigate = useNavigate()
  const { getAuthHeaders } = useAuth()
  const queryClient = useQueryClient()
  
  const [tabValue, setTabValue] = useState(0)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const { data, isLoading, error, refetch } = useQuery<WorklistResponse>({
    queryKey: ['pharmacy-worklist'],
    queryFn: async () => {
      try {
        apiClient.setAuthHeaders(getAuthHeaders())
        const result = await apiClient.get<WorklistResponse>('/pharmacy/worklist')
        console.log('Pharmacy Worklist API response:', result)
        return result
      } catch (err) {
        console.error('Pharmacy Worklist API error:', err)
        throw err
      }
    },
    refetchInterval: 30000,
    refetchOnMount: 'always',
    staleTime: 0,
  })

  const bulkApproveMutation = useMutation({
    mutationFn: async (caseIds: string[]) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post<BulkApproveResponse>('/pharmacy/bulk-approve', { caseIds })
    },
    onSuccess: (result) => {
      const okCount = result.ok.length
      const failedCount = result.failed.length
      
      setSnackbar({
        open: true,
        message: `批次核准完成：${okCount} 成功，${failedCount} 失敗`,
        severity: failedCount > 0 ? 'error' : 'success',
      })
      
      setSelectedIds(new Set())
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
    },
    onError: (error) => {
      setSnackbar({
        open: true,
        message: `批次核准失敗：${(error as Error).message}`,
        severity: 'error',
      })
    },
  })

  const handleRowClick = (caseId: string) => {
    navigate(`/case/${caseId}`)
  }

  const handleSelectAll = (items: WorklistItem[]) => {
    if (selectedIds.size === items.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(items.map(i => i.caseId)))
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

  const handleBulkApprove = () => {
    if (selectedIds.size === 0) return
    bulkApproveMutation.mutate(Array.from(selectedIds))
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    setSelectedIds(new Set()) // 切換 tab 時清除選取
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

  const groups = data?.groups || []
  const physicianResponseGroup = groups.find(g => g.groupKey === 'physicianResponse')
  const batchEligibleGroup = groups.find(g => g.groupKey === 'batchEligible')
  const exceptionsGroup = groups.find(g => g.groupKey === 'exceptions')
  const approvedGroup = groups.find(g => g.groupKey === 'approved')

  // Tab 數據：醫師回覆、可批次核准、需逐筆審查、已批准
  const tabData = [
    {
      label: '醫師回覆',
      count: physicianResponseGroup?.count || 0,
      items: physicianResponseGroup?.items || [],
      showCheckbox: false,
      badgeColor: 'warning' as const,
    },
    {
      label: '可批次核准',
      count: batchEligibleGroup?.count || 0,
      items: batchEligibleGroup?.items || [],
      showCheckbox: true,
      badgeColor: 'success' as const,
    },
    {
      label: '需逐筆審查',
      count: exceptionsGroup?.count || 0,
      items: exceptionsGroup?.items || [],
      showCheckbox: false,
      badgeColor: 'error' as const,
    },
    {
      label: '已批准',
      count: approvedGroup?.count || 0,
      items: approvedGroup?.items || [],
      showCheckbox: false,
      badgeColor: 'primary' as const,
    },
  ]

  const currentTab = tabData[tabValue]

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          藥師工作清單
        </Typography>
        <Stack direction="row" spacing={2}>
          {selectedIds.size > 0 && tabValue === 0 && (
            <Button
              variant="contained"
              color="success"
              startIcon={<ApproveIcon />}
              onClick={handleBulkApprove}
              disabled={bulkApproveMutation.isPending}
            >
              批次核准 ({selectedIds.size})
            </Button>
          )}
          <Tooltip title="重新整理">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {/* Tabs */}
      <Tabs
        value={tabValue}
        onChange={handleTabChange}
        sx={{ mb: 2 }}
      >
        {tabData.map((tab, index) => (
          <Tab
            key={index}
            label={
              <Badge badgeContent={tab.count} color={tab.badgeColor} max={99}>
                <Typography sx={{ pr: tab.count > 0 ? 2 : 0 }}>{tab.label}</Typography>
              </Badge>
            }
          />
        ))}
      </Tabs>

      {/* 內容區 */}
      <Paper variant="outlined">
        {currentTab.items.length === 0 ? (
          <Box p={4} textAlign="center">
            <Typography color="text.secondary">目前沒有案件</Typography>
          </Box>
        ) : (
          <WorklistTable
            items={currentTab.items}
            selectedIds={selectedIds}
            onSelect={handleSelect}
            onSelectAll={() => handleSelectAll(currentTab.items)}
            onRowClick={handleRowClick}
            showCheckbox={currentTab.showCheckbox}
            showApprovedDate={tabValue === 2}
          />
        )}
      </Paper>

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

interface WorklistTableProps {
  items: WorklistItem[]
  selectedIds: Set<string>
  onSelect?: (id: string) => void
  onSelectAll?: () => void
  onRowClick: (id: string) => void
  showCheckbox?: boolean
  showApprovedDate?: boolean
}

function WorklistTable({ 
  items, 
  selectedIds, 
  onSelect, 
  onSelectAll, 
  onRowClick, 
  showCheckbox,
  showApprovedDate = false,
}: WorklistTableProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-TW', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            {showCheckbox && (
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selectedIds.size === items.length && items.length > 0}
                  indeterminate={selectedIds.size > 0 && selectedIds.size < items.length}
                  onChange={onSelectAll}
                />
              </TableCell>
            )}
            <TableCell>病人</TableCell>
            <TableCell>檢查</TableCell>
            <TableCell>期望執行時間</TableCell>
            <TableCell>CDS</TableCell>
            <TableCell>Flags</TableCell>
            <TableCell>{showApprovedDate ? '批准時間' : '更新時間'}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item) => (
            <TableRow
              key={item.caseId}
              hover
              onClick={() => onRowClick(item.caseId)}
              sx={{ cursor: 'pointer' }}
            >
              {showCheckbox && (
                <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selectedIds.has(item.caseId)}
                    onChange={() => onSelect?.(item.caseId)}
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
                  label={item.ruleEval.overallSeverity}
                  size="small"
                  sx={{
                    bgcolor: severityColors[item.ruleEval.overallSeverity],
                    color: '#FFF',
                  }}
                />
              </TableCell>
              <TableCell>
                {item.ruleEval.flags.length > 0 ? (
                  <Stack direction="row" spacing={0.5}>
                    {item.ruleEval.flags.slice(0, 3).map((flag, i) => (
                      <Tooltip key={i} title={flag.title}>
                        {flag.severity === 'FAIL' ? (
                          <ErrorIcon color="error" sx={{ fontSize: 18 }} />
                        ) : (
                          <WarningIcon color="warning" sx={{ fontSize: 18 }} />
                        )}
                      </Tooltip>
                    ))}
                    {item.ruleEval.flags.length > 3 && (
                      <Typography variant="caption">+{item.ruleEval.flags.length - 3}</Typography>
                    )}
                  </Stack>
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
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
