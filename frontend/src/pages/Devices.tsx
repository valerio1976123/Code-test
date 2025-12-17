import * as React from "react";
import { toast } from "sonner";
import { api } from "../api/client";
import type { AuthType, Device, Vendor } from "../api/types";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";

const vendors: Vendor[] = [
  "cisco_ios",
  "cisco_nxos",
  "paloalto_panos",
  "fortigate",
  "mikrotik",
  "generic",
];

type DeviceUpsert = {
  name: string;
  vendor: Vendor;
  host: string;
  port: number;
  username: string;
  auth_type: AuthType;
  password?: string;
  private_key_path?: string;
  key_passphrase?: string;
  enable_secret?: string;
  is_enabled: boolean;
};

const empty: DeviceUpsert = {
  name: "",
  vendor: "cisco_ios",
  host: "",
  port: 22,
  username: "",
  auth_type: "password",
  password: "",
  private_key_path: "keys/device.key",
  key_passphrase: "",
  enable_secret: "",
  is_enabled: true,
};

export function DevicesPage() {
  const [devices, setDevices] = React.useState<Device[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [search, setSearch] = React.useState("");
  const [vendor, setVendor] = React.useState<string>("");
  const [selected, setSelected] = React.useState<Device | null>(null);
  const [createForm, setCreateForm] = React.useState<DeviceUpsert>(empty);
  const [editForm, setEditForm] = React.useState<DeviceUpsert>(empty);

  const load = React.useCallback(async () => {
    setLoading(true);
    const res = await api.get<{ devices: Device[] }>("/devices", {
      params: { search: search || undefined, vendor: vendor || undefined },
    });
    setDevices(res.data.devices);
    setLoading(false);
  }, [search, vendor]);

  React.useEffect(() => {
    void load();
  }, [load]);

  React.useEffect(() => {
    if (!selected) return;
    setEditForm({
      name: selected.name,
      vendor: selected.vendor,
      host: selected.host,
      port: selected.port,
      username: selected.username,
      auth_type: selected.auth_type,
      password: "",
      private_key_path: selected.private_key_path ?? "keys/device.key",
      key_passphrase: "",
      enable_secret: "",
      is_enabled: selected.is_enabled,
    });
  }, [selected]);

  async function createDevice() {
    const payload: Record<string, unknown> = { ...createForm };
    if (createForm.auth_type === "password" && !createForm.password) {
      toast.error("Password required for password auth");
      return;
    }
    if (createForm.auth_type === "key" && !createForm.private_key_path) {
      toast.error("Private key path required for key auth");
      return;
    }
    await api.post("/devices", payload);
    toast.success("Device created");
    setCreateForm(empty);
    await load();
  }

  async function updateDevice() {
    if (!selected) return;
    const payload: Record<string, unknown> = { ...editForm };
    if (!editForm.password) delete payload.password; // don't overwrite unless provided
    await api.put(`/devices/${selected.id}`, payload);
    toast.success("Device updated");
    await load();
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Create device</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Name</div>
              <Input
                value={createForm.name}
                onChange={(e) =>
                  setCreateForm((s) => ({ ...s, name: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Vendor</div>
              <select
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                value={createForm.vendor}
                onChange={(e) =>
                  setCreateForm((s) => ({ ...s, vendor: e.target.value as Vendor }))
                }
              >
                {vendors.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Host</div>
              <Input
                value={createForm.host}
                onChange={(e) =>
                  setCreateForm((s) => ({ ...s, host: e.target.value }))
                }
              />
            </div>

            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Port</div>
              <Input
                type="number"
                value={createForm.port}
                onChange={(e) =>
                  setCreateForm((s) => ({ ...s, port: Number(e.target.value) }))
                }
              />
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Username</div>
              <Input
                value={createForm.username}
                onChange={(e) =>
                  setCreateForm((s) => ({ ...s, username: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Auth type</div>
              <select
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                value={createForm.auth_type}
                onChange={(e) =>
                  setCreateForm((s) => ({
                    ...s,
                    auth_type: e.target.value as AuthType,
                  }))
                }
              >
                <option value="password">password</option>
                <option value="key">key</option>
              </select>
            </div>

            {createForm.auth_type === "password" ? (
              <div className="space-y-1 md:col-span-2">
                <div className="text-xs font-medium text-slate-700">Password</div>
                <Input
                  type="password"
                  value={createForm.password ?? ""}
                  onChange={(e) =>
                    setCreateForm((s) => ({ ...s, password: e.target.value }))
                  }
                />
              </div>
            ) : (
              <div className="space-y-1 md:col-span-2">
                <div className="text-xs font-medium text-slate-700">
                  Private key path (storage/app/...)
                </div>
                <Input
                  value={createForm.private_key_path ?? ""}
                  onChange={(e) =>
                    setCreateForm((s) => ({
                      ...s,
                      private_key_path: e.target.value,
                    }))
                  }
                />
              </div>
            )}

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={createForm.is_enabled}
                onChange={(e) =>
                  setCreateForm((s) => ({ ...s, is_enabled: e.target.checked }))
                }
              />
              <span className="text-sm text-slate-700">Enabled</span>
            </div>

            <div className="md:col-span-3">
              <Button onClick={() => void createDevice()}>Create</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Devices</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center">
            <Input
              placeholder="Search…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm"
              value={vendor}
              onChange={(e) => setVendor(e.target.value)}
            >
              <option value="">All vendors</option>
              {vendors.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
            <Button variant="secondary" onClick={() => void load()}>
              Refresh
            </Button>
          </div>

          {loading ? (
            <div className="text-sm text-slate-600">Loading…</div>
          ) : (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-slate-500">
                  <tr>
                    <th className="py-2">Name</th>
                    <th className="py-2">Vendor</th>
                    <th className="py-2">Host</th>
                    <th className="py-2">Enabled</th>
                    <th className="py-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {devices.map((d) => (
                    <tr key={d.id}>
                      <td className="py-2 font-medium text-slate-900">{d.name}</td>
                      <td className="py-2 text-slate-700">{d.vendor}</td>
                      <td className="py-2 text-slate-700">
                        {d.host}:{d.port}
                      </td>
                      <td className="py-2 text-slate-700">
                        <input
                          type="checkbox"
                          checked={d.is_enabled}
                          onChange={async (e) => {
                            await api.put(`/devices/${d.id}`, {
                              ...d,
                              is_enabled: e.target.checked,
                            });
                            await load();
                          }}
                        />
                      </td>
                      <td className="py-2">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => setSelected(d)}
                          >
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            onClick={async () => {
                              await api.post(`/devices/${d.id}/run-now`);
                              toast.success("Backup queued");
                            }}
                            disabled={!d.is_enabled}
                          >
                            Run now
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={async () => {
                              if (!confirm(`Delete ${d.name}?`)) return;
                              await api.delete(`/devices/${d.id}`);
                              toast.success("Deleted");
                              await load();
                            }}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {selected ? (
        <Card>
          <CardHeader>
            <CardTitle>Edit: {selected.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Name</div>
                <Input
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm((s) => ({ ...s, name: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Vendor</div>
                <select
                  className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                  value={editForm.vendor}
                  onChange={(e) =>
                    setEditForm((s) => ({ ...s, vendor: e.target.value as Vendor }))
                  }
                >
                  {vendors.map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Host</div>
                <Input
                  value={editForm.host}
                  onChange={(e) =>
                    setEditForm((s) => ({ ...s, host: e.target.value }))
                  }
                />
              </div>

              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Port</div>
                <Input
                  type="number"
                  value={editForm.port}
                  onChange={(e) =>
                    setEditForm((s) => ({ ...s, port: Number(e.target.value) }))
                  }
                />
              </div>
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Username</div>
                <Input
                  value={editForm.username}
                  onChange={(e) =>
                    setEditForm((s) => ({ ...s, username: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-700">Auth type</div>
                <select
                  className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                  value={editForm.auth_type}
                  onChange={(e) =>
                    setEditForm((s) => ({
                      ...s,
                      auth_type: e.target.value as AuthType,
                    }))
                  }
                >
                  <option value="password">password</option>
                  <option value="key">key</option>
                </select>
              </div>

              {editForm.auth_type === "password" ? (
                <div className="space-y-1 md:col-span-2">
                  <div className="text-xs font-medium text-slate-700">
                    Password (leave blank to keep)
                  </div>
                  <Input
                    type="password"
                    value={editForm.password ?? ""}
                    onChange={(e) =>
                      setEditForm((s) => ({ ...s, password: e.target.value }))
                    }
                  />
                </div>
              ) : (
                <div className="space-y-1 md:col-span-2">
                  <div className="text-xs font-medium text-slate-700">
                    Private key path (storage/app/...)
                  </div>
                  <Input
                    value={editForm.private_key_path ?? ""}
                    onChange={(e) =>
                      setEditForm((s) => ({
                        ...s,
                        private_key_path: e.target.value,
                      }))
                    }
                  />
                </div>
              )}

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={editForm.is_enabled}
                  onChange={(e) =>
                    setEditForm((s) => ({ ...s, is_enabled: e.target.checked }))
                  }
                />
                <span className="text-sm text-slate-700">Enabled</span>
              </div>

              <div className="flex gap-2 md:col-span-3">
                <Button onClick={() => void updateDevice()}>Save</Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSelected(null);
                  }}
                >
                  Close
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

