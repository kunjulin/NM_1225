/**
 * API Hooks
 * 封裝常用 API 呼叫
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import {
  WorklistResponse,
  PatientSnapshot,
  AnalyticsSummary,
  AutofillSummary,
  BulkApproveResponse,
} from '../types'

// NM Worklist
export function useNMWorklist() {
  const { getAuthHeaders } = useAuth()
  
  return useQuery<WorklistResponse>({
    queryKey: ['nm-worklist'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<WorklistResponse>('/nm/worklist')
    },
  })
}

// Pharmacy Worklist
export function usePharmacyWorklist() {
  const { getAuthHeaders } = useAuth()
  
  return useQuery<WorklistResponse>({
    queryKey: ['pharmacy-worklist'],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<WorklistResponse>('/pharmacy/worklist')
    },
  })
}

// Case Snapshot
export function useCaseSnapshot(caseId: string | undefined) {
  const { getAuthHeaders } = useAuth()
  
  return useQuery<PatientSnapshot>({
    queryKey: ['case-snapshot', caseId],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<PatientSnapshot>(`/cases/${caseId}/snapshot`)
    },
    enabled: !!caseId,
  })
}

// Analytics Summary
export function useAnalyticsSummary(fromDate: string, toDate: string) {
  const { getAuthHeaders } = useAuth()
  
  return useQuery<AnalyticsSummary>({
    queryKey: ['analytics-summary', fromDate, toDate],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<AnalyticsSummary>('/analytics/summary', {
        from: fromDate,
        to: toDate,
      })
    },
  })
}

// Autofill Summary
export function useAutofillSummary(fromDate: string, toDate: string) {
  const { getAuthHeaders } = useAuth()
  
  return useQuery<AutofillSummary>({
    queryKey: ['analytics-autofill', fromDate, toDate],
    queryFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.get<AutofillSummary>('/analytics/autofill/summary', {
        from: fromDate,
        to: toDate,
      })
    },
  })
}

// Bulk Approve Mutation
export function useBulkApprove() {
  const { getAuthHeaders } = useAuth()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (caseIds: string[]) => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post<BulkApproveResponse>('/pharmacy/bulk-approve', { caseIds })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
    },
  })
}

// Claim Case
export function useClaimCase(caseId: string) {
  const { getAuthHeaders } = useAuth()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/pharmacy/cases/${caseId}/claim`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-snapshot', caseId] })
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
    },
  })
}

// Approve Case
export function useApproveCase(caseId: string) {
  const { getAuthHeaders } = useAuth()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/pharmacy/cases/${caseId}/approve`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
    },
  })
}

// Submit to Pharmacy
export function useSubmitToPharmacy(caseId: string) {
  const { getAuthHeaders } = useAuth()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post(`/nm/cases/${caseId}/submit`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
    },
  })
}

// Seed Demo Data
export function useSeedDemo() {
  const { getAuthHeaders } = useAuth()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      apiClient.setAuthHeaders(getAuthHeaders())
      return apiClient.post('/demo/seed')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nm-worklist'] })
      queryClient.invalidateQueries({ queryKey: ['pharmacy-worklist'] })
    },
  })
}






