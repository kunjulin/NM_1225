import React, { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react'
import { apiClient } from '../api/client'

// 角色類型
export type ActingRole = 'NM_PHYSICIAN' | 'PHARMACIST' | 'ADMIN'

// 認證狀態
interface AuthState {
  subject: string
  displayName: string
  actingRole: ActingRole
  isAuthenticated: boolean
  isDemo: boolean
}

// Context 值
interface AuthContextValue extends AuthState {
  login: (subject: string, actingRole: ActingRole, displayName?: string) => Promise<void>
  logout: () => void
  setActingRole: (role: ActingRole) => void
  getAuthHeaders: () => Record<string, string>
}

// 預設狀態
const defaultState: AuthState = {
  subject: '',
  displayName: '',
  actingRole: 'NM_PHYSICIAN',
  isAuthenticated: false,
  isDemo: true, // 預設值，會從後端更新
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    // 從 localStorage 恢復狀態
    const saved = localStorage.getItem('nm_auth')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        return { ...defaultState, ...parsed, isAuthenticated: !!parsed.subject }
      } catch {
        return defaultState
      }
    }
    return defaultState
  })
  
  // 從後端取得實際的模式設定
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config = await apiClient.get<{ isDemo: boolean }>('/config')
        setState(prev => ({ ...prev, isDemo: config.isDemo }))
        
        // 如果是 Production Mode，驗證認證資訊是否有效
        if (!config.isDemo && state.isAuthenticated) {
          // 在 Production Mode 下，如果沒有有效的 SMART 認證，清除舊的認證資訊
          // 這會在第一次 API 調用時由 401 錯誤處理
        }
      } catch (err) {
        console.error('Failed to load app config:', err)
        // 保持預設值
      }
    }
    loadConfig()
  }, [])

  // 設置 401 錯誤處理
  useEffect(() => {
    apiClient.setOnUnauthorized(() => {
      // 清除認證狀態
      setState(defaultState)
      localStorage.removeItem('nm_auth')
      // 重定向到登入頁（如果不在登入頁）
      // 使用 /fhir base path
      if (window.location.pathname !== '/fhir/login' && window.location.pathname !== '/fhir/auth/callback') {
        window.location.href = '/fhir/login'
      }
    })
  }, [])

  const login = useCallback(async (subject: string, actingRole: ActingRole, displayName?: string) => {
    // 如果沒有提供 displayName，嘗試從後端獲取
    let userDisplayName = displayName || ''
    if (!userDisplayName) {
      try {
        const userInfo = await apiClient.get<{ display_name: string }>(`/auth/user-info?subject=${subject}`)
        userDisplayName = userInfo.display_name
      } catch (err) {
        // 如果獲取失敗，使用 subject 作為顯示名稱
        userDisplayName = subject
      }
    }
    
    const newState = {
      ...state,
      subject,
      displayName: userDisplayName,
      actingRole,
      isAuthenticated: true,
    }
    setState(newState)
    localStorage.setItem('nm_auth', JSON.stringify(newState))
  }, [state])

  const logout = useCallback(() => {
    setState(defaultState)
    localStorage.removeItem('nm_auth')
  }, [])

  const setActingRole = useCallback((role: ActingRole) => {
    const newState = { ...state, actingRole: role }
    setState(newState)
    localStorage.setItem('nm_auth', JSON.stringify(newState))
  }, [state])

  const getAuthHeaders = useCallback(() => {
    return {
      'X-Subject': state.subject,
      'X-Acting-Role': state.actingRole,
    }
  }, [state.subject, state.actingRole])

  const value = useMemo<AuthContextValue>(() => ({
    ...state,
    login,
    logout,
    setActingRole,
    getAuthHeaders,
  }), [state, login, logout, setActingRole, getAuthHeaders])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

