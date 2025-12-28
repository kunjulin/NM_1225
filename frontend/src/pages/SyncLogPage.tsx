/**
 * FHIR 同步記錄頁面
 * 顯示 MedicationRequest 上傳到 FHIR Server 的記錄
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
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
  Paper,
  Chip,
  TextField,
  Stack,
  Button,
  CircularProgress,
  Alert,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  IconButton,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Schedule as InProgressIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { SyncLogResponse } from '../types'

const statusConfig: Record<string, { label: string; color: 'success' | 'error' | 'warning' | 'info'; icon: React.ReactNode }> = {
  DONE: { label: '成功', color: 'success', icon: <SuccessIcon fontSize="small" /> },
  FAILED: { label: '失敗', color: 'error', icon: <ErrorIcon fontSize="small" /> },
  PENDING: { label: '待處理', color: 'warning', icon: <PendingIcon fontSize="small" /> },
  IN_PROGRESS: { label: '處理中', color: 'info', icon: <InProgressIcon fontSize="small" /> },
}

export function SyncLogPage() {
  const { getAuthHeaders } = useAuth()
  const navigate = useNavigate()
  
  // 預設最近 7 天
  const today = new Date()
  const sevenDaysAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
  
  const [fromDate, setFromDate] = useState(sevenDaysAgo.toISOString().split('T')[0])
  const [toDate, setToDate] = useState(today.toISOString().split('T')[0])
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const pageSize = 20

  const { data, isLoading, error, refetch } = useQuery<SyncLogResponse>({
    queryKey: ['sync-logs', fromDate, toDate, page, statusFilter],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      const params: Record<string, string> = {
        from: fromDate,
        to: toDate,
        page: page.toString(),
        page_size: pageSize.toString(),
      }
      if (statusFilter) {
        params.status = statusFilter
      }
      return apiClient.get<SyncLogResponse>('/analytics/sync-logs', params)
    },
  })

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-TW')
    } catch {
      return dateStr
    }
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Stack direction="row" spacing={2} alignItems="center">
          <IconButton onClick={() => navigate('/analytics')}>
            <BackIcon />
          </IconButton>
          <Typography variant="h5" fontWeight={600}>
            FHIR 上傳記錄
          </Typography>
        </Stack>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            type="date"
            size="small"
            label="起始日期"
            value={fromDate}
            onChange={(e) => { setFromDate(e.target.value); setPage(1); }}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            type="date"
            size="small"
            label="結束日期"
            value={toDate}
            onChange={(e) => { setToDate(e.target.value); setPage(1); }}
            InputLabelProps={{ shrink: true }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>狀態</InputLabel>
            <Select
              value={statusFilter}
              label="狀態"
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            >
              <MenuItem value="">全部</MenuItem>
              <MenuItem value="DONE">成功</MenuItem>
              <MenuItem value="FAILED">失敗</MenuItem>
              <MenuItem value="PENDING">待處理</MenuItem>
              <MenuItem value="IN_PROGRESS">處理中</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
          >
            重新整理
          </Button>
        </Stack>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          載入失敗：{(error as Error).message}
        </Alert>
      )}

      <Card>
        <CardContent>
          {isLoading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>病患</TableCell>
                      <TableCell>操作</TableCell>
                      <TableCell>狀態</TableCell>
                      <TableCell>MedicationRequest</TableCell>
                      <TableCell>重試次數</TableCell>
                      <TableCell>建立時間</TableCell>
                      <TableCell>更新時間</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data?.logs.map((log) => {
                      const config = statusConfig[log.status] || { label: log.status, color: 'default' as const, icon: null }
                      
                      return (
                        <TableRow key={log.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight={500}>
                              {log.patient_name || '-'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {log.patient_id || log.case_id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {log.operation === 'CREATE_MEDICATION_REQUEST' ? '建立 MedicationRequest' : log.operation}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              icon={config.icon as React.ReactElement}
                              label={config.label}
                              color={config.color}
                              size="small"
                            />
                            {log.last_error && (
                              <Tooltip title={log.last_error}>
                                <Typography 
                                  variant="caption" 
                                  color="error" 
                                  display="block"
                                  sx={{ 
                                    maxWidth: 200, 
                                    overflow: 'hidden', 
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    cursor: 'help',
                                  }}
                                >
                                  {log.last_error}
                                </Typography>
                              </Tooltip>
                            )}
                          </TableCell>
                          <TableCell>
                            {log.medication_request_ref ? (
                              <Typography variant="body2" fontFamily="monospace">
                                {log.medication_request_ref}
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                -
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {log.retry_count}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDate(log.created_at)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDate(log.updated_at)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                    {(!data?.logs || data.logs.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={7} align="center">
                          <Typography color="text.secondary" py={4}>
                            沒有記錄
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {totalPages > 1 && (
                <Box display="flex" justifyContent="center" mt={3}>
                  <Pagination
                    count={totalPages}
                    page={page}
                    onChange={(_, value) => setPage(value)}
                    color="primary"
                  />
                </Box>
              )}

              <Box mt={2}>
                <Typography variant="body2" color="text.secondary">
                  共 {data?.total || 0} 筆記錄
                </Typography>
              </Box>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}




