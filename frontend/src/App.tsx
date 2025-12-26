import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { LoginPage } from './pages/LoginPage'
import { NMWorklistPage } from './pages/NMWorklistPage'
import { PharmacyWorklistPage } from './pages/PharmacyWorklistPage'
import { CaseDetailPage } from './pages/CaseDetailPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { UserManagementPage } from './pages/UserManagementPage'
import { SyncLogPage } from './pages/SyncLogPage'
import { useAuth } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      {/* 登入頁面 */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* SMART on FHIR 授權回呼 */}
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      
      {/* 受保護的路由 */}
      <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
        {/* 核醫工作清單 */}
        <Route path="/nm/worklist" element={<NMWorklistPage />} />
        
        {/* 藥師工作清單 */}
        <Route path="/pharmacy/worklist" element={<PharmacyWorklistPage />} />
        
        {/* 案件詳情 */}
        <Route path="/case/:caseId" element={<CaseDetailPage />} />
        
        {/* 分析儀表板 */}
        <Route path="/analytics" element={<AnalyticsPage />} />
        
        {/* FHIR 同步記錄 */}
        <Route path="/analytics/sync-logs" element={<SyncLogPage />} />
        
        {/* 使用者管理（管理員專用） */}
        <Route path="/admin/users" element={<UserManagementPage />} />
        
        {/* 預設路由 */}
        <Route path="/" element={
          isAuthenticated ? <Navigate to="/nm/worklist" replace /> : <Navigate to="/login" replace />
        } />
      </Route>
      
      {/* 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App


