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
  Button,
  Checkbox,
  IconButton,
  Tooltip,
  Snackbar,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as ApproveIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { WorklistResponse, WorklistItem, BulkApproveResponse } from '../types'
import { severityColors, statusColors } from '../theme'

export function PharmacyWorklistPage() {
  const navigate = useNavigate()
  const { getAuthHeaders, subject } = useAuth()
  const queryClient = useQueryClient()
  
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

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-TW', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
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
  const batchEligibleGroup = groups.find(g => g.groupKey === 'batchEligible')
  const exceptionsGroup = groups.find(g => g.groupKey === 'exceptions')
  const myClaimedGroup = groups.find(g => g.groupKey === 'myClaimed')

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          藥師工作清單
        </Typography>
        <Stack direction="row" spacing={2}>
          {selectedIds.size > 0 && (
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

      {/* 可批次核准 */}
      {batchEligibleGroup && (
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Badge badgeContent={batchEligibleGroup.count} color="success">
              <Typography fontWeight={600}>{batchEligibleGroup.title}</Typography>
            </Badge>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 0 }}>
            <WorklistTable
              items={batchEligibleGroup.items}
              selectedIds={selectedIds}
              onSelect={handleSelect}
              onSelectAll={() => handleSelectAll(batchEligibleGroup.items)}
              onRowClick={handleRowClick}
              showCheckbox
            />
          </AccordionDetails>
        </Accordion>
      )}

      {/* 需逐筆審查 */}
      {exceptionsGroup && (
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Badge badgeContent={exceptionsGroup.count} color="error">
              <Typography fontWeight={600}>{exceptionsGroup.title}</Typography>
            </Badge>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 0 }}>
            <WorklistTable
              items={exceptionsGroup.items}
              selectedIds={new Set()}
              onRowClick={handleRowClick}
            />
          </AccordionDetails>
        </Accordion>
      )}

      {/* 我已 Claim */}
      {myClaimedGroup && myClaimedGroup.count > 0 && (
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Badge badgeContent={myClaimedGroup.count} color="primary">
              <Typography fontWeight={600}>{myClaimedGroup.title}</Typography>
            </Badge>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 0 }}>
            <WorklistTable
              items={myClaimedGroup.items}
              selectedIds={new Set()}
              onRowClick={handleRowClick}
            />
          </AccordionDetails>
        </Accordion>
      )}

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
}

function WorklistTable({ items, selectedIds, onSelect, onSelectAll, onRowClick, showCheckbox }: WorklistTableProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-TW', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (items.length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Typography color="text.secondary">目前沒有案件</Typography>
      </Box>
    )
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
            <TableCell>CDS</TableCell>
            <TableCell>Flags</TableCell>
            <TableCell>更新時間</TableCell>
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
                        ) : flag.severity === 'WARN' ? (
                          <WarningIcon color="warning" sx={{ fontSize: 18 }} />
                        ) : null}
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

