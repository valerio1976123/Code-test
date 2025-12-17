export type Vendor =
  | "cisco_ios"
  | "cisco_nxos"
  | "paloalto_panos"
  | "fortigate"
  | "mikrotik"
  | "generic";

export type ExecutionStatus = "queued" | "running" | "success" | "failed";

export type AuthType = "password" | "key";

export type User = {
  id: number | string;
  name: string;
  email: string;
};

export type Device = {
  id: string;
  name: string;
  vendor: Vendor;
  host: string;
  port: number;
  username: string;
  auth_type: AuthType;
  private_key_path: string | null;
  is_enabled: boolean;
  command_profile_json: unknown;
  last_execution: {
    id: string;
    status: ExecutionStatus;
    start_time: string | null;
    end_time: string | null;
    created_at: string | null;
  } | null;
  next_run_at: string | null;
};

export type ScheduleType = "run_once" | "daily" | "weekly" | "every_n_hours";

export type Schedule = {
  id: string;
  device_id: string;
  type: ScheduleType;
  run_at: string | null;
  hour: number | null;
  minute: number | null;
  day_of_week: number | null;
  every_n_hours: number | null;
  is_enabled: boolean;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Execution = {
  id: string;
  device_id: string;
  schedule_id: string | null;
  status: ExecutionStatus;
  start_time: string | null;
  end_time: string | null;
  output_path: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  device?: { id: string; name: string; vendor: Vendor } | null;
};

