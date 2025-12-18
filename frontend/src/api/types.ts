export type Stock = {
  id: number
  symbol: string
  name: string
  exchange: string
  country: string
  created_at: string
}

export type Index = {
  id: number
  symbol: string
  name: string
  country: string
  created_at: string
}

export type PriceBar = {
  instrument_type: 'stock' | 'index'
  symbol: string
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type Prediction = {
  target_type: 'stock' | 'index' | 'country'
  target_identifier: string
  timestamp_generated: string
  forecast_horizon: string
  predicted_direction: 'UP' | 'DOWN' | 'FLAT'
  predicted_return: number
  model_used: string
  confidence_score: number
  extra?: Record<string, unknown> | null
}

export type Alert = {
  id: number
  user_id: number
  target_type: string
  target_identifier: string
  triggered_at: string
  severity: string
  message: string
  is_read: boolean
}

export type Overview = {
  watchlist_items: number
  bullish_predictions: number
  bearish_predictions: number
  unread_alerts: number
}

export type WatchlistItemSummary = {
  target_type: 'stock' | 'index'
  symbol: string
  name: string
  country: string
  last_price?: number | null
  daily_change_pct?: number | null
  latest_prediction?: Prediction | null
}

