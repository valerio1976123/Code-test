import { Badge } from "./ui/badge";
import type { ExecutionStatus } from "../api/types";

export function StatusBadge({ status }: { status: ExecutionStatus }) {
  const variant =
    status === "success"
      ? "success"
      : status === "failed"
        ? "destructive"
        : status === "running"
          ? "warning"
          : "muted";

  return <Badge variant={variant}>{status}</Badge>;
}

