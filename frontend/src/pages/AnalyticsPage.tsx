import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  TextField,
  Stack,
  Button,
  Paper,
} from '@mui/material'
import {
  Download as DownloadIcon,
  DateRange as DateIcon,
} from '@mui/icons-material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { AnalyticsSummary, AutofillSummary } from '../types'

const COLORS = ['#0D47A1', '#00ACC1', '#ED6C02', '#D32F2F', '#2E7D32']

export function AnalyticsPage() {
  const { getAuthHeaders } = useAuth()
  
  // 預設最近 30 天
  const today = new Date()
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
  
  const [fromDate, setFromDate] = useState(thirtyDaysAgo.toISOString().split('T')[0])
  const [toDate, setToDate] = useState(today.toISOString().split('T')[0])

  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery<AnalyticsSummary>({
    queryKey: ['analytics-summary', fromDate, toDate],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<AnalyticsSummary>('/analytics/summary', {
        from: fromDate,
        to: toDate,
      })
    },
  })

  const { data: autofillSummary, isLoading: autofillLoading } = useQuery<AutofillSummary>({
    queryKey: ['analytics-autofill', fromDate, toDate],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<AutofillSummary>('/analytics/autofill/summary', {
        from: fromDate,
        to: toDate,
      })
    },
  })

  const isLoading = summaryLoading || autofillLoading

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    )
  }

  if (summaryError) {
    return (
      <Alert severity="error">
        載入分析資料失敗：{(summaryError as Error).message}
      </Alert>
    )
  }

  // 退回原因圖表資料
  const returnReasonsData = summary?.returnReasons.map(r => ({
    name: r.code,
    value: r.count,
  })) || []

  // 回應動作圖表資料
  const responseActionsData = summary?.responseActions.map(r => ({
    name: r.action,
    value: r.count,
  })) || []

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          分析儀表板
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            type="date"
            size="small"
            label="起始日期"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            type="date"
            size="small"
            label="結束日期"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <Button variant="outlined" startIcon={<DownloadIcon />}>
            匯出 CSV
          </Button>
        </Stack>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                總案件數
              </Typography>
              <Typography variant="h3" fontWeight={700}>
                {summary?.totalCases || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                藥師介入率
              </Typography>
              <Typography variant="h3" fontWeight={700}>
                {((summary?.pharmacistInterventionRate || 0) * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                批次核准率
              </Typography>
              <Typography variant="h3" fontWeight={700}>
                {((summary?.batchApprovalRate || 0) * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Auto-fill 接受率
              </Typography>
              <Typography variant="h3" fontWeight={700}>
                {((autofillSummary?.acceptRate || 0) * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* 退回原因分佈 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                退回原因分佈
              </Typography>
              {returnReasonsData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={returnReasonsData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={100}
                      dataKey="value"
                    >
                      {returnReasonsData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Box textAlign="center" py={4}>
                  <Typography color="text.secondary">無資料</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 回應動作分佈 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                醫師回應動作分佈
              </Typography>
              {responseActionsData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={responseActionsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#0D47A1" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box textAlign="center" py={4}>
                  <Typography color="text.secondary">無資料</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Auto-fill 統計 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Auto-fill 統計
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={4}>
                  <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">產生候選值</Typography>
                    <Typography variant="h4">{autofillSummary?.candidatesGenerated || 0}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">已接受</Typography>
                    <Typography variant="h4" color="success.main">
                      {autofillSummary?.candidatesAccepted || 0}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={4}>
                  <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">已拒絕</Typography>
                    <Typography variant="h4" color="error.main">
                      {autofillSummary?.candidatesRejected || 0}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

