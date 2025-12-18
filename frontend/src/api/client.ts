import type { Alert, Index, Overview, Prediction, PriceBar, Stock, WatchlistItemSummary } from './types'

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText} ${txt}`.trim())
  }
  return (await res.json()) as T
}

export const marketApi = {
  overview: () => api<Overview>('/api/overview'),
  watchlistSummary: () => api<WatchlistItemSummary[]>('/api/watchlist/summary'),
  stocks: () => api<Stock[]>('/api/stocks'),
  indexes: () => api<Index[]>('/api/indexes'),
  prices: (symbol: string, instrumentType: 'stock' | 'index', days = 180) =>
    api<PriceBar[]>(`/api/prices/${encodeURIComponent(symbol)}?instrument_type=${instrumentType}&days=${days}`),
  predictions: (symbol: string, targetType: 'stock' | 'index', limit = 50) =>
    api<Prediction[]>(`/api/predictions/${encodeURIComponent(symbol)}?target_type=${targetType}&limit=${limit}`),
  alerts: (isRead?: boolean) =>
    api<Alert[]>(`/api/alerts${typeof isRead === 'boolean' ? `?is_read=${isRead}` : ''}`),
  markAlertRead: (id: number, isRead: boolean) =>
    api<Alert>(`/api/alerts/${id}`, { method: 'PATCH', body: JSON.stringify({ is_read: isRead }) }),
  refreshData: () => api<{ prices_inserted: number; macro_inserted: number }>('/api/admin/refresh-data', { method: 'POST' }),
  retrain: () => api<{ predictions_created: number; timestamp: number }>('/api/admin/retrain', { method: 'POST' }),
}

