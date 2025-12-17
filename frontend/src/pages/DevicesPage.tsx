import {
  Button,
  Card,
  Group,
  Loader,
  Modal,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import type { Device } from '../lib/types'

type DeviceForm = {
  name: string
  host: string
  port: number
  vendor: string
  username: string
  password?: string
  enable_secret?: string
  passphrase?: string
  is_enabled: boolean
  command_profile_json?: string
}

const vendorOptions = [
  { value: 'cisco_ios', label: 'Cisco IOS/NX-OS' },
  { value: 'panos', label: 'Palo Alto (PAN-OS)' },
  { value: 'fortigate', label: 'FortiGate' },
  { value: 'mikrotik', label: 'MikroTik' },
  { value: 'generic', label: 'Generic' },
]

export default function DevicesPage() {
  const [items, setItems] = useState<Device[] | null>(null)
  const [q, setQ] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Device | null>(null)
  const [form, setForm] = useState<DeviceForm>({
    name: '',
    host: '',
    port: 22,
    vendor: 'generic',
    username: 'admin',
    is_enabled: false,
    command_profile_json: '',
  })

  async function load() {
    const res = await api.get<Device[]>('/devices', { params: q ? { q } : undefined })
    setItems(res.data)
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    if (!items) return null
    const s = q.trim().toLowerCase()
    if (!s) return items
    return items.filter((d) => d.name.toLowerCase().includes(s) || d.host.toLowerCase().includes(s))
  }, [items, q])

  if (!filtered) return <Loader />

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Devices</Title>
        <Button
          onClick={() => {
            setEditing(null)
            setForm({ name: '', host: '', port: 22, vendor: 'generic', username: 'admin', is_enabled: false, command_profile_json: '' })
            setModalOpen(true)
          }}
        >
          New device
        </Button>
      </Group>

      <Card withBorder>
        <Group>
          <TextInput placeholder="Search (name/host)" value={q} onChange={(e) => setQ(e.currentTarget.value)} flex={1} />
          <Button variant="light" onClick={() => load()}>
            Refresh
          </Button>
        </Group>
      </Card>

      <Card withBorder>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Host</Table.Th>
              <Table.Th>Vendor</Table.Th>
              <Table.Th>Enabled</Table.Th>
              <Table.Th></Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {filtered.map((d) => (
              <Table.Tr key={d.id}>
                <Table.Td>{d.name}</Table.Td>
                <Table.Td>
                  {d.host}:{d.port}
                </Table.Td>
                <Table.Td>{d.vendor}</Table.Td>
                <Table.Td>{d.is_enabled ? 'Yes' : 'No'}</Table.Td>
                <Table.Td>
                  <Group gap="xs" justify="flex-end">
                    <Button
                      size="xs"
                      variant="light"
                      onClick={async () => {
                        try {
                          const res = await api.post<{ execution_id: number }>(`/devices/${d.id}/run-now`)
                          notifications.show({ color: 'green', message: `Queued execution #${res.data.execution_id}` })
                        } catch (e: any) {
                          notifications.show({ color: 'red', message: e?.response?.data?.detail || 'Run now failed' })
                        }
                      }}
                    >
                      Run now
                    </Button>
                    <Button
                      size="xs"
                      onClick={() => {
                        setEditing(d)
                        setForm({
                          name: d.name,
                          host: d.host,
                          port: d.port,
                          vendor: d.vendor,
                          username: d.username,
                          is_enabled: d.is_enabled,
                          command_profile_json: d.command_profile_json || '',
                        })
                        setModalOpen(true)
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      size="xs"
                      color="red"
                      variant="light"
                      onClick={async () => {
                        if (!confirm(`Delete device ${d.name}?`)) return
                        await api.delete(`/devices/${d.id}`)
                        notifications.show({ color: 'green', message: 'Deleted' })
                        load()
                      }}
                    >
                      Delete
                    </Button>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {filtered.length === 0 && <Text c="dimmed" mt="sm">No devices.</Text>}
      </Card>

      <Modal opened={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit device' : 'New device'} size="lg">
        <Stack>
          <TextInput label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.currentTarget.value })} />
          <Group grow>
            <TextInput label="Host" value={form.host} onChange={(e) => setForm({ ...form, host: e.currentTarget.value })} />
            <TextInput
              label="Port"
              type="number"
              value={String(form.port)}
              onChange={(e) => setForm({ ...form, port: Number(e.currentTarget.value || 22) })}
            />
          </Group>
          <Group grow>
            <Select label="Vendor" data={vendorOptions} value={form.vendor} onChange={(v) => setForm({ ...form, vendor: v || 'generic' })} />
            <TextInput label="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.currentTarget.value })} />
          </Group>

          <Group grow>
            <TextInput label="Password (optional)" value={form.password || ''} onChange={(e) => setForm({ ...form, password: e.currentTarget.value })} />
            <TextInput
              label="Enable secret (optional)"
              value={form.enable_secret || ''}
              onChange={(e) => setForm({ ...form, enable_secret: e.currentTarget.value })}
            />
          </Group>
          <TextInput
            label="Passphrase (optional)"
            value={form.passphrase || ''}
            onChange={(e) => setForm({ ...form, passphrase: e.currentTarget.value })}
          />

          <Textarea
            label="Generic command profile JSON (optional)"
            description='Example: {"commands": ["show version", "show running-config"]}'
            value={form.command_profile_json || ''}
            onChange={(e) => setForm({ ...form, command_profile_json: e.currentTarget.value })}
            autosize
            minRows={3}
          />

          <Switch label="Enabled" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.currentTarget.checked })} />

          <Group justify="flex-end">
            <Button
              onClick={async () => {
                try {
                  if (editing) {
                    await api.put(`/devices/${editing.id}`, form)
                    notifications.show({ color: 'green', message: 'Updated' })
                  } else {
                    await api.post('/devices', form)
                    notifications.show({ color: 'green', message: 'Created' })
                  }
                  setModalOpen(false)
                  load()
                } catch (e: any) {
                  notifications.show({ color: 'red', message: e?.response?.data?.detail || 'Save failed' })
                }
              }}
            >
              Save
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
