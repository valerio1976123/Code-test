import { Card, Grid, Group, Loader, Stack, Table, Text, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { DashboardSummary } from '../lib/types'

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null)

  useEffect(() => {
    api.get('/dashboard/summary').then((r) => setData(r.data))
  }, [])

  if (!data) return <Loader />

  return (
    <Stack>
      <Title order={2}>Dashboard</Title>

      <Grid>
        <Grid.Col span={{ base: 12, sm: 4 }}>
          <Card withBorder>
            <Text fw={700}>Devices</Text>
            <Group justify="space-between" mt="sm">
              <Text>Total</Text>
              <Text>{data.devices.total}</Text>
            </Group>
            <Group justify="space-between">
              <Text>Enabled</Text>
              <Text>{data.devices.enabled}</Text>
            </Group>
            <Group justify="space-between">
              <Text>Disabled</Text>
              <Text>{data.devices.disabled}</Text>
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 4 }}>
          <Card withBorder>
            <Text fw={700}>Executions (24h)</Text>
            <Group justify="space-between" mt="sm">
              <Text>Total</Text>
              <Text>{data.executions_last_24h.total}</Text>
            </Group>
            <Group justify="space-between">
              <Text>Success</Text>
              <Text>{data.executions_last_24h.success}</Text>
            </Group>
            <Group justify="space-between">
              <Text>Failed</Text>
              <Text>{data.executions_last_24h.failed}</Text>
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      <Card withBorder>
        <Text fw={700} mb="sm">
          Recent executions
        </Text>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>ID</Table.Th>
              <Table.Th>Device</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Created</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data.recent_executions.map((e) => (
              <Table.Tr key={e.id}>
                <Table.Td>{e.id}</Table.Td>
                <Table.Td>{e.device_id}</Table.Td>
                <Table.Td>{e.status}</Table.Td>
                <Table.Td>{new Date(e.created_at).toLocaleString()}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Card>
    </Stack>
  )
}
