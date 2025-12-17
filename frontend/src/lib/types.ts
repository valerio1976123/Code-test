export type User = { id: number; username: string; is_active: boolean }

export type Device = {
  id: number
  name: string
  host: string
  port: number
  vendor: string
  username: string
  is_enabled: boolean
  command_profile_json?: string | null
  created_at: string
  updated_at: string
}

export type Schedule = {
  id: number
  name: string
  device_id: number
  schedule_type: 'run_once' | 'daily' | 'weekly' | 'every_n_hours'
  run_once_at?: string | null
  time_of_day?: string | null
  weekdays?: string | null
  every_n_hours?: number | null
  is_enabled: boolean
  next_run_at?: string | null
  last_run_at?: string | null
  created_at: string
  updated_at: string
}

export type Execution = {
  id: number
  device_id: number
  schedule_id?: number | null
  status: 'queued' | 'running' | 'success' | 'failed'
  created_at: string
  started_at?: string | null
  finished_at?: string | null
  output_path?: string | null
  error_message?: string | null
}

export type DashboardSummary = {
  devices: { total: number; enabled: number; disabled: number }
  executions_last_24h: { total: number; failed: number; success: number }
  recent_executions: Execution[]
}
