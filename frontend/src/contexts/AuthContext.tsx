import React, { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react'
import { apiClient } from '../api/client'

// 角色類型
export type ActingRole = 'NM_PHYSICIAN' | 'PHARMACIST' | 'ADMIN'

// 認證狀態
interface AuthState {
  subject: string
  actingRole: ActingRole
  isAuthenticated: boolean
  isDemo: boolean
}

// Context 值
interface AuthContextValue extends AuthState {
  login: (subject: string, actingRole: ActingRole) => void
  logout: () => void
  setActingRole: (role: ActingRole) => void
  getAuthHeaders: () => Record<string, string>
}

// 預設狀態
const defaultState: AuthState = {
  subject: '',
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
      } catch (err) {
        console.error('Failed to load app config:', err)
        // 保持預設值
      }
    }
    loadConfig()
  }, [])

  const login = useCallback((subject: string, actingRole: ActingRole) => {
    const newState = {
      ...state,
      subject,
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

