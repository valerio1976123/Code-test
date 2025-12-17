import { Button, Card, Group, Loader, Select, Stack, Table, Text, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import type { Device, Execution } from '../lib/types'

export default function HistoryPage() {
  const [items, setItems] = useState<Execution[] | null>(null)
  const [devices, setDevices] = useState<Device[] | null>(null)

  const [status, setStatus] = useState<string | null>(null)
  const [deviceId, setDeviceId] = useState<string | null>(null)

  async function load() {
    const [dRes, eRes] = await Promise.all([
      api.get<Device[]>('/devices'),
      api.get<Execution[]>('/executions', {
        params: {
          status: status || undefined,
          device_id: deviceId ? Number(deviceId) : undefined,
          limit: 200,
        },
      }),
    ])
    setDevices(dRes.data)
    setItems(eRes.data)
  }

  useEffect(() => {
    load()
  }, [])

  const deviceOptions = useMemo(() => (devices || []).map((d) => ({ value: String(d.id), label: d.name })), [devices])

  if (!items || !devices) return <Loader />

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>History</Title>
        <Button variant="light" onClick={() => load()}>
          Refresh
        </Button>
      </Group>

      <Card withBorder>
        <Group align="end">
          <Select label="Device" data={deviceOptions} value={deviceId} onChange={setDeviceId} clearable searchable />
          <Select
            label="Status"
            data={[
              { value: 'queued', label: 'queued' },
              { value: 'running', label: 'running' },
              { value: 'success', label: 'success' },
              { value: 'failed', label: 'failed' },
            ]}
            value={status}
            onChange={setStatus}
            clearable
          />
          <Button onClick={() => load()}>Apply</Button>
        </Group>
      </Card>

      <Card withBorder>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>ID</Table.Th>
              <Table.Th>Device</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th>Error</Table.Th>
              <Table.Th></Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {items.map((e) => (
              <Table.Tr key={e.id}>
                <Table.Td>{e.id}</Table.Td>
                <Table.Td>{e.device_id}</Table.Td>
                <Table.Td>{e.status}</Table.Td>
                <Table.Td>{new Date(e.created_at).toLocaleString()}</Table.Td>
                <Table.Td>
                  <Text size="xs" c={e.error_message ? 'red' : 'dimmed'} lineClamp={1}>
                    {e.error_message || '-'}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Group justify="flex-end" gap="xs">
                    <Button
                      size="xs"
                      variant="light"
                      disabled={!e.output_path}
                      onClick={async () => {
                        try {
                          const res = await api.get(`/executions/${e.id}/download`, { responseType: 'blob' })
                          const blob = new Blob([res.data], { type: 'text/plain' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `execution_${e.id}.txt`
                          document.body.appendChild(a)
                          a.click()
                          a.remove()
                          URL.revokeObjectURL(url)
                        } catch (err: any) {
                          notifications.show({ color: 'red', message: err?.response?.data?.detail || 'Download failed' })
                        }
                      }}
                    >
                      Download
                    </Button>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {items.length === 0 && <Text c="dimmed" mt="sm">No executions.</Text>}
      </Card>
    </Stack>
  )
}
