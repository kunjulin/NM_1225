import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Stack,
  Divider,
  CircularProgress,
} from '@mui/material'
import {
  Science as NMIcon,
  LocalPharmacy as PharmacyIcon,
  Login as LoginIcon,
} from '@mui/icons-material'
import { useAuth, ActingRole } from '../contexts/AuthContext'
import { apiClient } from '../api/client'
import { AuthConfig, AuthResultResponse, SMARTLaunchResponse } from '../types'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { login } = useAuth()
  
  const [subject, setSubject] = useState('')
  const [actingRole, setActingRole] = useState<ActingRole>('NM_PHYSICIAN')
  const [error, setError] = useState('')
  
  // SMART 認證相關狀態
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [smartLoading, setSmartLoading] = useState(false)
  
  // 角色選擇模式（從 SMART 登入後有多個角色時使用）
  const [roleSelectMode, setRoleSelectMode] = useState(false)
  const [smartAuthResult, setSmartAuthResult] = useState<AuthResultResponse | null>(null)

  const from = (location.state as { from?: Location })?.from?.pathname || '/'

  // 載入認證設定
  useEffect(() => {
    const loadAuthConfig = async () => {
      try {
        const config = await apiClient.get<AuthConfig>('/auth/config')
        setAuthConfig(config)
      } catch (err) {
        console.error('Failed to load auth config:', err)
        // 預設為 demo mode
        setAuthConfig({ is_demo_mode: true, smart_enabled: false })
      } finally {
        setLoading(false)
      }
    }
    
    loadAuthConfig()
  }, [])

  // 檢查是否需要選擇角色（從 SMART 回呼頁面跳轉過來）
  useEffect(() => {
    const selectRole = searchParams.get('select_role')
    if (selectRole === 'true') {
      const savedResult = sessionStorage.getItem('smartAuthResult')
      if (savedResult) {
        const result = JSON.parse(savedResult) as AuthResultResponse
        setSmartAuthResult(result)
        setRoleSelectMode(true)
        sessionStorage.removeItem('smartAuthResult')
      }
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!subject.trim()) {
      setError('請輸入使用者識別碼')
      return
    }
    
    await login(subject.trim(), actingRole)
    
    // 根據角色導向對應頁面
    if (actingRole === 'ADMIN') {
      navigate('/admin/users')
    } else if (actingRole === 'NM_PHYSICIAN') {
      navigate('/nm/worklist')
    } else if (actingRole === 'PHARMACIST') {
      navigate('/pharmacy/worklist')
    } else {
      navigate(from)
    }
  }

  const handleQuickLogin = async (role: ActingRole) => {
    const demoSubject = role === 'NM_PHYSICIAN' ? 'demo-nm-physician' : 'demo-pharmacist'
    await login(demoSubject, role)
    
    if (role === 'NM_PHYSICIAN') {
      navigate('/nm/worklist')
    } else {
      navigate('/pharmacy/worklist')
    }
  }

  const handleSMARTLogin = async () => {
    setSmartLoading(true)
    setError('')
    
    try {
      const response = await apiClient.get<SMARTLaunchResponse>('/auth/smart/launch')
      
      // 儲存 state 以便驗證
      sessionStorage.setItem('smartState', response.state)
      
      // 重導向到 THAS 授權頁面
      window.location.href = response.authorization_url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'SMART 登入初始化失敗')
      setSmartLoading(false)
    }
  }

  const handleRoleSelect = async (role: ActingRole) => {
    if (!smartAuthResult?.subject) return
    
    await login(smartAuthResult.subject, role, smartAuthResult.display_name || undefined)
    
    if (role === 'PHARMACIST') {
      navigate('/pharmacy/worklist')
    } else {
      navigate('/nm/worklist')
    }
  }

  // 載入中
  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%)',
        }}
      >
        <CircularProgress sx={{ color: 'white' }} />
      </Box>
    )
  }

  // 角色選擇模式
  if (roleSelectMode && smartAuthResult) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%)',
          p: 2,
        }}
      >
        <Card sx={{ maxWidth: 450, width: '100%' }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Typography variant="h5" component="h1" gutterBottom fontWeight={700}>
                選擇操作角色
              </Typography>
              <Typography variant="body2" color="text.secondary">
                歡迎，{smartAuthResult.display_name}
              </Typography>
            </Box>

            <Stack spacing={2}>
              {smartAuthResult.allowed_roles.includes('NM_PHYSICIAN') && (
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<NMIcon />}
                  onClick={() => handleRoleSelect('NM_PHYSICIAN')}
                  sx={{ py: 2 }}
                >
                  核醫醫師
                </Button>
              )}
              {smartAuthResult.allowed_roles.includes('PHARMACIST') && (
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<PharmacyIcon />}
                  onClick={() => handleRoleSelect('PHARMACIST')}
                  sx={{ py: 2 }}
                >
                  藥師
                </Button>
              )}
              {smartAuthResult.allowed_roles.includes('ADMIN') && (
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => handleRoleSelect('ADMIN')}
                  sx={{ py: 2 }}
                >
                  系統管理員
                </Button>
              )}
            </Stack>

            <Button
              variant="text"
              fullWidth
              sx={{ mt: 3 }}
              onClick={() => {
                setRoleSelectMode(false)
                setSmartAuthResult(null)
              }}
            >
              取消
            </Button>
          </CardContent>
        </Card>
      </Box>
    )
  }

  const isDemo = authConfig?.is_demo_mode
  const smartEnabled = authConfig?.smart_enabled && !isDemo

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%)',
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 450, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
              NM Stewardship
            </Typography>
            <Typography variant="body2" color="text.secondary">
              核子醫學放射藥物用藥治理系統
            </Typography>
            {isDemo && (
              <Alert severity="info" sx={{ mt: 2 }}>
                DEMO MODE - 展示模式
              </Alert>
            )}
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* SMART on FHIR 登入（Production Mode） */}
          {smartEnabled && (
            <>
              <Button
                variant="contained"
                size="large"
                fullWidth
                startIcon={smartLoading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
                onClick={handleSMARTLogin}
                disabled={smartLoading}
                sx={{ py: 1.5, mb: 3 }}
              >
                {smartLoading ? '正在連接 THAS...' : '透過 THAS 登入'}
              </Button>
              
              <Divider sx={{ my: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  或使用 Demo 登入
                </Typography>
              </Divider>
            </>
          )}

          {/* Demo Mode 登入表單 */}
          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>
              <TextField
                fullWidth
                label="使用者識別碼"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="例如: A12345"
              />

              <FormControl fullWidth>
                <InputLabel>操作角色</InputLabel>
                <Select
                  value={actingRole}
                  label="操作角色"
                  onChange={(e) => setActingRole(e.target.value as ActingRole)}
                >
                  <MenuItem value="NM_PHYSICIAN">核醫醫師</MenuItem>
                  <MenuItem value="PHARMACIST">藥師</MenuItem>
                  <MenuItem value="ADMIN">系統管理員</MenuItem>
                </Select>
              </FormControl>

              <Button
                type="submit"
                variant={smartEnabled ? "outlined" : "contained"}
                size="large"
                fullWidth
                sx={{ py: 1.5 }}
              >
                {isDemo ? '登入' : 'Demo 登入'}
              </Button>
            </Stack>
          </form>

          {isDemo && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="body2" color="text.secondary" textAlign="center" mb={2}>
                或使用快速登入
              </Typography>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  startIcon={<NMIcon />}
                  onClick={() => handleQuickLogin('NM_PHYSICIAN')}
                  fullWidth
                >
                  核醫醫師
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<PharmacyIcon />}
                  onClick={() => handleQuickLogin('PHARMACIST')}
                  fullWidth
                >
                  藥師
                </Button>
              </Stack>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

