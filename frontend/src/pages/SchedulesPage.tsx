import { Button, Card, Group, Loader, Modal, Select, Stack, Switch, Table, Text, TextInput, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import type { Device, Schedule } from '../lib/types'

type ScheduleForm = {
  name: string
  device_id: number
  schedule_type: 'run_once' | 'daily' | 'weekly' | 'every_n_hours'
  run_once_at?: string | null
  time_of_day?: string | null
  weekdays?: string | null
  every_n_hours?: number | null
  is_enabled: boolean
}

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[] | null>(null)
  const [devices, setDevices] = useState<Device[] | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Schedule | null>(null)
  const [form, setForm] = useState<ScheduleForm>({
    name: '',
    device_id: 0,
    schedule_type: 'daily',
    time_of_day: '02:00:00',
    weekdays: '0,1,2,3,4',
    every_n_hours: 6,
    run_once_at: null,
    is_enabled: true,
  })

  async function load() {
    const [dRes, sRes] = await Promise.all([api.get<Device[]>('/devices'), api.get<Schedule[]>('/schedules')])
    setDevices(dRes.data)
    setSchedules(sRes.data)
  }

  useEffect(() => {
    load()
  }, [])

  const deviceOptions = useMemo(() => (devices || []).map((d) => ({ value: String(d.id), label: `${d.name} (${d.host})` })), [devices])

  if (!schedules || !devices) return <Loader />

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Schedules</Title>
        <Button
          onClick={() => {
            setEditing(null)
            setForm({
              name: '',
              device_id: devices[0]?.id || 0,
              schedule_type: 'daily',
              time_of_day: '02:00:00',
              weekdays: '0,1,2,3,4',
              every_n_hours: 6,
              run_once_at: null,
              is_enabled: true,
            })
            setModalOpen(true)
          }}
        >
          New schedule
        </Button>
      </Group>

      <Card withBorder>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Device</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>Enabled</Table.Th>
              <Table.Th>Next run</Table.Th>
              <Table.Th></Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {schedules.map((s) => (
              <Table.Tr key={s.id}>
                <Table.Td>{s.name}</Table.Td>
                <Table.Td>{s.device_id}</Table.Td>
                <Table.Td>{s.schedule_type}</Table.Td>
                <Table.Td>{s.is_enabled ? 'Yes' : 'No'}</Table.Td>
                <Table.Td>{s.next_run_at ? new Date(s.next_run_at).toLocaleString() : '-'}</Table.Td>
                <Table.Td>
                  <Group gap="xs" justify="flex-end">
                    <Button
                      size="xs"
                      onClick={() => {
                        setEditing(s)
                        setForm({
                          name: s.name,
                          device_id: s.device_id,
                          schedule_type: s.schedule_type,
                          run_once_at: s.run_once_at || null,
                          time_of_day: s.time_of_day || null,
                          weekdays: s.weekdays || null,
                          every_n_hours: s.every_n_hours || null,
                          is_enabled: s.is_enabled,
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
                        if (!confirm(`Delete schedule ${s.name}?`)) return
                        await api.delete(`/schedules/${s.id}`)
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
        {schedules.length === 0 && <Text c="dimmed" mt="sm">No schedules.</Text>}
      </Card>

      <Modal opened={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit schedule' : 'New schedule'} size="lg">
        <Stack>
          <TextInput label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.currentTarget.value })} />
          <Select
            label="Device"
            data={deviceOptions}
            value={String(form.device_id)}
            onChange={(v) => setForm({ ...form, device_id: Number(v || 0) })}
          />
          <Select
            label="Type"
            data={[
              { value: 'run_once', label: 'Run once' },
              { value: 'daily', label: 'Daily' },
              { value: 'weekly', label: 'Weekly' },
              { value: 'every_n_hours', label: 'Every N hours' },
            ]}
            value={form.schedule_type}
            onChange={(v) => setForm({ ...form, schedule_type: (v as any) || 'daily' })}
          />

          {form.schedule_type === 'run_once' && (
            <TextInput
              label="Run once at (UTC ISO)"
              placeholder="2025-12-17T10:00:00"
              value={form.run_once_at || ''}
              onChange={(e) => setForm({ ...form, run_once_at: e.currentTarget.value })}
            />
          )}

          {(form.schedule_type === 'daily' || form.schedule_type === 'weekly') && (
            <TextInput
              label="Time of day (HH:MM:SS UTC)"
              value={form.time_of_day || ''}
              onChange={(e) => setForm({ ...form, time_of_day: e.currentTarget.value })}
            />
          )}

          {form.schedule_type === 'weekly' && (
            <TextInput
              label="Weekdays CSV (0=Mon .. 6=Sun)"
              value={form.weekdays || ''}
              onChange={(e) => setForm({ ...form, weekdays: e.currentTarget.value })}
            />
          )}

          {form.schedule_type === 'every_n_hours' && (
            <TextInput
              label="Every N hours"
              type="number"
              value={String(form.every_n_hours || 0)}
              onChange={(e) => setForm({ ...form, every_n_hours: Number(e.currentTarget.value || 0) })}
            />
          )}

          <Switch label="Enabled" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.currentTarget.checked })} />

          <Group justify="flex-end">
            <Button
              onClick={async () => {
                try {
                  const payload: any = { ...form }

                  // server expects time type for time_of_day; send as "HH:MM:SS"
                  if (payload.time_of_day === '') payload.time_of_day = null
                  if (payload.weekdays === '') payload.weekdays = null
                  if (payload.run_once_at === '') payload.run_once_at = null

                  if (editing) {
                    await api.put(`/schedules/${editing.id}`, payload)
                    notifications.show({ color: 'green', message: 'Updated' })
                  } else {
                    await api.post('/schedules', payload)
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
