/**
 * SMART on FHIR 授權回呼頁面
 * 處理 THAS 授權完成後的回呼
 */
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Stack,
} from '@mui/material'
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
} from '@mui/icons-material'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { AuthResultResponse } from '../types'

export function AuthCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login } = useAuth()
  
  const [status, setStatus] = useState<'loading' | 'success' | 'pending' | 'error'>('loading')
  const [result, setResult] = useState<AuthResultResponse | null>(null)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const state = searchParams.get('state')
      const errorParam = searchParams.get('error')
      const errorDesc = searchParams.get('error_description')
      
      // EHR Launch 模式參數
      const iss = searchParams.get('iss')
      const launch = searchParams.get('launch')

      // 檢查是否有授權錯誤
      if (errorParam) {
        setStatus('error')
        setError(errorDesc || errorParam)
        return
      }

      // EHR Launch 模式：使用 iss 和 launch 參數
      if (iss && launch) {
        try {
          // 取得 EHR Launch 授權 URL
          const launchResponse = await apiClient.post<{ 
            authorization_url: string
            state: string
            token_endpoint: string
            iss: string
          }>('/auth/smart/ehr-launch-url', {
            iss,
            launch,
          })
          
          // 儲存 state 和 token_endpoint 以便後續使用
          sessionStorage.setItem('smartState', launchResponse.state)
          sessionStorage.setItem('smartTokenEndpoint', launchResponse.token_endpoint)
          sessionStorage.setItem('smartIss', launchResponse.iss)
          
          // 重導向到授權頁面
          window.location.href = launchResponse.authorization_url
          return
        } catch (err) {
          setStatus('error')
          setError(err instanceof Error ? err.message : 'EHR Launch 初始化失敗')
        }
        return
      }

      // 標準授權碼流程
      // 檢查是否有授權碼
      if (!code) {
        setStatus('error')
        setError('未收到授權碼或 Launch 參數')
        return
      }

      try {
        // 檢查是否有儲存的 token_endpoint（EHR Launch）
        const tokenEndpoint = sessionStorage.getItem('smartTokenEndpoint')
        
        // 呼叫後端處理授權回呼
        const response = await apiClient.post<AuthResultResponse>('/auth/smart/callback', {
          code,
          state: state || '',
          token_endpoint: tokenEndpoint || undefined,
        })
        
        // 清除儲存的資訊
        if (tokenEndpoint) {
          sessionStorage.removeItem('smartTokenEndpoint')
          sessionStorage.removeItem('smartIss')
        }

        setResult(response)

        if (!response.success) {
          setStatus('error')
          setError(response.error || '認證失敗')
          return
        }

        // 處理認證結果
        await handleAuthResult(response)
      } catch (err) {
        setStatus('error')
        setError(err instanceof Error ? err.message : '認證過程發生錯誤')
      }
    }

    const handleAuthResult = async (response: AuthResultResponse) => {
      // 根據使用者狀態處理
      if (response.status === 'PENDING') {
        setStatus('pending')
      } else if (response.status === 'INACTIVE') {
        setStatus('error')
        setError('您的帳號已被停用，請聯繫管理員')
      } else if (response.allowed_roles.length === 0) {
        setStatus('pending')
      } else if (response.allowed_roles.length === 1) {
        // 只有一個角色，自動登入
        const role = response.allowed_roles[0] as 'NM_PHYSICIAN' | 'PHARMACIST' | 'ADMIN'
        login(response.subject!, role)
        setStatus('success')
        
        // 延遲後跳轉
        setTimeout(() => {
          if (role === 'PHARMACIST') {
            navigate('/pharmacy/worklist')
          } else {
            navigate('/nm/worklist')
          }
        }, 1500)
      } else {
        // 多個角色，需要選擇
        // 儲存認證結果到 sessionStorage，讓登入頁面處理
        sessionStorage.setItem('smartAuthResult', JSON.stringify(response))
        navigate('/login?select_role=true')
      }
    }

    handleCallback()
  }, [searchParams, login, navigate])

  const handleReturnToLogin = () => {
    navigate('/login')
  }

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
      <Card sx={{ maxWidth: 480, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          {status === 'loading' && (
            <Stack alignItems="center" spacing={3}>
              <CircularProgress size={60} />
              <Typography variant="h6">
                正在處理授權...
              </Typography>
              <Typography color="text.secondary">
                請稍候，系統正在驗證您的身份
              </Typography>
            </Stack>
          )}

          {status === 'success' && (
            <Stack alignItems="center" spacing={3}>
              <SuccessIcon sx={{ fontSize: 60, color: 'success.main' }} />
              <Typography variant="h6">
                登入成功！
              </Typography>
              <Typography color="text.secondary">
                歡迎，{result?.display_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                正在跳轉至工作清單...
              </Typography>
            </Stack>
          )}

          {status === 'pending' && (
            <Stack alignItems="center" spacing={3}>
              <PendingIcon sx={{ fontSize: 60, color: 'warning.main' }} />
              <Typography variant="h6">
                帳號待審核
              </Typography>
              <Alert severity="info" sx={{ width: '100%' }}>
                {result?.is_new_user ? (
                  <>
                    您是首次登入系統，帳號已建立但需要管理員審核並指派角色後才能使用。
                    <br /><br />
                    請聯繫系統管理員完成審核程序。
                  </>
                ) : (
                  <>
                    您的帳號尚未被指派角色，請聯繫管理員。
                  </>
                )}
              </Alert>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  使用者：{result?.display_name}
                </Typography>
                {result?.practitioner_ref && (
                  <Typography variant="body2" color="text.secondary">
                    Practitioner: {result.practitioner_ref}
                  </Typography>
                )}
              </Box>
              <Button
                variant="outlined"
                onClick={handleReturnToLogin}
              >
                返回登入頁面
              </Button>
            </Stack>
          )}

          {status === 'error' && (
            <Stack alignItems="center" spacing={3}>
              <ErrorIcon sx={{ fontSize: 60, color: 'error.main' }} />
              <Typography variant="h6">
                登入失敗
              </Typography>
              <Alert severity="error" sx={{ width: '100%' }}>
                {error}
              </Alert>
              <Button
                variant="contained"
                onClick={handleReturnToLogin}
              >
                返回登入頁面
              </Button>
            </Stack>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}


