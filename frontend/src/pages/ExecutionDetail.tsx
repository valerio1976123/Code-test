import * as React from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Execution } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

function apiBase(): string {
  return (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api").replace(
    /\/$/,
    "",
  );
}

export function ExecutionDetailPage() {
  const { id } = useParams();
  const [execution, setExecution] = React.useState<Execution | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (!id) return;
    void (async () => {
      setLoading(true);
      const res = await api.get<{ execution: Execution }>(`/executions/${id}`);
      setExecution(res.data.execution);
      setLoading(false);
    })();
  }, [id]);

  if (loading && !execution) {
    return <div className="text-sm text-slate-600">Loading…</div>;
  }

  if (!execution) {
    return <div className="text-sm text-slate-600">Not found</div>;
  }

  const downloadUrl = `${apiBase()}/executions/${execution.id}/download`;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Execution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex items-center gap-2">
          <StatusBadge status={execution.status} />
          <div className="text-slate-900 font-medium">
            {execution.device?.name ?? execution.device_id}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          <div>
            <div className="text-xs text-slate-500">Created at</div>
            <div>{new Date(execution.created_at).toLocaleString()}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Output path</div>
            <div className="truncate">{execution.output_path ?? "—"}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Start</div>
            <div>{execution.start_time ? new Date(execution.start_time).toLocaleString() : "—"}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">End</div>
            <div>{execution.end_time ? new Date(execution.end_time).toLocaleString() : "—"}</div>
          </div>
        </div>

        {execution.error_message ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-red-700">
            {execution.error_message}
          </div>
        ) : null}

        <div className="flex gap-2">
          <Button
            onClick={() => {
              window.open(downloadUrl, "_blank", "noopener,noreferrer");
            }}
            disabled={!execution.output_path}
          >
            Download
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

