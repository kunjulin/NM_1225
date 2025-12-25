import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
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
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as PassIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { WorklistResponse, WorklistItem, Severity } from '../types'
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
  const { getAuthHeaders } = useAuth()
  const [tabValue, setTabValue] = React.useState(0)

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
  })

  const handleRowClick = (caseId: string) => {
    navigate(`/case/${caseId}`)
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

  // 如果沒有群組，顯示空狀態
  if (groups.length === 0) {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" fontWeight={600}>
            核醫工作清單
          </Typography>
          <Tooltip title="重新整理">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Card>
          <CardContent>
            <Box p={4} textAlign="center">
              <Typography variant="h6" color="text.secondary" gutterBottom>
                目前沒有待處理的案件
              </Typography>
              <Typography variant="body2" color="text.secondary">
                請使用 Demo 功能建立示範資料
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          核醫工作清單
        </Typography>
        <Tooltip title="重新整理">
          <IconButton onClick={() => refetch()}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Tabs
        value={tabValue}
        onChange={(_, v) => setTabValue(v)}
        sx={{ mb: 2 }}
      >
        {groups.map((group, index) => (
          <Tab
            key={group.groupKey}
            label={
              <Badge badgeContent={group.count} color="primary">
                {group.title}
              </Badge>
            }
          />
        ))}
      </Tabs>

      {groups.map((group, index) => (
        <Box
          key={group.groupKey}
          role="tabpanel"
          hidden={tabValue !== index}
        >
          {tabValue === index && (
            <Card>
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
                          <TableCell>病人</TableCell>
                          <TableCell>檢查</TableCell>
                          <TableCell>狀態</TableCell>
                          <TableCell>CDS</TableCell>
                          <TableCell>Flags</TableCell>
                          <TableCell>更新時間</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {group.items.map((item: WorklistItem) => (
                          <TableRow
                            key={item.caseId}
                            hover
                            onClick={() => handleRowClick(item.caseId)}
                            sx={{ cursor: 'pointer' }}
                          >
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
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          )}
        </Box>
      ))}
    </Box>
  )
}

