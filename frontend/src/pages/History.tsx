import * as React from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Execution } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";

export function HistoryPage() {
  const [executions, setExecutions] = React.useState<Execution[]>([]);
  const [status, setStatus] = React.useState("");
  const [deviceId, setDeviceId] = React.useState("");
  const [from, setFrom] = React.useState("");
  const [to, setTo] = React.useState("");
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    const res = await api.get<{ executions: Execution[] }>("/executions", {
      params: {
        status: status || undefined,
        deviceId: deviceId || undefined,
        from: from || undefined,
        to: to || undefined,
      },
    });
    setExecutions(res.data.executions);
    setLoading(false);
  }, [status, deviceId, from, to]);

  React.useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Status</div>
              <select
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="">All</option>
                <option value="queued">queued</option>
                <option value="running">running</option>
                <option value="success">success</option>
                <option value="failed">failed</option>
              </select>
            </div>
            <div className="space-y-1 md:col-span-2">
              <div className="text-xs font-medium text-slate-700">Device ID</div>
              <Input value={deviceId} onChange={(e) => setDeviceId(e.target.value)} />
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">From</div>
              <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">To</div>
              <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
            </div>
          </div>

          <div className="mt-3">
            <Button variant="secondary" onClick={() => void load()}>
              Apply
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Executions</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-sm text-slate-600">Loading…</div>
          ) : (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-slate-500">
                  <tr>
                    <th className="py-2">When</th>
                    <th className="py-2">Device</th>
                    <th className="py-2">Status</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {executions.map((e) => (
                    <tr key={e.id}>
                      <td className="py-2 text-slate-700">
                        {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
                      </td>
                      <td className="py-2 text-slate-900">
                        {e.device?.name ?? e.device_id}
                      </td>
                      <td className="py-2">
                        <StatusBadge status={e.status} />
                      </td>
                      <td className="py-2">
                        <Link
                          to={`/executions/${e.id}`}
                          className="text-sm font-medium text-slate-900 hover:underline"
                        >
                          Details
                        </Link>
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

