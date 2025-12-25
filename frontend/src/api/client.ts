/**
 * API Client
 * 使用 Fetch API 與後端通訊
 */

const API_BASE_URL = '/api'

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: Record<string, string>
  body?: unknown
  params?: Record<string, string>
}

interface ApiError {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

export class ApiClient {
  private baseUrl: string
  private defaultHeaders: Record<string, string>

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    }
  }

  setAuthHeaders(headers: Record<string, string>) {
    this.defaultHeaders = {
      ...this.defaultHeaders,
      ...headers,
    }
  }

  private buildUrl(path: string, params?: Record<string, string>): string {
    const url = new URL(`${this.baseUrl}${path}`, window.location.origin)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value)
      })
    }
    return url.toString()
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', headers = {}, body, params } = options
    
    const url = this.buildUrl(path, params)
    
    console.log(`[API] ${method} ${url}`, { headers: this.defaultHeaders, body })
    
    const response = await fetch(url, {
      method,
      headers: {
        ...this.defaultHeaders,
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    })

    console.log(`[API] Response status: ${response.status}`, response)

    if (!response.ok) {
      let errorData: ApiError
      try {
        errorData = await response.json()
      } catch {
        const text = await response.text()
        errorData = {
          error: {
            code: 'UNKNOWN_ERROR',
            message: `HTTP ${response.status}: ${response.statusText} - ${text}`,
          },
        }
      }
      console.error('[API] Error:', errorData)
      throw new Error(errorData.error.message || 'Request failed')
    }

    const data = await response.json()
    console.log('[API] Response data:', data)
    return data
  }

  // 便捷方法
  get<T>(path: string, params?: Record<string, string>, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, { method: 'GET', params, headers })
  }

  post<T>(path: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, { method: 'POST', body, headers })
  }

  put<T>(path: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, { method: 'PUT', body, headers })
  }

  delete<T>(path: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(path, { method: 'DELETE', headers })
  }
}

// 全域 API Client 實例
export const apiClient = new ApiClient()

