/**
 * 使用者管理頁面
 * 管理員專用 - 審核使用者、指派角色
 */
import { useState } from 'react'
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
  Paper,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormGroup,
  FormControlLabel,
  Checkbox,
  TextField,
  Alert,
  Stack,
  Tabs,
  Tab,
  CircularProgress,
  Tooltip,
} from '@mui/material'
import {
  Check as ApproveIcon,
  Block as BlockIcon,
  Edit as EditIcon,
  PersonAdd as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { UserListResponse, UserListItem } from '../types'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  )
}

const statusColors: Record<string, 'warning' | 'success' | 'error'> = {
  PENDING: 'warning',
  ACTIVE: 'success',
  INACTIVE: 'error',
}

const statusLabels: Record<string, string> = {
  PENDING: '待審核',
  ACTIVE: '已啟用',
  INACTIVE: '已停用',
}

const roleLabels: Record<string, string> = {
  NM_PHYSICIAN: '核醫醫師',
  PHARMACIST: '藥師',
  ADMIN: '管理員',
}

export function UserManagementPage() {
  const { getAuthHeaders } = useAuth()
  const queryClient = useQueryClient()
  
  const [tabValue, setTabValue] = useState(0)
  const [selectedUser, setSelectedUser] = useState<UserListItem | null>(null)
  const [dialogType, setDialogType] = useState<'approve' | 'edit' | 'create' | null>(null)
  const [selectedRoles, setSelectedRoles] = useState<string[]>([])
  const [newUserData, setNewUserData] = useState({ subject: '', display_name: '', email: '' })
  const [error, setError] = useState('')

  // 取得所有使用者
  const { data: allUsers, isLoading: allLoading, refetch: refetchAll } = useQuery<UserListResponse>({
    queryKey: ['admin-users-all'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<UserListResponse>('/admin/users')
    },
  })

  // 取得待審核使用者
  const { data: pendingUsers, isLoading: pendingLoading, refetch: refetchPending } = useQuery<UserListResponse>({
    queryKey: ['admin-users-pending'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<UserListResponse>('/admin/users/pending')
    },
  })

  // 審核通過 mutation
  const approveMutation = useMutation({
    mutationFn: async ({ userId, roles }: { userId: string; roles: string[] }) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/admin/users/${userId}/approve`, { allowed_roles: roles })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users-all'] })
      queryClient.invalidateQueries({ queryKey: ['admin-users-pending'] })
      handleCloseDialog()
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : '操作失敗')
    },
  })

  // 更新使用者 mutation
  const updateMutation = useMutation({
    mutationFn: async ({ userId, data }: { userId: string; data: { allowed_roles?: string[]; display_name?: string; email?: string } }) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.put(`/admin/users/${userId}`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users-all'] })
      handleCloseDialog()
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : '操作失敗')
    },
  })

  // 建立使用者 mutation
  const createMutation = useMutation({
    mutationFn: async (data: { subject: string; display_name: string; email?: string; allowed_roles: string[] }) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post('/admin/users', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users-all'] })
      handleCloseDialog()
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : '操作失敗')
    },
  })

  // 停用/啟用 mutation
  const toggleStatusMutation = useMutation({
    mutationFn: async ({ userId, activate }: { userId: string; activate: boolean }) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/admin/users/${userId}/${activate ? 'activate' : 'deactivate'}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users-all'] })
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : '操作失敗')
    },
  })

  const handleOpenApprove = (user: UserListItem) => {
    setSelectedUser(user)
    setSelectedRoles([])
    setDialogType('approve')
    setError('')
  }

  const handleOpenEdit = (user: UserListItem) => {
    setSelectedUser(user)
    setSelectedRoles(user.allowed_roles)
    setDialogType('edit')
    setError('')
  }

  const handleOpenCreate = () => {
    setNewUserData({ subject: '', display_name: '', email: '' })
    setSelectedRoles([])
    setDialogType('create')
    setError('')
  }

  const handleCloseDialog = () => {
    setDialogType(null)
    setSelectedUser(null)
    setSelectedRoles([])
    setError('')
  }

  const handleRoleToggle = (role: string) => {
    setSelectedRoles(prev => 
      prev.includes(role) 
        ? prev.filter(r => r !== role)
        : [...prev, role]
    )
  }

  const handleApprove = () => {
    if (!selectedUser || selectedRoles.length === 0) {
      setError('請至少選擇一個角色')
      return
    }
    approveMutation.mutate({ userId: selectedUser.id, roles: selectedRoles })
  }

  const handleUpdate = () => {
    if (!selectedUser) return
    updateMutation.mutate({ userId: selectedUser.id, data: { allowed_roles: selectedRoles } })
  }

  const handleCreate = () => {
    if (!newUserData.subject || !newUserData.display_name) {
      setError('請填寫必要欄位')
      return
    }
    if (selectedRoles.length === 0) {
      setError('請至少選擇一個角色')
      return
    }
    createMutation.mutate({
      subject: newUserData.subject,
      display_name: newUserData.display_name,
      email: newUserData.email || undefined,
      allowed_roles: selectedRoles,
    })
  }

  const handleRefresh = () => {
    refetchAll()
    refetchPending()
  }

  const renderUserTable = (users: UserListItem[], showActions: boolean = true) => (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>使用者</TableCell>
            <TableCell>識別碼</TableCell>
            <TableCell>狀態</TableCell>
            <TableCell>角色</TableCell>
            <TableCell>最後登入</TableCell>
            {showActions && <TableCell align="right">操作</TableCell>}
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map((user) => (
            <TableRow key={user.id}>
              <TableCell>
                <Typography variant="body2" fontWeight={500}>
                  {user.display_name}
                </Typography>
                {user.email && (
                  <Typography variant="caption" color="text.secondary">
                    {user.email}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                <Typography variant="body2" fontFamily="monospace">
                  {user.subject}
                </Typography>
                {user.practitioner_ref && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    {user.practitioner_ref}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                <Chip
                  label={statusLabels[user.status] || user.status}
                  color={statusColors[user.status] || 'default'}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                  {user.allowed_roles.map((role) => (
                    <Chip
                      key={role}
                      label={roleLabels[role] || role}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                  {user.allowed_roles.length === 0 && (
                    <Typography variant="caption" color="text.secondary">
                      未指派
                    </Typography>
                  )}
                </Stack>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {user.last_login_at 
                    ? new Date(user.last_login_at).toLocaleString('zh-TW')
                    : '-'
                  }
                </Typography>
              </TableCell>
              {showActions && (
                <TableCell align="right">
                  {user.status === 'PENDING' && (
                    <Tooltip title="審核通過">
                      <IconButton
                        color="success"
                        onClick={() => handleOpenApprove(user)}
                      >
                        <ApproveIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                  {user.status === 'ACTIVE' && (
                    <>
                      <Tooltip title="編輯角色">
                        <IconButton onClick={() => handleOpenEdit(user)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="停用">
                        <IconButton
                          color="error"
                          onClick={() => toggleStatusMutation.mutate({ userId: user.id, activate: false })}
                        >
                          <BlockIcon />
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                  {user.status === 'INACTIVE' && (
                    <Tooltip title="啟用">
                      <IconButton
                        color="success"
                        onClick={() => toggleStatusMutation.mutate({ userId: user.id, activate: true })}
                      >
                        <ApproveIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              )}
            </TableRow>
          ))}
          {users.length === 0 && (
            <TableRow>
              <TableCell colSpan={showActions ? 6 : 5} align="center">
                <Typography color="text.secondary" py={4}>
                  沒有資料
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  )

  const isLoading = allLoading || pendingLoading

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>
          使用者管理
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
          >
            重新整理
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenCreate}
          >
            新增使用者
          </Button>
        </Stack>
      </Box>

      {pendingUsers && pendingUsers.pending_count > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          有 {pendingUsers.pending_count} 位使用者等待審核
        </Alert>
      )}

      <Card>
        <CardContent>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab 
              label={
                <Stack direction="row" spacing={1} alignItems="center">
                  <span>待審核</span>
                  {pendingUsers && pendingUsers.pending_count > 0 && (
                    <Chip label={pendingUsers.pending_count} size="small" color="warning" />
                  )}
                </Stack>
              } 
            />
            <Tab label="所有使用者" />
          </Tabs>

          {isLoading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TabPanel value={tabValue} index={0}>
                {renderUserTable(pendingUsers?.users || [])}
              </TabPanel>
              <TabPanel value={tabValue} index={1}>
                {renderUserTable(allUsers?.users || [])}
              </TabPanel>
            </>
          )}
        </CardContent>
      </Card>

      {/* 審核/編輯對話框 */}
      <Dialog open={dialogType === 'approve' || dialogType === 'edit'} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'approve' ? '審核使用者' : '編輯使用者角色'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {selectedUser && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  使用者名稱
                </Typography>
                <Typography variant="body1">
                  {selectedUser.display_name}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  識別碼
                </Typography>
                <Typography variant="body1" fontFamily="monospace">
                  {selectedUser.subject}
                </Typography>
              </Box>
              
              {selectedUser.practitioner_ref && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Practitioner 參考
                  </Typography>
                  <Typography variant="body1">
                    {selectedUser.practitioner_ref}
                  </Typography>
                </Box>
              )}
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  指派角色
                </Typography>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedRoles.includes('NM_PHYSICIAN')}
                        onChange={() => handleRoleToggle('NM_PHYSICIAN')}
                      />
                    }
                    label="核醫醫師"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedRoles.includes('PHARMACIST')}
                        onChange={() => handleRoleToggle('PHARMACIST')}
                      />
                    }
                    label="藥師"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedRoles.includes('ADMIN')}
                        onChange={() => handleRoleToggle('ADMIN')}
                      />
                    }
                    label="系統管理員"
                  />
                </FormGroup>
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button
            variant="contained"
            onClick={dialogType === 'approve' ? handleApprove : handleUpdate}
            disabled={selectedRoles.length === 0}
          >
            {dialogType === 'approve' ? '審核通過' : '儲存'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 新增使用者對話框 */}
      <Dialog open={dialogType === 'create'} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>新增使用者</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="使用者識別碼"
              value={newUserData.subject}
              onChange={(e) => setNewUserData(prev => ({ ...prev, subject: e.target.value }))}
              required
              placeholder="例如: A12345"
            />
            
            <TextField
              fullWidth
              label="顯示名稱"
              value={newUserData.display_name}
              onChange={(e) => setNewUserData(prev => ({ ...prev, display_name: e.target.value }))}
              required
              placeholder="例如: 王醫師"
            />
            
            <TextField
              fullWidth
              label="電子郵件"
              type="email"
              value={newUserData.email}
              onChange={(e) => setNewUserData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="選填"
            />
            
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                指派角色
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedRoles.includes('NM_PHYSICIAN')}
                      onChange={() => handleRoleToggle('NM_PHYSICIAN')}
                    />
                  }
                  label="核醫醫師"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedRoles.includes('PHARMACIST')}
                      onChange={() => handleRoleToggle('PHARMACIST')}
                    />
                  }
                  label="藥師"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedRoles.includes('ADMIN')}
                      onChange={() => handleRoleToggle('ADMIN')}
                    />
                  }
                  label="系統管理員"
                />
              </FormGroup>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newUserData.subject || !newUserData.display_name || selectedRoles.length === 0}
          >
            建立
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}


