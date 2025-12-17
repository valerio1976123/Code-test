import * as React from "react";
import { toast } from "sonner";
import { api } from "../api/client";
import type { Device, Schedule, ScheduleType } from "../api/types";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";

const types: ScheduleType[] = ["run_once", "daily", "weekly", "every_n_hours"];

type NewSchedule = {
  device_id: string;
  type: ScheduleType;
  run_at?: string;
  hour?: number;
  minute?: number;
  day_of_week?: number;
  every_n_hours?: number;
  is_enabled: boolean;
};

export function SchedulesPage() {
  const [devices, setDevices] = React.useState<Device[]>([]);
  const [deviceId, setDeviceId] = React.useState<string>("");
  const [schedules, setSchedules] = React.useState<Schedule[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [form, setForm] = React.useState<NewSchedule>({
    device_id: "",
    type: "daily",
    hour: 2,
    minute: 0,
    is_enabled: true,
  });

  const loadDevices = React.useCallback(async () => {
    const res = await api.get<{ devices: Device[] }>("/devices");
    setDevices(res.data.devices);
    if (!deviceId && res.data.devices.length > 0) {
      setDeviceId(res.data.devices[0].id);
    }
  }, [deviceId]);

  const loadSchedules = React.useCallback(async () => {
    if (!deviceId) return;
    setLoading(true);
    const res = await api.get<{ schedules: Schedule[] }>("/schedules", {
      params: { deviceId },
    });
    setSchedules(res.data.schedules);
    setLoading(false);
  }, [deviceId]);

  React.useEffect(() => {
    void loadDevices();
  }, [loadDevices]);

  React.useEffect(() => {
    void loadSchedules();
    setForm((s) => ({ ...s, device_id: deviceId }));
  }, [deviceId, loadSchedules]);

  async function createSchedule() {
    if (!deviceId) return;
    const payload: Record<string, unknown> = {
      ...form,
      device_id: deviceId,
    };
    await api.post("/schedules", payload);
    toast.success("Schedule created");
    await loadSchedules();
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Create schedule</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Device</div>
              <select
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
              >
                {devices.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Type</div>
              <select
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                value={form.type}
                onChange={(e) =>
                  setForm((s) => ({ ...s, type: e.target.value as ScheduleType }))
                }
              >
                {types.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                checked={form.is_enabled}
                onChange={(e) => setForm((s) => ({ ...s, is_enabled: e.target.checked }))}
              />
              <span className="text-sm text-slate-700">Enabled</span>
            </div>

            {form.type === "run_once" ? (
              <div className="space-y-1 md:col-span-2">
                <div className="text-xs font-medium text-slate-700">Run at</div>
                <Input
                  type="datetime-local"
                  value={form.run_at ?? ""}
                  onChange={(e) => setForm((s) => ({ ...s, run_at: e.target.value }))}
                />
              </div>
            ) : null}

            {form.type === "daily" || form.type === "weekly" ? (
              <>
                <div className="space-y-1">
                  <div className="text-xs font-medium text-slate-700">Hour</div>
                  <Input
                    type="number"
                    value={form.hour ?? 0}
                    onChange={(e) =>
                      setForm((s) => ({ ...s, hour: Number(e.target.value) }))
                    }
                  />
                </div>
                <div className="space-y-1">
                  <div className="text-xs font-medium text-slate-700">Minute</div>
                  <Input
                    type="number"
                    value={form.minute ?? 0}
                    onChange={(e) =>
                      setForm((s) => ({ ...s, minute: Number(e.target.value) }))
                    }
                  />
                </div>
              </>
            ) : null}

            {form.type === "weekly" ? (
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Day of week (0-6)</div>
                <Input
                  type="number"
                  value={form.day_of_week ?? 1}
                  onChange={(e) =>
                    setForm((s) => ({ ...s, day_of_week: Number(e.target.value) }))
                  }
                />
              </div>
            ) : null}

            {form.type === "every_n_hours" ? (
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Every N hours</div>
                <Input
                  type="number"
                  value={form.every_n_hours ?? 6}
                  onChange={(e) =>
                    setForm((s) => ({ ...s, every_n_hours: Number(e.target.value) }))
                  }
                />
              </div>
            ) : null}
          </div>

          <Button onClick={() => void createSchedule()}>Create</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Schedules</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-sm text-slate-600">Loading…</div>
          ) : (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-slate-500">
                  <tr>
                    <th className="py-2">Type</th>
                    <th className="py-2">Params</th>
                    <th className="py-2">Enabled</th>
                    <th className="py-2">Next run</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {schedules.map((s) => (
                    <tr key={s.id}>
                      <td className="py-2 font-medium text-slate-900">{s.type}</td>
                      <td className="py-2 text-slate-700">
                        {s.type === "run_once"
                          ? s.run_at
                          : s.type === "daily"
                            ? `${s.hour}:${String(s.minute).padStart(2, "0")}`
                            : s.type === "weekly"
                              ? `dow=${s.day_of_week} ${s.hour}:${String(s.minute).padStart(2, "0")}`
                              : `n=${s.every_n_hours}`}
                      </td>
                      <td className="py-2">
                        <input
                          type="checkbox"
                          checked={s.is_enabled}
                          onChange={async (e) => {
                            await api.put(`/schedules/${s.id}`, {
                              ...s,
                              is_enabled: e.target.checked,
                            });
                            await loadSchedules();
                          }}
                        />
                      </td>
                      <td className="py-2 text-slate-700">
                        {s.next_run_at ? new Date(s.next_run_at).toLocaleString() : "—"}
                      </td>
                      <td className="py-2">
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={async () => {
                            if (!confirm("Delete schedule?")) return;
                            await api.delete(`/schedules/${s.id}`);
                            toast.success("Deleted");
                            await loadSchedules();
                          }}
                        >
                          Delete
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

