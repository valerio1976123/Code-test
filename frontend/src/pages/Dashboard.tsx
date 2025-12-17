import * as React from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Device, Execution } from "../api/types";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { StatusBadge } from "../components/StatusBadge";

type DashboardSummary = {
  summary: {
    total_devices: number;
    enabled_devices: number;
    backups_24h: number;
    failed_24h: number;
  };
  devices: Array<
    Pick<Device, "id" | "name" | "vendor" | "is_enabled" | "next_run_at"> & {
      last_execution: Device["last_execution"] extends infer T ? T : null;
    }
  >;
  recent_executions: Array<
    Pick<
      Execution,
      | "id"
      | "status"
      | "start_time"
      | "end_time"
      | "created_at"
      | "error_message"
      | "output_path"
    > & { device: Execution["device"] }
  >;
};

export function DashboardPage() {
  const [data, setData] = React.useState<DashboardSummary | null>(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    const res = await api.get<DashboardSummary>("/dashboard/summary");
    setData(res.data);
    setLoading(false);
  }, []);

  React.useEffect(() => {
    void load();
    const t = window.setInterval(() => void load(), 12_000);
    return () => window.clearInterval(t);
  }, [load]);

  if (loading && !data) {
    return <div className="text-sm text-slate-600">Loading…</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Total devices</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {data?.summary.total_devices ?? 0}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Enabled</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {data?.summary.enabled_devices ?? 0}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Backups (24h)</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {data?.summary.backups_24h ?? 0}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Failed (24h)</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-red-600">
            {data?.summary.failed_24h ?? 0}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Devices</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-slate-500">
                <tr>
                  <th className="py-2">Name</th>
                  <th className="py-2">Vendor</th>
                  <th className="py-2">Enabled</th>
                  <th className="py-2">Last backup</th>
                  <th className="py-2">Next run</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.devices.map((d) => (
                  <tr key={d.id}>
                    <td className="py-2 font-medium text-slate-900">{d.name}</td>
                    <td className="py-2 text-slate-700">{d.vendor}</td>
                    <td className="py-2 text-slate-700">
                      {d.is_enabled ? "yes" : "no"}
                    </td>
                    <td className="py-2">
                      {d.last_execution ? (
                        <div className="flex items-center gap-2">
                          <StatusBadge status={d.last_execution.status} />
                          <span className="text-xs text-slate-500">
                            {d.last_execution.created_at
                              ? new Date(d.last_execution.created_at).toLocaleString()
                              : ""}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-2 text-slate-700">
                      {d.next_run_at ? new Date(d.next_run_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent executions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data?.recent_executions.map((e) => (
              <div
                key={e.id}
                className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={e.status} />
                    <Link
                      to={`/executions/${e.id}`}
                      className="truncate text-sm font-medium text-slate-900 hover:underline"
                    >
                      {e.device?.name ?? "unknown device"}
                    </Link>
                    <span className="text-xs text-slate-500">
                      {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
                    </span>
                  </div>
                  {e.error_message ? (
                    <div className="truncate text-xs text-red-600">
                      {e.error_message}
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

