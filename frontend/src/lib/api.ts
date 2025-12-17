import axios from 'axios'
import type { AxiosError, AxiosInstance } from 'axios'
import { clearTokens, getAccessToken, getRefreshToken, setTokens, type TokenPair } from './auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const api: AxiosInstance = axios.create({
  baseURL,
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshing: Promise<TokenPair> | null = null

async function refreshTokens(): Promise<TokenPair> {
  const refresh = getRefreshToken()
  if (!refresh) throw new Error('No refresh token')
  const res = await axios.post<TokenPair>(`${baseURL}/auth/refresh`, { refresh_token: refresh })
  setTokens(res.data)
  return res.data
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const status = error.response?.status
    const original = error.config

    if (status === 401 && original && !(original as any)._retry) {
      ;(original as any)._retry = true
      try {
        refreshing = refreshing ?? refreshTokens()
        await refreshing
        refreshing = null
        return api.request(original)
      } catch (_e) {
        refreshing = null
        clearTokens()
      }
    }

    return Promise.reject(error)
  },
)

export async function login(username: string, password: string): Promise<TokenPair> {
  const res = await api.post<TokenPair>('/auth/login', { username, password })
  setTokens(res.data)
  return res.data
}
